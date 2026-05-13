"""tests/test_prefill.py — Couverture du module clinical/prefill.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clinical.prefill import (
    atcd_to_charlson,
    atcd_contains_anticoag,
    gcs_to_avpu,
    motif_is_trauma,
    motif_is_avc_suspect,
    build_triage_payload,
    build_mortality_payload,
    build_readmission_prefill,
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


# ─── atcd_to_charlson ────────────────────────────────────────────────────────
def test_atcd_empty_returns_empty():
    assert atcd_to_charlson([]) == []
    assert atcd_to_charlson(None) == []

def test_atcd_diabete_maps_to_charlson():
    keys = atcd_to_charlson(["Diabète type 2"])
    assert "diabete_sans_compl" in keys

def test_atcd_avc_maps():
    assert "avc" in atcd_to_charlson(["AVC / AIT antérieur"])

def test_atcd_multiple_no_duplicates():
    # Type 1 + Type 2 → ne doivent produire qu'une seule entrée diabete
    keys = atcd_to_charlson(["Diabète type 1", "Diabète type 2"])
    assert keys.count("diabete_sans_compl") == 1

def test_atcd_bpco_asthme_dedupe():
    keys = atcd_to_charlson(["BPCO", "Asthme"])
    assert keys.count("bpco") == 1

def test_atcd_unknown_ignored():
    keys = atcd_to_charlson(["HTA", "Diabète type 2"])
    # HTA n'est pas dans Charlson
    assert "diabete_sans_compl" in keys
    assert len(keys) == 1


# ─── atcd_contains_anticoag ─────────────────────────────────────────────────
def test_anticoag_detection():
    assert atcd_contains_anticoag(["Anticoagulants/AOD"]) is True
    assert atcd_contains_anticoag(["HTA"]) is False
    assert atcd_contains_anticoag([]) is False
    assert atcd_contains_anticoag(["traitement par Eliquis"]) is True


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


# ─── build_mortality_payload ────────────────────────────────────────────────
def test_build_mortality_payload_sans_reev():
    """Pas de réévaluations → mean = courant, min/max ± variation."""
    ss = _FakeSS({"v_fc": 100, "v_pas": 100, "v_spo2": 92, "v_fr": 22,
                  "v_temp": 38.0, "v_gcs": 14, "age": 72, "sexe": "Femme",
                  "niv": "1", "reevs": []})
    p = build_mortality_payload(ss)
    assert p["hr_mean"]  == 100.0
    assert p["hr_min"]   < 100.0     # min étendu vers le bas
    assert p["hr_max"]   > 100.0
    assert p["spo2_mean"] == 92.0
    assert p["gender_enc"] == 1      # femme
    assert p["age_approx"] == 72.0
    assert p["admission_type_enc"] == 2   # niv=1 → EMERGENCY


def test_build_mortality_payload_avec_reev():
    """Avec 3+ réévaluations → vrais agrégats min/max."""
    reevs = [
        {"fc": 120, "pas": 80, "spo2": 88, "fr": 28, "temp": 39.0,
         "h": "2026-01-01T08:00:00"},
        {"fc": 130, "pas": 75, "spo2": 85, "fr": 30, "temp": 39.5,
         "h": "2026-01-01T08:30:00"},
        {"fc": 140, "pas": 70, "spo2": 82, "fr": 32, "temp": 40.0,
         "h": "2026-01-01T09:00:00"},
    ]
    ss = _FakeSS({"v_fc": 110, "v_pas": 85, "v_spo2": 90, "v_fr": 26,
                  "v_temp": 38.5, "age": 65, "sexe": "Homme",
                  "niv": "1", "reevs": reevs})
    p = build_mortality_payload(ss)
    # min = 110 (la valeur courante reste la plus basse pour FC croissante)
    assert p["hr_max"] == 140
    assert p["spo2_min"] == 82
    assert p["gender_enc"] == 0


# ─── build_readmission_prefill ──────────────────────────────────────────────
def test_readmission_prefill_urgence_si_triage_critique():
    ss = _FakeSS({"niv": "2", "atcd": ["BPCO", "Diabète type 2"], "age": 67})
    p = build_readmission_prefill(ss)
    assert p["urgence_admission"] is True
    assert "bpco" in p["comorbidites_charlson"]
    assert "diabete_sans_compl" in p["comorbidites_charlson"]
    assert p["age"] == 67


def test_readmission_prefill_pas_urgence_triage_5():
    ss = _FakeSS({"niv": "5", "atcd": [], "age": 45})
    p = build_readmission_prefill(ss)
    assert p["urgence_admission"] is False
    assert p["comorbidites_charlson"] == []


def test_readmission_prefill_anticoag_detection():
    ss = _FakeSS({"niv": "3A", "atcd": ["HTA", "Anticoagulants/AOD"]})
    p = build_readmission_prefill(ss)
    assert p["anticoag"] is True
