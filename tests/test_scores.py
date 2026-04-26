# tests/test_scores.py — Tests unitaires pour les scores cliniques
# AKIR-IAO v19.0 — Tests pour validation des calculs médicaux

import pytest
from clinical.scores import calculer_gcs, calculer_qsofa

def test_calculer_gcs_normal():
    """Test GCS normal (15)"""
    result = calculer_gcs(4, 5, 6, 25)  # Yeux 4, Verbal 5, Moteur 6
    assert result["score_val"] == 15
    assert "normale" in result["interpretation"]

def test_calculer_gcs_coma():
    """Test GCS coma (3)"""
    result = calculer_gcs(1, 1, 1, 25)
    assert result["score_val"] == 3
    assert "Coma" in result["interpretation"]

def test_calculer_qsofa_normal():
    """Test qSOFA normal (0)"""
    result = calculer_qsofa(16, 15, 120)  # FR normal, GCS normal, PAS normal
    assert result["score_val"] == 0
    assert "peu probable" in result["interpretation"]

def test_calculer_qsofa_severe():
    """Test qSOFA sepsis (3)"""
    result = calculer_qsofa(25, 13, 95)  # FR élevé, GCS altéré, PAS basse
    assert result["score_val"] == 3
    assert "SEPSIS SUSPECTÉ" in result["interpretation"]

if __name__ == "__main__":
    pytest.main([__file__])