# tests/test_scores.py — Tests unitaires pour les scores cliniques
# AKIR-IAO v20 — Tests pour validation des calculs médicaux

import pytest
from clinical.scores import calculer_gcs, calculer_qsofa
from clinical.news2 import calculer_news2
from clinical.vitaux import si
from clinical.pharmaco import (
    paracetamol, morphine, piritramide,
    sepsis_bundle_1h, _format_dose,
)
from clinical.tools import (
    calculer_recharge_volemique, calculer_dfge, convertir_opioides, corriger_natrémie,
)
from clinical.scores import calculer_ciwa
from persistence.registry import _load, _save


# ─── GCS ──────────────────────────────────────────────────────────────────────

def test_gcs_normal():
    r = calculer_gcs(4, 5, 6, 25)
    assert r["score_val"] == 15
    assert "normale" in r["interpretation"]

def test_gcs_coma():
    r = calculer_gcs(1, 1, 1, 25)
    assert r["score_val"] == 3
    assert "Coma" in r["interpretation"]

def test_gcs_clamp_haut():
    r = calculer_gcs(5, 6, 7, 25)  # valeurs hors bornes → clampé à 15
    assert r["score_val"] == 15

def test_gcs_clamp_bas():
    r = calculer_gcs(0, 0, 0, 25)  # sous le minimum → clampé à 3
    assert r["score_val"] == 3


# ─── qSOFA ────────────────────────────────────────────────────────────────────

def test_qsofa_normal():
    r = calculer_qsofa(16, 15, 120)
    assert r["score_val"] == 0
    assert "peu probable" in r["interpretation"]

def test_qsofa_sepsis():
    r = calculer_qsofa(25, 13, 95)
    assert r["score_val"] == 3
    assert "SEPSIS SUSPECTÉ" in r["interpretation"]

def test_qsofa_un_critere():
    r = calculer_qsofa(25, 15, 120)  # seule FR élevée
    assert r["score_val"] == 1


# ─── NEWS2 ────────────────────────────────────────────────────────────────────

def test_news2_patient_normal():
    score, alertes = calculer_news2(16, 97, False, 37.0, 120, 75, 15, False)
    assert score == 0
    assert alertes == []

def test_news2_critique():
    # FR=30, SpO2=85, O2=True, T=38.5, PAS=85, FC=120, GCS=10
    score, alertes = calculer_news2(30, 85, True, 38.5, 85, 120, 10, False)
    assert score >= 9
    assert any("ENGAGEMENT VITAL" in a for a in alertes)

def test_news2_bpco_hyperoxie():
    # SpO2=98 sous O2 chez un BPCO → alerte hyperoxie attendue
    score, alertes = calculer_news2(16, 98, True, 37.0, 120, 75, 15, True)
    assert any("hyperoxie" in a.lower() or "hypercapnie" in a.lower() for a in alertes)

def test_news2_valeurs_invalides_type():
    """Sécurité patient : fail-loud sur types non numériques.
    Un score=0 silencieux trierait à tort un patient critique en P5.
    """
    import pytest
    with pytest.raises(ValueError, match="non numérique"):
        calculer_news2("x", None, False, "y", 120, 75, 15, False)


def test_news2_valeurs_hors_plage():
    """Sécurité patient : fail-loud sur vitaux hors plages physiologiques."""
    import pytest
    # FC = 999 (impossible physiologiquement)
    with pytest.raises(ValueError, match="FC hors plage"):
        calculer_news2(16, 97, False, 37.0, 120, 999, 15, False)
    # SpO2 = 150 % (impossible)
    with pytest.raises(ValueError, match="SpO2 hors plage"):
        calculer_news2(16, 150, False, 37.0, 120, 75, 15, False)
    # GCS = 20 (max = 15)
    with pytest.raises(ValueError, match="GCS hors plage"):
        calculer_news2(16, 97, False, 37.0, 120, 75, 20, False)


# ─── Shock Index si() ─────────────────────────────────────────────────────────

def test_si_normal():
    assert si(75, 120) == 0.62  # 75/120=0.625, banker's rounding → 0.62

def test_si_choc():
    assert si(120, 80) == 1.5

def test_si_pas_zero():
    # PAS=0 → retourne 0.0 sans lever d'exception
    assert si(80, 0) == 0.0

def test_si_pas_negative():
    assert si(80, -1) == 0.0


# ─── Pharmacologie ────────────────────────────────────────────────────────────

def test_paracetamol_adulte():
    r, err = paracetamol(70, 35, [])
    assert err is None
    assert r["dose_mg"] == 1000

