from typing import Callable, Dict, Tuple
import unicodedata

from config import GLYC, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD, NEWS2_TRI_M, ORD
from clinical.vitaux import si
from clinical.french_v12 import get_protocol

TriageResult = Tuple[str, str, str]
Handler = Callable[..., TriageResult]


def _norm(value) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def _has(items, label: str) -> bool:
    labels = {_norm(x) for x in (items or [])}
    return _norm(label) in labels


def _truthy(det: dict, *keys: str) -> bool:
    nd = {_norm(k): v for k, v in (det or {}).items()}
    return any(bool(nd.get(_norm(k))) for k in keys)


def _value(det: dict, key: str, default=None):
    nd = {_norm(k): v for k, v in (det or {}).items()}
    return nd.get(_norm(key), default)


def _more_urgent(a: TriageResult, b: TriageResult) -> TriageResult:
    return a if ORD.get(a[0], 99) <= ORD.get(b[0], 99) else b


def _selected_french_result(motif: str, det: dict) -> TriageResult | None:
    level = _value(det, "french_level")
    if not level:
        return None
    level = str(level)
    protocol = get_protocol(motif) or {}
    criterion = _value(det, "french_criterion", "") or protocol.get("motif", motif)
    return level, f"FRENCH v1.2 - {criterion}", "FRENCH v1.2"


def _triage_acr(**_) -> TriageResult:
    return "1", "ACR confirme - RCP immediate", "FRENCH Tri 1"


def _triage_hypotension(pas, fc, **_) -> TriageResult:
    if pas <= 70:
        return "1", f"PAS {pas} mmHg <= 70 - collapsus", "FRENCH Tri 1"
    if pas <= 90 or (pas <= 100 and fc > 100):
        return "2", f"PAS {pas} mmHg - choc debutant", "FRENCH Tri 2"
    if pas <= 100:
        return "3B", f"PAS {pas} mmHg - valeur limite", "FRENCH Tri 3B"
    return "4", "PAS normale", "FRENCH Tri 4"


def _triage_sca(fc, spo2, det, **_) -> TriageResult:
    ecg = _value(det, "ecg", "Normal")
    doul = _value(det, "douleur", "Atypique")
    if ecg == "Anormal typique SCA" or "typique" in _norm(doul):
        return "1", "SCA - ECG anormal ou douleur typique", "FRENCH Tri 1"
    if _truthy(det, "douleur_intense", "douleur persistante"):
        return "2", "Douleur thoracique intense ou persistante", "FRENCH Tri 2"
    if fc >= 120 or spo2 < 94:
        return "2", "Douleur thoracique instable", "FRENCH Tri 2"
    if _value(det, "frcv", 0) >= 2:
        return "2", "Douleur coronaire probable avec facteurs de risque", "FRENCH Tri 2"
    return "3A", "Douleur thoracique stable", "FRENCH Tri 3A"


def _triage_arythmie(fc, det, **_) -> TriageResult:
    if fc >= 180 or fc <= 30:
        return "1", f"FC {fc} bpm - arythmie extreme", "FRENCH Tri 1"
    if fc >= 150 or fc <= 40:
        return "2", f"FC {fc} bpm - arythmie severe", "FRENCH Tri 2"
    if _truthy(det, "tol_mal", "mauvaise tolerance", "syncope", "douleur"):
        return "2", "Arythmie mal toleree", "FRENCH Tri 2"
    return "3B", f"FC {fc} bpm - arythmie toleree", "FRENCH Tri 3B"


def _triage_hta(pas, fc, det, **_) -> TriageResult:
    if pas >= 220:
        return "2", f"PAS {pas} mmHg >= 220 - urgence hypertensive", "FRENCH Tri 2"
    if _truthy(det, "sf", "neuro", "douleur thoracique", "dyspnee") or (pas >= 180 and fc > 100):
        return "2", "HTA avec signes fonctionnels", "FRENCH Tri 2"
    if pas >= 180:
        return "3B", "HTA severe sans signe fonctionnel", "FRENCH Tri 3B"
    return "4", "HTA moderee", "FRENCH Tri 4"


