"""tests/test_prefill.py — Couverture du module clinical/prefill.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clinical.prefill import (
    gcs_to_avpu,
    motif_is_trauma,
    motif_is_avc_suspect,
    build_triage_payload,
)


# ─── gcs_to_avpu ─────────────────────────────────────────────────────────────
def test_gcs_15_returns_alert():
    assert gcs_to_avpu(15) == "A"

def test_gcs_13_14_returns_voice():
    assert gcs_to_avpu(13) == "V"
    assert gcs_to_avpu(14) == "V"

def test_gcs_9_12_returns_pain():
    assert gcs_to_avpu(9)  == "P"
    assert gcs_to_avpu(12) == "P"

def test_gcs_low_returns_unresponsive():
    assert gcs_to_avpu(8) == "U"
    assert gcs_to_avpu(3) == "U"

def test_gcs_none_or_invalid_defaults_to_alert():
    assert gcs_to_avpu(None) == "A"
    assert gcs_to_avpu("abc") == "A"


# ─── motif_is_trauma ────────────────────────────────────────────────────────
def test_trauma_keywords():
    assert motif_is_trauma("Traumatisme crânien") is True
    assert motif_is_trauma("Chute échelle") is True
    assert motif_is_trauma("Fracture du poignet") is True
    assert motif_is_trauma("Douleur thoracique") is False
    assert motif_is_trauma("") is False
    assert motif_is_trauma(None) is False


# ─── motif_is_avc_suspect ───────────────────────────────────────────────────
def test_avc_suspect():
    assert motif_is_avc_suspect("AVC suspecté") is True
    assert motif_is_avc_suspect("Déficit moteur droit") is True
    assert motif_is_avc_suspect("BE-FAST positif") is True
    assert motif_is_avc_suspect("Douleur abdo") is False


# ─── build_triage_payload ───────────────────────────────────────────────────
class _FakeSS(dict):
    """Simule un session_state qui supporte .get() comme un dict."""
    pass


def test_build_triage_payload_defaults():
    ss = _FakeSS({"v_fc": 110, "v_pas": 85, "v_spo2": 90, "v_fr": 26,
                  "v_temp": 38.5, "v_gcs": 13, "eva": 7,
                  "motif": "traumatisme jambe gauche"})
    p = build_triage_payload(ss, ambulance=True)
    assert p["fc"] == 110.0
    assert p["pas"] == 85.0
    assert p["pad"] == 85.0 * 0.65   # estimé si absent
    assert p["spo2"] == 90.0
    assert p["avpu"] == "V"          # GCS 13
    assert p["nrs_pain"] == 7
    assert p["arrival_ambulance"] == 1
    assert p["injury"] == 1          # traumatisme dans motif


def test_build_triage_payload_no_trauma():
    ss = _FakeSS({"v_fc": 75, "v_pas": 120, "v_spo2": 98, "v_fr": 14,
                  "v_temp": 37.0, "v_gcs": 15, "eva": 0,
                  "motif": "Douleur abdominale"})
    p = build_triage_payload(ss)
    assert p["avpu"] == "A"
    assert p["injury"] == 0
