from typing import Tuple
from config import SIPA_0_1AN, SIPA_1_4ANS, SIPA_4_7ANS

def si(fc: float, pas: float) -> float:
    return round(fc/pas, 2) if pas and pas > 0 else 0.0

def sipa(fc: float, age: float) -> Tuple[float, str, bool]:
    # Formule de PAS normale basse estimée pour le calcul du ratio
    pas_min = float(age) * 2 + 70 if age >= 1 else 70
    v = round(fc / max(1.0, pas_min), 2)
    
    if age <= 1: seuil = SIPA_0_1AN
    elif age <= 4: seuil = SIPA_1_4ANS
    elif age <= 7: seuil = SIPA_4_7ANS
    else: seuil = 1.7
    
    alerte = v > seuil
    txt = f"SIPA {v} {'>' if alerte else '<='} {seuil} — {'⚠️ CHOC PÉDIATRIQUE' if alerte else 'Hémodynamique stable'}"
    return v, txt, alerte

def mgdl_mmol(v: float) -> float:
    return round(v/18.016, 1)