def _triage_anaphylaxie(spo2, pas, gcs, det, **_) -> TriageResult:
    if spo2 < 94 or pas < 90 or gcs < 15:
        return "1", "Anaphylaxie severe - engagement systemique", "FRENCH Tri 1"
    if _truthy(det, "dyspnee", "urticaire", "oedeme", "vomissements"):
        return "2", "Allergie systemique", "FRENCH Tri 2"
    return "3B", "Reaction allergique localisee", "FRENCH Tri 3B"


def _triage_dyspnee(spo2, fr, det, **_) -> TriageResult:
    bpco = _truthy(det, "bpco")
    cible = 92 if bpco else 95
    seuil_crit = 88 if bpco else 91
    if spo2 < seuil_crit or fr >= 40:
        return "1", f"Detresse respiratoire SpO2 {spo2}% FR {fr}/min", "FRENCH Tri 1"
    if spo2 < cible or fr >= 30 or _truthy(det, "parole impossible", "mots isoles"):
        return "2", f"Dyspnee severe SpO2 {spo2}%", "FRENCH Tri 2"
    if _truthy(det, "orthopnee", "tirage", "cyanose"):
        return "2", "Orthopnee, tirage ou cyanose", "FRENCH Tri 2"
    return "3B", f"Dyspnee moderee SpO2 {spo2}%", "FRENCH Tri 3B"


def _triage_abdomen(fc, pas, det, **_) -> TriageResult:
    shock = si(fc, pas)
    if pas < 90 or shock >= 1.0:
        return "2", f"Douleur abdominale avec choc (SI {shock})", "FRENCH Tri 2"
    if _truthy(det, "grossesse", "geu"):
        return "2", "Douleur abdominale sur grossesse - GEU a exclure", "FRENCH Tri 2"
    if _truthy(det, "defense", "contracture"):
        return "2", "Abdomen chirurgical", "FRENCH Tri 2"
    if _truthy(det, "tol_mal", "vomissements incoercibles"):
        return "3A", "Douleur abdominale mal toleree", "FRENCH Tri 3A"
    return "3B", "Douleur abdominale toleree", "FRENCH Tri 3B"


def _triage_digestif(fc, pas, det, **_) -> TriageResult:
    shock = si(fc, pas)
    if pas < 90 or shock >= 1.0 or _truthy(det, "deshydratation severe"):
        return "2", f"Trouble digestif avec signe de gravite (SI {shock})", "FRENCH Tri 2"
    if _truthy(det, "vomissements incoercibles", "sang", "douleur intense"):
        return "3A", "Vomissements/diarrhee mal toleres", "FRENCH Tri 3A"
    return "4", "Vomissements/diarrhee bien toleres", "FRENCH Tri 4"


def _triage_hemo_digestive(fc, pas, det, **_) -> TriageResult:
    shock = si(fc, pas)
    if pas < 90 or shock >= 1.0 or _truthy(det, "malaise", "syncope"):
        return "1", f"Hemorragie digestive instable (SI {shock})", "FRENCH Tri 1"
    if fc >= 110 or _truthy(det, "abondant", "melena"):
        return "2", "Hemorragie digestive probable", "FRENCH Tri 2"
    return "3A", "Saignement digestif stable", "FRENCH Tri 3A"


def _triage_colique(pas, gcs, det, **_) -> TriageResult:
    if gcs < 15 or pas < 90:
        return "2", "Douleur lombaire avec alteration clinique", "FRENCH Tri 2"
    if _truthy(det, "fievre", "anurie", "rein unique", "grossesse"):
        return "2", "Colique nephretique compliquee", "FRENCH Tri 2"
    if _truthy(det, "eva forte", "vomissements"):
        return "3A", "Colique nephretique mal toleree", "FRENCH Tri 3A"
    return "3B", "Colique nephretique stable", "FRENCH Tri 3B"


