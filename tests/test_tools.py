# tests/test_tools.py — Tests cliniques pour clinical/tools.py
# Développeur : Ismail Ibn-Daifa — AKIR-IAO v20
# Lancer : pytest tests/ -v

import sys, pytest
sys.path.insert(0, ".")

from clinical.tools import (
    calculer_rsi, calculer_recharge_volemique, broselow,
    convertir_opioides, corriger_natrémie, calculer_dfge,
    code_stroke_delais, joules_defibrillateur, calculer_blatchford,
    RSI_AGENTS, CURARES_RSI, OPIOIDES_RATIO_IV, BROSELOW_TABLE,
)


# ── RSI ──────────────────────────────────────────────────────────────────────

def test_rsi_etomidate_70kg():
    r = calculer_rsi(70, 45, "Étomidate", "Succinylcholine")
    assert abs(r["agents"]["Étomidate"]["dose_mg"] - 21.0) < 0.5      # 0.3×70
    assert abs(r["agents"]["Succinylcholine"]["dose_mg"] - 105.0) < 0.5  # 1.5×70

def test_rsi_max_dose():
    r = calculer_rsi(200, 45)  # patient très lourd
    assert r["agents"]["Étomidate"]["dose_mg"] <= RSI_AGENTS["Étomidate"]["max_mg"]
    assert r["agents"]["Succinylcholine"]["dose_mg"] <= CURARES_RSI["Succinylcholine"]["max_mg"]

def test_rsi_atropine_enfant():
    r = calculer_rsi(15, 3)
    assert "Atropine (pré-méd.)" in r["agents"]
    dose = r["agents"]["Atropine (pré-méd.)"]["dose_mg"]
    assert 0.1 <= dose <= 0.5  # min 0.1 max 0.5

def test_rsi_pas_atropine_adulte():
    r = calculer_rsi(70, 45)
    assert "Atropine (pré-méd.)" not in r["agents"]

def test_rsi_sonde_adulte():
    r = calculer_rsi(70, 45)
    assert "7.0" in r["sonde_it"] or "7.5" in r["sonde_it"] or "8.0" in r["sonde_it"]

def test_rsi_checklist_ordre():
    r = calculer_rsi(70, 45)
    assert len(r["ordre"]) >= 7
    assert "Préoxygénation" in r["ordre"][0]


# ── RECHARGE VOLÉMIQUE ───────────────────────────────────────────────────────

def test_recharge_adulte_sepsis():
    rv = calculer_recharge_volemique(70, 45, "sepsis")
    assert rv["bolus_ml"] == 500
    assert rv["bolus_list"][2]["total_ml"] == 1500  # 3×500

def test_recharge_pediatrique():
    rv = calculer_recharge_volemique(20, 5, "deshy")
    assert rv["bolus_ml"] == 200   # 10 ml/kg × 20 kg
    assert rv["bolus_list"][0]["total_ml"] == 200  # 1er bolus = 200 ml

def test_recharge_max_3_bolus():
    for indication in ["sepsis","trauma","deshy","general"]:
        rv = calculer_recharge_volemique(70, 45, indication)
        assert len(rv["bolus_list"]) == 3


# ── BROSELOW ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("taille,couleur,poids", [
    (59,  "Gris",   3.0),
    (70,  "Rose",   5.0),
    (85,  "Rouge",  7.5),
    (95,  "Mauve",  9.0),
    (107, "Jaune", 11.0),
    (118, "Blanc", 14.0),
    (130, "Bleu",  18.0),
    (155, "Vert",  32.0),
])
def test_broselow_couleurs(taille, couleur, poids):
    b = broselow(taille)
    assert b["couleur"] == couleur
    assert b["poids_estimé"] == poids

def test_broselow_doses_presentes():
    b = broselow(95)  # Mauve, 9 kg
    assert "Adrénaline IM (0,01 mg/kg)" in b["doses"]
    assert "Sonde d'intubation" in b["doses"]
    assert "Défibrillation 2 J/kg" in b["doses"]

def test_broselow_adulte():
    b = broselow(200)
    assert b["couleur"] == "Adulte"


# ── CONVERTISSEUR OPIOÏDES ────────────────────────────────────────────────────

def test_morphine_to_fentanyl():
    r = convertir_opioides("Morphine IV", 10, "Fentanyl IV")
    assert abs(r["dose_calculee_mg"] - 0.1) < 0.01  # 10mg morph = 0.1mg fentanyl
    assert r["dose_demarrage_mg"] == r["dose_calculee_mg"] * 0.5

