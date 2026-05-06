# tests/test_medical.py — Suite de tests automatisés AKIR-IAO
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Lancer : pytest tests/test_medical.py -v
#
# Objectif : garantir qu'aucune régression médicale n'est introduite
# lors des modifications du code. Chaque test représente un cas clinique
# réel dont une classification erronée pourrait impacter un patient.

import sys, math, pytest
sys.path.insert(0, ".")

from clinical.triage import french_triage
from clinical.news2 import calculer_news2, calculer_pews, seuils_normaux_ped
from clinical.scores import (
    calculer_gcs, calculer_qsofa, calculer_curb65, calculer_wells_ep,
    calculer_heart, calculer_timi, calculer_grace, calculer_nihss_rapide,
    calculer_pram, calculer_pss,
    evaluer_tricycliques_ecg, evaluer_paracetamol_intox,
)
from clinical.pharmaco import (
    paracetamol, morphine, piritramide, adrenaline, naloxone,
    ceftriaxone, litican, ketorolac, poids_ideal_theorique,
)
from clinical.perfusion import perf_morphine, perf_noradrenaline, perf_insuline


# ═══════════════════════════════════════════════════════════════════════════════
# A. NEWS2 — 26 cas RCP London 2017
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("fr,spo2,o2,temp,pas,fc,gcs,bpco,expected,desc", [
    # FR
    (12, 96, False, 37.0, 120, 80, 15, False, 0, "Normal"),
    ( 8, 96, False, 37.0, 120, 80, 15, False, 3, "FR ≤ 8"),
    ( 9, 96, False, 37.0, 120, 80, 15, False, 1, "FR 9"),
    (21, 96, False, 37.0, 120, 80, 15, False, 2, "FR 21"),
    (25, 96, False, 37.0, 120, 80, 15, False, 3, "FR ≥ 25"),
    # SpO2
    (16, 91, False, 37.0, 120, 80, 15, False, 3, "SpO2 ≤ 91"),
    (16, 92, False, 37.0, 120, 80, 15, False, 2, "SpO2 92"),
    (16, 95, False, 37.0, 120, 80, 15, False, 1, "SpO2 95"),
    (16, 96,  True, 37.0, 120, 80, 15, False, 2, "O2 supp"),
    # Température
    (16, 96, False, 35.0, 120, 80, 15, False, 3, "T° ≤ 35"),
    (16, 96, False, 36.0, 120, 80, 15, False, 1, "T° 36"),
    (16, 96, False, 38.5, 120, 80, 15, False, 1, "T° 38.5"),
    (16, 96, False, 39.1, 120, 80, 15, False, 2, "T° ≥ 39.1"),
    # PAS
    (16, 96, False, 37.0,  90, 80, 15, False, 3, "PAS ≤ 90"),
    (16, 96, False, 37.0, 100, 80, 15, False, 2, "PAS 100"),
    (16, 96, False, 37.0, 110, 80, 15, False, 1, "PAS 110"),
    (16, 96, False, 37.0, 220, 80, 15, False, 3, "PAS ≥ 220"),
    # FC
    (16, 96, False, 37.0, 120,  40, 15, False, 3, "FC ≤ 40"),
    (16, 96, False, 37.0, 120,  50, 15, False, 1, "FC 50"),
    (16, 96, False, 37.0, 120, 110, 15, False, 1, "FC 110"),
    (16, 96, False, 37.0, 120, 130, 15, False, 2, "FC 130"),
    (16, 96, False, 37.0, 120, 131, 15, False, 3, "FC ≥ 131"),
    # GCS
    (16, 96, False, 37.0, 120,  80, 14, False, 3, "GCS 14"),
    (16, 96, False, 37.0, 120,  80,  3, False, 3, "GCS 3"),
    # BPCO
    (16, 92, False, 37.0, 120,  80, 15,  True, 0, "BPCO SpO2 92 = 0"),
    (16, 97,  True, 37.0, 120,  80, 15,  True, 5, "BPCO SpO2 97+O2 = 5"),
])
def test_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco, expected, desc):
    result, _ = calculer_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco)
    assert result == expected, f"NEWS2 {desc}: {result} ≠ {expected}"


# ═══════════════════════════════════════════════════════════════════════════════
# B. PEWS — Seuils pédiatriques
# ═══════════════════════════════════════════════════════════════════════════════

