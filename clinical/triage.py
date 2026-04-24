# clinical/triage.py — Moteur de triage FRENCH V1.1 — Architecture dispatch
# Développeur : Ismail Ibn-Daifa — AKIR-IAO v18.0 — Hainaut, Belgique
#
# Références :
#   Taboulet P. et al. FRENCH Triage SFMU V1.1. Juin 2018.
#   ILAE 2015 — SFNP / EpiCARE 2023.

from typing import Optional, Tuple
from config import (
    NEWS2_TRI_M, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD,
    GLYC, AVC_DELAI_THROMBOLYSE_H,
    EME_SEUIL_MIN, EME_OPERATIONNEL_MIN, EME_ETABLI_MIN,
    FIEVRE_TRES_HAUTE_ENFANT, FIEVRE_NOURR_SEUIL, FIEVRE_HAUT_RISQUE_AGE,
    FC_TACHY_NOURR, FC_TACHY_BEBE, FC_TACHY_ENFANT, FC_TACHY_GRAND,
    VOMISS_FREQ_SEVERE,
    SIPA_0_1AN, SIPA_1_4ANS, SIPA_4_7ANS, SIPA_7_12ANS,
)

TriageResult = Tuple[str, str, str]  # (niveau, justification, référence)


# ── Utilitaire Shock Index ────────────────────────────────────────────────────
def _si(fc: float, pas: float) -> float:
    """Shock Index = FC / PAS."""
    return round(fc / pas, 2) if pas and pas > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS CARDIO-CIRCULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_acr(**_) -> TriageResult:
    """Arrêt Cardio-Respiratoire — Tri 1 absolu."""
    return "1", "ACR confirmé — RCP en cours", "FRENCH Tri 1"


def _triage_hypotension(pas, fc, **_) -> TriageResult:
    """Hypotension artérielle — gradient de gravité PAS / FC."""
    if pas <= 70:
        return "1", f"PAS {pas} mmHg ≤ 70 — collapsus vasculaire", "FRENCH Tri 1"
    if pas <= 90 or (pas <= 100 and fc > 100):
        return "2", f"PAS {pas} mmHg — choc débutant", "FRENCH Tri 2"
    if pas <= 100:
        return "3B", f"PAS {pas} mmHg — valeur limite", "FRENCH Tri 3B"
    return "4", "PAS dans les normes", "FRENCH Tri 4"


def _triage_sca(fc, spo2, det, **_) -> TriageResult:
    """Douleur thoracique / SCA — filière coronaire."""
    ecg  = det.get("ecg", "Normal")
    doul = det.get("douleur", "Atypique")
    if ecg == "Anormal typique SCA" or doul == "Typique (constrictive, irradiante)":
        return "1", "SCA — ECG anormal ou douleur typique", "FRENCH Tri 1"
    if fc >= 120 or spo2 < 94:
        return "2", "Douleur thoracique instable", "FRENCH Tri 2"
    if doul == "Coronaire probable" or det.get("frcv", 0) >= 2:
        return "2", "Douleur coronaire probable ≥ 2 FRCV", "FRENCH Tri 2"
    return "3A", "Douleur thoracique atypique stable", "FRENCH Tri 3A"


def _triage_arythmie(fc, det, **_) -> TriageResult:
    """Tachycardie / Bradycardie / Palpitations."""
    if fc >= 180 or fc <= 30:
        return "1", f"FC {fc} bpm — arythmie extrême", "FRENCH Tri 1"
    if fc >= 150 or fc <= 40:
        return "2", f"FC {fc} bpm — arythmie sévère", "FRENCH Tri 2"
    if det.get("tol_mal"):
        return "2", "Arythmie mal tolérée", "FRENCH Tri 2"
    return "3B", f"FC {fc} bpm — arythmie tolérée", "FRENCH Tri 3B"


def _triage_hta(pas, fc, det, **_) -> TriageResult:
    """Hypertension artérielle."""
    if pas >= 220:
        return "2", f"PAS {pas} mmHg — urgence hypertensive", "FRENCH Tri 2"
    if det.get("sf") or (pas >= 180 and fc > 100):
        return "2", "HTA avec signes fonctionnels", "FRENCH Tri 2"
    if pas >= 180:
        return "3B", "HTA sévère sans signe fonctionnel", "FRENCH Tri 3B"
    return "4", "HTA modérée", "FRENCH Tri 4"