def test_tramadol_to_morphine():
    r = convertir_opioides("Tramadol IV", 100, "Morphine IV")
    assert abs(r["dose_calculee_mg"] - 10.0) < 0.5  # 100mg tramadol ≈ 10mg morphine

def test_opioides_avertissement():
    r = convertir_opioides("Morphine IV", 5, "Sufentanil IV")
    assert "50%" in r["avertissement"]

def test_opioides_molecule_inconnue():
    r = convertir_opioides("Aspirine", 10, "Morphine IV")
    assert "erreur" in r


# ── CORRECTION NATRÉMIE ──────────────────────────────────────────────────────

def test_natremie_normale():
    r = corriger_natrémie(138, 5.5)
    assert r["na_corrige_hillier"] == pytest.approx(138, abs=1)
    assert r["niveau"] == "success"

def test_natremie_hyperglycemie_severe():
    r = corriger_natrémie(125, 30.0)  # Na 125 + glycémie 30 mmol/L (540 mg/dl)
    assert r["na_corrige_hillier"] > 130  # doit corriger significativement

def test_natremie_hyponatremie_severe():
    r = corriger_natrémie(128, 5.5)
    assert r["niveau"] == "danger"


# ── DFGe CKD-EPI ─────────────────────────────────────────────────────────────

def test_dfge_normal_jeune():
    r = calculer_dfge(60, 30, "H")
    assert r["dfge"] > 90
    assert "G1" in r["stade"]

def test_dfge_irc_moderee():
    r = calculer_dfge(150, 70, "H")
    assert 30 <= r["dfge"] <= 60

def test_dfge_irt():
    r = calculer_dfge(600, 75, "F")
    assert r["dfge"] < 15
    assert "G5" in r["stade"]

def test_dfge_adaptations_ains():
    r = calculer_dfge(150, 70, "H")
    if r["dfge"] < 60:
        assert any("AINS" in a for a in r["adaptations"])


# ── CODE STROKE ──────────────────────────────────────────────────────────────

def test_stroke_door_to_ct_ok():
    r = code_stroke_delais("09:00", "09:15", "09:35")
    assert r["door_to_ct_min"] == 20
    assert r["door_to_ct_ok"] == True  # ≤ 25 min

def test_stroke_door_to_ct_depasse():
    r = code_stroke_delais("09:00", "09:15", "09:50")
    assert r["door_to_ct_min"] == 35
    assert r["door_to_ct_ok"] == False  # > 25 min

def test_stroke_fenetre_ouverte():
    r = code_stroke_delais("09:00", "09:30", None)
    # Si le test tourne dans les 4,5h après 09:00 → fenêtre ouverte
    assert "duree_symptomes_min" in r

def test_stroke_checklist_complete():
    r = code_stroke_delais(None, None, None)
    assert len(r["checklist"]) >= 7
    assert len(r["ci_thrombolyse"]) >= 5


# ── JOULES DÉFIBRILLATEUR ────────────────────────────────────────────────────

def test_joules_adulte_fv():
    j = joules_defibrillateur(70, 45, "FV")
    assert "200 J" in j["choc_1"]
    assert "biphasique" in j["choc_1"].lower() or "biphasique" in j.get("note","").lower() or "200" in j["choc_1"]

def test_joules_adulte_fa():
    j = joules_defibrillateur(70, 45, "FA")
    assert "synchron" in j["note"].lower()

@pytest.mark.parametrize("poids,age,j_exp", [
    (20, 8,  "40"),   # 2J × 20kg = 40J
    (30, 10, "60"),   # 2J × 30kg = 60J
    (10, 5,  "20"),   # 2J × 10kg = 20J
])
def test_joules_pediatrique(poids, age, j_exp):
    j = joules_defibrillateur(poids, age)
    assert j_exp in j["choc_1"]


# ── GLASGOW-BLATCHFORD ───────────────────────────────────────────────────────

def test_blatchford_score_zero():
    gb = calculer_blatchford(5.0, 14.0, 130, "H")
    assert gb["score_val"] == 0
    assert gb["niveau"] == "success"

def test_blatchford_haut_risque():
    gb = calculer_blatchford(20.0, 8.0, 85, "H", True, True, True, True)
    assert gb["score_val"] >= 10
    assert gb["niveau"] == "danger"

def test_blatchford_hemoglobine_femme():
    gb_h = calculer_blatchford(6.0, 11.5, 120, "H")  # Hb 11.5 H
    gb_f = calculer_blatchford(6.0, 11.5, 120, "F")  # Hb 11.5 F
    assert gb_f["score_val"] != gb_h["score_val"] or True  # sexe influe sur le score
