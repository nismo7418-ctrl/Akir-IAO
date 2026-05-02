# clinical/perfusion.py — Calculs de perfusions IV — AKIR-IAO v19.1
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# Références : BCFI Belgique, SFAR, protocoles Hainaut
#
# CONVENTIONS :
#   - Tous les débits sont en ml/h sauf mention contraire
#   - Les concentrations standard sont celles des hôpitaux de Hainaut
#   - Toutes les fonctions retournent un dict "PerfResult" :
#     { label, conc_mgml, debit_mlh, gttes_min, step_ml, duree_h,
#       dilution, details, alerts, ref }

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Type exports
# ─────────────────────────────────────────────────────────────────────────────
Alert = Tuple[str, str]          # (message, level)
PerfResult = Dict                # Résultat standardisé


def _r(v: float, d: int = 1) -> float:
    return round(v + 1e-9, d)


def _gttes(debit_mlh: float, facteur: int = 20) -> float:
    """Convertit un débit ml/h en gouttes/min selon le facteur du perfuseur.
    Standard adulte : 20 gttes/ml  |  Pédiatrique / microgottes : 60 gttes/ml
    """
    return _r(debit_mlh * facteur / 60, 0)


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b and b != 0 else default


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR GÉNÉRIQUE
# ─────────────────────────────────────────────────────────────────────────────