def _triage_anaphylaxie(spo2, pas, gcs, det, **_) -> TriageResult:
    """Allergie / Anaphylaxie — EAACI 2023."""
    if spo2 < 94 or pas < 90 or gcs < 15:
        return "1", "Anaphylaxie sévère — engagement systémique", "FRENCH Tri 1"
    if det.get("dyspnee") or det.get("urticaire"):
        return "2", "Allergie systémique", "FRENCH Tri 2"
    return "3B", "Réaction allergique localisée", "FRENCH Tri 3B"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS NEUROLOGIE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_avc(gcs, det, **_) -> TriageResult:
    """AVC / Déficit neurologique — filière Stroke."""
    d = det.get("delai", 99)
    if d <= AVC_DELAI_THROMBOLYSE_H:
        return "1", f"AVC {d} h — fenêtre thrombolyse — filière Stroke", "FRENCH Tri 1"
    if det.get("def_prog") or gcs < 15:
        return "2", "Déficit progressif ou altération GCS", "FRENCH Tri 2"
    return "2", "Déficit neurologique — bilan urgent", "FRENCH Tri 2"


def _triage_tc(gcs, det, **_) -> TriageResult:
    """Traumatisme Crânien."""
    if gcs <= 8:
        return "1", f"TC grave — GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 12 or det.get("aod"):
        return "2", f"TC GCS {gcs}/15 ou anticoagulant — TDM urgent", "FRENCH Tri 2"
    if det.get("pdc"):
        return "3A", "TC avec perte de conscience", "FRENCH Tri 3A"
    return "4", "TC bénin", "FRENCH Tri 4"


def _triage_coma(gcs, gl, **_) -> TriageResult:
    """Altération de conscience / Coma."""
    if gl and gl < GLYC["hs"]:
        return "2", f"Hypoglycémie {gl} mg/dl — Glucose 30 % IV", "FRENCH Tri 2"
    if gcs <= 8:
        return "1", f"Coma profond — GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 13:
        return "2", f"Altération de conscience — GCS {gcs}/15", "FRENCH Tri 2"
    return "2", "Altération légère de conscience", "FRENCH Tri 2"


def _triage_convulsions(det, **_) -> TriageResult:
    """Convulsions / EME adulte."""
    if det.get("multi"):
        return "2", "Crises multiples ou état de mal épileptique", "FRENCH Tri 2"
    if det.get("conf"):
        return "2", "Confusion post-critique persistante", "FRENCH Tri 2"
    return "3B", "Convulsion récupérée", "FRENCH Tri 3B"


def _triage_cephalee(det, **_) -> TriageResult:
    """Céphalée — HSA suspectée si foudroyante."""
    if det.get("brutal"):
        return "1", "Céphalée foudroyante — HSA suspectée", "FRENCH Tri 1"
    if det.get("nuque") or det.get("fiev_ceph"):
        return "2", "Céphalée avec signes méningés", "FRENCH Tri 2"
    return "3B", "Céphalée sans signe de gravité", "FRENCH Tri 3B"


def _triage_malaise(n2, gl, det, **_) -> TriageResult:
    """Malaise récupéré."""
    if gl and gl < GLYC["hs"]:
        return "2", f"Malaise hypoglycémique {gl} mg/dl", "FRENCH Tri 2"
    if n2 >= 2 or det.get("anom_vit"):
        return "2", "Malaise avec anomalie vitale", "FRENCH Tri 2"
    return "3B", "Malaise récupéré", "FRENCH Tri 3B"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS RESPIRATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_dyspnee(spo2, fr, det, **_) -> TriageResult:
    """Dyspnée — seuils adaptés BPCO (Échelle 2)."""
    bp    = det.get("bpco", False)
    cible = 92 if bp else 95
    seuil = 88 if bp else 91
    if spo2 < seuil or fr >= 40:
        return "1", f"Détresse respiratoire — SpO2 {spo2} % FR {fr}/min", "FRENCH Tri 1"
    if spo2 < cible or fr >= 30 or not det.get("parole", True):
        return "2", f"Dyspnée sévère — SpO2 {spo2} %", "FRENCH Tri 2"
    if det.get("orth") or det.get("tirage"):
        return "2", "Orthopnée ou tirage intercostal", "FRENCH Tri 2"
    return "3B", f"Dyspnée modérée — SpO2 {spo2} %", "FRENCH Tri 3B"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS DIGESTIF
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_abdomen(fc, pas, det, **_) -> TriageResult:
    """Douleur abdominale — Shock Index et GEU."""
    sh = _si(fc, pas)
    if pas < 90 or sh >= 1.0:
        return "2", f"Abdomen avec choc (SI {sh})", "FRENCH Tri 2"
    if det.get("grossesse") or det.get("geu"):
        return "2", "Abdomen sur grossesse — GEU à éliminer", "FRENCH Tri 2"
    if det.get("defense"):
        return "2", "Abdomen chirurgical", "FRENCH Tri 2"
    if det.get("tol_mal"):
        return "3A", "Douleur mal tolérée", "FRENCH Tri 3A"
    return "3B", "Douleur tolérée", "FRENCH Tri 3B"


