# tests/test_evaluate_ecg.py — AKIR-IAO v21
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ml.evaluate_ecg import (
    per_class_metrics, group_recall, confusion_matrix,
    calibrate_temperature, softmax, markdown_report,
)


# ── Métriques par classe sur un cas déterministe ─────────────────────────────

def test_sensibilite_specificite_connues():
    y_true = ["NORM", "NORM", "FA", "STEMI_INF"]
    y_pred = ["NORM", "FA",   "FA", "NORM"]
    m = per_class_metrics(y_true, y_pred)
    assert math.isclose(m["NORM"]["sensitivity"], 0.5)
    assert math.isclose(m["NORM"]["specificity"], 0.5)
    assert math.isclose(m["AFIB"]["sensitivity"], 1.0)
    assert math.isclose(m["AFIB"]["specificity"], 2 / 3)
    assert math.isclose(m["ST_ELEVATION"]["sensitivity"], 0.0)


def test_support_compte_les_vrais():
    y_true = ["FA", "FA", "FA", "NORM"]
    y_pred = ["FA", "NORM", "FA", "NORM"]
    m = per_class_metrics(y_true, y_pred)
    assert m["AFIB"]["support"] == 3


# ── Rappel STEMI groupé (tous les territoires — ST_ELEVATION) ─────────────────

def test_rappel_stemi_groupe():
    y_true = ["STEMI_ANT", "STEMI_INF", "NORM"]
    y_pred = ["STEMI_LAT", "NORM",      "NORM"]   # 1 STEMI retrouvé sur 2
    assert math.isclose(group_recall(y_true, y_pred), 0.5)


def test_rappel_stemi_parfait():
    y_true = ["STEMI_ANT", "STEMI_INF"]
    y_pred = ["STEMI_INF", "STEMI_ANT"]           # territoires confondus mais STEMI vu
    assert math.isclose(group_recall(y_true, y_pred), 1.0)


# ── Matrice de confusion ─────────────────────────────────────────────────────

def test_confusion_matrix():
    classes, mat = confusion_matrix(["NORM", "FA"], ["NORM", "NORM"])
    i_norm = classes.index("NORM")
    assert mat[i_norm][i_norm] == 1


# ── Calibration : la sur-confiance doit être corrigée par T > 1 ──────────────

def test_calibration_reduit_nll_si_surconfiant():
    # 3 classes ; modèle très piqué mais qui se trompe parfois — sur-confiant.
    val_logits = [
        [8.0, 0.0, 0.0],   # vrai 0 — correct
        [0.0, 8.0, 0.0],   # vrai 1 — correct
        [8.0, 0.0, 0.0],   # vrai 2 — FAUX et très confiant
    ]
    true_idx = [0, 1, 2]
    res = calibrate_temperature(val_logits, true_idx)
    assert res["temperature"] > 1.0
    assert res["nll_after"] < res["nll_before"]
    assert res["ece_after"] <= res["ece_before"] + 1e-9


def test_calibration_temperature_dans_plage():
    res = calibrate_temperature([[2.0, 1.0], [1.0, 2.0]], [0, 1])
    assert 0.5 <= res["temperature"] <= 5.0


def test_calibration_vide_leve():
    import pytest
    with pytest.raises(ValueError):
        calibrate_temperature([], [])


# ── Rapport markdown ─────────────────────────────────────────────────────────

def test_markdown_report_contient_gate_stemi():
    y_true = ["STEMI_ANT", "NORM"]
    y_pred = ["STEMI_ANT", "NORM"]
    rep = markdown_report(y_true, y_pred)
    assert "Rappel STEMI" in rep
    assert "100.0%" in rep


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
