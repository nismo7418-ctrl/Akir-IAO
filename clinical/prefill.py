"""
clinical/prefill.py — Helpers de pré-remplissage inter-modules.

Évite à l'IAO de re-saisir les mêmes données dans l'onglet IA Triage (KTAS).
Pures functions, sans dépendance Streamlit.

Fonctions publiques :
    gcs_to_avpu(gcs)           → str ("A","V","P","U")
    motif_is_trauma(motif)     → bool
    motif_is_avc_suspect(motif)→ bool
    build_triage_payload(ss)   → dict prêt pour ml.triage_predictor
"""
from __future__ import annotations

from typing import Iterable


# ──────────────────────────────────────────────────────────────────────────────
# Mapping GCS → AVPU (pour le modèle triage KTAS)
# Source : Kelly CA et al., Resuscitation 2004 — équivalence cliniquement admise.
# ──────────────────────────────────────────────────────────────────────────────

def gcs_to_avpu(gcs: int | None) -> str:
    """Convertit un GCS (3-15) en lettre AVPU.

    Mapping (Kelly 2004) :
        GCS 15      → "A" (Alert)
        GCS 13-14   → "V" (Voice — répond à la voix)
        GCS 9-12    → "P" (Pain — répond à la douleur)
        GCS ≤ 8     → "U" (Unresponsive)
    """
    if gcs is None:
        return "A"
    try:
        g = int(gcs)
    except (TypeError, ValueError):
        return "A"
    if g >= 15:
        return "A"
    if g >= 13:
        return "V"
    if g >= 9:
        return "P"
    return "U"


# ──────────────────────────────────────────────────────────────────────────────
# Détection trauma / AVC depuis motif libre
# ──────────────────────────────────────────────────────────────────────────────

_TRAUMA_KEYWORDS = (
    "trauma", "traumat", "chute", "accident", "fracture", "plaie",
    "brûlure", "brulure", "polytrauma", "ecrasement", "écrasement",
    "agression", "morsure", "blessure",
)


def motif_is_trauma(motif: str | None) -> bool:
    """True si le motif décrit un traumatisme."""
    if not motif:
        return False
    return any(k in str(motif).lower() for k in _TRAUMA_KEYWORDS)


def motif_is_avc_suspect(motif: str | None) -> bool:
    """True si le motif évoque un AVC / déficit neurologique."""
    if not motif:
        return False
    return any(k in str(motif).lower() for k in (
        "avc", "déficit", "deficit", "hémiplégie", "hemiplegie",
        "aphasie", "stroke", "be-fast", "fast",
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Builder de payload pour le modèle KTAS
# `ss` = streamlit session_state (passé en argument pour rester pure)
# ──────────────────────────────────────────────────────────────────────────────

def _sget(ss, key: str, default=None):
    """Helper compatible session_state ET dict (pour les tests)."""
    if hasattr(ss, "get"):
        return ss.get(key, default)
    return getattr(ss, key, default)


def build_triage_payload(ss, *, ambulance: bool = False) -> dict:
    """Construit le dict prêt pour ml.triage_predictor.get_ml_priority().

    Utilise les vitaux courants saisis dans l'onglet Triage + dérive AVPU
    depuis le GCS et le flag 'injury' depuis le motif.
    """
    fc   = float(_sget(ss, "v_fc", 80))
    pas  = float(_sget(ss, "v_pas", 120))
    pad  = float(_sget(ss, "v_pad", pas * 0.65))
    return {
        "fc":   fc,
        "fr":   float(_sget(ss, "v_fr", 16)),
        "pas":  pas,
        "pad":  pad,
        "spo2": float(_sget(ss, "v_spo2", 98)),
        "temp": float(_sget(ss, "v_temp", 37.0)),
        "avpu": gcs_to_avpu(_sget(ss, "v_gcs", 15)),
        "nrs_pain":          int(_sget(ss, "eva", 0) or 0),
        "arrival_ambulance": int(bool(ambulance)),
        "injury":            int(motif_is_trauma(_sget(ss, "motif", ""))),
    }