def _triage_colique_nephretique(fc, pas, det, **_) -> TriageResult:
    """Colique néphrétique — pyélonéphrite obstructive si fièvre."""
    if det.get("fievre") and det.get("douleur_lombaire"):
        return "1", "Colique + fièvre — Pyélonéphrite obstructive — Chirurgie urgente", "FRENCH Tri 1"
    if det.get("anurie") or pas < 90:
        return "2", "Colique + anurie ou hypotension — Bilan urgent", "FRENCH Tri 2"
    if det.get("tol_mal"):
        return "2", "Colique mal tolérée — Antalgie IV urgente", "FRENCH Tri 2"
    return "3A", "Colique tolérée — Antalgie orale + imagerie", "FRENCH Tri 3A"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS INFECTIOLOGIE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_fievre(fc, pas, temp, det, **_) -> TriageResult:
    """Fièvre — purpura, sepsis, tolérance."""
    if det.get("purpura"):
        return "1", "Fièvre + purpura — Ceftriaxone 2 g IV immédiat", "FRENCH Tri 1"
    if temp >= 40 or temp <= 35.2 or det.get("conf"):
        return "2", f"Fièvre avec critère de gravité (T {temp} °C)", "FRENCH Tri 2"
    if det.get("tol_mal") or pas < 100 or _si(fc, pas) >= 1.0:
        return "3B", "Fièvre mal tolérée", "FRENCH Tri 3B"
    return "5", "Fièvre bien tolérée", "FRENCH Tri 5"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS TRAUMATOLOGIE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_hemorragie(fc, pas, det, **_) -> TriageResult:
    """Hémorragie active — Shock Index."""
    sh = _si(fc, pas)
    if sh >= 1.0 or pas < 90:
        return "1", f"Choc hémorragique — SI {sh} — Acide tranexamique < 3 h", "CRASH-2 / FRENCH Tri 1"
    if det.get("hemoptysie_mas") or det.get("hematemese"):
        return "2", "Hémorragie digestive ou respiratoire haute", "FRENCH Tri 2"
    if sh >= 0.8:
        return "2", f"Hémorragie avec SI {sh} — instabilité débutante", "FRENCH Tri 2"
    return "3A", "Hémorragie active tolérée — surveillance rapprochée", "FRENCH Tri 3A"


def _triage_trauma_axial(fc, pas, spo2, det, **_) -> TriageResult:
    """Traumatisme thorax / abdomen / rachis cervical / bassin."""
    if det.get("pen") or det.get("cin") == "Haute":
        return "1", "Traumatisme pénétrant ou haute cinétique", "FRENCH Tri 1"
    if _si(fc, pas) >= 1.0 or spo2 < 94:
        return "2", f"Traumatisme avec choc (SI {_si(fc, pas)})", "FRENCH Tri 2"
    return "2", "Traumatisme axial — évaluation urgente", "FRENCH Tri 2"


