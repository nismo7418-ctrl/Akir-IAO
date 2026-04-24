from config import AVC_DELAI_THROMBOLYSE_H, GLYC

def _triage_avc(gcs, det, **_) -> tuple:
    d = det.get("delai", 99)
    if d <= AVC_DELAI_THROMBOLYSE_H: return "1", f"AVC {d} h — fenêtre thrombolyse", "FRENCH Tri 1"
    if det.get("def_prog") or gcs < 15: return "2", "Déficit progressif ou altération GCS", "FRENCH Tri 2"
    return "2", "Déficit neurologique — bilan urgent", "FRENCH Tri 2"

def _triage_tc(gcs, det, **_) -> tuple:
    if gcs <= 8: return "1", f"TC grave — GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 12 or det.get("aod"): return "2", f"TC GCS {gcs}/15 ou anticoagulant — TDM urgent", "FRENCH Tri 2"
    if det.get("pdc"): return "3A", "TC avec perte de conscience", "FRENCH Tri 3A"
    return "4", "TC bénin", "FRENCH Tri 4"

def _triage_coma(gcs, gl, **_) -> tuple:
    if gl and gl < GLYC["hs"]: return "2", f"Hypoglycémie {gl} mg/dl — Glucose 30% IV", "FRENCH Tri 2"
    if gcs <= 8: return "1", f"Coma profond — GCS {gcs}/15", "FRENCH Tri 1"
    if gcs <= 13: return "2", f"Altération de conscience — GCS {gcs}/15", "FRENCH Tri 2"
    return "2", "Altération légère de conscience", "FRENCH Tri 2"

def _triage_convulsions(det, **_) -> tuple:
    if det.get("multi"): return "2", "Crises multiples ou état de mal épileptique", "FRENCH Tri 2"
    if det.get("conf"): return "2", "Confusion post-critique persistante", "FRENCH Tri 2"
    return "3B", "Convulsion récupérée", "FRENCH Tri 3B"

def _triage_cephalee(det, **_) -> tuple:
    if det.get("brutal"): return "1", "Céphalée foudroyante — HSA suspectée", "FRENCH Tri 1"
    if det.get("nuque") or det.get("fiev_ceph"): return "2", "Céphalée avec signes méningés", "FRENCH Tri 2"
    return "3B", "Céphalée sans signe de gravité", "FRENCH Tri 3B"

def _triage_malaise(n2, gl, det, **_) -> tuple:
    if gl and gl < GLYC["hs"]: return "2", f"Malaise hypoglycémique {gl} mg/dl", "FRENCH Tri 2"
    if n2 >= 2 or det.get("anom_vit"): return "2", "Malaise avec anomalie vitale", "FRENCH Tri 2"
    return "3B", "Malaise récupéré", "FRENCH Tri 3B"