def test_paracetamol_enfant():
    r, err = paracetamol(30, 8, [])
    assert err is None
    assert r["dose_mg"] == pytest.approx(450, abs=5)

def test_morphine_adulte_standard():
    r, err = morphine(70, 35, [])
    assert err is None
    assert r["dose_min"] > 0
    assert r["dose_max"] <= 10.0

def test_morphine_sujet_age():
    r, err = morphine(60, 75, [])
    assert err is None
    assert r["facteur"] == 0.5  # réduction 50 % attendue

def test_morphine_irc():
    r, err = morphine(70, 45, ["Insuffisance rénale chronique"])
    assert err is None
    assert r["facteur"] == 0.5

def test_piritramide_nourrisson_ci():
    r, err = piritramide(5, 0.5, [])  # < 1 an → CI absolue
    assert r is None
    assert "CONTRE-INDIQUÉ" in err

def test_format_dose_poids_zero():
    # Poids=0 ne doit pas lever ZeroDivisionError
    result = _format_dose(500, 0, 10)
    assert "invalide" in result


# ─── Sepsis bundle ────────────────────────────────────────────────────────────

def test_sepsis_choc_frank():
    r = sepsis_bundle_1h(80, 4.5, 38.5, 125, 70)
    assert r["choc_septique"] is True
    assert "choc_intermediaire" in r  # correction #12 — doit être présent

def test_sepsis_intermediaire():
    r = sepsis_bundle_1h(105, 2.5, 38.0, 90, 70)
    assert r["choc_septique"] is False
    assert r["choc_intermediaire"] is True  # lactate 2-4

def test_sepsis_stable():
    r = sepsis_bundle_1h(120, 1.0, 37.5, 80, 70)
    assert r["choc_septique"] is False
    assert r["choc_intermediaire"] is False


# ─── Recharge volémique ───────────────────────────────────────────────────────

def test_recharge_adulte():
    r = calculer_recharge_volemique(70, 40, "sepsis")
    assert r["bolus_ml"] == 500
    assert len(r["bolus_list"]) == 3

def test_recharge_pediatrique():
    r = calculer_recharge_volemique(20, 8, "deshy")
    assert r["bolus_ml"] == 200  # 10 ml/kg × 20 kg

def test_recharge_poids_zero():
    # poids=0 ne doit pas lever ZeroDivisionError (correction #15)
    r = calculer_recharge_volemique(0, 40, "sepsis")
    for bolus in r["bolus_list"]:
        assert bolus["total_ml_kg"] == 0.0


# ─── Registry ─────────────────────────────────────────────────────────────────

def test_registry_roundtrip(tmp_path, monkeypatch):
    import persistence.registry as reg
    test_file = str(tmp_path / "test_reg.json")
    monkeypatch.setattr(reg, "RF", test_file)
    data = [{"uid": "ABCD1234", "motif": "test", "niv": "3A"}]
    reg._save(data)
    loaded = reg._load()
    assert loaded == data

def test_registry_load_json_corrompu(tmp_path, monkeypatch):
    import persistence.registry as reg
    test_file = str(tmp_path / "bad_reg.json")
    monkeypatch.setattr(reg, "RF", test_file)
    with open(test_file, "w") as f:
        f.write("{invalid json{{")
    result = reg._load()
    assert result == []  # retourne liste vide sans crash


# ─── DFGe CKD-EPI ─────────────────────────────────────────────────────────────

def test_dfge_adulte_normal():
    r = calculer_dfge(80, 45, "H")  # créatinine 80 µmol/L, homme 45 ans
    assert r.get("dfge") is not None
    assert r["dfge"] > 60  # DFGe normal attendu

def test_dfge_insuffisance_rénale():
    r = calculer_dfge(350, 70, "H")  # créatinine très élevée
    assert r["dfge"] < 30  # insuffisance rénale sévère attendue

def test_dfge_creatinine_zero():
    # correction #18 — ne doit pas crasher avec ZeroDivisionError
    r = calculer_dfge(0, 45, "H")
    assert "erreur" in r
    assert r["dfge"] is None

def test_dfge_creatinine_negative():
    r = calculer_dfge(-10, 45, "H")
    assert "erreur" in r

def test_dfge_sexe_femme():
    r = calculer_dfge(80, 45, "F")
    assert r.get("dfge") is not None
    assert r["dfge"] > 60


# ─── Convertisseur opioïdes ───────────────────────────────────────────────────