def _triage_trauma_distal(det, **_) -> TriageResult:
    """Traumatisme membre / épaule."""
    if det.get("isch"):
        return "1", "Ischémie distale", "FRENCH Tri 1"
    if det.get("imp") and det.get("deform"):
        return "2", "Fracture déplacée avec impotence totale", "FRENCH Tri 2"
    if det.get("imp"):
        return "3A", "Impotence fonctionnelle totale", "FRENCH Tri 3A"
    if det.get("deform"):
        return "3A", "Déformation visible", "FRENCH Tri 3A"
    return "4", "Traumatisme distal modéré", "FRENCH Tri 4"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS MÉTABOLIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_hypoglycemie(gcs, gl, **_) -> TriageResult:
    """Hypoglycémie — seuils GLYC belges (mg/dl)."""
    if gl and gl < GLYC["hs"]:
        return "2", f"Hypoglycémie sévère {gl} mg/dl — Glucose 30 % IV", "FRENCH Tri 2"
    if gcs < 15:
        return "2", f"Hypoglycémie avec altération GCS {gcs}/15", "FRENCH Tri 2"
    return "3B", "Hypoglycémie légère — resucrage oral", "FRENCH Tri 3B"


def _triage_hyperglycemie(gcs, det, **_) -> TriageResult:
    """Hyperglycémie / Cétoacidose diabétique."""
    if det.get("ceto") or gcs < 15:
        return "2", "Cétoacidose ou altération de conscience", "FRENCH Tri 2"
    return "4", "Hyperglycémie tolérée", "FRENCH Tri 4"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS PEAU
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_purpura(temp, det, **_) -> TriageResult:
    """Pétéchie / Purpura — test du verre."""
    if det.get("neff"):
        return "1", "Purpura non effaçable — Ceftriaxone 2 g IV immédiat", "SPILF/SFP 2017"
    if temp >= 38.0:
        return "2", "Purpura fébrile — suspicion fulminans", "FRENCH Tri 2"
    return "3B", "Pétéchies — bilan hémostase à prévoir", "FRENCH Tri 3B"


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS PÉDIATRIE
# ═══════════════════════════════════════════════════════════════════════════════

def _triage_fievre_nourr(**_) -> TriageResult:
    """Fièvre nourrisson ≤ 3 mois — Tri 2 systématique."""
    return "2", "Fièvre nourrisson ≤ 3 mois — bilan urgent systématique", "FRENCH Pédiatrie Tri 2"


def _triage_ped_fievre(fc, spo2, temp, age, det, **_) -> TriageResult:
    """Fièvre enfant 3 mois – 15 ans — SFMU / SFP 2021."""
    if age < 1/12:
        fc_seuil = FC_TACHY_NOURR
    elif age < 1.0:
        fc_seuil = FC_TACHY_BEBE
    elif age < 5.0:
        fc_seuil = FC_TACHY_ENFANT
    else:
        fc_seuil = FC_TACHY_GRAND
    tachycardie = fc > fc_seuil

    if age <= 0.5 and temp >= FIEVRE_NOURR_SEUIL:
        return "2", f"Fièvre nourrisson {int(age*12)} mois — risque infectieux élevé", "SFP / SFMU Tri 2"
    if det.get("purpura") and temp >= FIEVRE_NOURR_SEUIL:
        return "1", "Fièvre + purpura — Méningococcémie — Ceftriaxone 2 g IV", "SPILF / SFP 2017"
    if det.get("convulsion_prolongee") or det.get("convulsion_focale"):
        return "1", "Convulsion fébrile prolongée ou focale — Tri 1", "FRENCH Pédiatrie Tri 1"
    if temp >= FIEVRE_TRES_HAUTE_ENFANT:
        return "2", f"Fièvre {temp} °C ≥ 40 °C — hyperthermie sévère", "FRENCH Pédiatrie Tri 2"
    if det.get("nuque") or det.get("kernig"):
        return "2", "Fièvre avec signes méningés", "FRENCH Pédiatrie Tri 2"
    if det.get("encephalopathie") or det.get("agitation") or det.get("somnolence"):
        return "2", "Fièvre avec encéphalopathie", "FRENCH Pédiatrie Tri 2"
    if tachycardie and det.get("tol_mal"):
        return "2", f"Fièvre avec tachycardie {fc} bpm et mauvaise tolérance", "FRENCH Pédiatrie Tri 2"
    if det.get("tol_mal") or tachycardie:
        return "3A", "Fièvre mal tolérée — évaluation médicale rapide", "FRENCH Tri 3A"
    return "3B", "Fièvre bien tolérée — sans signe de gravité", "FRENCH Tri 3B"


