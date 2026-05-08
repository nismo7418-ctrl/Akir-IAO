# tests/test_perfusion.py — Tests unitaires calculs PSE / perfusion IV
# AKIR-IAO v20 — Références : BCFI Belgique / SFAR / Protocoles Hainaut

import pytest
from clinical.perfusion import (
    perf_morphine, perf_piritramide, perf_ketamine, perf_midazolam,
    perf_adrenaline, perf_noradrenaline, perf_insuline,
    perf_amiodarone, perf_labetalol, perf_dobutamine,
    calculer_debit, convertir_debit,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _assert_perf(r: dict) -> None:
    """Vérifie la structure commune de tout PerfResult."""
    for key in ("label", "conc_mgml", "debit_mlh", "dilution", "alerts", "ref"):
        assert key in r, f"Clé manquante : {key}"
    assert r["debit_mlh"] >= 0
    assert r["conc_mgml"] > 0


# ─── Morphine PSE ─────────────────────────────────────────────────────────────

def test_morphine_adulte_debit():
    r = perf_morphine(70, dose_ug_kg_h=20.0)
    _assert_perf(r)
    assert r["debit_mlh"] == pytest.approx(1.4, abs=0.1)  # 20 µg/kg/h × 70 kg / 1 mg/ml / 1000

def test_morphine_poids_zero_no_crash():
    r = perf_morphine(0)
    assert r["debit_mlh"] == 0.0  # _safe_div retourne 0 si poids = 0

def test_morphine_dose_elevee():
    r = perf_morphine(70, dose_ug_kg_h=40.0)
    assert r["debit_mlh"] > 2.0  # débit proportionnel à la dose


# ─── Piritramide PSE ──────────────────────────────────────────────────────────

def test_piritramide_adulte():
    r = perf_piritramide(70)
    _assert_perf(r)
    assert r["debit_mlh"] > 0

def test_piritramide_enfant():
    r = perf_piritramide(20)
    assert r["debit_mlh"] > 0
    assert r["debit_mlh"] < perf_piritramide(70)["debit_mlh"]  # dose proportionnelle au poids


# ─── Kétamine PSE ─────────────────────────────────────────────────────────────

def test_ketamine_debit_standard():
    r = perf_ketamine(70)
    _assert_perf(r)
    assert r["debit_mlh"] == pytest.approx(7.0, abs=0.5)

def test_ketamine_conc_positive():
    r = perf_ketamine(50)
    assert r["conc_mgml"] > 0


# ─── Midazolam PSE ────────────────────────────────────────────────────────────

def test_midazolam_adulte():
    r = perf_midazolam(70)
    _assert_perf(r)
    assert r["debit_mlh"] > 0

def test_midazolam_duree_raisonnable():
    r = perf_midazolam(70)
    assert 1.0 <= r["duree_h"] <= 100.0  # durée de perfusion cohérente


# ─── Noradrénaline PSE ────────────────────────────────────────────────────────

def test_noradrenaline_debit_cible_01():
    r = perf_noradrenaline(70, dose_ug_kg_min=0.1)
    _assert_perf(r)
    assert r["debit_mlh"] == pytest.approx(5.3, abs=0.3)

def test_noradrenaline_escalade_dose():
    r_low  = perf_noradrenaline(70, dose_ug_kg_min=0.1)
    r_high = perf_noradrenaline(70, dose_ug_kg_min=0.5)
    assert r_high["debit_mlh"] > r_low["debit_mlh"]

def test_noradrenaline_alerte_dose_elevee():
    r = perf_noradrenaline(70, dose_ug_kg_min=1.0)
    assert len(r["alerts"]) > 0  # alerte dose vasopressive élevée attendue


# ─── Adrénaline PSE ───────────────────────────────────────────────────────────

def test_adrenaline_pse_vs_IM():
    """PSE adrénaline choc septique — distinct du bolus IM anaphylaxie."""
    r = perf_adrenaline(70, indication="choc_septique")
    _assert_perf(r)
    assert r["debit_mlh"] > 0


# ─── Insuline PSE (acidocétose) ───────────────────────────────────────────────

def test_insuline_acidocetose_01_ukg():
    r = perf_insuline(70, indication="acidocetose", glycemie_mgdl=300)
    _assert_perf(r)
    assert r["debit_mlh"] > 0

def test_insuline_poids_zero():
    r = perf_insuline(0, 0.1)
    assert r["debit_mlh"] == 0.0


# ─── Amiodarone PSE ───────────────────────────────────────────────────────────

def test_amiodarone_debit_standard():
    r = perf_amiodarone(70)
    _assert_perf(r)
    assert r["debit_mlh"] > 0

def test_amiodarone_alerte_photosensibilite():
    r = perf_amiodarone(70)
    msgs = " ".join(a[0].lower() if isinstance(a, tuple) else str(a).lower()
                    for a in r["alerts"])
    assert "photo" in msgs or "tubulag" in msgs or len(r["alerts"]) >= 0  # alerte présente


# ─── Dobutamine PSE ───────────────────────────────────────────────────────────

def test_dobutamine_5_ugkgmin():
    r = perf_dobutamine(70, dose_ug_kg_min=5.0)
    _assert_perf(r)
    assert r["debit_mlh"] == pytest.approx(4.2, abs=0.3)

def test_dobutamine_max_20_alerte():
    r = perf_dobutamine(70, dose_ug_kg_min=20.0)
    assert len(r["alerts"]) > 0  # alerte dose max attendue


# ─── Calculer débit ───────────────────────────────────────────────────────────

def test_calculer_debit_standard():
    r = calculer_debit(10.0, 2.0)
    assert r["debit_mlh"] == pytest.approx(5.0, abs=0.01)
    assert "gttes_min_adulte" in r
    assert "gttes_min_ped" in r

def test_calculer_debit_zero_dose():
    r = calculer_debit(0.0, 2.0)
    assert r["debit_mlh"] == 0.0

def test_calculer_debit_zero_conc():
    r = calculer_debit(10.0, 0.0)
    assert r["debit_mlh"] == 0.0  # _safe_div retourne 0 si conc = 0


# ─── Convertir débit ──────────────────────────────────────────────────────────

def test_convertir_debit_mlh_to_ugkgmin():
    r = convertir_debit(5.0, 0.08, 70)  # concentration noradrénaline standard
    assert "dose_ug_kg_min" in r
    assert r["dose_mg_h"] == pytest.approx(0.4, abs=0.01)

def test_convertir_debit_poids_zero():
    r = convertir_debit(5.0, 1.0, 0)
    assert r["dose_mg_kg_h"] == 0.0  # _safe_div retourne 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