def test_pews_seuils_normaux():
    """Vérifier que les seuils normaux sont corrects par tranche d'âge."""
    assert seuils_normaux_ped(0.05)["fc"] == (100, 180), "< 1 mois FC"
    assert seuils_normaux_ped(0.5)["fc"]  == (90, 160),  "6 mois FC"
    assert seuils_normaux_ped(5.0)["fc"]  == (60, 120),  "5 ans FC"
    assert seuils_normaux_ped(14.0)["fc"] == (55, 110),  "14 ans FC"

def test_pews_enfant_sain():
    score, _, _ = calculer_pews(90, 20, 98, 15, 37.0, 5)
    assert score == 0, f"Enfant sain PEWS {score} ≠ 0"

def test_pews_detresse_severe():
    score, alertes, _ = calculer_pews(200, 60, 82, 10, 39.5, 0.5)
    assert score >= 6, f"Détresse sévère PEWS {score} < 6"
    assert any("réanimation" in a.lower() for a in alertes)


# ═══════════════════════════════════════════════════════════════════════════════
# C. TRIAGE — Cas critiques (ne jamais sous-trier)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("motif,det,vitaux,exp,desc", [
    # Urgences vitales absolues → Tri 1
    ("Douleur thoracique / SCA", {"ecg": "Anormal typique SCA"},
     dict(fc=90, pas=120, spo2=98, fr=16, gcs=15, temp=37, age=55, n2=2), "1",
     "SCA sus-ST"),
    ("Pétéchie / Purpura", {"neff": True},
     dict(fc=140, pas=90, spo2=97, fr=24, gcs=15, temp=39, age=8, n2=5), "1",
     "Purpura non effaçable"),
    ("Allergie / anaphylaxie", {"dyspnee": True},
     dict(fc=130, pas=82, spo2=91, fr=26, gcs=15, temp=37, age=35, n2=6), "1",
     "Anaphylaxie sévère"),
    ("Fièvre", {},
     dict(fc=160, pas=65, spo2=96, fr=55, gcs=15, temp=38.5, age=0.1, n2=5), "1",
     "Fièvre nourrisson < 3 mois"),
    ("Altération de conscience / Coma", {},
     dict(fc=100, pas=95, spo2=92, fr=20, gcs=6, temp=37, age=60, n2=8), "1",
     "Coma GCS 6"),
    ("Pédiatrie - Bronchiolite", {"apnee": True},
     dict(fc=165, pas=65, spo2=86, fr=58, gcs=15, temp=38.5, age=0.15, n2=7), "1",
     "Bronchiolite apnée"),
    ("Pédiatrie - Asthme / Bronchospasme", {"silencieux": True},
     dict(fc=145, pas=80, spo2=85, fr=48, gcs=15, temp=37.5, age=7, n2=6), "1",
     "Asthme quasi-fatal silencieux"),
    # Hypoglycémie coma → Tri 1
    ("Hypoglycémie", {},
     dict(fc=110, pas=115, spo2=98, fr=16, gcs=8, temp=37, age=60, n2=4, gl=38.0), "1",
     "Coma hypoglycémique GCS 8"),
    # Hypoglycémie sévère GCS normal → Tri 2
    ("Hypoglycémie", {},
     dict(fc=110, pas=115, spo2=98, fr=16, gcs=11, temp=37, age=60, n2=4, gl=42.0), "2",
     "Hypoglycémie sévère GCS 11"),
    # Cas non urgents → ne pas sur-trier
    ("Renouvellement ordonnance", {},
     dict(fc=72, pas=120, spo2=99, fr=14, gcs=15, temp=37, age=50, n2=0), "5",
     "Renouvellement ordonnance"),
    # AVC fenêtre thrombolyse → Tri 2
    ("AVC / Déficit neurologique", {"delai": 2.0},
     dict(fc=80, pas=155, spo2=97, fr=16, gcs=15, temp=37, age=70, n2=2), "2",
     "AVC délai < 4.5h"),
    # Worst-case terrain anticoagulants
    ("Traumatisme membre / épaule", {"atcd": ["Anticoagulants/AOD"]},
     dict(fc=80, pas=120, spo2=98, fr=16, gcs=15, temp=37, age=65, n2=1), "2",
     "Trauma + anticoagulants"),
])
def test_triage_critique(motif, det, vitaux, exp, desc):
    gl = vitaux.pop("gl", None)
    niv, just, _ = french_triage(motif, det, gl=gl, **vitaux)
    assert niv == exp, f"[{desc}] Tri {niv} ≠ {exp} — {just}"