def test_opioides_morphine_vers_piritramide():
    r = convertir_opioides("Morphine IV", 10.0, "Piritramide IV")
    assert "erreur" not in r
    assert r["dose_calculee_mg"] == pytest.approx(10.0 / 0.7, abs=0.1)
    assert r["dose_demarrage_mg"] == pytest.approx(r["dose_calculee_mg"] * 0.5, abs=0.1)

def test_opioides_molecule_inconnue():
    r = convertir_opioides("DrugXYZ", 10.0, "Morphine IV")
    assert "erreur" in r

def test_opioides_cible_inconnue():
    r = convertir_opioides("Morphine IV", 10.0, "DrugXYZ")
    assert "erreur" in r

def test_opioides_fentanyl_puissant():
    r = convertir_opioides("Fentanyl IV", 0.1, "Morphine IV")
    assert r["morphine_iv_eq_mg"] == pytest.approx(10.0, abs=0.1)  # 0.1 mg × 100


# ─── Correction natrémie ──────────────────────────────────────────────────────

def test_natremie_normale():
    r = corriger_natrémie(138, 6.0)  # glycémie légèrement élevée
    assert r["na_corrige_hillier"] > 138
    assert r["niveau"] == "success"

def test_natremie_hyperglycemie_severe():
    r = corriger_natrémie(128, 30.0)  # hyperglycémie cétoacidosique
    assert r["na_corrige_hillier"] > 128

def test_natremie_glycemie_invalide():
    r = corriger_natrémie(138, 0)
    assert "erreur" in r

def test_natremie_hyponatremie():
    r = corriger_natrémie(126, 5.6)
    assert r["niveau"] == "danger"


# ─── CIWA sevrage alcoolique ──────────────────────────────────────────────────

def test_ciwa_leger():
    r = calculer_ciwa(1, 1, 1, 0, 0, 0, 0, 0, 0, 0)  # score = 3
    assert r["score_val"] == 3
    assert "léger" in r["interpretation"].lower()

def test_ciwa_delirium_tremens():
    r = calculer_ciwa(7, 7, 7, 7, 7, 7, 7, 7, 7, 4)  # score = 66
    assert r["score_val"] >= 20
    assert "Delirium" in r["interpretation"]

def test_ciwa_normal():
    r = calculer_ciwa(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert r["score_val"] == 0


# ─── Moteur de triage FRENCH ──────────────────────────────────────────────────

from clinical.triage import french_triage, _MOTIF_INDEX, _norm

def test_triage_bassin_handler_distinct_from_axial():
    # Correction #20/#21 — _h_trauma_pelvi ≠ _h_trauma_axial dans le dispatch
    handler_axial  = _MOTIF_INDEX.get(_norm("traumatisme thorax/abdomen/rachis cervical"))
    handler_bassin = _MOTIF_INDEX.get(_norm("traumatisme bassin/hanche/femur"))
    assert handler_axial is not None
    assert handler_bassin is not None
    assert handler_axial is not handler_bassin  # handlers doivent être distincts

def test_triage_acr_tri_M():
    niv, msg, _ = french_triage("arrêt cardiorespiratoire", {})
    assert niv == "M"

def test_triage_spo2_bas_tri1():
    niv, msg, _ = french_triage("dyspnée / insuffisance respiratoire", {},
                                  spo2=85, fr=18)
    assert niv == "1"

def test_triage_news2_eleve_upgrade():
    # NEWS2=8 ≥ 7 → Tri 2 minimum même si le motif donne 3B
    niv, _, _ = french_triage("autre motif", {}, n2=8)
    assert niv in ("M", "1", "2")

def test_triage_nourrisson_tri1():
    # Nourrisson ≤ 3 mois → worst-case Tri 1 quel que soit le motif
    niv, _, _ = french_triage("fièvre", {}, age=0.1, temp=38.5)
    assert niv == "1"

def test_triage_fallback_motif_inconnu():
    # Motif inconnu → fallback Tri 3B (jamais exception)
    niv, _, _ = french_triage("motif_inexistant_xyz", {})
    assert niv in ("M", "1", "2", "3A", "3B", "4", "5")

def test_triage_trauma_bassin_choc():
    # Choc hémorragique sur fracture bassin → Tri 1
    niv, _, _ = french_triage("traumatisme bassin/hanche/fémur", {},
                                fc=130, pas=60)
    assert niv in ("M", "1")

def test_triage_pas_zero_no_crash():
    # PAS=0 ne doit pas lever ZeroDivisionError dans verifier_coherence
    from clinical.triage import verifier_coherence
    d, w = verifier_coherence(80, 0, 98, 16, 15, 37.0, 0,
                               "fièvre", [], {}, 2)
    assert isinstance(d, list)
    assert isinstance(w, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
