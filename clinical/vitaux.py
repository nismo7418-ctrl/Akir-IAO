# clinical/vitaux.py — Indices hémodynamiques
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Références : Acker 2015 (SIPA), Allgöwer 1967 (Shock Index)

from typing import Tuple
from config import SIPA_0_1AN, SIPA_1_4ANS, SIPA_4_7ANS, SIPA_7_12ANS


def si(fc: float, pas: float) -> float:
    """Shock Index adulte = FC / PAS. Seuil critique ≥ 1.0."""
    return round(fc / pas, 2) if pas and pas > 0 else 0.0


def sipa(fc: float, age: float) -> Tuple[float, str, bool]:
    """
    SIPA — Shock Index Pédiatrique adapté à l'âge.
    Retourne (valeur, texte_alerte, est_alerte).
    Source : Acker SN et al., J Trauma 2015.
    """
    # PAS normale basse estimée selon l'âge (formule simplifiée)
    pas_min = float(age) * 2 + 70 if age >= 1 else 70.0
    v = round(fc / max(1.0, pas_min), 2)

    if age <= 1:
        seuil = SIPA_0_1AN
    elif age <= 4:
        seuil = SIPA_1_4ANS
    elif age <= 7:
        seuil = SIPA_4_7ANS
    else:
        seuil = SIPA_7_12ANS

    alerte = v > seuil
    txt = (
        f"SIPA {v} {'>' if alerte else '<='} {seuil} — "
        f"{'⚠️ CHOC PÉDIATRIQUE' if alerte else 'Hémodynamique stable'}"
    )
    return v, txt, alerte


def mgdl_mmol(v: float) -> float:
    """Conversion glycémie mg/dl → mmol/l."""
    return round(v / 18.016, 1)
