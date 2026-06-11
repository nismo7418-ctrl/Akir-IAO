# tests/test_ecg_eval.py — AKIR-IAO v21
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ml.ecg_eval import (
    confusion_matrix, per_class_metrics, grouped_sensitivity,
    negative_log_likelihood, fit_temperature, expected_calibration_error,
    safety_gate, STEMI_GROUP,
)

LABELS = ["NORM", "STEMI_INF", "NSTEMI"]


# ── Métriques par classe (maths vérifiables) ─────────────────────────────────

def test_predictions_parfaites():
    yt = ["NORM", "STEMI_INF", "NSTEMI", "NORM"]
    m = per_class_metrics(yt, yt, LABELS)
    for c in LABELS:
        if m[c]["support"]:
            assert m[c]["sensitivity"] == 1.0

def test_sensibilite_connue():
    # 2 STEMI vrais, 1 raté — sensibilité 0.5
    yt = ["STEMI_INF", "STEMI_INF", "NORM", "NORM"]
    yp = ["STEMI_INF", "NORM",      "NORM", "NORM"]
    m = per_class_metrics(yt, yp, LABELS)
    assert m["STEMI_INF"]["sensitivity"] == 0.5
    assert m["STEMI_INF"]["support"] == 2

def test_confusion_matrix_somme():
    yt = ["NORM", "STEMI_INF", "NSTEMI"]
    yp = ["NORM", "NORM", "NSTEMI"]
    cm = confusion_matrix(yt, yp, LABELS)
    assert sum(sum(r) for r in cm) == 3
    assert cm[1][0] == 1   # un STEMI_INF prédit NORM (le pire cas)


# ── Sensibilité groupée STEMI ────────────────────────────────────────────────

def test_grouped_sensitivity_stemi():
    yt = ["STEMI_ANT", "STEMI_INF", "NORM"]
    yp = ["STEMI_LAT", "NORM", "NORM"]   # 1er détecté (territoire faux mais STEMI), 2e raté
    assert grouped_sensitivity(yt, yp, STEMI_GROUP) == 0.5

def test_grouped_sensitivity_aucun():
    assert grouped_sensitivity(["NORM"], ["NORM"], STEMI_GROUP) is None


# ── Calibration ──────────────────────────────────────────────────────────────

def test_temperature_corrige_surconfiance():
    # Logits très tranchés mais souvent faux — T* doit s'éloigner de 1 vers le haut.
    logits = [[6.0, 0.0, 0.0]] * 5 + [[0.0, 6.0, 0.0]] * 5
    y_idx  = [1] * 5 + [0] * 5   # systématiquement la 2e classe (modèle sûr et faux)
    t_star, nll = fit_temperature(logits, y_idx)
    assert t_star > 1.0

def test_nll_diminue_avec_temperature_adaptee():
    logits = [[5.0, 0.0, 0.0]]
    y_idx = [1]                  # vrai = classe 1, mais le modèle pointe la 0
    nll_t1 = negative_log_likelihood(logits, y_idx, 1.0)
    nll_t3 = negative_log_likelihood(logits, y_idx, 3.0)
    assert nll_t3 < nll_t1       # adoucir aide quand le modèle a tort avec confiance

def test_ece_zero_si_parfait():
    # Confiance 1.0 et toujours correct — ECE nul.
    assert expected_calibration_error([1.0, 1.0, 1.0], [True, True, True]) == 0.0

def test_ece_detecte_surconfiance():
    # Confiance 0.9 mais 0 % correct — ECE élevé.
    ece = expected_calibration_error([0.9, 0.9, 0.9, 0.9], [False] * 4)
    assert ece > 0.5


# ── Gate de déployabilité ────────────────────────────────────────────────────

def test_gate_bloque_si_stemi_rate():
    yt = ["STEMI_INF"] * 10 + ["NORM"] * 10
    yp = ["STEMI_INF"] * 8 + ["NORM"] * 2 + ["NORM"] * 10  # rappel STEMI 0.8
    g = safety_gate(yt, yp, LABELS)
    assert g["deployable"] is False
    assert g["stemi_sensitivity"] == 0.8

def test_gate_ok_si_stemi_haut():
    yt = ["STEMI_INF"] * 20 + ["NORM"] * 10
    yp = ["STEMI_INF"] * 20 + ["NORM"] * 10  # rappel 1.0
    g = safety_gate(yt, yp, LABELS)
    assert g["deployable"] is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