def _triage_ped_gastro(fc, pas, temp, age, det, **_) -> TriageResult:
    """Gastro-entérite pédiatrique — déshydratation OMS / ESPGHAN 2014."""
    if age < 1/12:
        fc_seuil = FC_TACHY_NOURR
    elif age < 1.0:
        fc_seuil = FC_TACHY_BEBE
    elif age < 5.0:
        fc_seuil = FC_TACHY_ENFANT
    else:
        fc_seuil = FC_TACHY_GRAND
    tachycardie = fc > fc_seuil
    sh = _si(fc, pas)

    if det.get("bilieux"):
        return "1", "Vomissements bilieux — occlusion / volvulus à éliminer", "FRENCH Pédiatrie Tri 1"
    if det.get("fontanelle_bombante"):
        return "1", "Fontanelle bombante — HTIC / méningite", "FRENCH Pédiatrie Tri 1"
    if det.get("pleurs_inconsolables"):
        return "1", "Pleurs inconsolables + vomissements — invagination intestinale", "FRENCH Pédiatrie Tri 1"
    if det.get("convulsions"):
        return "1", "Vomissements + convulsions", "FRENCH Pédiatrie Tri 1"
    if sh >= 1.0 or pas < 90 or det.get("deshydrat_severe"):
        return "1", f"Choc hypovolémique — déshydratation sévère (SI {sh})", "FRENCH Pédiatrie Tri 1"
    if det.get("deshydrat_moderee"):
        return "2", "Déshydratation modérée — réhydratation IV / SNG", "ESPGHAN 2014 Tri 2"
    if age < FIEVRE_HAUT_RISQUE_AGE and temp >= FIEVRE_NOURR_SEUIL:
        return "2", f"Nourrisson {int(age*12)} mois — vomissements + fièvre {temp} °C", "FRENCH Pédiatrie Tri 2"
    if tachycardie and temp >= 38.5:
        return "2", f"Tachycardie {fc} bpm + fièvre {temp} °C", "FRENCH Pédiatrie Tri 2"
    if det.get("vomiss_freq"):
        return "2", f"Vomissements très fréquents (> {VOMISS_FREQ_SEVERE}/h)", "FRENCH Pédiatrie Tri 2"
    if det.get("deshydrat_legere") or tachycardie:
        return "3A", "Déshydratation légère — réhydratation orale", "ESPGHAN 2014 Tri 3A"
    return "3B", "Gastro-entérite — vomissements tolérés", "FRENCH Tri 3B"


def _triage_ped_epilepsie(fc, spo2, temp, age, det, gl=None, **_) -> TriageResult:
    """Crise épileptique pédiatrique — SFNP / ISPE 2023."""
    duree = det.get("duree_min", 0) or 0
    if det.get("eme_etabli") or duree > EME_ETABLI_MIN:
        return "1", f"EME établi > {EME_ETABLI_MIN} min — Réanimation pédiatrique", "ISPE 2022 Tri 1"
    if duree > EME_OPERATIONNEL_MIN:
        return "1", f"EME opérationnel {duree} min — Risque lésionnel", "ILAE 2015 Tri 1"
    if spo2 < 92:
        return "1", f"Crise + SpO2 {spo2} % — Détresse respiratoire", "FRENCH Pédiatrie Tri 1"
    if age < 1/12:
        return "1", "Convulsion néonatale (< 1 mois) — Bilan urgent", "SFNP Tri 1"
    if det.get("tc_associe"):
        return "1", "Crise + traumatisme crânien — Imagerie urgente", "FRENCH Tri 1"
    if det.get("signes_meninges") and temp >= 38.0:
        return "1", "Crise fébrile + signes méningés — Méningite / Encéphalite", "FRENCH Pédiatrie Tri 1"
    if gl and gl < 54 and det.get("conscience_incomplete"):
        return "1", f"Hypoglycémie sévère {gl} mg/dl + conscience altérée", "FRENCH Tri 1"
    if det.get("en_cours"):
        return "2", "Crise EN COURS — Midazolam buccal 0,3 mg/kg MAINTENANT", "SFNP 2023 Tri 2"
    if duree > EME_SEUIL_MIN:
        return "2", f"Crise prolongée {duree} min > {EME_SEUIL_MIN} min", "SFNP 2023 Tri 2"
    if det.get("premiere_crise") and "Epilepsie" not in det.get("atcd", []):
        return "2", "1ère crise non fébrile — Bilan étiologique urgent", "FRENCH Pédiatrie Tri 2"
    if det.get("focale") or det.get("repetee_24h"):
        return "2", "Crise fébrile complexe (focale ou répétée < 24 h)", "SFNP 2023 Tri 2"
    if det.get("conscience_incomplete") or det.get("avpu") in ("V", "P", "U"):
        return "2", "Conscience altérée après crise", "FRENCH Pédiatrie Tri 2"
    if det.get("febrile") and not det.get("focale") and det.get("recuperee"):
        return "3A", "Crise fébrile simple récupérée — Surveillance médicale", "SFNP 2023 Tri 3A"
    if "Epilepsie" in det.get("atcd", []) and det.get("recuperee") and det.get("habituelle"):
        return "3A", "Épilepsie connue — Crise habituelle récupérée", "FRENCH Tri 3A"
    if "Epilepsie" in det.get("atcd", []) and det.get("recuperee") and det.get("plan_urgence"):
        return "3B", "Épilepsie connue — Crise récupérée — Plan d'urgence", "FRENCH Tri 3B"
    return "2", "Crise épileptique pédiatrique — Évaluation urgente", "SFNP 2023 Tri 2"


