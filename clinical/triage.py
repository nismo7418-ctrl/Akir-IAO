# clinical/triage.py — Moteur FRENCH V1.1 — Arbres de Décision
# AKIR-IAO v19.0 — Système Expert Grade Hospitalier
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
#
# ARCHITECTURE
#   Niveau 0 : Priorités Absolues (verrouillage immédiat Tri 1 / Tri M)
#   Niveau 1 : Arbre de Décision par motif (handler spécialisé)
#   Niveau 2 : Ajustement NEWS2 (never downgrade)
#   Niveau 3 : Fallback sécurisé Tri 3B
#
# Références :
#   Taboulet P. et al. FRENCH Triage SFMU V1.1. Juin 2018.
#   ILAE 2015 — Singer/JAMA 2016 — ESC 2023 — BCFI Belgique

from __future__ import annotations
from typing import Optional, Callable, Dict, Tuple
from config import (
    NEWS2_TRI_M, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD,
    GLYC, AVC_DELAI_THROMBOLYSE_H,
    EME_SEUIL_MIN, EME_OPERATIONNEL_MIN, EME_ETABLI_MIN,
    FIEVRE_TRES_HAUTE_ENFANT, FIEVRE_NOURR_SEUIL,
    FC_TACHY_NOURR, FC_TACHY_BEBE, FC_TACHY_ENFANT, FC_TACHY_GRAND,
    SIPA_0_1AN, SIPA_1_4ANS, SIPA_4_7ANS, SIPA_7_12ANS,
)

TriageResult = Tuple[str, str, str]   # (niveau, justification, référence)
Handler      = Callable[..., TriageResult]

# Ordre de sévérité des niveaux FRENCH
_ORD: Dict[str, int] = {"M":0,"1":1,"2":2,"3A":3,"3B":4,"4":5,"5":6}


def _norm(s: str) -> str:
    """Normalise un motif pour lookup insensible à la casse."""
    import unicodedata
    return unicodedata.normalize("NFD", s.lower()).encode("ascii","ignore").decode()


def _more_urgent(a: TriageResult, b: TriageResult) -> TriageResult:
    """Retourne le résultat le plus urgent des deux (jamais downgrade)."""
    return a if _ORD.get(a[0], 9) <= _ORD.get(b[0], 9) else b


def _truthy(d: dict, *keys) -> bool:
    """Retourne True si l'une des clés est truthy dans le dict."""
    return any(d.get(k) for k in keys)


# ═══════════════════════════════════════════════════════════════════════════════
# PRIORITÉS ABSOLUES — Niveau 0 — Verrouillage immédiat
# Ces critères court-circuitent TOUT le reste du moteur.
# ═══════════════════════════════════════════════════════════════════════════════

_CRITERES_ABSOLUS_M = [
    # (clé_dans_det, description_alerte)
    ("acr",               "ACR confirmé — RCP en cours"),
    ("arret_respiratoire","Arrêt respiratoire — ventilation immédiate"),
]

_CRITERES_ABSOLUS_1 = [
    ("purpura",           "Purpura non effaçable — Ceftriaxone 2 g IV IMMÉDIAT"),
    ("neff",              "Purpura non effaçable — Ceftriaxone 2 g IV IMMÉDIAT"),
    ("torsion_testiculaire","Torsion testiculaire — Chirurgie dans les 6 h"),
    ("cephalee_foudroyante","Céphalée foudroyante — HSA suspectée — TDM urgent"),
    ("bilieux",           "Vomissements bilieux — Occlusion / volvulus — Chirurgie urgente"),
    ("eme_etabli",        f"EME établi > {EME_ETABLI_MIN} min — Réanimation pédiatrique"),
    ("ischémie_distale",  "Ischémie distale — Urgence vasculaire"),
    ("otorragie",         "Otorragie — Fracture base du crâne suspectée"),
    ("ecg_stemi",         "Sus-décalage ST — SCA STEMI — Filière cathlab"),
    ("dissection_aortique","Dissection aortique suspectée — Angio-TDM urgent"),
]


