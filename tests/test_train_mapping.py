# tests/test_train_mapping.py — AKIR-IAO v21
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ml.train_ecg_model import (
    scp_to_canonical, select_primary_label, TRAINABLE_LABELS,
)
from clinical.ecg_labels import UNSUPPORTED_CODES


# ── Mapping code SCP — canonique ─────────────────────────────────────────────

def test_norm_mappe():
    assert scp_to_canonical("NORM") == "NORM"

def test_mi_vers_st_elevation():
    assert scp_to_canonical("IMI") == "ST_ELEVATION"
    assert scp_to_canonical("AMI") == "ST_ELEVATION"

def test_ischemie_non_st():
    assert scp_to_canonical("NDT") == "ISCHEMIA_NONST"

def test_conduction():
    assert scp_to_canonical("1AVB") == "AVB1"
    assert scp_to_canonical("3AVB") == "AVB3"
    assert scp_to_canonical("CLBBB") == "LBBB"
    assert scp_to_canonical("CRBBB") == "RBBB"

def test_code_inconnu_ignore():
    assert scp_to_canonical("ZZZ") is None
    assert scp_to_canonical("") is None


# ── Classes sans données jamais entraînées ───────────────────────────────────

def test_classes_non_supportees_exclues():
    for c in UNSUPPORTED_CODES:          # VT, VF, HYPERK
        assert c not in TRAINABLE_LABELS

def test_aucun_mapping_vers_classe_exclue():
    # Aucun code ne doit produire une classe sans données.
    for code in ("IMI", "NDT", "AFIB", "3AVB", "NORM"):
        assert scp_to_canonical(code) not in UNSUPPORTED_CODES


# ── Sélection « pire cas » du label primaire ─────────────────────────────────

def test_plus_urgent_l_emporte():
    # MI (ST_ELEVATION, P1) + BAV1 (P3) — on garde le plus urgent.
    assert select_primary_label(["IMI", "1AVB"]) == "ST_ELEVATION"

def test_norm_seulement_si_seul():
    assert select_primary_label(["NORM"]) == "NORM"
    # NORM accompagné d'une anomalie — l'anomalie l'emporte.
    assert select_primary_label(["NORM", "1AVB"]) == "AVB1"

def test_aucun_code_pertinent():
    assert select_primary_label(["ZZZ", "QQQ"]) is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
