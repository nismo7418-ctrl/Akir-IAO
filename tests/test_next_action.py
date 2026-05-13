"""tests/test_next_action.py — Couverture du moteur Next-Best-Action."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clinical.next_action import (
    compute_next_action,
    URGENCY_CRITICAL,
    URGENCY_HIGH,
    URGENCY_MEDIUM,
    URGENCY_LOW,
    URGENCY_DONE,
)


def _base_state(**overrides) -> dict:
    """État de base : patient avec vitaux normaux complets."""
    state = {
        "fc": 75, "pas": 125, "spo2": 98, "fr": 14, "temp": 37.0, "gcs": 15,
        "news2": 0, "news2_error": None,
        "qsofa": 0, "eva": 0,
        "triage_validated": False, "triage_level": None,
        "triage_elapsed_min": 0, "last_reev_min": None,
        "sbar_generated": False, "antalgie_initiee": False,
        "aod_or_avk": False, "trauma": False,
        "avc_suspect": False, "avc_delai_h": None,
        "readmission_risk": None,
    }
    state.update(overrides)
    return state


# ─── 1. Vitaux invalides (priorité absolue) ──────────────────────────────────
def test_vitaux_invalides_prend_priorite():
    action = compute_next_action(_base_state(news2_error="FC hors plage : 999 bpm"))
    assert action.urgency == URGENCY_CRITICAL
    assert "Corriger les vitaux" in action.label


# ─── 2. Vitaux manquants ─────────────────────────────────────────────────────
def test_vitaux_manquants_demande_saisie():
    action = compute_next_action(_base_state(fc=None, pas=None, spo2=None, fr=None))
    assert action.urgency == URGENCY_HIGH
    assert "Saisir" in action.label
    assert action.target_anchor == "akir-anchor-vitaux"


# ─── 3. NEWS2 critique sans triage ───────────────────────────────────────────
def test_news2_critique_declenche_urgence_triage():
    action = compute_next_action(_base_state(news2=9, triage_validated=False))
    assert action.urgency == URGENCY_CRITICAL
    assert "URGENCE" in action.label
    assert "9" in action.label


# ─── 4. AVC fenêtre thrombolyse ──────────────────────────────────────────────
def test_avc_fenetre_ouverte_passe_avant_news2_eleve():
    """L'AVC doit gagner sur NEWS2 6 (sauf si NEWS2 ≥ 7)."""
    action = compute_next_action(_base_state(
        news2=6,
        avc_suspect=True, avc_delai_h=2.5,
    ))
    assert action.urgency == URGENCY_CRITICAL
    assert "Stroke" in action.label or "stroke" in action.label.lower()


def test_avc_fenetre_fermee_pas_de_code_stroke():
    action = compute_next_action(_base_state(
        avc_suspect=True, avc_delai_h=10.0,
        triage_validated=True, triage_level="3A",
    ))
    assert "stroke" not in action.label.lower()


# ─── 5. Sepsis bundle 1h ─────────────────────────────────────────────────────
def test_sepsis_qsofa2_fievre_declenche_bundle():
    action = compute_next_action(_base_state(qsofa=2, temp=38.5))
    assert action.urgency == URGENCY_CRITICAL
    assert "Sepsis" in action.label


# ─── 6. NEWS2 élevé sans triage ──────────────────────────────────────────────
def test_news2_eleve_sans_triage():
    action = compute_next_action(_base_state(news2=5, triage_validated=False))
    assert action.urgency == URGENCY_HIGH
    assert "Valider" in action.label


# ─── 7. AOD + trauma ─────────────────────────────────────────────────────────
def test_aod_trauma_prepare_antidote():
    action = compute_next_action(_base_state(
        aod_or_avk=True, trauma=True,
        triage_validated=True, triage_level="2",
    ))
    assert action.urgency == URGENCY_HIGH
    assert "antidote" in action.label.lower()


# ─── 8. P1 sans SBAR ─────────────────────────────────────────────────────────
def test_p1_valide_sans_sbar_demande_sbar():
    action = compute_next_action(_base_state(
        triage_validated=True, triage_level="1",
        sbar_generated=False,
    ))
    assert action.urgency == URGENCY_HIGH
    assert "SBAR" in action.label
    assert action.target_tabs == "Suivi|SBAR"


# ─── 9. Délai triage dépassé ─────────────────────────────────────────────────
def test_delai_triage_2_depasse():
    action = compute_next_action(_base_state(
        triage_validated=True, triage_level="2",
        triage_elapsed_min=22,  # cible 15 min
        sbar_generated=True,    # pour ne pas matcher P1/SBAR
    ))
    assert action.urgency == URGENCY_CRITICAL
    assert "DÉPASSÉ" in action.label


# ─── 10. Réévaluation due ────────────────────────────────────────────────────
def test_reevaluation_due_apres_30_min():
    action = compute_next_action(_base_state(
        triage_validated=True, triage_level="3A",
        last_reev_min=35,
        sbar_generated=True,
    ))
    assert action.urgency == URGENCY_MEDIUM
    assert "Réévaluation" in action.label


# ─── 11. EVA élevé ───────────────────────────────────────────────────────────
def test_eva_eleve_sans_antalgie():
    action = compute_next_action(_base_state(
        eva=8, antalgie_initiee=False,
        triage_validated=True, triage_level="3A",
    ))
    assert action.urgency == URGENCY_MEDIUM
    assert "Antalgie" in action.label


# ─── 12. Réadmission élevée sous-triée ───────────────────────────────────────
def test_readmission_elevee_triage_4():
    action = compute_next_action(_base_state(
        triage_validated=True, triage_level="4",
        readmission_risk="Élevé",
    ))
    assert action.urgency == URGENCY_MEDIUM
    assert "Réadmission" in action.label


# ─── 13. État stable ─────────────────────────────────────────────────────────
def test_patient_stable_apres_triage():
    action = compute_next_action(_base_state(
        triage_validated=True, triage_level="4",
        last_reev_min=5, sbar_generated=True,
    ))
    assert action.urgency == URGENCY_DONE
    assert "stable" in action.label.lower()


def test_etat_initial_avant_motif():
    """Vitaux OK mais pas encore de triage validé → 'compléter évaluation'."""
    action = compute_next_action(_base_state(news2=2, triage_validated=False))
    assert action.urgency == URGENCY_LOW
    assert "Compléter" in action.label


# ─── Priorités croisées ──────────────────────────────────────────────────────
def test_vitaux_invalides_battent_tout():
    """Même avec NEWS2 critique, les vitaux invalides passent en premier."""
    action = compute_next_action(_base_state(
        news2=None, news2_error="PAS hors plage : 999 mmHg",
        qsofa=2, temp=39.5, avc_suspect=True, avc_delai_h=1.0,
    ))
    assert "Corriger" in action.label


def test_news2_critique_bat_avc():
    """NEWS2 ≥ 7 prend priorité sur AVC car engagement vital immédiat."""
    action = compute_next_action(_base_state(
        news2=9, avc_suspect=True, avc_delai_h=2.0,
    ))
    assert "URGENCE" in action.label