def _check_priorites_absolues(
    det: dict, gcs: int, pas: float, spo2: float, fr: float
) -> Optional[TriageResult]:
    """
    Vérifie les critères de verrouillage absolu.
    Retourne un TriageResult si verrouillé, None sinon.
    Cet ordre est délibéré et cliniquement validé.
    """
    # Tri M — engagement vital immédiat
    for key, msg in _CRITERES_ABSOLUS_M:
        if det.get(key):
            return "M", msg, "FRENCH Tri M — Priorité absolue"
    if gcs <= 3:
        return "M", "GCS 3 — Coma profond — Engagement vital", "FRENCH Tri M"
    if spo2 < 70 or fr >= 50:
        return "M", f"SpO2 {spo2:.0f} % ou FR {fr:.0f}/min — Détresse respiratoire extrême", "FRENCH Tri M"

    # Tri 1 — urgence extrême
    for key, msg in _CRITERES_ABSOLUS_1:
        if det.get(key):
            return "1", msg, "FRENCH Tri 1 — Priorité absolue"
    if pas <= 60:
        return "1", f"PAS {pas:.0f} mmHg ≤ 60 — Collapsus vasculaire", "FRENCH Tri 1"
    if gcs <= 8:
        return "1", f"GCS {gcs}/15 — Altération sévère de la conscience", "FRENCH Tri 1"
    if spo2 < 82:
        return "1", f"SpO2 {spo2:.0f} % — Hypoxémie sévère — O2 urgent", "FRENCH Tri 1"

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# ARBRES DE DÉCISION — Niveau 1
# Chaque handler reçoit l'intégralité du contexte patient.
# ═══════════════════════════════════════════════════════════════════════════════

def _h_acr(**_) -> TriageResult:
    return "M", "ACR — RCP en cours", "FRENCH Tri M"


def _h_hypotension(pas, fc, det, **_) -> TriageResult:
    sh = round(fc / max(pas, 1), 2)
    if pas <= 70 or sh >= 1.2:
        return "1", f"PAS {pas:.0f} mmHg — Shock Index {sh} — Choc sévère", "FRENCH Tri 1"
    if pas <= 90 or sh >= 1.0 or (pas <= 100 and fc > 110):
        return "2", f"PAS {pas:.0f} mmHg — SI {sh} — Choc débutant", "FRENCH Tri 2"
    if pas <= 100:
        return "3B", f"PAS {pas:.0f} mmHg — Hypotension orthostatique probable", "FRENCH Tri 3B"
    return "4", "Tension dans les normes", "FRENCH Tri 4"


def _h_sca(fc, spo2, det, **_) -> TriageResult:
    """
    Arbre de décision SCA — 4 niveaux basés sur ECG + caractère douleur + FRCV.
    Le score HEART > 6 force le Tri 1.
    """
    ecg   = det.get("ecg", "Normal")
    doul  = det.get("douleur_type", "Atypique")
    frcv  = det.get("frcv", 0)
    trop  = det.get("troponine_positive", False) or det.get("trop", False)
    heart = det.get("heart_score", 0)
    stemi = ecg in ("Anormal typique SCA", "Sus-décalage ST / STEMI")

    if stemi or heart >= 7:
        return "1", f"ECG STEMI ou HEART {heart} — Filière cathlab", "FRENCH Tri 1"
    if ecg == "Anormal non typique" or doul == "Typique (constrictive, irradiante)" or trop:
        return "2", "ECG anormal ou douleur typique ou troponine +" , "FRENCH Tri 2"
    if frcv >= 3 or det.get("coronaropathie_connue") or heart >= 4:
        return "3A", f"{frcv} FRCV — Probabilité coronaire à évaluer", "FRENCH Tri 3A"
    if doul == "Coronaire probable" or heart >= 2:
        return "3B", "Douleur thoracique atypique — Bilan", "FRENCH Tri 3B"
    return "4", "Douleur atypique sans critère de gravité", "FRENCH Tri 4"


def _h_arythmie(fc, det, **_) -> TriageResult:
    if fc >= 200 or fc <= 25:
        return "1", f"FC {fc} bpm — Arythmie extrême", "FRENCH Tri 1"
    if fc >= 150 or fc <= 35:
        return "2", f"FC {fc} bpm — Arythmie sévère", "FRENCH Tri 2"
    if det.get("mauvaise_tolerance") or det.get("syncope") or det.get("douleur_thora"):
        return "2", "Arythmie mal tolérée", "FRENCH Tri 2"
    if fc >= 130 or fc <= 45:
        return "3A", f"FC {fc} bpm — Surveillance rapprochée", "FRENCH Tri 3A"
    return "3B", f"FC {fc} bpm — Arythmie tolérée", "FRENCH Tri 3B"