def _triage_ped_asthme(fc, spo2, det, age, **_) -> TriageResult:
    """Asthme pédiatrique — Score PRAM / GINA."""
    pram = det.get("pram", 0) or 0
    if spo2 < 92 or pram >= 8 or det.get("silence_auscultatoire"):
        return "1", f"Asthme sévère — SpO2 {spo2} % — PRAM {pram}", "FRENCH Pédiatrie Tri 1"
    if spo2 < 95 or pram >= 4 or (fr_ok := det.get("fr", 16)) and (
        (fr_ok > 40 and age < 5) or (fr_ok > 30 and age >= 5)
    ):
        return "2", f"Asthme modéré — SpO2 {spo2} % — Salbutamol nébulisation", "GINA / FRENCH Pédiatrie Tri 2"
    if pram >= 1 or spo2 < 97:
        return "3A", "Asthme léger — Salbutamol nébulisation — surveillance", "FRENCH Tri 3A"
    return "3B", "Asthme léger — Bronchodilatateur inhalateur", "FRENCH Tri 3B"


def _triage_non_urgent(**_) -> TriageResult:
    """Motifs non urgents."""
    return "5", "Consultation non urgente", "FRENCH Tri 5"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DE DISPATCH — motif → handler
# ═══════════════════════════════════════════════════════════════════════════════

_TRIAGE_DISPATCH: dict = {
    "Arret cardio-respiratoire":                          _triage_acr,
    "Hypotension arterielle":                             _triage_hypotension,
    "Douleur thoracique / SCA":                           _triage_sca,
    ("Tachycardie / tachyarythmie",
     "Bradycardie / bradyarythmie",
     "Palpitations"):                                     _triage_arythmie,
    "Hypertension arterielle":                            _triage_hta,
    "Allergie / anaphylaxie":                             _triage_anaphylaxie,
    "AVC / Deficit neurologique":                         _triage_avc,
    "Traumatisme cranien":                                _triage_tc,
    "Alteration de conscience / Coma":                    _triage_coma,
    "Convulsions / EME":                                  _triage_convulsions,
    "Cephalee":                                           _triage_cephalee,
    "Malaise":                                            _triage_malaise,
    ("Dyspnee / insuffisance respiratoire",
     "Dyspnee / insuffisance cardiaque"):                 _triage_dyspnee,
    "Douleur abdominale":                                 _triage_abdomen,
    "Colique nephretique / Douleur lombaire":             _triage_colique_nephretique,
    "Fievre":                                             _triage_fievre,
    "Hemorragie active":                                  _triage_hemorragie,
    ("Traumatisme thorax/abdomen/rachis cervical",
     "Traumatisme bassin/hanche/femur"):                  _triage_trauma_axial,
    "Traumatisme membre / epaule":                        _triage_trauma_distal,
    "Hypoglycemie":                                       _triage_hypoglycemie,
    "Hyperglycemie / Cetoacidose":                        _triage_hyperglycemie,
    "Petechie / Purpura":                                 _triage_purpura,
    "Pediatrie - Fievre <= 3 mois":                       _triage_fievre_nourr,
    "Pediatrie - Fievre enfant (3 mois - 15 ans)":        _triage_ped_fievre,
    "Pediatrie - Vomissements / Gastro-enterite":         _triage_ped_gastro,
    "Pediatrie - Crise epileptique":                      _triage_ped_epilepsie,
    "Pediatrie - Asthme / Bronchospasme":                 _triage_ped_asthme,
    ("Renouvellement ordonnance",
     "Examen administratif"):                             _triage_non_urgent,
}