def _triage_avc(gcs, det, **_) -> TriageResult:
    delai = _value(det, "delai", 99)
    try:
        delai = float(delai)
    except (TypeError, ValueError):
        delai = 99
    if delai <= 4.5:
        return "1", f"AVC {delai:g} h - fenetre thrombolyse", "FRENCH Tri 1"
    if delai <= 24:
        return "2", f"AVC {delai:g} h - filiere neurovasculaire urgente", "FRENCH Tri 2"
    if _truthy(det, "def_prog", "deficit progressif") or gcs < 15:
        return "2", "Deficit progressif ou alteration GCS", "FRENCH Tri 2"
    return "2", "Deficit neurologique - bilan urgent", "FRENCH Tri 2"


def _triage_tc(gcs, det, **_) -> TriageResult:
    if gcs <= 8:
        return "1", f"TC grave - GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 12 or _truthy(det, "aod", "anticoagulant", "convulsion", "vomissements repetes", "otorragie"):
        return "2", f"TC GCS {gcs}/15 ou critere TDM urgent", "FRENCH Tri 2"
    if _truthy(det, "pdc", "perte de connaissance"):
        return "3A", "TC avec perte de connaissance", "FRENCH Tri 3A"
    return "4", "TC benin", "FRENCH Tri 4"


