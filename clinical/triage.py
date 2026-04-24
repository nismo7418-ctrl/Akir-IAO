from typing import Optional, Dict, Tuple
from config import NEWS2_TRI_M, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD, GLYC

TriageResult = Tuple[str, str, str]

def french_triage(motif, det, fc, pas, spo2, fr, gcs, temp, age, n2, gl=None):
    fc, pas, spo2, fr, gcs, temp, n2 = fc or 80, pas or 120, spo2 or 98, fr or 16, gcs or 15, temp or 37.0, n2 or 0
    det = det or {}

    try:
        if n2 >= NEWS2_TRI_M:
            return "M", f"NEWS2 {n2} ≥ {NEWS2_TRI_M} — engagement vital", "NEWS2 Tri M"
        if det.get("purpura"):
            return "1", "PURPURA FULMINANS — Ceftriaxone 2 g IV immédiat", "SPILF/SFP 2017"

        # Note: Le resolve_handler sera intégré ici plus tard
        if n2 >= NEWS2_RISQUE_ELEVE:
            return "2", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_ELEVE} — risque élevé", "NEWS2 Tri 2"
        if n2 >= NEWS2_RISQUE_MOD:
            return "3A", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_MOD} — risque modéré", "NEWS2 Tri 3A"
        return "3B", f"Évaluation standard — {motif}", "FRENCH Tri 3B"
    except Exception as e:
        return "2", f"Erreur moteur de triage : {e}", "Sécurité Tri 2"

def verifier_coherence(fc, pas, spo2, fr, gcs, temp, eva, motif, atcd, det, n2, gl=None):
    D, A = [], []
    if "IMAO (inhibiteurs MAO)" in atcd:
        D.append("IMAO — Tramadol CONTRE-INDIQUÉ (syndrome sérotoninergique fatal)")
    if "Antidépresseurs ISRS/IRSNA" in atcd:
        A.append("ISRS/IRSNA — Tramadol déconseillé — Préférer Dipidolor ou Morphine")
    if gl:
        if gl < GLYC["hs"]: D.append(f"HYPOGLYCÉMIE SÉVÈRE {gl}mg/dl — Glucose 30% IV")
        elif gl < GLYC["hm"]: A.append(f"Hypoglycémie modérée {gl}mg/dl — corriger avant antalgique")
    
    from clinical.vitaux import si
    sh = si(fc, pas)
    if sh >= 1.0: D.append(f"Shock Index {sh}>=1.0 — état de choc probable")
    if spo2 < 90: D.append(f"SpO2 {spo2}% — O₂ urgent")
    if fr >= 30: A.append(f"FR {fr}/min — tachypnée")
    if fc >= 150 or fc <= 40: D.append(f"FC {fc}bpm — arythmie critique")
    if "Anticoagulants/AOD" in atcd and "Traumatisme crânien" in motif:
        D.append("TC sous AOD/AVK — TDM urgent")
    return D, A