def _h_hta(pas, det, **_) -> TriageResult:
    sf = det.get("sf_associes", False)
    if pas >= 220 or (pas >= 180 and sf):
        return "2", f"PAS {pas:.0f} mmHg — Urgence hypertensive", "FRENCH Tri 2"
    if pas >= 180:
        return "3B", f"PAS {pas:.0f} mmHg — HTA sévère sans signe fonctionnel", "FRENCH Tri 3B"
    return "4", f"PAS {pas:.0f} mmHg — HTA modérée", "FRENCH Tri 4"


def _h_anaphylaxie(spo2, pas, gcs, det, **_) -> TriageResult:
    if spo2 < 94 or pas < 90 or gcs < 15 or det.get("stridor"):
        return "1", "Anaphylaxie sévère — Adrénaline IM — Engagement systémique", "FRENCH Tri 1"
    if det.get("dyspnee") or det.get("urticaire_gen"):
        return "2", "Anaphylaxie — Réaction systémique", "FRENCH Tri 2"
    return "3B", "Réaction allergique localisée", "FRENCH Tri 3B"


def _h_avc(gcs, det, **_) -> TriageResult:
    """Arbre AVC — délai thrombolyse comme critère pivot."""
    delai = det.get("delai_heures", 99)
    def_ = det.get("deficit_moteur") or det.get("aphasie") or det.get("deficit_sensitif")
    if delai <= AVC_DELAI_THROMBOLYSE_H and def_:
        return "1", f"AVC à {delai} h — Fenêtre thrombolyse — Filière Stroke IMMÉDIATE", "FRENCH Tri 1"
    if det.get("deficit_progressif") or gcs < 15:
        return "2", "Déficit progressif ou GCS < 15", "FRENCH Tri 2"
    if def_:
        return "2", "Déficit neurologique — Bilan urgent", "FRENCH Tri 2"
    return "2", "Déficit neurologique — Évaluation urgente", "FRENCH Tri 2"


def _h_tc(gcs, det, **_) -> TriageResult:
    """Arbre TC — Règle Canadienne et facteurs de risque."""
    if gcs <= 8:
        return "1", f"TC grave — GCS {gcs}/15", "FRENCH Tri 1"
    # Facteurs haut risque règle canadienne
    hr = (gcs < 15 or det.get("vomissements_rep") or
          det.get("suspicion_skull") or det.get("age_gte65_tc"))
    if hr or det.get("aod") or det.get("convulsion_post") or det.get("otorragie"):
        return "2", "TC — Critère TDM urgent (règle canadienne / AOD)", "FRENCH Tri 2"
    if gcs <= 12 or det.get("pdc"):
        return "3A", f"TC — GCS {gcs}/15 ou PDC", "FRENCH Tri 3A"
    return "4", "TC bénin — Pas de critère d'imagerie", "FRENCH Tri 4"