def _triage_coma(gcs, gl, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Hypoglycemie {gl} mg/dl - glucose IV", "FRENCH Tri 2"
    if gcs <= 8:
        return "1", f"Coma profond - GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 13:
        return "2", f"Alteration de conscience - GCS {gcs}/15", "FRENCH Tri 2"
    return "2", "Alteration de conscience", "FRENCH Tri 2"


def _triage_cephalee(det, **_) -> TriageResult:
    if _truthy(det, "brutal", "foudroyante"):
        return "1", "Cephalee foudroyante - HSA suspectee", "FRENCH Tri 1"
    if _truthy(det, "nuque", "fievre", "deficit", "confusion"):
        return "2", "Cephalee avec signe de gravite", "FRENCH Tri 2"
    return "3B", "Cephalee sans signe de gravite", "FRENCH Tri 3B"


def _triage_convulsions(det, gcs, **_) -> TriageResult:
    if _truthy(det, "en_cours", "multi", "etat de mal"):
        return "2", "Crise en cours, multiple ou EME", "FRENCH Tri 2"
    if _truthy(det, "tc", "traumatisme cranien"):
        return "2", "Convulsion apres traumatisme cranien", "FRENCH Tri 2"
    if _truthy(det, "confusion", "conf") or gcs < 15:
        return "2", "Confusion post-critique persistante", "FRENCH Tri 2"
    return "3B", "Convulsion recuperee", "FRENCH Tri 3B"


def _triage_confusion(gcs, temp, det, **_) -> TriageResult:
    if gcs <= 13:
        return "2", f"Syndrome confusionnel avec GCS {gcs}/15", "FRENCH Tri 2"
    if temp >= 38.5 or _truthy(det, "brutal", "agitation"):
        return "2", "Confusion aigue avec facteur de gravite", "FRENCH Tri 2"
    return "3A", "Syndrome confusionnel stable", "FRENCH Tri 3A"


def _triage_malaise(n2, gl, det, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Malaise hypoglycemique {gl} mg/dl", "FRENCH Tri 2"
    if n2 >= 2 or _truthy(det, "anom_vit", "douleur thoracique", "syncope effort"):
        return "2", "Malaise avec anomalie vitale ou signe d'alerte", "FRENCH Tri 2"
    return "3B", "Malaise recupere", "FRENCH Tri 3B"


def _triage_trauma_axial(fc, pas, spo2, det, **_) -> TriageResult:
    if _truthy(det, "penetrant", "pen") or _norm(_value(det, "cin", "")) == "haute":
        return "1", "Traumatisme penetrant ou haute cinetique", "FRENCH Tri 1"
    if si(fc, pas) >= 1.0 or spo2 < 94:
        return "2", f"Traumatisme avec signe de choc SI {si(fc, pas)}", "FRENCH Tri 2"
    return "2", "Traumatisme axial - evaluation urgente", "FRENCH Tri 2"


def _triage_trauma_distal(det, **_) -> TriageResult:
    if _truthy(det, "isch", "ischemie"):
        return "1", "Ischemie distale", "FRENCH Tri 1"
    if _truthy(det, "impotence", "imp") and _truthy(det, "deformation", "deform"):
        return "2", "Fracture deplacee avec impotence totale", "FRENCH Tri 2"
    if _truthy(det, "impotence", "imp", "deformation", "deform"):
        return "3A", "Traumatisme distal avec impotence ou deformation", "FRENCH Tri 3A"
    return "4", "Traumatisme distal modere", "FRENCH Tri 4"


def _triage_hemorragie(fc, pas, det, **_) -> TriageResult:
    shock = si(fc, pas)
    if pas < 90 or shock >= 1.0 or _truthy(det, "massive", "incontrolable"):
        return "1", f"Hemorragie active instable (SI {shock})", "FRENCH Tri 1"
    if fc >= 110 or _truthy(det, "anticoagulant", "aod"):
        return "2", "Hemorragie active stable mais a risque", "FRENCH Tri 2"
    return "3A", "Hemorragie active controlee", "FRENCH Tri 3A"


def _triage_fievre(fc, pas, temp, det, **_) -> TriageResult:
    if _truthy(det, "purpura", "neff"):
        return "1", "Fievre + purpura - ceftriaxone immediate", "FRENCH Tri 1"
    if temp >= 40 or temp <= 35.2 or _truthy(det, "confusion", "conf"):
        return "2", f"Fievre avec critere de gravite (T {temp} C)", "FRENCH Tri 2"
    if _truthy(det, "tol_mal") or pas < 100 or si(fc, pas) >= 1.0:
        return "3B", "Fievre mal toleree", "FRENCH Tri 3B"
    return "5", "Fievre bien toleree", "FRENCH Tri 5"


def _triage_ped_fievre_nourr(temp, age, **_) -> TriageResult:
    if age <= 0.25 and temp >= 38.0:
        return "2", "Nourrisson <= 3 mois febrile", "FRENCH Pediatrie Tri 2"
    return "3A", "Nourrisson avec suspicion infectieuse", "FRENCH Pediatrie Tri 3A"


def _triage_ped_fievre(fc, temp, age, det, **_) -> TriageResult:
    if _truthy(det, "purpura", "neff"):
        return "1", "Fievre pediatrique + purpura", "FRENCH Pediatrie Tri 1"
    if temp >= 40 or _truthy(det, "somnolence", "geignement", "marbrures"):
        return "2", "Fievre enfant avec signe de gravite", "FRENCH Pediatrie Tri 2"
    if fc >= _fc_tachy_ped(age):
        return "3A", "Fievre enfant avec tachycardie", "FRENCH Pediatrie Tri 3A"
    return "4", "Fievre enfant bien toleree", "FRENCH Pediatrie Tri 4"


def _fc_tachy_ped(age) -> int:
    if age < 1 / 12:
        return 160
    if age < 1:
        return 150
    if age < 5:
        return 140
    return 120


def _triage_ped_gastro(fc, pas, age, det, **_) -> TriageResult:
    if _truthy(det, "deshydratation severe", "lethargie", "sang"):
        return "2", "Gastro-enterite pediatrique avec signe de gravite", "FRENCH Pediatrie Tri 2"
    if _value(det, "vomissements_h", 0) >= 6 or fc >= _fc_tachy_ped(age):
        return "3A", "Vomissements frequents ou tachycardie", "FRENCH Pediatrie Tri 3A"
    if pas < 70 + 2 * max(age, 1):
        return "2", "Suspicion choc pediatrique", "FRENCH Pediatrie Tri 2"
    return "4", "Gastro-enterite pediatrique toleree", "FRENCH Pediatrie Tri 4"


def _triage_ped_epilepsie(gcs, det, **_) -> TriageResult:
    if _truthy(det, "en_cours", "etat de mal") or gcs < 15:
        return "2", "Crise epileptique pediatrique active ou non recuperee", "FRENCH Pediatrie Tri 2"
    if _truthy(det, "premiere crise", "fievre"):
        return "3A", "Crise pediatrique a evaluer", "FRENCH Pediatrie Tri 3A"
    return "3B", "Crise pediatrique recuperee", "FRENCH Pediatrie Tri 3B"


def _triage_ped_asthme(spo2, fr, det, **_) -> TriageResult:
    if spo2 < 92 or fr >= 40 or _truthy(det, "silence auscultatoire", "epuisement"):
        return "1", "Asthme pediatrique severe", "FRENCH Pediatrie Tri 1"
    if spo2 < 95 or _truthy(det, "tirage", "parole impossible"):
        return "2", "Asthme pediatrique avec detresse", "FRENCH Pediatrie Tri 2"
    return "3A", "Bronchospasme pediatrique modere", "FRENCH Pediatrie Tri 3A"


def _triage_purpura(temp, det, **_) -> TriageResult:
    if _truthy(det, "purpura", "neff", "non effacable"):
        return "1", "Purpura non effacable - ceftriaxone immediate", "SPILF/SFP"
    if temp >= 38.0:
        return "2", "Purpura febrile - suspicion fulminans", "FRENCH Tri 2"
    return "3B", "Petechies - bilan hemostase", "FRENCH Tri 3B"


def _triage_erytheme(temp, det, **_) -> TriageResult:
    if temp >= 38.5 or _truthy(det, "extension rapide", "necrose", "douleur intense"):
        return "2", "Erytheme etendu avec signe de gravite", "FRENCH Tri 2"
    return "3B", "Erytheme etendu stable", "FRENCH Tri 3B"


def _triage_accouchement(det, **_) -> TriageResult:
    if _truthy(det, "poussee", "tete visible", "contractions rapprochees"):
        return "1", "Accouchement imminent", "FRENCH Tri 1"
    return "2", "Travail obstetrical probable", "FRENCH Tri 2"


def _triage_grossesse(det, pas, **_) -> TriageResult:
    if pas < 90 or _truthy(det, "douleur intense", "saignement abondant", "syncope"):
        return "2", "Complication de grossesse avec signe de gravite", "FRENCH Tri 2"
    return "3A", "Complication de grossesse stable", "FRENCH Tri 3A"


def _triage_metrorragie(fc, pas, det, **_) -> TriageResult:
    shock = si(fc, pas)
    if pas < 90 or shock >= 1.0 or _truthy(det, "abondant", "grossesse"):
        return "2", "Saignement gynecologique a risque", "FRENCH Tri 2"
    return "3A", "Metrorragie stable", "FRENCH Tri 3A"


def _triage_hypoglycemie(gcs, gl, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Hypoglycemie severe {gl} mg/dl - glucose IV", "FRENCH Tri 2"
    if gcs < 15:
        return "2", f"Hypoglycemie avec alteration GCS {gcs}/15", "FRENCH Tri 2"
    return "3B", "Hypoglycemie legere - resucrage oral", "FRENCH Tri 3B"


def _triage_hyperglycemie(gcs, det, gl=None, **_) -> TriageResult:
    if _truthy(det, "ceto", "dyspnee de kussmaul") or gcs < 15:
        return "2", "Cetoacidose ou alteration de conscience", "FRENCH Tri 2"
    if gl and gl >= GLYC["Hs2"]:
        return "3A", f"Hyperglycemie severe {gl} mg/dl", "FRENCH Tri 3A"
    return "4", "Hyperglycemie toleree", "FRENCH Tri 4"


def _triage_non_urgent(**_) -> TriageResult:
    return "5", "Consultation non urgente", "FRENCH Tri 5"


_TRIAGE_DISPATCH: Dict[str, Handler] = {
    "Arret cardio-respiratoire": _triage_acr,
    "Hypotension arterielle": _triage_hypotension,
    "Douleur thoracique / SCA": _triage_sca,
    "Tachycardie / tachyarythmie": _triage_arythmie,
    "Bradycardie / bradyarythmie": _triage_arythmie,
    "Palpitations": _triage_arythmie,
    "Hypertension arterielle": _triage_hta,
    "Allergie / anaphylaxie": _triage_anaphylaxie,
    "Dyspnee / insuffisance respiratoire": _triage_dyspnee,
    "Dyspnee / insuffisance cardiaque": _triage_dyspnee,
    "Douleur abdominale": _triage_abdomen,
    "Vomissements / Diarrhee": _triage_digestif,
    "Hematemese / Rectorragie": _triage_hemo_digestive,
    "Colique nephretique / Douleur lombaire": _triage_colique,
    "AVC / Deficit neurologique": _triage_avc,
    "Traumatisme cranien": _triage_tc,
    "Alteration de conscience / Coma": _triage_coma,
    "Cephalee": _triage_cephalee,
    "Convulsions / EME": _triage_convulsions,
    "Syndrome confusionnel": _triage_confusion,
    "Malaise": _triage_malaise,
    "Traumatisme thorax/abdomen/rachis cervical": _triage_trauma_axial,
    "Traumatisme bassin/hanche/femur": _triage_trauma_axial,
    "Traumatisme membre / epaule": _triage_trauma_distal,
    "Hemorragie active": _triage_hemorragie,
    "Fievre": _triage_fievre,
    "Pediatrie - Fievre <= 3 mois": _triage_ped_fievre_nourr,
    "Pediatrie - Fievre enfant (3 mois - 15 ans)": _triage_ped_fievre,
    "Pediatrie - Vomissements / Gastro-enterite": _triage_ped_gastro,
    "Pediatrie - Crise epileptique": _triage_ped_epilepsie,
    "Pediatrie - Asthme / Bronchospasme": _triage_ped_asthme,
    "Petechie / Purpura": _triage_purpura,
    "Erytheme etendu": _triage_erytheme,
    "Accouchement imminent": _triage_accouchement,
    "Complication grossesse T1/T2": _triage_grossesse,
    "Menorragie / Metrorragie": _triage_metrorragie,
    "Hypoglycemie": _triage_hypoglycemie,
    "Hyperglycemie / Cetoacidose": _triage_hyperglycemie,
    "Renouvellement ordonnance": _triage_non_urgent,
    "Examen administratif": _triage_non_urgent,
    "Autre motif": _triage_non_urgent,
}

_MOTIF_INDEX: Dict[str, Handler] = {_norm(k): v for k, v in _TRIAGE_DISPATCH.items()}


def french_triage(motif, det, fc, pas, spo2, fr, gcs, temp, age, n2, gl=None) -> TriageResult:
    fc = fc or 80
    pas = pas or 120
    spo2 = spo2 or 98
    fr = fr or 16
    gcs = gcs or 15
    temp = temp or 37.0
    age = age if age is not None else 45
    n2 = n2 or 0
    det = det or {}

    try:
        if n2 >= NEWS2_TRI_M:
            return "M", f"NEWS2 {n2} >= {NEWS2_TRI_M} - engagement vital", "NEWS2 Tri M"
        if _truthy(det, "purpura", "neff", "non effacable"):
            return "1", "Purpura non effacable - ceftriaxone immediate", "SPILF/SFP"
        if pas <= 70 or gcs <= 8:
            return "1", "Critere vital majeur", "Triage transversal"

        selected = _selected_french_result(motif, det)
        protocol = get_protocol(motif)
        handler = _MOTIF_INDEX.get(_norm(motif))
        if selected:
            result = selected
        elif handler:
            result = handler(
                motif=motif, det=det, fc=fc, pas=pas, spo2=spo2, fr=fr,
                gcs=gcs, temp=temp, age=age, n2=n2, gl=gl,
            )
        elif protocol:
            result = (
                protocol["default"],
                f"FRENCH v1.2 - niveau par defaut - {protocol['motif']}",
                "FRENCH v1.2",
            )
        else:
            result = "3B", f"Evaluation standard - {motif}", "FRENCH Tri 3B"

        if n2 >= NEWS2_RISQUE_ELEVE:
            result = _more_urgent(result, ("2", f"NEWS2 {n2} >= {NEWS2_RISQUE_ELEVE} - risque eleve", "NEWS2 Tri 2"))
        elif n2 >= NEWS2_RISQUE_MOD:
            result = _more_urgent(result, ("3A", f"NEWS2 {n2} >= {NEWS2_RISQUE_MOD} - risque modere", "NEWS2 Tri 3A"))

        if spo2 < 90 or fr >= 35 or fc >= 150 or fc <= 40 or pas <= 90:
            result = _more_urgent(result, ("2", "Anomalie vitale transversale", "Triage transversal"))
        if gl and gl < GLYC["hs"]:
            result = _more_urgent(result, ("2", f"Hypoglycemie severe {gl} mg/dl", "Triage transversal"))

        return result
    except Exception as e:
        return "2", f"Erreur moteur de triage : {e}", "Securite Tri 2"


def verifier_coherence(fc, pas, spo2, fr, gcs, temp, eva, motif, atcd, det, n2, gl=None):
    danger, alertes = [], []
    atcd = atcd or []
    det = det or {}

    if _has(atcd, "IMAO (inhibiteurs MAO)"):
        danger.append("IMAO - Tramadol contre-indique (syndrome serotoninergique)")
    if _has(atcd, "Antidepresseurs ISRS/IRSNA"):
        alertes.append("ISRS/IRSNA - Tramadol deconseille - preferer Dipidolor ou Morphine")
    if gl:
        if gl < GLYC["hs"]:
            danger.append(f"Hypoglycemie severe {gl} mg/dl - glucose IV")
        elif gl < GLYC["hm"]:
            alertes.append(f"Hypoglycemie moderee {gl} mg/dl - corriger avant antalgique")
        elif gl >= GLYC["Hs2"]:
            alertes.append(f"Hyperglycemie severe {gl} mg/dl")

    shock = si(fc, pas)
    if shock >= 1.0:
        danger.append(f"Shock Index {shock} >= 1.0 - etat de choc probable")
    if spo2 < 90:
        danger.append(f"SpO2 {spo2}% - oxygene et avis medical urgent")
    if fr >= 30:
        alertes.append(f"FR {fr}/min - tachypnee")
    if fc >= 150 or fc <= 40:
        danger.append(f"FC {fc} bpm - arythmie critique")
    if gcs < 15:
        alertes.append(f"GCS {gcs}/15 - alteration neurologique")
    if temp >= 40 or temp <= 35:
        alertes.append(f"Temperature {temp} C - anomalie thermique severe")
    if eva >= 7:
        alertes.append(f"EVA {eva}/10 - antalgie rapide a prioriser")
    if _has(atcd, "Anticoagulants/AOD") and "traumatisme cranien" in _norm(motif):
        danger.append("TC sous AOD/AVK - TDM urgente")
    if _truthy(det, "purpura", "neff", "non effacable"):
        danger.append("Purpura non effacable - ceftriaxone immediate")
    if n2 >= NEWS2_RISQUE_ELEVE:
        danger.append(f"NEWS2 {n2} - appel medical immediat")
    elif n2 >= NEWS2_RISQUE_MOD:
        alertes.append(f"NEWS2 {n2} - surveillance rapprochee")

    return danger, alertes
