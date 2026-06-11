# clinical/ecg_labels.py — Taxonomie ECG honnête + support données — AKIR-IAO v21
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Étape 1 de la finalisation ECG (verrou de l'audit) : relabelliser honnêtement.
#
# Principe : l'ECG seul ne « diagnostique » pas un STEMI/NSTEMI (la distinction
# repose sur la troponine). Le modèle DÉTECTE un pattern. On nomme donc les
# sorties pour ce qu'elles sont, et on expose pour chaque classe son SUPPORT
# DONNÉES réel sur PTB-XL :
#     FULL    — couvert correctement
#     PARTIAL — présent mais non distinctif / surtout séquellaire
#     NONE    — quasi absent de PTB-XL — prédiction non fiable, à signaler
#
# Ce module est la SOURCE UNIQUE DE VÉRITÉ pour la criticité et la priorité de
# base ; clinical/ecg_garde_fous.py le consomme.

from __future__ import annotations

import unicodedata
from typing import Tuple

FULL, PARTIAL, NONE = "FULL", "PARTIAL", "NONE"
_P1, _P2, _P3, _P4 = 1, 2, 3, 4

# code — (libellé honnête, critique, priorité de base, support données)
LABELS: dict[str, dict] = {
    "NORM": dict(
        name="ECG sans anomalie aiguë détectée", critical=False,
        base_priority=_P4, support=FULL),
    "ST_ELEVATION": dict(
        name="Sus-décalage ST / pattern ischémique aigu — territoire à préciser, "
             "confirmation troponine + cardiologue",
        critical=True, base_priority=_P1, support=PARTIAL),
    "ISCHEMIA_NONST": dict(
        name="Anomalie ischémique sans sus-décalage (sous-décalage / T inversées) — "
             "un NSTEMI est un diagnostic troponine, pas ECG",
        critical=False, base_priority=_P2, support=PARTIAL),
    "AFIB": dict(
        name="Fibrillation auriculaire", critical=False,
        base_priority=_P3, support=FULL),
    "AFLUTTER": dict(
        name="Flutter auriculaire", critical=False,
        base_priority=_P3, support=FULL),
    "VT": dict(
        name="Tachycardie ventriculaire", critical=True,
        base_priority=_P1, support=NONE),
    "VF": dict(
        name="Fibrillation ventriculaire", critical=True,
        base_priority=_P1, support=NONE),
    "AVB1": dict(
        name="BAV 1er degré", critical=False,
        base_priority=_P3, support=FULL),
    "AVB2": dict(
        name="BAV 2e degré", critical=False,
        base_priority=_P2, support=PARTIAL),
    "AVB3": dict(
        name="BAV 3e degré (complet)", critical=True,
        base_priority=_P1, support=PARTIAL),
    "LBBB": dict(
        name="Bloc de branche gauche", critical=False,
        base_priority=_P3, support=FULL),
    "RBBB": dict(
        name="Bloc de branche droit", critical=False,
        base_priority=_P3, support=FULL),
    "HYPERK": dict(
        name="Aspect évocateur d'hyperkaliémie", critical=True,
        base_priority=_P1, support=NONE),
    "UNKNOWN": dict(
        name="Tracé non classé", critical=False,
        base_priority=_P3, support=PARTIAL),
}

CRITICAL_CODES = {c for c, m in LABELS.items() if m["critical"]}
# Classes dont l'usage clinique est déconseillé tant qu'aucune donnée ne les couvre.
UNSUPPORTED_CODES = {c for c, m in LABELS.items() if m["support"] == NONE}


def _norm(label: str) -> str:
    s = unicodedata.normalize("NFKD", str(label or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper().replace(" ", "").replace("_", "").replace("-", "")


def resolve_code(label: str) -> str:
    """Résout un libellé (canonique OU hérité : STEMI_INF, TV, BBD…) en code canonique."""
    n = _norm(label)
    # Ordre important : NSTEMI avant STEMI ; BAV3 avant BAV2 avant BAV1.
    if "NSTEMI" in n or ("ISCHEM" in n and "NONST" in n):       return "ISCHEMIA_NONST"
    if "STEMI" in n or "SUSDEC" in n or "STELEVATION" in n:     return "ST_ELEVATION"
    if n in ("TV", "VT") or "TACHVENTRIC" in n or "VTACH" in n: return "VT"
    if n in ("FV", "VF") or "FIBVENTRIC" in n or "VFIB" in n:   return "VF"
    if "BAV3" in n or "BAVIII" in n or "AVB3" in n or "AVBIII" in n: return "AVB3"
    if "BAV2" in n or "BAVII" in n or "AVB2" in n or "AVBII" in n:   return "AVB2"
    if "BAV1" in n or "BAVI" in n or "AVB1" in n or "AVBI" in n:     return "AVB1"
    if "HYPERK" in n:                                            return "HYPERK"
    if n == "FA" or "AFIB" in n or "FIBRILLATIONAUR" in n:       return "AFIB"
    if "FLUTTER" in n or "AFLT" in n:                            return "AFLUTTER"
    if "LBBB" in n or "BBG" in n or "BRANCHEG" in n:             return "LBBB"
    if "RBBB" in n or "BBD" in n or "BRANCHED" in n:             return "RBBB"
    if "NORM" in n:                                              return "NORM"
    return "UNKNOWN"


def classify(label: str) -> Tuple[bool, int]:
    """Retourne (est_critique, priorité_de_base) pour un libellé ECG."""
    m = LABELS[resolve_code(label)]
    return m["critical"], m["base_priority"]


def data_support(label: str) -> str:
    """Retourne le niveau de support données (FULL / PARTIAL / NONE)."""
    return LABELS[resolve_code(label)]["support"]


def is_reliable(label: str) -> bool:
    """True seulement si la classe est correctement couverte par les données."""
    return data_support(label) == FULL


def is_normal(label: str) -> bool:
    return resolve_code(label) == "NORM"


def display_name(label: str) -> str:
    return LABELS[resolve_code(label)]["name"]