# ═══════════════════════════════════════════════════════════════════════════════
# D. PHARMACOLOGIE — Doses BCFI
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("poids,age,expected_mg,desc", [
    (10,  3,  150, "Para 10kg → 15mg/kg"),
    (30,  8,  450, "Para 30kg → 15mg/kg"),
    (49, 14,  735, "Para 49kg → 15mg/kg (< pivot)"),
    (50, 15, 1000, "Para 50kg → 1g fixe (pivot)"),
    (70, 45, 1000, "Para 70kg → 1g fixe"),
])
def test_paracetamol_pivot_poids(poids, age, expected_mg, desc):
    r, _ = paracetamol(poids, age, [])
    assert abs(r["dose_mg"] - expected_mg) < 5, f"{desc}: {r['dose_mg']} ≠ {expected_mg}"


def test_morphine_doses_bcfi():
    # 0.05-0.10 mg/kg × 70 kg = 3.5-7.0 mg
    r, _ = morphine(70, 45, [])
    assert abs(r["dose_min"] - 3.5) < 0.1, f"Morphine min: {r['dose_min']}"
    assert abs(r["dose_max"] - 7.0) < 0.1, f"Morphine max: {r['dose_max']}"

def test_morphine_personne_agee():
    # Facteur 0.5 si âge ≥ 70 → 1.75-3.5 mg pour 70kg
    r, _ = morphine(70, 75, [])
    assert r["dose_max"] <= 4.0, f"Morphine PA: max {r['dose_max']} > 4mg"

def test_adrenaline_pivot_poids():
    """BCFI anaphylaxie : 0.01 mg/kg si < 30kg, 0.5 mg si ≥ 30kg."""
    r10, _ = adrenaline(10, [])
    r30, _ = adrenaline(30, [])
    r70, _ = adrenaline(70, [])
    assert abs(r10["dose_mg"] - 0.10) < 0.02, f"Adré 10kg: {r10['dose_mg']}"
    assert abs(r30["dose_mg"] - 0.50) < 0.02, f"Adré 30kg: {r30['dose_mg']}"
    assert abs(r70["dose_mg"] - 0.50) < 0.02, f"Adré 70kg: {r70['dose_mg']}"

def test_naloxone_pediatrique():
    r, _ = naloxone(20, 6, False, [])  # 0.01 mg/kg × 20 kg = 0.2 mg
    assert abs(r["dose"] - 0.2) < 0.02, f"Naloxone 20kg: {r['dose']}"

def test_ceftriaxone_pediatrique():
    # 100 mg/kg × 20 kg = 2g (plafond adulte)
    r, _ = ceftriaxone(20, 5, [])
    assert abs(r["dose_g"] - 2.0) < 0.1, f"Ceftriaxone 20kg: {r['dose_g']}"

def test_litican_ci_enfant():
    r, err = litican(30, 12, [])
    assert r is None, "Litican doit être CI avant 15 ans"
    assert "15 ans" in (err or "")

def test_ketorolac_adaptation_age():
    r_jeune, _ = ketorolac(70, 45, [])
    r_vieux, _ = ketorolac(70, 66, [])
    assert r_jeune and abs(r_jeune["dose_mg"] - 30) < 1, f"Kéto < 65: {r_jeune}"
    assert r_vieux and abs(r_vieux["dose_mg"] - 15) < 1, f"Kéto ≥ 65: {r_vieux}"

def test_poids_ideal_theorique_devine():
    """Devine 1974 : H = 50 + 0.91 × (taille - 152.4), F = 45.5 + 0.91 × (taille - 152.4)."""
    pit_h = poids_ideal_theorique(170, "H")
    pit_f = poids_ideal_theorique(170, "F")
    assert pit_h and 62 <= pit_h <= 67, f"PIT H 170cm: {pit_h}"
    assert pit_f and 57 <= pit_f <= 62, f"PIT F 170cm: {pit_f}"


# ═══════════════════════════════════════════════════════════════════════════════
# E. SCORES CLINIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def test_gcs_min_max():
    assert calculer_gcs(4,5,6)["score_val"] == 15
    assert calculer_gcs(1,1,1)["score_val"] == 3

def test_qsofa_septique():
    r = calculer_qsofa(fr=24, gcs=14, pas=98)
    assert r["score_val"] == 3