def _h_coma(gcs, gl, det, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Coma hypoglycémique {gl:.0f} mg/dl — Glucose 30 % IV", "FRENCH Tri 2"
    if gcs <= 8:
        return "1", f"Coma — GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 12:
        return "2", f"Altération de conscience — GCS {gcs}/15", "FRENCH Tri 2"
    return "2", "Altération légère de conscience — Évaluation urgente", "FRENCH Tri 2"


def _h_convulsions(det, gl, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Convulsions + hypoglycémie {gl:.0f} mg/dl — Cause curable", "FRENCH Tri 2"
    if det.get("crises_multiples") or det.get("en_cours"):
        return "2", "EME ou crises multiples — Benzodiazépines", "FRENCH Tri 2"
    if det.get("confusion_post") or det.get("deficit_focal"):
        return "2", "Confusion post-critique ou déficit focal", "FRENCH Tri 2"
    return "3B", "Convulsion récupérée sans critère de gravité", "FRENCH Tri 3B"


def _h_cephalee(det, **_) -> TriageResult:
    """Arbre céphalée — céphalée foudroyante = HSA jusqu'à preuve du contraire."""
    if det.get("brutale") or det.get("cephalee_foudroyante"):
        return "1", "Céphalée foudroyante — HSA suspectée — TDM urgent", "FRENCH Tri 1"
    if det.get("nuque") or det.get("fievre_assoc") or det.get("deficit_neuro"):
        return "2", "Céphalée avec signes méningés ou déficit", "FRENCH Tri 2"
    if det.get("inhabituelle") or det.get("premiere_episode"):
        return "3A", "Céphalée inhabituelle — 1er épisode — Bilan", "FRENCH Tri 3A"
    return "3B", "Céphalée habituelle sans signe de gravité", "FRENCH Tri 3B"


def _h_dyspnee(spo2, fr, det, **_) -> TriageResult:
    bpco = det.get("bpco", False)
    s_min = 88 if bpco else 91
    s_cib = 92 if bpco else 95
    if spo2 < s_min or fr >= 40 or det.get("silence_auscultatoire"):
        return "1", f"Détresse respiratoire — SpO2 {spo2:.0f} % FR {fr:.0f}/min", "FRENCH Tri 1"
    if spo2 < s_cib or fr >= 30:
        return "2", f"Dyspnée sévère — SpO2 {spo2:.0f} %", "FRENCH Tri 2"
    if not det.get("parole_ok", True) or det.get("orthopnee") or det.get("tirage"):
        return "2", "Dyspnée à la parole / orthopnée / tirage", "FRENCH Tri 2"
    return "3B", f"Dyspnée modérée tolérée — SpO2 {spo2:.0f} %", "FRENCH Tri 3B"


def _h_abdomen(fc, pas, det, **_) -> TriageResult:
    sh = round(fc / max(pas, 1), 2)
    if sh >= 1.0 or pas < 90 or det.get("contracture"):
        return "2", f"Abdomen chirurgical — SI {sh} ou contracture", "FRENCH Tri 2"
    if det.get("grossesse") or det.get("geu"):
        return "2", "Douleur abdominale sur grossesse — GEU à éliminer", "FRENCH Tri 2"
    if det.get("defense") or det.get("mauvaise_tolerance"):
        return "3A", "Défense abdominale ou douleur sévère", "FRENCH Tri 3A"
    if det.get("regressive"):
        return "4", "Douleur abdominale régressive", "FRENCH Tri 4"
    return "3B", "Douleur abdominale tolérée", "FRENCH Tri 3B"


def _h_colique(fc, pas, det, **_) -> TriageResult:
    if det.get("fievre") and det.get("douleur_lombaire"):
        return "1", "Colique + fièvre — Pyélonéphrite obstructive — Chirurgie urgente", "FRENCH Tri 1"
    if det.get("anurie") or pas < 90:
        return "2", "Colique + anurie ou hypotension", "FRENCH Tri 2"
    if det.get("intense") or det.get("mauvaise_tolerance"):
        return "2", "Colique mal tolérée — Antalgie IV urgente", "FRENCH Tri 2"
    return "3A", "Colique tolérée — Antalgie orale + imagerie", "FRENCH Tri 3A"


def _h_fievre(fc, pas, temp, det, **_) -> TriageResult:
    if det.get("purpura"):
        return "1", "Fièvre + purpura — Ceftriaxone 2 g IV IMMÉDIAT", "FRENCH Tri 1"
    if temp >= 40 or temp <= 35.2 or det.get("confusion"):
        return "2", f"Fièvre {temp:.1f} °C avec critère de gravité", "FRENCH Tri 2"
    if round(fc / max(pas, 1), 2) >= 1.0 or det.get("hypotension_fiev"):
        return "2", "Fièvre avec instabilité hémodynamique", "FRENCH Tri 2"
    if det.get("mauvaise_tolerance"):
        return "3B", "Fièvre mal tolérée", "FRENCH Tri 3B"
    return "5", "Fièvre bien tolérée", "FRENCH Tri 5"


def _h_hemorragie(fc, pas, det, **_) -> TriageResult:
    sh = round(fc / max(pas, 1), 2)
    if sh >= 1.0 or pas < 90:
        return "1", f"Choc hémorragique — SI {sh} — Acide tranexamique < 3 h", "CRASH-2 / FRENCH Tri 1"
    if det.get("hemoptysie_mas") or det.get("hematemese") or det.get("abondante_active"):
        return "2", "Hémorragie digestive / respiratoire haute active", "FRENCH Tri 2"
    if sh >= 0.8:
        return "2", f"Hémorragie — SI {sh} — Instabilité débutante", "FRENCH Tri 2"
    return "3A", "Hémorragie active tolérée — Surveillance rapprochée", "FRENCH Tri 3A"


def _h_trauma_axial(fc, pas, spo2, det, **_) -> TriageResult:
    if det.get("penetrant") or det.get("cinetique") == "Haute":
        return "1", "Traumatisme pénétrant ou haute cinétique — Déchocage", "FRENCH Tri 1"
    sh = round(fc / max(pas, 1), 2)
    if sh >= 1.0 or spo2 < 94:
        return "2", f"Traumatisme axial — Choc (SI {sh})", "FRENCH Tri 2"
    if det.get("mauvaise_tolerance"):
        return "3A", "Traumatisme axial — Mauvaise tolérance", "FRENCH Tri 3A"
    return "3B", "Traumatisme axial — Basse cinétique", "FRENCH Tri 3B"


def _h_trauma_distal(det, **_) -> TriageResult:
    if det.get("ischemie") or det.get("ischémie_distale"):
        return "1", "Ischémie distale — Urgence vasculaire", "FRENCH Tri 1"
    if det.get("impotence_totale") and det.get("deformation"):
        return "2", "Fracture déplacée avec impotence totale", "FRENCH Tri 2"
    if det.get("impotence_totale"):
        return "3A", "Impotence fonctionnelle totale", "FRENCH Tri 3A"
    if det.get("deformation") or det.get("cinetique") == "Haute":
        return "3A", "Déformation visible ou haute cinétique", "FRENCH Tri 3A"
    return "4", "Traumatisme distal modéré", "FRENCH Tri 4"


def _h_hypoglycemie(gcs, gl, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Hypoglycémie sévère {gl:.0f} mg/dl — Glucose 30 % IV", "FRENCH Tri 2"
    if gcs < 15:
        return "2", f"Hypoglycémie avec altération GCS {gcs}/15", "FRENCH Tri 2"
    if gl and gl < GLYC["hm"]:
        return "3B", f"Hypoglycémie modérée {gl:.0f} mg/dl — Resucrage oral", "FRENCH Tri 3B"
    return "3B", "Hypoglycémie légère — Resucrage oral", "FRENCH Tri 3B"


def _h_hyperglycemie(gcs, det, **_) -> TriageResult:
    if det.get("cetose_positive") or gcs < 15:
        return "2", "Acidocétose ou altération de conscience", "FRENCH Tri 2"
    return "4", "Hyperglycémie tolérée sans cétose", "FRENCH Tri 4"


def _h_purpura(temp, det, **_) -> TriageResult:
    if det.get("neff") or det.get("non_effacable"):
        return "1", "Purpura NON effaçable — Ceftriaxone 2 g IV IMMÉDIAT", "SPILF/SFP 2017"
    if temp >= 38.0:
        return "2", "Purpura fébrile — Suspicion fulminans", "FRENCH Tri 2"
    return "3B", "Pétéchies — Bilan hémostase", "FRENCH Tri 3B"


def _h_malaise(n2, gl, det, **_) -> TriageResult:
    if gl and gl < GLYC["hs"]:
        return "2", f"Malaise hypoglycémique {gl:.0f} mg/dl", "FRENCH Tri 2"
    if n2 >= 2 or det.get("anomalie_vitaux"):
        return "2", "Malaise avec anomalie vitale", "FRENCH Tri 2"
    return "3B", "Malaise récupéré", "FRENCH Tri 3B"


# ─── Pédiatrie ────────────────────────────────────────────────────────────────

def _h_ped_fievre_nourr(**_) -> TriageResult:
    return "2", "Fièvre nourrisson ≤ 3 mois — TRI 2 SYSTÉMATIQUE", "FRENCH Pédiatrie Tri 2"


def _h_ped_fievre(fc, spo2, temp, age, det, **_) -> TriageResult:
    if age < 1/12:   fc_s = FC_TACHY_NOURR
    elif age < 1:    fc_s = FC_TACHY_BEBE
    elif age < 5:    fc_s = FC_TACHY_ENFANT
    else:            fc_s = FC_TACHY_GRAND
    tachy = fc > fc_s
    if det.get("purpura") and temp >= 38.0:
        return "1", "Fièvre + purpura — Méningococcémie — Ceftriaxone 2 g IV", "SPILF/SFP"
    if det.get("convulsion_prolongee") or det.get("convulsion_focale"):
        return "1", "Convulsion fébrile prolongée ou focale", "FRENCH Tri 1"
    if temp >= FIEVRE_TRES_HAUTE_ENFANT or det.get("nuque") or det.get("encephalopathie"):
        return "2", f"Fièvre {temp:.1f} °C ou signes de gravité", "FRENCH Tri 2"
    if tachy and det.get("tol_mal"):
        return "2", f"Fièvre — Tachycardie {fc} bpm + mauvaise tolérance", "FRENCH Tri 2"
    if det.get("tol_mal") or tachy:
        return "3A", "Fièvre mal tolérée ou tachycardie", "FRENCH Tri 3A"
    return "3B", "Fièvre bien tolérée sans signe de gravité", "FRENCH Tri 3B"


def _h_ped_gastro(fc, pas, temp, age, det, **_) -> TriageResult:
    sh = round(fc / max(pas, 1), 2)
    if det.get("bilieux"):
        return "1", "Vomissements bilieux — Occlusion / Volvulus — CHIRURGIE URGENTE", "FRENCH Tri 1"
    if det.get("fontanelle_bombante") or det.get("pleurs_inconsolables"):
        return "1", "Fontanelle bombante ou pleurs inconsolables — HTIC / invagination", "FRENCH Tri 1"
    if sh >= 1.0 or det.get("deshydrat_severe"):
        return "1", f"Choc hypovolémique pédiatrique — SI {sh}", "FRENCH Tri 1"
    if det.get("deshydrat_moderee") or (age < 0.25 and temp >= FIEVRE_NOURR_SEUIL):
        return "2", "Déshydratation modérée ou nourrisson fébrile", "FRENCH Tri 2"
    return "3B", "Gastro-entérite tolérée", "FRENCH Tri 3B"


def _h_ped_epilepsie(fc, spo2, temp, age, det, gl=None, **_) -> TriageResult:
    duree = det.get("duree_min", 0) or 0
    if det.get("eme_etabli") or duree > EME_ETABLI_MIN:
        return "1", f"EME établi > {EME_ETABLI_MIN} min — Réanimation pédiatrique", "ILAE 2015"
    if duree > EME_OPERATIONNEL_MIN:
        return "1", f"EME opérationnel {duree} min — Risque lésionnel", "ILAE 2015"
    if spo2 < 92 or age < 1/12:
        return "1", "Convulsion pédiatrique + SpO2 < 92 % ou néonatal", "FRENCH Tri 1"
    if det.get("en_cours") or duree > EME_SEUIL_MIN:
        return "2", "Crise EN COURS — Midazolam buccal 0,3 mg/kg MAINTENANT", "SFNP 2023"
    if det.get("premiere_crise") or det.get("focale") or det.get("signes_meninges"):
        return "2", "1ère crise / focale / signes méningés — Bilan urgent", "FRENCH Tri 2"
    if det.get("recuperee") and det.get("febrile") and not det.get("focale"):
        return "3A", "Convulsion fébrile simple récupérée", "SFNP 2023"
    return "2", "Crise épileptique — Évaluation urgente", "SFNP 2023"


def _h_ped_asthme(fc, spo2, det, age, **_) -> TriageResult:
    pram = det.get("pram", 0) or 0
    if spo2 < 92 or pram >= 8 or det.get("silence_auscultatoire"):
        return "1", f"Asthme sévère — SpO2 {spo2:.0f} % — PRAM {pram}", "FRENCH Tri 1"
    if spo2 < 95 or pram >= 4 or not det.get("parole_ok", True):
        return "2", f"Asthme modéré — SpO2 {spo2:.0f} % — Salbutamol", "GINA / FRENCH Tri 2"
    return "3A", "Asthme léger — Salbutamol", "FRENCH Tri 3A"


def _h_non_urgent(**_) -> TriageResult:
    return "5", "Consultation non urgente", "FRENCH Tri 5"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DE DISPATCH — motif normalisé → handler
# ═══════════════════════════════════════════════════════════════════════════════

_TRIAGE_DISPATCH: Dict[str, Handler] = {
    "arret cardio-respiratoire":                    _h_acr,
    "hypotension arterielle":                        _h_hypotension,
    "douleur thoracique / sca":                      _h_sca,
    "tachycardie / tachyarythmie":                   _h_arythmie,
    "bradycardie / bradyarythmie":                   _h_arythmie,
    "palpitations":                                  _h_arythmie,
    "hypertension arterielle":                       _h_hta,
    "allergie / anaphylaxie":                        _h_anaphylaxie,
    "avc / deficit neurologique":                    _h_avc,
    "traumatisme cranien":                           _h_tc,
    "alteration de conscience / coma":               _h_coma,
    "convulsions / eme":                             _h_convulsions,
    "cephalee":                                      _h_cephalee,
    "malaise":                                       _h_malaise,
    "dyspnee / insuffisance respiratoire":           _h_dyspnee,
    "dyspnee / insuffisance cardiaque":              _h_dyspnee,
    "asthme ou aggravation bpco":                    _h_dyspnee,
    "douleur abdominale":                            _h_abdomen,
    "colique nephretique / douleur lombaire":        _h_colique,
    "fievre":                                        _h_fievre,
    "hemorragie active":                             _h_hemorragie,
    "hematemese / vomissements sanglants":           _h_hemorragie,
    "rectorragie / melena":                          _h_hemorragie,
    "traumatisme thorax/abdomen/rachis cervical":    _h_trauma_axial,
    "traumatisme bassin/hanche/femur":               _h_trauma_axial,
    "traumatisme membre / epaule":                   _h_trauma_distal,
    "hypoglycemie":                                  _h_hypoglycemie,
    "hyperglycemie / cetoacidose":                   _h_hyperglycemie,
    "petechie / purpura":                            _h_purpura,
    "pediatrie - fievre <= 3 mois":                  _h_ped_fievre_nourr,
    "pediatrie - fievre enfant (3 mois - 15 ans)":   _h_ped_fievre,
    "pediatrie - vomissements / gastro-enterite":    _h_ped_gastro,
    "pediatrie - crise epileptique":                 _h_ped_epilepsie,
    "pediatrie - asthme / bronchospasme":            _h_ped_asthme,
    "renouvellement ordonnance":                     _h_non_urgent,
    "examen administratif":                          _h_non_urgent,
    "autre motif":                                   _h_non_urgent,
}

# Index O(1) — lookup normalisé
_MOTIF_INDEX: Dict[str, Handler] = {_norm(k): v for k, v in _TRIAGE_DISPATCH.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def french_triage(
    motif: str,
    det: Optional[dict],
    fc: Optional[float]   = None,
    pas: Optional[float]  = None,
    spo2: Optional[float] = None,
    fr: Optional[float]   = None,
    gcs: Optional[int]    = None,
    temp: Optional[float] = None,
    age: Optional[float]  = None,
    n2: Optional[int]     = None,
    gl: Optional[float]   = None,
) -> TriageResult:
    """
    Moteur FRENCH V1.1 — Système Expert à 3 niveaux.

    Hiérarchie de décision :
      0. NEWS2 ≥ 9 → Tri M (transversal absolu)
      1. Priorités absolues (verrouillage clinique)
      2. Arbre de décision du handler motif
      3. Ajustement NEWS2 (never downgrade)
      4. Fallback sécurisé Tri 3B
    """
    # Valeurs par défaut sécurisées
    fc   = float(fc   or 80)
    pas  = float(pas  or 120)
    spo2 = float(spo2 or 98)
    fr   = float(fr   or 16)
    gcs  = int(gcs    or 15)
    temp = float(temp or 37.0)
    age  = float(age  or 45)
    n2   = int(n2     or 0)
    det  = det or {}

    try:
        # ── Niveau 0 : NEWS2 ≥ 9 → Tri M absolu ──────────────────────────
        if n2 >= NEWS2_TRI_M:
            return "M", f"NEWS2 {n2} ≥ {NEWS2_TRI_M} — Engagement vital immédiat", "NEWS2 Tri M"

        # ── Niveau 1 : Priorités absolues verrouillées ────────────────────
        priorite = _check_priorites_absolues(det, gcs, pas, spo2, fr)
        if priorite:
            return priorite

        # ── Niveau 2 : Arbre de décision motif ───────────────────────────
        handler = _MOTIF_INDEX.get(_norm(motif))
        if handler is not None:
            result = handler(
                fc=fc, pas=pas, spo2=spo2, fr=fr,
                gcs=gcs, temp=temp, age=age, n2=n2,
                gl=gl, det=det, motif=motif,
            )
        else:
            result = ("3B", f"Évaluation standard — {motif}", "FRENCH Tri 3B")

        # ── Niveau 3 : Ajustement NEWS2 (jamais downgrade) ───────────────
        if n2 >= NEWS2_RISQUE_ELEVE:
            result = _more_urgent(result, ("2", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_ELEVE} — Risque élevé", "NEWS2"))
        elif n2 >= NEWS2_RISQUE_MOD:
            result = _more_urgent(result, ("3A", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_MOD} — Risque modéré", "NEWS2"))

        return result

    except Exception as e:
        # Failsafe : ne jamais laisser planter — triage conservateur
        return "2", f"Erreur moteur triage — Évaluation médicale urgente ({e})", "Sécurité Tri 2"


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTES CLINIQUES TRANSVERSALES
# ═══════════════════════════════════════════════════════════════════════════════

def verifier_coherence(
    fc: float, pas: float, spo2: float, fr: float,
    gcs: int, temp: float, eva: int,
    motif: str, atcd: list, det: dict,
    n2: int, gl: Optional[float] = None,
) -> Tuple[list, list]:
    """
    Alertes transversales post-triage.
    Retourne (alertes_danger, alertes_warning).
    """
    D: list = []
    A: list = []
    sh = round(fc / max(pas, 1), 2)

    # ── Alertes critiques (rouge) ─────────────────────────────────────────
    if "IMAO (inhibiteurs MAO)" in atcd:
        D.append("IMAO — Tramadol CONTRE-INDIQUÉ ABSOLU (syndrome sérotoninergique fatal)")
    if gl:
        if gl < GLYC["hs"]:
            D.append(f"HYPOGLYCÉMIE SÉVÈRE {gl:.0f} mg/dl — Glucose 30 % IV IMMÉDIAT")
        elif gl > 360:
            D.append(f"HYPERGLYCÉMIE SÉVÈRE {gl:.0f} mg/dl — Bilan acidocétose")
    if sh >= 1.0:
        D.append(f"Shock Index {sh} ≥ 1,0 — État de choc probable")
    if spo2 < 90:
        D.append(f"SpO2 {spo2:.0f} % — Hypoxémie sévère — O₂ urgent")
    if fc >= 150 or fc <= 40:
        D.append(f"FC {fc:.0f} bpm — Arythmie critique")
    if "Anticoagulants/AOD" in atcd and "Traumatisme cranien" in motif:
        D.append("TC sous AOD/AVK — TDM cérébral urgent")
    if "Anticoagulants/AOD" in atcd and "Hemorragie" in motif:
        D.append("Hémorragie sous AOD — Envisager neutralisation (Praxbind / Ondexxya)")
    if det.get("purpura") or det.get("neff"):
        D.append("PURPURA FULMINANS — Ceftriaxone 2 g IV IMMÉDIAT — Ne pas retarder")
    if spo2 > 96 and "BPCO" in atcd:
        D.append(f"BPCO — SpO2 {spo2:.0f} % > 96 % — Risque narcose CO₂ — Réduire l'O₂")

    # ── Alertes importantes (orange) ─────────────────────────────────────
    if "Antidépresseurs ISRS/IRSNA" in atcd:
        A.append("ISRS/IRSNA — Tramadol déconseillé — Préférer Piritramide ou Morphine")
    if fr >= 30:
        A.append(f"FR {fr:.0f}/min — Tachypnée significative")
    if gl and GLYC["hm"] > gl >= GLYC["hs"]:
        A.append(f"Hypoglycémie modérée {gl:.0f} mg/dl — Corriger avant antalgique")
    if "Immunodépression" in atcd or "Chimiothérapie en cours" in atcd:
        A.append("IMMUNODÉPRIMÉ — Seuil d'alerte abaissé — Tout signe infectieux = urgence")
        if temp >= 38.3:
            D.append(f"Immunodéprimé + fièvre {temp:.1f} °C ≥ 38,3 °C — Neutropénie fébrile possible — ATB < 1 h")
    if eva >= 7:
        A.append(f"EVA {eva}/10 — Douleur intense — Réévaluation à 30 min post-antalgie obligatoire")
    if "Drépanocytose" in atcd and eva >= 6:
        A.append("Drépanocytose + douleur intense — Morphine titrée < 30 min (objectif SFMU)")
    if sh >= 0.8 and sh < 1.0:
        A.append(f"Shock Index {sh} — Instabilité débutante — Surveiller de près")

    return D, A
