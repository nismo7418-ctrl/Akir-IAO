# tests/test_triage.py — Validation FRENCH Triage V1.1 (SFMU 2018)
# AKIR-IAO v20 — 10 cas critiques P1 (Tri M) → P5 (Tri 5)

import pytest
from clinical.triage import french_triage, verifier_coherence, _MOTIF_INDEX, _norm


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _niv(motif, det=None, **kw):
    """Retourne uniquement le niveau de triage (str) pour alléger les assertions."""
    niv, _, _ = french_triage(motif, det or {}, **kw)
    return niv


URGENT = {"M", "1"}
SEMI_URGENT = {"2"}
NON_URGENT = {"4", "5"}


# ─── CAS 1 — Tri M : Arrêt Cardio-Respiratoire ────────────────────────────────

def test_tri_M_acr():
    """ACR → Tri M quel que soit le contexte."""
    assert _niv("arret cardiorespiratoire", {}) == "M"


# ─── CAS 2 — Tri M : NEWS2 absolu ≥ 9 ────────────────────────────────────────

def test_tri_M_news2_absolu():
    """NEWS2 ≥ 9 verrouille Tri M même sur motif banal."""
    assert _niv("autre motif", {}, n2=9) == "M"


# ─── CAS 3 — Tri 1 : Coma (GCS ≤ 8) ─────────────────────────────────────────

def test_tri_1_coma_gcs():
    """GCS ≤ 8 → priorité absolue Tri 1 via _check_priorites_absolues."""
    assert _niv("alteration de la conscience / coma", {}, gcs=7) == "1"


# ─── CAS 4 — Tri 1 : Purpura fulminans ───────────────────────────────────────

def test_tri_1_purpura_fulminans():
    """Purpura non effaçable → Tri 1 absolu (Ceftriaxone immédiat)."""
    assert _niv("petechie / purpura", {"purpura": True}) == "1"


# ─── CAS 5 — Tri 1 : Détresse respiratoire sévère (SpO2 < 88 %) ──────────────

def test_tri_1_detresse_respiratoire():
    """SpO2 = 82 % + FR = 32 → détresse sévère, Tri 1 absolu."""
    assert _niv("dyspnee / insuffisance respiratoire", {}, spo2=82, fr=32) == "1"


# ─── CAS 6 — Tri 1 : Choc hémorragique (PAS < 80 mmHg) ──────────────────────

def test_tri_1_choc_hemorragique():
    """PAS = 70 mmHg sur hémorragie active → choc hémodynamique Tri 1."""
    assert _niv("hemorragie active", {}, pas=70, fc=130) == "1"


# ─── CAS 7 — Tri 2 : AVC dans fenêtre thrombolyse (≤ 4,5 h) ─────────────────

def test_tri_2_avc_fenetre_thrombolyse():
    """Délai AVC = 3 h ≤ 4,5 h → fenêtre thrombolyse → Tri 2 (ESO 2023)."""
    niv, msg, _ = french_triage("avc / deficit neurologique", {"delai": 3.0}, pas=155)
    assert niv == "2"
    assert "thrombolyse" in msg.lower() or "delai" in msg.lower() or "4,5" in msg


# ─── CAS 8 — Tri 2 : NEWS2 risque élevé (≥ 7) sur motif courant ─────────────

def test_tri_2_news2_risque_eleve():
    """NEWS2 = 7 ≥ seuil risque élevé → upgrade Tri 2 minimum."""
    niv = _niv("fievre", {}, n2=7, age=35)
    assert niv in ("M", "1", "2")


# ─── CAS 9 — Tri 3B : Malaise résolu, patient stable ─────────────────────────

def test_tri_3B_malaise_stable():
    """Malaise résolu, constantes normales → Tri 3B (évaluation différée)."""
    niv = _niv("malaise", {}, gcs=15, pas=120, fc=80, spo2=98, fr=16)
    assert niv in ("3A", "3B")


# ─── CAS 10 — Tri 5 : Motif non urgent / administratif ───────────────────────

def test_tri_5_renouvellement_ordonnance():
    """Renouvellement d'ordonnance → Tri 5, réorientation vers médecine de ville."""
    assert _niv("renouvellement ordonnance", {}) == "5"


# ─── Tests de robustesse ──────────────────────────────────────────────────────

def test_no_exception_motif_inconnu():
    """Motif inconnu ne doit jamais lever d'exception — fallback Tri 3B."""
    niv, _, _ = french_triage("motif_completement_inconnu_xyz", {})
    assert niv in ("M", "1", "2", "3A", "3B", "4", "5")


def test_no_exception_pas_zero_coherence():
    """PAS = 0 dans verifier_coherence ne doit pas lever ZeroDivisionError."""
    danger, warning = verifier_coherence(
        80, 0, 98, 16, 15, 37.0, 0, "fievre", [], {}, 2
    )
    assert isinstance(danger, list)
    assert isinstance(warning, list)


def test_dispatch_bassin_distinct_axial():
    """Correction #20/#21 — handler bassin/hanche ≠ handler thorax/abdomen/rachis."""
    h_axial  = _MOTIF_INDEX.get(_norm("traumatisme thorax / abdomen / rachis cervical"))
    h_bassin = _MOTIF_INDEX.get(_norm("traumatisme bassin / hanche / femur"))
    assert h_axial is not None
    assert h_bassin is not None
    assert h_axial is not h_bassin


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