# Index O(1) : motif_str → handler
_MOTIF_INDEX: dict = {}
for _key, _handler in _TRIAGE_DISPATCH.items():
    if isinstance(_key, tuple):
        for _m in _key:
            _MOTIF_INDEX[_m] = _handler
    else:
        _MOTIF_INDEX[_key] = _handler


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def french_triage(
    motif: str,
    det: Optional[dict],
    fc: float, pas: float, spo2: float,
    fr: float, gcs: int, temp: float,
    age: float, n2: int,
    gl: Optional[float] = None,
) -> TriageResult:
    """
    Moteur FRENCH V1.1 — Dispatch par handlers indépendants.

    Hiérarchie :
      1. NEWS2 ≥ 9 → Tri M (transversal)
      2. Purpura fulminans → Tri 1 (transversal)
      3. Handler spécifique au motif
      4. Fallback NEWS2 (motif inconnu)
    """
    fc   = fc   or 80
    pas  = pas  or 120
    spo2 = spo2 or 98
    fr   = fr   or 16
    gcs  = gcs  or 15
    temp = temp or 37.0
    n2   = n2   or 0
    det  = det  or {}

    try:
        # Critères transversaux
        if n2 >= NEWS2_TRI_M:
            return "M", f"NEWS2 {n2} ≥ {NEWS2_TRI_M} — engagement vital", "NEWS2 Tri M"
        if det.get("purpura"):
            return "1", "PURPURA FULMINANS — Ceftriaxone 2 g IV immédiat", "SPILF/SFP 2017"

        # Dispatch par handler
        handler = _MOTIF_INDEX.get(motif)
        if handler is not None:
            return handler(
                fc=fc, pas=pas, spo2=spo2, fr=fr,
                gcs=gcs, temp=temp, age=age, n2=n2,
                gl=gl, det=det,
            )

        # Fallback NEWS2
        if n2 >= NEWS2_RISQUE_ELEVE:
            return "2", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_ELEVE} — risque élevé", "NEWS2 Tri 2"
        if n2 >= NEWS2_RISQUE_MOD:
            return "3A", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_MOD} — risque modéré", "NEWS2 Tri 3A"
        return "3B", f"Évaluation standard — {motif}", "FRENCH Tri 3B"

    except Exception as e:
        return "2", f"Erreur moteur de triage : {e}", "Sécurité Tri 2"


def verifier_coherence(
    fc: float, pas: float, spo2: float,
    fr: float, gcs: int, temp: float, eva: int,
    motif: str, atcd: list, det: dict,
    n2: int, gl: Optional[float] = None,
):
    """Alertes transversales post-triage."""
    D, A = [], []
    if "IMAO (inhibiteurs MAO)" in atcd:
        D.append("IMAO — Tramadol CONTRE-INDIQUÉ (syndrome sérotoninergique fatal)")
    if "Antidépresseurs ISRS/IRSNA" in atcd:
        A.append("ISRS/IRSNA — Tramadol déconseillé — Préférer Piritramide ou Morphine")
    if gl:
        if gl < GLYC["hs"]:
            D.append(f"HYPOGLYCÉMIE SÉVÈRE {gl} mg/dl — Glucose 30 % IV")
        elif gl < GLYC["hm"]:
            A.append(f"Hypoglycémie modérée {gl} mg/dl — corriger avant antalgique")
    sh = _si(fc, pas)
    if sh >= 1.0:
        D.append(f"Shock Index {sh} ≥ 1,0 — état de choc probable")
    if spo2 < 90:
        D.append(f"SpO2 {spo2} % — hypoxémie sévère — O₂ urgent")
    if fr >= 30:
        A.append(f"FR {fr}/min — tachypnée significative")
    if fc >= 150 or fc <= 40:
        D.append(f"FC {fc} bpm — arythmie critique")
    if "Anticoagulants/AOD" in atcd and "Traumatisme cranien" in motif:
        D.append("TC sous AOD/AVK — TDM urgent")
    return D, Agit 