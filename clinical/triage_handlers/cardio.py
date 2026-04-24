from clinical.vitaux import si

def _triage_acr(**_) -> tuple:
    return "1", "ACR confirmé — RCP en cours", "FRENCH Tri 1"

def _triage_hypotension(pas, fc, **_) -> tuple:
    if pas <= 70: return "1", f"PAS {pas} mmHg ≤ 70 — collapsus", "FRENCH Tri 1"
    if pas <= 90 or (pas <= 100 and fc > 100): return "2", f"PAS {pas} mmHg — choc débutant", "FRENCH Tri 2"
    if pas <= 100: return "3B", f"PAS {pas} mmHg — valeur limite", "FRENCH Tri 3B"
    return "4", "PAS normale", "FRENCH Tri 4"

def _triage_sca(fc, spo2, det, **_) -> tuple:
    ecg = det.get("ecg", "Normal")
    doul = det.get("douleur", "Atypique")
    if ecg == "Anormal typique SCA" or doul == "Typique (constrictive, irradiante)":
        return "1", "SCA — ECG anormal ou douleur typique", "FRENCH Tri 1"
    if fc >= 120 or spo2 < 94: return "2", "Douleur thoracique instable", "FRENCH Tri 2"
    if doul == "Coronaire probable" or det.get("frcv", 0) >= 2: return "2", "Douleur coronaire probable ≥ 2 FRCV", "FRENCH Tri 2"
    return "3A", "Douleur thoracique atypique stable", "FRENCH Tri 3A"

def _triage_arythmie(fc, det, **_) -> tuple:
    if fc >= 180 or fc <= 30: return "1", f"FC {fc} bpm — arythmie extrême", "FRENCH Tri 1"
    if fc >= 150 or fc <= 40: return "2", f"FC {fc} bpm — arythmie sévère", "FRENCH Tri 2"
    if det.get("tol_mal"): return "2", "Arythmie mal tolérée", "FRENCH Tri 2"
    return "3B", f"FC {fc} bpm — arythmie tolérée", "FRENCH Tri 3B"

def _triage_hta(pas, fc, det, **_) -> tuple:
    if pas >= 220: return "2", f"PAS {pas} mmHg ≥ 220 — urgence hypertensive", "FRENCH Tri 2"
    if det.get("sf") or (pas >= 180 and fc > 100): return "2", "HTA avec signes fonctionnels", "FRENCH Tri 2"
    if pas >= 180: return "3B", "HTA sévère sans signe fonctionnel", "FRENCH Tri 3B"
    return "4", "HTA modérée", "FRENCH Tri 4"

def _triage_anaphylaxie(spo2, pas, gcs, det, **_) -> tuple:
    if spo2 < 94 or pas < 90 or gcs < 15: return "1", "Anaphylaxie sévère — engagement systémique", "FRENCH Tri 1"
    if det.get("dyspnee") or det.get("urticaire"): return "2", "Allergie systémique", "FRENCH Tri 2"
    return "3B", "Réaction allergique localisée", "FRENCH Tri 3B"