def test_curb65_max():
    assert calculer_curb65(True,True,True,True,True)["score_val"] == 5

def test_wells_ep_max():
    r = calculer_wells_ep(True,True,True,True,True,True,True)
    assert abs(r["score_val"] - 12.5) < 0.1

def test_heart_max():
    assert calculer_heart(2,2,2,2,2)["score_val"] == 10

def test_timi_max():
    assert calculer_timi(True,True,True,True,True,True,True)["score_val"] == 7

def test_grace_risque_eleve():
    """GRACE > 140 = haut risque — coronarographie < 24h."""
    r = calculer_grace(75, 110, 85, 2.5, 4, True, True, True)
    assert r["score_val"] >= 140, f"GRACE {r['score_val']} < 140"

def test_nihss_avc_modere():
    """Conscience 1 + regard + facial 1 + moteur 2 + langage 1 = 6."""
    r = calculer_nihss_rapide(1, True, 1, 2, 1)
    assert r["score_val"] == 7, f"NIHSS: {r['score_val']}"

def test_pram_asthme_severe():
    """SpO2 88% + tirage + entrée d'air diminuée = PRAM ≥ 8."""
    r = calculer_pram(88, True, True, True, 3, 3)
    assert r["score_val"] >= 8, f"PRAM sévère: {r['score_val']}"

def test_pss_grade_max():
    assert calculer_pss(neuro=4)["score_val"] == 4

def test_adt_bicarbonate_seuil_100ms():
    """QRS ≥ 100 ms → bicarbonate urgent (Boehnert & Lovejoy NEJM 1985)."""
    r = evaluer_tricycliques_ecg(qrs_ms=100)
    assert r["bicarbonate_urgent"], "QRS 100ms doit déclencher bicarbonate"

def test_paracetamol_nomogramme_nac():
    """Dose 200 mg/kg → NAC urgente."""
    r = evaluer_paracetamol_intox(dose_mg_kg=200)
    assert r["nac_indiquee"], "200 mg/kg → NAC obligatoire"

def test_paracetamol_nomogramme_sous_ligne():
    """40 µg/ml à 8h → sous la ligne standard → NAC non indiquée."""
    r = evaluer_paracetamol_intox(heure_ingestion=8, paracetamol_serique_mgL=40)
    assert not r["nac_indiquee"], "40 µg/ml à 8h → NAC non indiquée"


# ═══════════════════════════════════════════════════════════════════════════════
# F. PERFUSIONS — Exactitude calculs
# ═══════════════════════════════════════════════════════════════════════════════

def test_perfusion_morphine():
    """20 µg/kg/h × 70 kg / 1 mg/ml = 1.4 ml/h."""
    r = perf_morphine(70, 20)
    assert abs(r["debit_mlh"] - 1.4) < 0.1, f"Morphine PSE: {r['debit_mlh']}"

def test_perfusion_noradrenaline():
    """0.1 µg/kg/min × 70 × 60 / 80 µg/ml = 5.25 ml/h (conc. clinical/perfusion.py)."""
    r = perf_noradrenaline(70, 0.1)
    assert abs(r["debit_mlh"] - 5.25) < 0.3, f"Noradr: {r['debit_mlh']}"

def test_perfusion_insuline_acidocetose():
    """0.1 UI/kg/h × 70 kg / 1 UI/ml = 7.0 ml/h."""
    r = perf_insuline(70, "acidocetose", 300)
    assert abs(r["debit_mlh"] - 7.0) < 0.1, f"Insuline: {r['debit_mlh']}"


# ═══════════════════════════════════════════════════════════════════════════════
# G. SÉCURITÉ — Jamais de Tri 1/2 pour motifs bénins
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("motif,expected_max,desc", [
    ("Renouvellement ordonnance", "5", "Renouvellement → Tri 5"),
    ("Examen administratif",      "5", "Administratif → Tri 5"),
])
def test_pas_de_surtriage_administratif(motif, expected_max, desc):
    niv, _, _ = french_triage(motif, {}, fc=72, pas=120, spo2=99,
                               fr=14, gcs=15, temp=37, age=50, n2=0)
    ordre = {"M": 0, "1": 1, "2": 2, "3A": 3, "3B": 4, "4": 5, "5": 6}
    assert ordre[niv] >= ordre[expected_max], f"{desc}: Tri {niv} (trop urgent)"
