from clinical.vitaux import si
from config import GLYC

def _triage_dyspnee(spo2, fr, det, **_) -> tuple:
    bp = det.get("bpco", False)
    cible = 92 if bp else 95
    seuil_crit = 88 if bp else 91
    if spo2 < seuil_crit or fr >= 40: return "1", f"Détresse respiratoire SpO2 {spo2}% FR {fr}/min", "FRENCH Tri 1"
    if spo2 < cible or fr >= 30 or not det.get("parole", True): return "2", f"Dyspnée sévère SpO2 {spo2}%", "FRENCH Tri 2"
    if det.get("orth") or det.get("tirage"): return "2", "Orthopnée ou tirage", "FRENCH Tri 2"
    return "3B", f"Dyspnée modérée SpO2 {spo2}%", "FRENCH Tri 3B"

def _triage_abdomen(fc, pas, det, **_) -> tuple:
    sh = si(fc, pas)
    if pas < 90 or sh >= 1.0: return "2", f"Abdomen avec choc (SI {sh})", "FRENCH Tri 2"
    if det.get("grossesse") or det.get("geu"): return "2", "Abdomen sur grossesse — GEU", "FRENCH Tri 2"
    if det.get("defense"): return "2", "Abdomen chirurgical", "FRENCH Tri 2"
    if det.get("tol_mal"): return "3A", "Douleur mal tolérée", "FRENCH Tri 3A"
    return "3B", "Douleur tolérée", "FRENCH Tri 3B"

def _triage_fievre(fc, pas, temp, det, **_) -> tuple:
    if det.get("purpura"): return "1", "Fièvre + purpura — Ceftriaxone 2 g IV", "FRENCH Tri 1"
    if temp >= 40 or temp <= 35.2 or det.get("conf"): return "2", f"Fièvre avec critère de gravité (T {temp}°C)", "FRENCH Tri 2"
    if det.get("tol_mal") or pas < 100 or si(fc,pas) >= 1.0: return "3B", "Fièvre mal tolérée", "FRENCH Tri 3B"
    return "5", "Fièvre bien tolérée", "FRENCH Tri 5"

def _triage_purpura(temp, det, **_) -> tuple:
    if det.get("neff"): return "1", "Purpura non effaçable — Ceftriaxone 2 g IV", "SPILF/SFP 2017"
    if temp >= 38.0: return "2", "Purpura fébrile — suspicion fulminans", "FRENCH Tri 2"
    return "3B", "Pétéchies — bilan hémostase", "FRENCH Tri 3B"

def _triage_trauma_axial(fc, pas, spo2, det, **_) -> tuple:
    if det.get("pen") or det.get("cin") == "Haute": return "1", "Traumatisme pénétrant/haute cinétique", "FRENCH Tri 1"
    if si(fc, pas) >= 1.0 or spo2 < 94: return "2", f"Traumatisme avec choc SI {si(fc,pas)}", "FRENCH Tri 2"
    return "2", "Traumatisme axial — évaluation urgente", "FRENCH Tri 2"

def _triage_trauma_distal(det, **_) -> tuple:
    if det.get("isch"): return "1", "Ischémie distale", "FRENCH Tri 1"
    if det.get("imp") and det.get("deform"): return "2", "Fracture déplacée impotence totale", "FRENCH Tri 2"
    if det.get("imp"): return "3A", "Impotence fonctionnelle totale", "FRENCH Tri 3A"
    if det.get("deform"): return "3A", "Déformation visible", "FRENCH Tri 3A"
    return "4", "Traumatisme distal modéré", "FRENCH Tri 4"

def _triage_hypoglycemie(gcs, gl, **_) -> tuple:
    if gl and gl < GLYC["hs"]: return "2", f"Hypoglycémie sévère {gl} mg/dl — Glucose 30% IV", "FRENCH Tri 2"
    if gcs < 15: return "2", f"Hypoglycémie avec altération GCS {gcs}/15", "FRENCH Tri 2"
    return "3B", "Hypoglycémie légère — resucrage oral", "FRENCH Tri 3B"

def _triage_hyperglycemie(gcs, det, **_) -> tuple:
    if det.get("ceto") or gcs < 15: return "2", "Cétoacidose ou altération de conscience", "FRENCH Tri 2"
    return "4", "Hyperglycémie tolérée", "FRENCH Tri 4"

def _triage_non_urgent(**_) -> tuple:
    return "5", "Consultation non urgente", "FRENCH Tri 5"