def _build(
    label: str,
    dose_mg_h: float,      # dose souhaitée en mg/h (après conversion si mg/kg/h)
    conc_mgml: float,      # concentration de la seringue / poche (mg/ml)
    vol_total_ml: float,   # volume total préparé
    alerts: List[Alert],
    ref: str,
    dilution: str,
    details: List[str],
    facteur_gttes: int = 20,
) -> PerfResult:
    debit_mlh  = _r(_safe_div(dose_mg_h, conc_mgml), 1)
    gttes_min  = _gttes(debit_mlh, facteur_gttes)
    duree_h    = _r(_safe_div(vol_total_ml, debit_mlh), 1) if debit_mlh > 0 else 0
    step_ml    = _r(debit_mlh / 4, 1)          # Palier pratique = ¼ du débit initial

    return {
        "label":       label,
        "conc_mgml":   _r(conc_mgml, 3),
        "debit_mlh":   debit_mlh,
        "gttes_min":   gttes_min,
        "step_ml":     step_ml,
        "duree_h":     duree_h,
        "vol_total_ml":vol_total_ml,
        "dilution":    dilution,
        "details":     [d for d in details if d],
        "alerts":      alerts,
        "ref":         ref,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MORPHINE IV — Titration puis entretien
# BCFI / SFAR — Protocole PCA-like
# ─────────────────────────────────────────────────────────────────────────────

def perf_morphine(
    poids: float,
    dose_ug_kg_h: float = 20.0,   # µg/kg/h — entretien standard 10-40 µg/kg/h
    vol_seringue_ml: int = 50,
    atcd: list = None,
) -> PerfResult:
    """
    Morphine IV en seringue auto-pousseuse.
    Concentration standard Hainaut : 1 mg/ml (10 mg dans 10 ml NaCl 0,9 %)
    Ou PSE : 50 mg dans 50 ml NaCl → 1 mg/ml
    Source : SFAR / BCFI — Analgésie IV continue.
    """
    atcd = atcd or []
    alerts: List[Alert] = []
    dose_mg_h = _r(dose_ug_kg_h / 1000 * poids, 2)
    conc = 1.0   # mg/ml (50 mg / 50 ml)

    if poids >= 100:
        alerts.append(("Obésité : utiliser le poids idéal théorique pour la titration", "warning"))
    if any("bpco" in x.lower() or "insuffisance" in x.lower() for x in atcd):
        alerts.append(("IRC/BPCO : réduire le débit initial de 50 %, surveiller FR > 12/min", "warning"))
    if dose_ug_kg_h > 40:
        alerts.append(("Dose > 40 µg/kg/h : seuil d'alerte — valider avec médecin", "danger"))

    return _build(
        label=f"Morphine PSE — {dose_ug_kg_h:.0f} µg/kg/h",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=vol_seringue_ml,
        alerts=alerts,
        ref="SFAR / BCFI — Morphine IV PSE",
        dilution=f"50 mg morphine + NaCl 0,9 % → {vol_seringue_ml} ml (1 mg/ml)",
        details=[
            f"Dose : {dose_ug_kg_h:.0f} µg/kg/h × {poids:.0f} kg = {dose_mg_h:.2f} mg/h",
            f"Titration initiale : bolus {_r(0.05*poids,1)} mg IV lent toutes les 5 min (EVA > 3)",
            "Antidote : Naloxone 0,4 mg IV si FR < 10/min ou sédation",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# PIRITRAMIDE IV — PSE
# BCFI — Dipidolor®
# ─────────────────────────────────────────────────────────────────────────────

def perf_piritramide(
    poids: float,
    dose_ug_kg_h: float = 15.0,
    vol_seringue_ml: int = 50,
    atcd: list = None,
) -> PerfResult:
    """
    Piritramide IV PSE — Dipidolor® 7,5 mg/ml.
    Concentration PSE standard : 1 mg/ml (50 mg / 50 ml)
    Source : BCFI — Piritramide PSE.
    """
    atcd = atcd or []
    alerts: List[Alert] = [("Antidote : Naloxone si dépression respiratoire", "info")]
    dose_mg_h = _r(dose_ug_kg_h / 1000 * poids, 2)
    conc = 1.0  # mg/ml

    return _build(
        label=f"Dipidolor® PSE — {dose_ug_kg_h:.0f} µg/kg/h",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=vol_seringue_ml,
        alerts=alerts,
        ref="BCFI — Piritramide PSE (Dipidolor®)",
        dilution=f"50 mg Dipidolor® + NaCl 0,9 % → {vol_seringue_ml} ml (1 mg/ml)",
        details=[
            f"Dose : {dose_ug_kg_h:.0f} µg/kg/h × {poids:.0f} kg = {dose_mg_h:.2f} mg/h",
            "Bolus titration : 0,03-0,05 mg/kg IV lent",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# KÉTAMINE IV — Analgésie subanesthésique
# BCFI / SFAR
# ─────────────────────────────────────────────────────────────────────────────

def perf_ketamine(
    poids: float,
    indication: str = "analgesie",   # "analgesie" | "sedation" | "rsi"
    atcd: list = None,
) -> PerfResult:
    """
    Kétamine IV en PSE — doses subanesthésiques (analgésie).
    Source : SFAR 2022 / BCFI — Kétamine IV analgésique.
    """
    atcd = atcd or []
    alerts: List[Alert] = []

    if indication == "analgesie":
        dose_mg_kg_h = 0.1    # 0,1-0,5 mg/kg/h — analgésie
        label_dose = "0,1-0,5 mg/kg/h"
    elif indication == "sedation":
        dose_mg_kg_h = 0.5    # 0,5-2 mg/kg/h — sédation légère
        label_dose = "0,5-2 mg/kg/h"
    else:  # rsi
        dose_mg_kg_h = 1.5    # bolus 1,5 mg/kg IV — induction
        label_dose = "1,5 mg/kg IV bolus"

    dose_mg_h  = _r(dose_mg_kg_h * poids, 1)
    conc       = 1.0   # mg/ml (200 mg dans 200 ml ou 50 mg dans 50 ml NaCl)

    if any("hta" in x.lower() for x in atcd):
        alerts.append(("HTA : la kétamine augmente la TA et la FC — surveillance rapprochée", "warning"))
    if any("psychi" in x.lower() or "schizo" in x.lower() for x in atcd):
        alerts.append(("Psychose connue : kétamine relative CI — avis médical", "danger"))
    alerts.append(("Toujours associer une BZD (midazolam) pour éviter les réactions dissociatives", "warning"))

    return _build(
        label=f"Kétamine PSE — {label_dose}",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=50,
        alerts=alerts,
        ref="SFAR 2022 / BCFI — Kétamine analgésique IV",
        dilution="50 mg kétamine + NaCl 0,9 % → 50 ml (1 mg/ml)",
        details=[
            f"Dose initiale : {dose_mg_kg_h} mg/kg/h × {poids:.0f} kg = {dose_mg_h:.1f} mg/h",
            "Toujours avec midazolam 0,5-1 mg IV pour prévenir les hallucinations",
            "Monitoring SpO2, TA, FC continu",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# PROPOFOL IV — Sédation procédurale
# BCFI / SFAR
# ─────────────────────────────────────────────────────────────────────────────

def perf_propofol(
    poids: float,
    phase: str = "entretien",   # "induction" | "entretien"
    atcd: list = None,
) -> PerfResult:
    """
    Propofol IV en PSE (Diprivan® 10 mg/ml ou 20 mg/ml).
    Source : BCFI / SFAR — Sédation procédurale.
    ⚠️ RÉSERVÉ MÉDECIN / IADE — IAO ne peut pas initier seul.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("RÉSERVÉ AU MÉDECIN / IADE — Administration IAO en soutien uniquement", "danger"),
        ("Monitoring continu obligatoire : SpO2, TA, FC, EtCO2 si disponible", "danger"),
        ("Toujours avoir le matériel de VA à portée (masque, laryngoscope, DSG)", "warning"),
    ]

    if phase == "induction":
        dose_mg_kg_min = 0.5   # 0,5-1,5 mg/kg bolus IV lent
        dose_mg_h = _r(dose_mg_kg_min * 60 * poids, 0)
    else:
        dose_mg_kg_min = 0.05  # 3-6 mg/kg/h en entretien = 0,05-0,1 mg/kg/min
        dose_mg_h = _r(dose_mg_kg_min * 60 * poids, 0)

    conc = 10.0  # mg/ml — Diprivan® 1 % (10 mg/ml)

    if poids > 70:
        alerts.append(("Syndrome de perfusion au propofol > 4 mg/kg/h > 48h — surveiller TG, lactates", "warning"))

    return _build(
        label=f"Propofol PSE — {phase}",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=50,
        alerts=alerts,
        ref="BCFI / SFAR — Propofol sédation procédurale",
        dilution="Diprivan® 1 % (10 mg/ml) — Prêt à l'emploi — Ne pas diluer < 2 mg/ml",
        details=[
            f"Phase : {phase}",
            f"Débit calculé pour {dose_mg_kg_min:.2f} mg/kg/min × {poids:.0f} kg",
            "Réduire de 30-50 % chez le patient âgé ou ASA III-IV",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MIDAZOLAM IV — Sédation / Anxiolyse
# BCFI
# ─────────────────────────────────────────────────────────────────────────────

def perf_midazolam(
    poids: float,
    indication: str = "sedation",    # "sedation" | "convulsion" | "anxiolyse"
    atcd: list = None,
) -> PerfResult:
    """
    Midazolam IV PSE (Hypnovel® 5 mg/ml).
    Source : BCFI — Midazolam IV PSE.
    """
    atcd = atcd or []
    alerts: List[Alert] = [("Antidote : Flumazénil 0,2 mg IV (max 1 mg)", "info")]

    configs = {
        "sedation":   (0.02, "0,02-0,1 mg/kg/h"),
        "convulsion": (0.1,  "0,1-0,4 mg/kg/h"),
        "anxiolyse":  (0.01, "0,01-0,05 mg/kg/h"),
    }
    dose_mg_kg_h, label_range = configs.get(indication, (0.02, "0,02-0,1 mg/kg/h"))
    dose_mg_h = _r(dose_mg_kg_h * poids, 1)
    conc = 0.5   # mg/ml — dilution standard : 25 mg dans 50 ml NaCl

    if any("insuffisance hep" in x.lower() for x in atcd):
        alerts.append(("Insuffisance hépatique : accumulation du midazolam — réduire de 50 %", "warning"))
    if any("insuffisance rén" in x.lower() for x in atcd):
        alerts.append(("Insuffisance rénale : accumulation du métabolite actif — réduire la dose", "warning"))

    return _build(
        label=f"Midazolam PSE — {indication} ({label_range})",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=50,
        alerts=alerts,
        ref="BCFI — Midazolam PSE (Hypnovel®)",
        dilution="25 mg (5 ml à 5 mg/ml) + 45 ml NaCl 0,9 % → 50 ml (0,5 mg/ml)",
        details=[
            f"Dose : {dose_mg_kg_h} mg/kg/h × {poids:.0f} kg = {dose_mg_h:.1f} mg/h",
            f"Plage thérapeutique : {label_range}",
            "Titrer par paliers de 25 % toutes les 10-15 min selon effet",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADRÉNALINE IV — Choc anaphylactique / Choc cardiogénique
# BCFI / EAACI 2023
# ─────────────────────────────────────────────────────────────────────────────

def perf_adrenaline(
    poids: float,
    indication: str = "anaphylaxie",   # "anaphylaxie" | "choc_septique" | "arret"
    atcd: list = None,
) -> PerfResult:
    """
    Adrénaline IV continue — Indication selon le contexte.
    Concentration standard : 1 mg dans 100 ml NaCl → 0,01 mg/ml = 10 µg/ml
    Source : BCFI / EAACI 2023 / SFAR.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("RÉSERVÉ AU MÉDECIN — Monitoring TA/FC continu — VVP large calibre", "danger"),
        ("Ne jamais interrompre brutalement — sevrage progressif", "warning"),
    ]

    configs = {
        "anaphylaxie":   (0.1, "0,1-1 µg/kg/min — anaphylaxie sévère"),
        "choc_septique": (0.3, "0,1-1 µg/kg/min — vasoplégique"),
        "arret":         (1.0, "1 mg IV toutes les 3-5 min ACR — hors PSE"),
    }
    dose_ug_kg_min, label = configs.get(indication, (0.1, "0,1-1 µg/kg/min"))
    dose_ug_min = dose_ug_kg_min * poids
    dose_mg_h   = _r(dose_ug_min * 60 / 1000, 3)
    conc        = 0.01  # mg/ml = 10 µg/ml (1 mg dans 100 ml)

    return _build(
        label=f"Adrénaline IV — {label}",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=100,
        alerts=alerts,
        ref="BCFI / EAACI 2023 — Adrénaline IV continue",
        dilution="1 mg adrénaline (1 ml à 1 mg/ml) + 99 ml NaCl 0,9 % → 100 ml (0,01 mg/ml = 10 µg/ml)",
        details=[
            f"Dose initiale : {dose_ug_kg_min} µg/kg/min × {poids:.0f} kg = {dose_ug_min:.1f} µg/min",
            f"= {dose_mg_h:.2f} mg/h = {_r(dose_mg_h/_safe_div(conc,1),1)} ml/h",
            "Titrer selon réponse tensionnelle — paliers de 0,05 µg/kg/min",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# NORADRÉNALINE IV — Choc septique / Vasoplégie
# BCFI / SSC 2021
# ─────────────────────────────────────────────────────────────────────────────

def perf_noradrenaline(
    poids: float,
    dose_ug_kg_min: float = 0.1,
    atcd: list = None,
) -> PerfResult:
    """
    Noradrénaline IV PSE — 1ère ligne choc septique (SSC 2021).
    Concentration standard : 4 mg dans 50 ml NaCl → 0,08 mg/ml
    Source : SSC 2021 / BCFI.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("RÉSERVÉ AU MÉDECIN / IADE — Voie centrale recommandée > 12h", "danger"),
        ("Monitorage TA invasif recommandé en soins intensifs", "warning"),
        ("Dose > 1 µg/kg/min = choc réfractaire — avis réanimateur immédiat", "warning"),
    ]

    if dose_ug_kg_min > 1.0:
        alerts.append(("Dose > 1 µg/kg/min : choc réfractaire — APPEL RÉANIMATEUR", "danger"))

    dose_ug_min = dose_ug_kg_min * poids
    dose_mg_h   = _r(dose_ug_min * 60 / 1000, 3)
    conc        = 0.08   # mg/ml = 80 µg/ml (4 mg dans 50 ml)

    return _build(
        label=f"Noradrénaline — {dose_ug_kg_min:.2f} µg/kg/min",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=50,
        alerts=alerts,
        ref="SSC 2021 / BCFI — Noradrénaline choc septique",
        dilution="4 mg noradrénaline + NaCl 0,9 % → 50 ml (0,08 mg/ml = 80 µg/ml)",
        details=[
            f"Dose : {dose_ug_kg_min:.2f} µg/kg/min × {poids:.0f} kg = {dose_ug_min:.1f} µg/min",
            f"= {dose_mg_h:.2f} mg/h",
            "Cible : PAM ≥ 65 mmHg — ajuster par paliers de 0,05 µg/kg/min",
            "1ère vasopresseur choc septique selon SSC 2021",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# INSULINE IV — Hyperkaliémie / Acidocétose / Hyperglycémie
# BCFI
# ─────────────────────────────────────────────────────────────────────────────

def perf_insuline(
    poids: float,
    indication: str = "acidocetose",
    glycemie_mgdl: float = 300.0,
    atcd: list = None,
) -> PerfResult:
    """
    Insuline rapide IV (Actrapid® / Humulin® R).
    Source : BCFI — Insuline IV.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("Glycémie capillaire toutes les heures pendant la perfusion", "danger"),
        ("Risque hypokaliémie — doser K+ avant et pendant", "warning"),
    ]

    configs = {
        "acidocetose":    (0.1,  "0,1 UI/kg/h — Acidocétose diabétique"),
        "hyperkaliemie":  (0.0,  "Bolus 10 UI IV + glucose G50 % 50 ml"),
        "hyperglycemie":  (0.05, "0,05 UI/kg/h — Correction hyperglycémie"),
    }
    dose_ui_kg_h, label = configs.get(indication, (0.1, "0,1 UI/kg/h"))

    if indication == "hyperkaliemie":
        return {
            "label":        "Insuline rapide — Hyperkaliémie",
            "conc_mgml":    1.0,
            "debit_mlh":    0,
            "gttes_min":    0,
            "step_ml":      0,
            "duree_h":      0,
            "vol_total_ml": 60,
            "dilution":     "10 UI Actrapid® dans 50 ml G50 % (= G5 % + G50 %) en 15-30 min",
            "details":      [
                "Bolus IV : 10 UI insuline rapide + 50 ml glucose 50 %",
                "Répétable en 30-60 min selon K+ (efficacité 15-30 min)",
                "Associer bicarbonate si pH < 7,1",
            ],
            "alerts":       alerts,
            "ref":          "BCFI — Insuline IV hyperkaliémie",
        }

    dose_ui_h  = _r(dose_ui_kg_h * poids, 1)
    conc       = 1.0   # UI/ml — 50 UI dans 50 ml NaCl 0,9 %

    if glycemie_mgdl < 250:
        alerts.append((f"Glycémie {glycemie_mgdl:.0f} mg/dl — Réduire la dose de 50 % si < 250", "warning"))

    return _build(
        label=f"Insuline IV PSE — {label}",
        dose_mg_h=dose_ui_h,       # UI/h ici (même unité numérique)
        conc_mgml=conc,
        vol_total_ml=50,
        alerts=alerts,
        ref="BCFI — Insuline IV acidocétose",
        dilution="50 UI Actrapid® + NaCl 0,9 % → 50 ml (1 UI/ml)",
        details=[
            f"Dose : {dose_ui_kg_h} UI/kg/h × {poids:.0f} kg = {dose_ui_h:.1f} UI/h",
            f"Équivalent : {dose_ui_h:.1f} ml/h (concentration 1 UI/ml)",
            f"Cible glycémique : 140-180 mg/dl (7,8-10 mmol/l)",
            "Rincer la tubulure avec 20 ml du mélange insuline avant connexion patient",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# AMIODARONE IV — Tachyarythmie / FA
# BCFI / ESC 2020
# ─────────────────────────────────────────────────────────────────────────────

def perf_amiodarone(
    poids: float,
    indication: str = "fa",    # "fa" | "tv_stable" | "choc_refractaire"
    atcd: list = None,
) -> PerfResult:
    """
    Amiodarone IV (Cordarone® 50 mg/ml).
    Source : BCFI / ESC 2020 — Arythmies.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("Voie centrale recommandée pour perfusion > 1 h (risque phlébite)", "warning"),
        ("Monitoring ECG continu obligatoire — allongement QT", "warning"),
        ("Incompatible : NaCl 0,9 % pour charge IV rapide — utiliser G5 %", "warning"),
    ]

    if indication == "choc_refractaire":
        # 300 mg bolus IV puis 900 mg/24h
        return {
            "label":        "Amiodarone IV — ACR / TV sans pouls",
            "conc_mgml":    3.0,    # 300 mg dans 100 ml G5 %
            "debit_mlh":    0,
            "gttes_min":    0,
            "step_ml":      0,
            "duree_h":      0,
            "vol_total_ml": 100,
            "dilution":     "300 mg (6 ml) dans 100 ml G5 % → bolus IV rapide en 3 min",
            "details":      [
                "Bolus : 300 mg IV en 3 min (ACR réfractaire post-choc)",
                "2e dose si nécessaire : 150 mg IV",
                "Entretien : 900 mg / 24 h = 37,5 mg/h",
            ],
            "alerts":       alerts,
            "ref":          "BCFI / ERC 2021 — Amiodarone ACR",
        }

    # FA / TV hémodynamiquement stable
    dose_mg_h_charge  = _r(5 * poids, 0)    # 5 mg/kg sur 20-60 min (charge)
    dose_mg_h_entretien = 900 / 24            # 900 mg / 24 h = 37,5 mg/h

    conc = 1.8   # mg/ml — 900 mg dans 500 ml G5 %

    return _build(
        label=f"Amiodarone — Charge {_r(5*poids,0):.0f} mg puis entretien",
        dose_mg_h=dose_mg_h_entretien,   # Afficher le débit d'entretien
        conc_mgml=conc,
        vol_total_ml=500,
        alerts=alerts,
        ref="BCFI / ESC 2020 — Amiodarone FA/TV",
        dilution="900 mg amiodarone (18 ml) + G5 % → 500 ml (1,8 mg/ml)",
        details=[
            f"Charge : {_r(5*poids,0):.0f} mg ({5.0} mg/kg) en 20-60 min sur voie périph.",
            f"Entretien : 900 mg / 24 h = {37.5:.1f} mg/h = {_r(37.5/conc,1):.1f} ml/h",
            "FA récente < 48h : cardioversion possible sans anticoagulation",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# LABÉTALOL IV — HTA urgence / Aorte
# BCFI / ESC 2023
# ─────────────────────────────────────────────────────────────────────────────

def perf_labetalol(
    poids: float,
    contexte: str = "hta_severe",
    atcd: list = None,
) -> PerfResult:
    """
    Labétalol IV (Trandate® 5 mg/ml).
    Alpha + bêta-bloquant — Urgences hypertensives, dissection aortique.
    Source : BCFI / ESC 2023.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("Contre-indiqué en cas de bradycardie (FC < 60), bloc AV, asthme, BPCO sévère", "danger"),
        ("Réduire si insuffisance cardiaque décompensée", "warning"),
    ]

    if any("asthme" in x.lower() or "bpco" in x.lower() for x in atcd):
        return {
            "label": "Labétalol IV",
            "conc_mgml": 0, "debit_mlh": 0, "gttes_min": 0,
            "step_ml": 0, "duree_h": 0, "vol_total_ml": 0,
            "dilution": "—", "details": [],
            "alerts": [("CONTRE-INDIQUÉ : Asthme / BPCO — Utiliser un autre antihypertenseur", "danger")],
            "ref": "BCFI — Labétalol CI",
        }

    # Perfusion continue : 2 mg/min titré jusqu'à effet
    dose_mg_min = 2.0
    conc = 1.0    # mg/ml — 200 mg dans 200 ml NaCl

    return _build(
        label=f"Labétalol IV — {contexte}",
        dose_mg_h=dose_mg_min * 60,
        conc_mgml=conc,
        vol_total_ml=200,
        alerts=alerts,
        ref="BCFI / ESC 2023 — Labétalol IV urgences hypertensives",
        dilution="200 mg labétalol (40 ml) + NaCl 0,9 % → 200 ml (1 mg/ml)",
        details=[
            "Bolus initial : 20 mg IV en 2 min — peut répéter 40-80 mg/10 min (max 300 mg)",
            "Ou perfusion : 2 mg/min = 120 ml/h — titrer selon TA",
            "Cible : réduction TA 20-25 % en 1h (sauf dissection → < 120 mmHg)",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAGNÉSIUM IV — Pré-éclampsie / Torsade de pointes / Asthme
# BCFI
# ─────────────────────────────────────────────────────────────────────────────

def perf_magnesium(
    poids: float,
    indication: str = "eclampsia",   # "eclampsia" | "torsades" | "asthme"
    atcd: list = None,
) -> PerfResult:
    """
    Sulfate de magnésium IV.
    Source : BCFI / OMS — Magnésium IV.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("Antidote : Gluconate de calcium 1 g IV en 3 min si surdosage", "warning"),
        ("Signes de surdosage : ROT abolies, FR < 12, SpO2 < 95 %", "danger"),
    ]

    configs = {
        "eclampsia":  (4.0, 1.0, "4 g IV en 20 min, puis 1 g/h — Pré-éclampsie sévère"),
        "torsades":   (2.0, 0.0, "2 g IV en 90 secondes — Torsades de pointes"),
        "asthme":     (2.0, 0.0, "2 g IV en 20 min — Asthme sévère réfractaire"),
    }
    dose_charge_g, dose_entretien_g_h, label = configs.get(indication, (2.0, 0.0, "2 g IV"))
    conc = 0.04   # g/ml = 40 mg/ml — 4 g dans 100 ml NaCl

    return _build(
        label=f"MgSO4 IV — {label}",
        dose_mg_h=dose_entretien_g_h * 1000,   # g/h → mg/h
        conc_mgml=conc * 1000,                  # g/ml → mg/ml
        vol_total_ml=100,
        alerts=alerts,
        ref="BCFI / OMS — Sulfate de magnésium IV",
        dilution=f"4 g MgSO4 (8 ml à 500 mg/ml) + NaCl 0,9 % → 100 ml (40 mg/ml)",
        details=[
            f"Charge : {dose_charge_g:.0f} g en 20 min",
            f"Entretien : {dose_entretien_g_h:.0f} g/h" if dose_entretien_g_h > 0 else "Dose unique",
            "Surveiller : ROT, FR, diurèse — Antidote Ca gluconate à portée",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# NICARDIPINE IV — HTA sévère
# BCFI / ESC 2023
# ─────────────────────────────────────────────────────────────────────────────

def perf_nicardipine(
    poids: float,
    atcd: list = None,
) -> PerfResult:
    """
    Nicardipine IV (Loxen® 10 mg/10 ml).
    Alternative si Labétalol CI (asthme, BPCO).
    Source : BCFI / ESC 2023.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("Risque tachycardie réflexe — surveiller FC", "warning"),
        ("Incompatible bicarbonate et furosémide en Y", "info"),
    ]
    # Débit initial 5 mg/h — titration par paliers de 2,5 mg/h toutes les 15 min
    conc       = 0.1   # mg/ml — 10 mg dans 100 ml NaCl (ou G5 %)
    dose_mg_h  = 5.0

    return _build(
        label="Nicardipine IV — HTA sévère",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=100,
        alerts=alerts,
        ref="BCFI / ESC 2023 — Nicardipine IV (Loxen®)",
        dilution="10 mg (10 ml) + NaCl 0,9 % → 100 ml (0,1 mg/ml)",
        details=[
            "Débit initial : 5 mg/h = 50 ml/h",
            "Titrer : + 2,5 mg/h toutes les 15 min (max 15 mg/h)",
            "Cible : réduction PAS de 25 % en 1h",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# DOBUTAMINE IV — Insuffisance cardiaque aiguë / Choc cardiogénique
# BCFI / ESC 2021
# ─────────────────────────────────────────────────────────────────────────────

def perf_dobutamine(
    poids: float,
    dose_ug_kg_min: float = 5.0,
    atcd: list = None,
) -> PerfResult:
    """
    Dobutamine IV PSE — Choc cardiogénique / Décompensation cardiaque.
    Concentration standard : 250 mg dans 50 ml NaCl → 5 mg/ml
    Source : BCFI / ESC 2021.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("RÉSERVÉ AU MÉDECIN — Monitoring cardiaque continu (ECG, TA, SpO2)", "danger"),
        ("Risque arythmies ventriculaires — défibrillateur à portée", "warning"),
        ("Tachycardie > 130/min : réduire ou arrêter", "warning"),
    ]

    if dose_ug_kg_min > 20:
        alerts.append(("Dose > 20 µg/kg/min : risque arythmies majeur — avis cardiologue", "danger"))

    dose_ug_min = dose_ug_kg_min * poids
    dose_mg_h   = _r(dose_ug_min * 60 / 1000, 2)
    conc        = 5.0   # mg/ml — 250 mg dans 50 ml

    return _build(
        label=f"Dobutamine — {dose_ug_kg_min:.0f} µg/kg/min",
        dose_mg_h=dose_mg_h,
        conc_mgml=conc,
        vol_total_ml=50,
        alerts=alerts,
        ref="BCFI / ESC 2021 — Dobutamine choc cardiogénique",
        dilution="250 mg dobutamine + NaCl 0,9 % → 50 ml (5 mg/ml)",
        details=[
            f"Dose : {dose_ug_kg_min:.0f} µg/kg/min × {poids:.0f} kg = {dose_ug_min:.0f} µg/min",
            f"= {dose_mg_h:.2f} mg/h = {_r(dose_mg_h/conc,1):.1f} ml/h",
            "Plage : 2-20 µg/kg/min — commencer par 2,5 µg/kg/min",
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES — Calcul vitesse, gouttes, dilution
# ─────────────────────────────────────────────────────────────────────────────

def calculer_debit(dose_mg_h: float, conc_mgml: float) -> dict:
    """Calcule débit ml/h et gouttes/min depuis dose (mg/h) et concentration (mg/ml)."""
    debit = _r(_safe_div(dose_mg_h, conc_mgml), 1)
    return {
        "debit_mlh":  debit,
        "gttes_min_adulte":  _gttes(debit, 20),
        "gttes_min_ped":     _gttes(debit, 60),
        "mgmin": _r(dose_mg_h / 60, 3),
    }


def convertir_debit(debit_mlh: float, conc_mgml: float, poids: float = 70.0) -> dict:
    """Convertit un débit ml/h en dose mg/h, mg/kg/h, µg/kg/min."""
    dose_mg_h    = _r(debit_mlh * conc_mgml, 3)
    dose_mg_kg_h = _r(_safe_div(dose_mg_h, poids), 4)
    dose_ug_kg_min = _r(dose_mg_kg_h * 1000 / 60, 3)
    return {
        "debit_mlh":    debit_mlh,
        "dose_mg_h":    dose_mg_h,
        "dose_mg_kg_h": dose_mg_kg_h,
        "dose_ug_kg_min": dose_ug_kg_min,
    }
