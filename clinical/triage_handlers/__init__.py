"""Compatibility layer for the triage dispatcher.

The active triage engine now lives in clinical.triage.  This module keeps the
old resolve_handler import path usable without importing Streamlit UI helpers.
"""

from clinical.triage import _MOTIF_INDEX, _TRIAGE_DISPATCH, _norm

TRIAGE_DISPATCH = _TRIAGE_DISPATCH


def resolve_handler(motif: str):
    return _MOTIF_INDEX.get(_norm(motif))
