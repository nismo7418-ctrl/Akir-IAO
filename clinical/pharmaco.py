# clinical/pharmaco.py — Protocoles pharmacologiques — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Référence : BCFI Belgique, protocoles locaux Hainaut

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from clinical.utils import norm
from config import (
    CLEV_DEBIT_INIT_MG_H, CLEV_DEBIT_MAX_MG_H, CLEV_PALIER_S,
    MEOPA_DEBIT_L_MIN, MEOPA_DUREE_MAX_MIN,
    MIDAZ_IV_KG, MIDAZ_IV_MAX_MG, MIDAZ_IV_CONVULS_KG, MIDAZ_IV_CONVULS_MAX,
    ADRE_DOSE_ADULTE_MG, ADRE_DOSE_KG, ADRE_POIDS_ADULTE_KG,
    CEFRTRX_ADULTE_G, CEFRTRX_PED_KG,
    CLONAZEPAM_IV_KG, CLONAZEPAM_IV_MAX_MG,
    DIAZEPAM_IV_KG, DIAZEPAM_IV_MAX_MG,
    DIAZEPAM_RECT_KG, DIAZEPAM_RECT_MAX_MG,
    EME_ETABLI_MIN, EME_OPERATIONNEL_MIN, EME_SEUIL_MIN,
    GLUCOSE_DOSE_KG, GLUCOSE_MAX_G,
    LEVETI_IV_KG, LEVETI_IV_MAX_MG,
    LITICAN_DOSE_ADULTE_MG, LITICAN_DOSE_KG_ENF, LITICAN_DOSE_MAX_ENF_MG,
    LITICAN_DOSE_MAX_JOUR, LITICAN_POIDS_PIVOT_KG,
    LORAZEPAM_IV_KG, LORAZEPAM_IV_MAX_MG,
    MIDAZOLAM_BUCC_MAX_MG, MIDAZOLAM_IM_IN_KG, MIDAZOLAM_IM_IN_MAX_MG,
    MORPH_MAX_KG, MORPH_MIN_KG, MORPH_PALIER_MG,
    MORPH_PLAFOND_GE100, MORPH_PLAFOND_STD,
    NALOO_ADULTE_MG, NALOO_DEP_MG, NALOO_PED_KG,
    PARA_DOSE_FIXE_G, PARA_DOSE_KG, PARA_POIDS_PIVOT_KG,
    PHENOBARB_DEBIT_MG_KG_MIN, PHENOBARB_IV_KG, PHENOBARB_IV_MAX_MG,
    PIRI_BOLUS_MAX, PIRI_BOLUS_MIN, PIRI_PLAFOND_GE70, PIRI_PLAFOND_LT70,
    VALPROATE_IV_DEBIT_MIN, VALPROATE_IV_KG, VALPROATE_IV_MAX_MG,
)

Alert  = Tuple[str, str]
Result = Tuple[Optional[Dict], Optional[str]]


def _has(atcd: list, *items: str) -> bool:
    known = {norm(x) for x in (atcd or [])}
    return any(norm(item) in known for item in items)


def _add(alerts: List[Alert], msg: str, level: str = "warning") -> None:
    alerts.append((msg, level))


def _r(value: float, digits: int = 1) -> float:
    return round(value + 1e-9, digits)


def _fmt(value: float) -> str:
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"


def _opioid_alerts(atcd: list) -> List[Alert]:
    alerts: List[Alert] = []
    if _has(atcd, "BPCO"):
        _add(alerts, "BPCO : monitorer la ventilation sous opioïdes")
    if _has(atcd, "Insuffisance hépatique"):
        _add(alerts, "Insuffisance hépatique : titration prudente", "warning")
    if _has(atcd, "Anticoagulants/AOD"):
        _add(alerts, "Anticoagulants/AOD : privilégier voie IV plutôt qu'IM", "warning")
    return alerts


def _nsaid_error(atcd: list) -> Optional[str]:
    blockers: List[str] = []
    if _has(atcd, "Insuffisance rénale chronique"):
        blockers.append("insuffisance rénale chronique")
    if _has(atcd, "Ulcère gastro-duodénal"):
        blockers.append("ulcère gastro-duodénal")
    if _has(atcd, "Anticoagulants/AOD"):
        blockers.append("anticoagulants/AOD")
    if _has(atcd, "Grossesse"):
        blockers.append("grossesse")
    if _has(atcd, "Insuffisance cardiaque"):
        blockers.append("insuffisance cardiaque")
    if not blockers:
        return None
    return "AINS à éviter : " + ", ".join(blockers)


def _use_mg_kg(age: float) -> bool:
    """Détermine si on utilise les doses en mg/kg (enfants) ou adultes standards."""
    return age < 15


def _format_dose(dose_mg: float, poids: float, age: float, unit: str = "mg") -> str:
    """Formate l'affichage de la dose selon l'âge."""
    if _use_mg_kg(age):
        dose_per_kg = dose_mg / poids
        return f"{_fmt(dose_per_kg)} mg/kg ({_fmt(dose_mg)} {unit})"
    else:
        return f"{_fmt(dose_mg)} {unit}"


# ─────────────────────────────────────────────────────────────────────────────
# POIDS IDÉAL THÉORIQUE (PIT) — Formule de Devine 1974
# Requis pour dosage opioïdes en cas d'obésité (IMC ≥ 35) — SFAR 2021
# ─────────────────────────────────────────────────────────────────────────────

def poids_ideal_theorique(taille_cm: float, sexe: str = "M") -> float:
    """Poids Idéal Théorique (Devine 1974).
    H : 50 + 0,91 × (taille_cm – 152,4)
    F : 45,5 + 0,91 × (taille_cm – 152,4)
    """
    base = 50.0 if sexe.upper() in ("M", "H") else 45.5
    return _r(max(30.0, base + 0.91 * max(0.0, taille_cm - 152.4)), 1)


def poids_dosage_opioides(poids_reel: float, taille_cm: float = 170.0, sexe: str = "M") -> tuple:
    """Retourne (poids_à_utiliser, note_alerte) pour les opioïdes.
    Si IMC ≥ 35 : Poids ajusté = PIT + 0,4 × (poids_réel – PIT) (SFAR 2021).
    Si IMC < 35 : poids réel.
    Source : SFAR — Analgésie IV chez l'obèse 2021.
    """
    if taille_cm <= 100:
        return poids_reel, ""
    imc = poids_reel / (taille_cm / 100) ** 2
    if imc >= 35:
        pit = poids_ideal_theorique(taille_cm, sexe)
        pa  = _r(pit + 0.4 * (poids_reel - pit), 1)
        note = f"Obésité IMC {imc:.0f} — Poids ajusté opioïdes : {pa} kg (PIT {pit} kg)"
        return pa, note
    return poids_reel, ""


# ─────────────────────────────────────────────────────────────────────────────
# ANTALGIQUES
# ─────────────────────────────────────────────────────────────────────────────

def paracetamol(poids: float, age: float, atcd: list) -> Result:
    """Paracétamol IV — BCFI Belgique.

    Règle BCFI (Perfalgan® IV) :
      • Poids < 50 kg  → 15 mg/kg (dose poids-dépendante), max 1 g
      • Poids ≥ 50 kg  → 1 g fixe
    Fréquence : toutes les 4-6 h, max 4 doses / 24 h (soit 60 mg/kg/j ou 4 g/j).
    """
    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance hépatique"):
        _add(alerts, "Insuffisance hépatique : dose max = 3 g/24 h — valider avec médecin", "warning")

    # BCFI : pivot poids (pas âge) — un adulte léger < 50 kg = 15 mg/kg
    if poids < PARA_POIDS_PIVOT_KG:
        dose_mg      = min(_r(PARA_DOSE_KG * poids, 0), 1000.0)   # 15 mg/kg, plafond 1g
        dose_display = f"{PARA_DOSE_KG:.0f} mg/kg ({dose_mg:.0f} mg)"
        note         = f"Poids < {PARA_POIDS_PIVOT_KG:.0f} kg → dose poids-dépendante 15 mg/kg"
    else:
        dose_mg      = PARA_DOSE_FIXE_G * 1000.0                  # 1 g fixe
        dose_display = f"{dose_mg:.0f} mg"
        note         = f"Poids ≥ {PARA_POIDS_PIVOT_KG:.0f} kg → 1 g fixe"

    return ({
        "dose_mg":      _r(dose_mg, 0),
        "dose_display": dose_display,
        "admin":        "IV en 15 min",
        "note":         note,
        "ref":          "BCFI — Paracétamol IV (Perfalgan®)",
        "alerts":       alerts,
    }, None)


def naproxene(poids: float, age: float, atcd: list) -> Result:
    """Naproxène PO — BCFI."""
    if age < 15:
        return None, "Naproxène non automatisé avant 15 ans dans ce protocole IAO"
    err = _nsaid_error(atcd)
    if err:
        return None, err
    dose_mg = 500.0 if poids >= 50 else 250.0
    return ({
        "dose_mg": dose_mg,
        "admin": "PO",
        "note": "250-500 mg puis 250-500 mg/12 h, max 1 g/24 h",
        "ref": "BCFI — Naproxène oral",
        "alerts": [("À prendre avec nourriture et hydratation correcte", "info")],
    }, None)


def ketorolac(poids: float, age: float, atcd: list = None) -> Result:
    """Taradyl® (Kétorolac) IM/IV — AINS puissant — BCFI / Hainaut.
    CI absolue : insuffisance rénale, anticoagulants, ulcère, grossesse.
    """
    atcd = atcd or []
    # Contra-indications renforcées vs naproxène
    if _has(atcd, "Insuffisance rénale chronique"):
        return None, "CONTRE-INDIQUÉ : Insuffisance rénale chronique (risque IRA)"
    if _has(atcd, "Anticoagulants/AOD", "Antiagrégants plaquettaires"):
        return None, "CONTRE-INDIQUÉ : Anticoagulants / antiagrégants (risque hémorragique)"
    err = _nsaid_error(atcd)
    if err:
        return None, err
    # Dose adulte : 30 mg IM/IV — réduit à 15 mg si âge ≥ 65 ou poids < 50 kg
    dose_mg = 15.0 if (age >= 65 or poids < 50) else 30.0
    return ({
        "dose_mg": dose_mg,
        "admin": "IM profonde ou IV lent 15 s — 1 injection",
        "note": f"30 mg adulte (15 mg si ≥ 65 ans / < 50 kg) — max 5 jours — max 90 mg/j",
        "ref": "BCFI / Taradyl® — Kétorolac IM",
        "alerts": [
            ("Éviter > 5 j et en cas de déshydratation", "warning"),
            ("Dose unique recommandée aux urgences avant réévaluation", "info"),
        ],
    }, None)


def diclofenac(poids: float, age: float, atcd: list = None) -> Result:
    """Voltarène® (Diclofénac) IM — AINS — BCFI.
    Adulte uniquement par voie IM. Enfant < 15 ans : contre-indiqué IM.
    """
    atcd = atcd or []
    if age < 15:
        return None, "CONTRE-INDIQUÉ : Voie IM non autorisée avant 15 ans (Voltarène)"
    err = _nsaid_error(atcd)
    if err:
        return None, err
    if _has(atcd, "Insuffisance rénale chronique"):
        return None, "CONTRE-INDIQUÉ : Insuffisance rénale (diclofénac néphrotoxique)"
    if _has(atcd, "Anticoagulants/AOD"):
        return None, "CONTRE-INDIQUÉ : Anticoagulants (risque hémorragique)"
    alerts: List[Alert] = [
        ("Injection IM dans le quadrant supéro-externe de la fesse", "info"),
        ("Ne pas répéter sans réévaluation — max 150 mg/j", "warning"),
    ]
    if _has(atcd, "HTA"):
        _add(alerts, "HTA : surveillance tensionnelle sous AINS", "warning")
    return ({
        "dose_mg": 75.0,
        "admin": "IM profonde quadrant supéro-ext. fesse — 75 mg",
        "note": "Max 150 mg/24 h — À éviter > 48 h",
        "ref": "BCFI / Voltarène® 75 mg/3 ml IM",
        "alerts": alerts,
    }, None)


def taradyl_im(poids: float, age: float, atcd: list = None) -> Result:
    """Taradyl® IM (Kétorolac) — AINS — BCFI."""
    atcd = atcd or []
    err = _nsaid_error(atcd)
    if err:
        return None, err

    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance rénale chronique"):
        _add(alerts, "Insuffisance rénale : contre-indiqué", "danger")
        return None, "CONTRE-INDIQUÉ : Insuffisance rénale chronique"

    # Dose adulte : 30 mg IM — réduit à 15 mg si âge ≥ 65 ou poids < 50 kg
    dose_mg = 15.0 if (age >= 65 or poids < 50) else 30.0

    if _use_mg_kg(age):
        dose_per_kg = dose_mg / poids
        dose_display = f"{_fmt(dose_per_kg)} mg/kg ({_fmt(dose_mg)} mg)"
    else:
        dose_display = f"{_fmt(dose_mg)} mg"

    alerts.extend([
        ("Éviter > 5 j et en cas de déshydratation", "warning"),
        ("Dose unique recommandée aux urgences avant réévaluation", "info"),
    ])

    return ({
        "dose_mg": dose_mg,
        "dose_display": dose_display,
        "admin": "IM profonde — 1 injection",
        "note": f"30 mg adulte (15 mg si ≥ 65 ans / < 50 kg) — max 5 jours — max 90 mg/j",
        "ref": "BCFI / Taradyl® — Kétorolac IM",
        "alerts": alerts,
    }, None)


def diclofenac_im(poids: float, age: float, atcd: list = None) -> Result:
    """Voltarène® IM (Diclofénac) — AINS — BCFI."""
    atcd = atcd or []
    if age < 15:
        return None, "CONTRE-INDIQUÉ : Voie IM non autorisée avant 15 ans"

    err = _nsaid_error(atcd)
    if err:
        return None, err

    if _has(atcd, "Insuffisance rénale chronique"):
        return None, "CONTRE-INDIQUÉ : Insuffisance rénale (diclofénac néphrotoxique)"
    if _has(atcd, "Anticoagulants/AOD"):
        return None, "CONTRE-INDIQUÉ : Anticoagulants (risque hémorragique)"

    alerts: List[Alert] = [
        ("Injection IM dans le quadrant supéro-externe de la fesse", "info"),
        ("Ne pas répéter sans réévaluation — max 150 mg/j", "warning"),
    ]
    if _has(atcd, "HTA"):
        _add(alerts, "HTA : surveillance tensionnelle sous AINS", "warning")

    dose_mg = 75.0
    if _use_mg_kg(age):
        dose_per_kg = dose_mg / poids
        dose_display = f"{_fmt(dose_per_kg)} mg/kg ({_fmt(dose_mg)} mg)"
    else:
        dose_display = f"{_fmt(dose_mg)} mg"

    return ({
        "dose_mg": dose_mg,
        "dose_display": dose_display,
        "admin": "IM profonde quadrant supéro-ext. fesse",
        "note": "Max 150 mg/24 h — À éviter > 48 h",
        "ref": "BCFI / Voltarène® 75 mg/3 ml IM",
        "alerts": alerts,
    }, None)


def tramadol(poids: float, age: float, atcd: list) -> Result:
    """Tramadol PO/IV — BCFI / EMA 2019.
    ⚠️ CONTRE-INDIQUÉ < 12 ans (EMA 2019 — risque dépression respiratoire).
    ⚠️ DÉCONSEILLÉ 12-18 ans en cas d'apnées du sommeil, obésité morbide, BPCO.
    Source : EMA PRAC 2019 — Restriction pédiatrique tramadol.
    """
    # CI absolue EMA 2019 — enfant < 12 ans
    if age < 12:
        return None, (
            f"CONTRE-INDIQUÉ chez l'enfant < 12 ans (EMA 2019) — "
            f"Risque dépression respiratoire — Utiliser paracétamol + ibuprofène"
        )
    if _has(atcd, "IMAO (inhibiteurs MAO)"):
        return None, "CONTRE-INDICATION ABSOLUE — IMAO : syndrome sérotoninergique potentiellement fatal"
    if _has(atcd, "Épilepsie"):
        return None, "CONTRE-INDIQUÉ — Épilepsie : le tramadol abaisse le seuil épileptogène"

    alerts = _opioid_alerts(atcd)

    # Déconseillé 12-18 ans si facteurs de risque respiratoire
    if age < 18:
        if _has(atcd, "BPCO", "Asthme", "Obésité morbide (IMC ≥ 40)"):
            _add(alerts, "12-18 ans + pathologie respiratoire : tramadol déconseillé (EMA 2019)", "warning")

    if _has(atcd, "Antidépresseurs ISRS/IRSNA"):
        _add(alerts, "ISRS/IRSNA : interaction sérotoninergique — surveiller (syndrome sérotoninergique)", "warning")

    dose_mg = 50.0 if age >= 18 else min(poids * 1.5, 50.0)
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "PO ou IV lent 100 mg dans 250 ml NaCl sur 30 min",
        "note": "Max 400 mg/24 h adulte — Intervalles ≥ 6 h",
        "ref": "BCFI / EMA 2019 — Tramadol",
        "alerts": alerts,
    }, None)


def piritramide(poids: float, age: float, atcd: list) -> Result:
    """Piritramide IV (Dipidolor® 7,5 mg/ml) — BCFI / SFAR 2010.
    ⚠️ CONTRE-INDIQUÉ < 1 an (BCFI — données insuffisantes nourrisson).
    Réduction de dose obligatoire : âge ≥ 70 ans, IRC, IH.
    Source : BCFI — Piritramide IV / Dipidolor®.
    """
    atcd = atcd or []
    # CI nourrisson < 1 an (BCFI)
    if age < 1:
        return None, (
            "CONTRE-INDIQUÉ < 1 an (BCFI) — Données insuffisantes chez le nourrisson. "
            "Utiliser morphine titrée avec monitoring continu."
        )

    alerts = _opioid_alerts(atcd)

    # Facteurs de réduction : âge ≥ 70 ans, IRC, IH, poids < 50 kg
    reduction = _has(atcd, "Insuffisance rénale chronique", "Insuffisance hépatique") or age >= 70
    facteur = 0.5 if reduction else 1.0
    if reduction:
        _add(alerts, "Dose réduite 50 % (âge ≥ 70 / IRC / IH) — Titration prudente", "warning")

    plafond = (PIRI_PLAFOND_LT70 if poids < 70 else PIRI_PLAFOND_GE70) * facteur
    dose_min = _r(min(PIRI_BOLUS_MIN * poids * facteur, plafond), 1)
    dose_max = _r(min(PIRI_BOLUS_MAX * poids * facteur, plafond), 1)

    # Antidote à portée
    _add(alerts, "Antidote : Naloxone 0,4 mg IV si FR < 10/min ou sédation excessive", "info")

    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "facteur_reduction": facteur,
        "admin": "IV lent 2-3 min — titrer, répéter si EVA > 3 après 15 min",
        "note": f"Dipidolor® 7,5 mg/ml → {_r(dose_max/7.5,2)} ml",
        "ref": "BCFI / SFAR — Piritramide IV (Dipidolor®)",
        "alerts": alerts,
    }, None)


def morphine(poids: float, age: float, atcd: list,
             taille_cm: float = 170.0, sexe: str = "M") -> Result:
    """Morphine IV titrée — SFAR / BCFI.
    Adaptation obligatoire : nourrisson < 6 mois, IRC, sujet âgé ≥ 70 ans.
    Obésité (IMC ≥ 35) : utilise le Poids Ajusté (SFAR 2021).
    Source : SFAR 2010 / BCFI — Morphine IV.
    """
    atcd = atcd or []
    alerts = _opioid_alerts(atcd)
    # Correction poids si obèse
    poids_eff, pit_note = poids_dosage_opioides(poids, taille_cm, sexe)
    if pit_note:
        _add(alerts, pit_note, "warning")
    poids = poids_eff  # utiliser le poids corrigé pour la suite

    # Nourrisson < 6 mois — seulement en réanimation avec monitoring respiratoire
    if age < 0.5:
        _add(alerts,
             "Nourrisson < 6 mois : morphine uniquement en réanimation avec monitoring "
             "respiratoire continu (SFAR). Utiliser morphine 0,05 mg/kg MAXIMUM, "
             "puis 0,025 mg/kg/h PSE avec capnographe.", "danger")

    # Facteur de réduction
    irc  = _has(atcd, "Insuffisance rénale chronique")
    aged = age >= 70
    if irc:
        _add(alerts, "IRC : accumulation M6G (métabolite actif) — réduire dose et espacer les injections", "warning")
    if aged:
        _add(alerts, "Âge ≥ 70 ans : réduire dose initiale de 30-50 %, palier 1 mg/5 min", "warning")

    facteur = 0.5 if (irc or aged) else 1.0
    plafond = (MORPH_PLAFOND_GE100 if poids >= 100 else MORPH_PLAFOND_STD) * facteur
    dose_min = _r(MORPH_MIN_KG * poids * facteur, 1)
    dose_max = _r(min(MORPH_MAX_KG * poids * facteur, plafond), 1)
    palier   = 1.0 if (irc or aged) else MORPH_PALIER_MG

    _add(alerts, "Antidote : Naloxone 0,4 mg IV si FR < 10/min ou score de sédation ≥ 3", "info")

    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "palier_mg": palier,
        "facteur": facteur,
        "admin": f"IV titration : {palier} mg / {'5 min' if palier >= 2 else '10 min'} jusqu'à EVA ≤ 3",
        "note": f"Dose initiale {dose_min} mg — plafond {dose_max} mg",
        "ref": "SFAR 2010 / BCFI — Morphine titrée",
        "alerts": alerts,
    }, None)


def naloxone(poids: float, age: float, dependant: bool = False, atcd: list = None) -> Result:
    """Naloxone IV/SC/IM (Narcan® 0,4 mg/ml) — Intoxication opioïdes — BCFI.
    
    Stratégie : titration douce si dépendant (éviter sevrage brutal),
    bolus standard si surdosage accidentel.
    Perfusion PSE continue si opioïde à longue demi-vie (méthadone, fentanyl patch).
    Source : BCFI / ESA 2021 — Naloxone.
    """
    atcd = atcd or []
    alerts: List[Alert] = [
        ("Demi-vie courte (30-90 min) vs opioïdes longs — surveiller récidive sur 4-12 h", "warning"),
        ("Si opioïde à longue demi-vie (méthadone, fentanyl patch) : PSE continue obligatoire", "warning"),
    ]

    if dependant:
        # Titration douce pour éviter le sevrage brutal (risque OAP, arythmies)
        dose   = NALOO_DEP_MG  # 0,04 mg par palier
        note   = (f"Dépendant : diluer 0,4 mg dans 10 ml NaCl 0,9 % → 0,04 mg/ml. "
                  f"Titrer 0,04 mg IV toutes les 2 min jusqu'à FR > 12/min (objectif : ventilation, pas réveil total)")
        _add(alerts, "Titration douce obligatoire (dépendant) — objectif ventilation, PAS réveil complet", "danger")
    elif age < 18:
        dose = min(_r(NALOO_PED_KG * poids, 2), NALOO_ADULTE_MG)
        note = f"Pédiatrique : {dose} mg IV — 0,01 mg/kg — répéter toutes les 2-3 min si FR < 12/min"
        _add(alerts, f"Pédiatrique : dose calculée {dose} mg pour {poids:.0f} kg", "info")
    else:
        dose = NALOO_ADULTE_MG
        note = "Adulte : 0,4 mg IV — répéter toutes les 2-3 min (max 10 mg total si besoin)"

    # Perfusion continue PSE (si opioïde longue demi-vie)
    # Règle : 2/3 de la dose de reversal efficace / heure (ESA 2021)
    dose_pse_h = _r(dose * 0.67, 2)
    vol_pse    = 50.0  # ml NaCl — concentration : dose_pse_h / 50
    conc_pse   = _r(dose_pse_h / vol_pse, 4) if vol_pse > 0 else 0

    return ({
        "dose": dose,
        "admin": note,
        "note": "Durée d'action 30-90 min — surveiller récidive",
        "pse_continue": {
            "dose_h": dose_pse_h,
            "dilution": f"Après reversal : {dose_pse_h:.2f} mg/h dans NaCl 0,9 %",
            "indication": "Si opioïde longue demi-vie (méthadone, fentanyl patch, héroïne retard)",
        },
        "ref": "BCFI / ESA 2021 — Naloxone (Narcan® 0,4 mg/ml)",
        "alerts": alerts,
    }, None)


def adrenaline(poids: float, atcd: list = None) -> Result:
    """Adrénaline IM — Anaphylaxie — BCFI / EAACI 2023."""
    atcd = atcd or []
    dose_mg = ADRE_DOSE_ADULTE_MG if poids >= ADRE_POIDS_ADULTE_KG else _r(ADRE_DOSE_KG * poids, 2)
    return ({
        "dose_mg": _r(dose_mg, 2),
        "voie": "IM cuisse antéro-latérale",
        "note": f"Sterop 1 mg/ml → volume = {_r(dose_mg, 2)} ml",
        "rep": "Répéter toutes les 5-10 min si choc persistant",
        "ref": "BCFI / EAACI — Adrénaline IM",
        "alerts": [("Ne jamais retarder l'injection si anaphylaxie", "danger")],
    }, None)


def glucose(poids: float, glycemie_mgdl: Optional[float], atcd: list = None) -> Result:
    """Glucose 30 % IV — Hypoglycémie — BCFI."""
    atcd = atcd or []
    if glycemie_mgdl is None:
        return None, "Glycémie capillaire manquante"
    if glycemie_mgdl >= 70:
        return None, f"Hypoglycémie non documentée ({glycemie_mgdl:.0f} mg/dl)"
    dose_g = min(GLUCOSE_DOSE_KG * poids, GLUCOSE_MAX_G)
    vol_ml = dose_g / 0.3
    return ({
        "dose_g": _r(dose_g, 1),
        "vol": f"{_fmt(vol_ml)} ml de glucose 30 %",
        "ctrl": "Recontôler la glycémie à 15 min",
        "ref": "BCFI — Glucose hypertonique IV",
        "alerts": [("Perfusion sur voie veineuse fiable : risque d'extravasation", "warning")],
    }, None)


def ceftriaxone(poids: float, age: float, atcd: list = None) -> Result:
    """Ceftriaxone IV — Urgence infectieuse — BCFI."""
    atcd = atcd or []
    dose_g = CEFRTRX_ADULTE_G if age >= 15 or poids >= 50 else min(CEFRTRX_PED_KG * poids, CEFRTRX_ADULTE_G)
    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance hépatique"):
        _add(alerts, "Insuffisance hépatique : vérifier protocole local", "warning")
    return ({
        "dose_g": _r(dose_g, 2),
        "admin": "IV lent 3-5 min ou perfusion selon dilution locale",
        "note": "Purpura / sepsis / méningite : ne pas retarder si indication forte",
        "ref": "BCFI / SPILF — Ceftriaxone IV",
        "alerts": alerts,
    }, None)


def litican(poids: float, age: float, atcd: list = None) -> Result:
    """Litican® IV/IM — Alizapride — Antiémétique dopaminergique.

    Principe actif : ALIZAPRIDE (benzamide substitué — antagoniste D2).
    Indications : nausées / vomissements post-opératoires, chimiothérapie,
                  colique néphrétique, migraine avec vomissements.
    NE PAS CONFONDRE avec :
      - Tiémonium (Visceralgine®) — antispasmodique anticholinergique
      - Phloroglucinol (Spasfon®) — antispasmodique musculotrope

    Contre-indications absolues :
      - Phéochromocytome (risque de poussée hypertensive)
      - Association IMAO (risque sérotoninergique)
      - Enfant < 15 ans (pas d'AMM pédiatrique)
    Source : BCFI — Alizapride (Litican®) / RCP Litican® 50 mg/2 ml.
    """
    atcd = atcd or []
    alerts: List[Alert] = []

    # Contre-indications absolues
    if _has(atcd, "IMAO (inhibiteurs MAO)"):
        return None, "CONTRE-INDIQUÉ : IMAO — risque sérotoninergique"
    if age < 15:
        return None, "CONTRE-INDIQUÉ : Litican® (alizapride) — pas d'AMM avant 15 ans"

    # Précautions
    if _has(atcd, "Insuffisance rénale chronique"):
        _add(alerts, "IRC : réduire la dose — élimination rénale de l'alizapride", "warning")
    if _has(atcd, "Épilepsie"):
        _add(alerts, "Épilepsie : les benzamides abaissent le seuil épileptogène", "warning")
    if _has(atcd, "Parkinson") or _has(atcd, "Antidépresseurs ISRS/IRSNA"):
        _add(alerts, "Parkinson / ISRS : risque de syndrome extrapyramidal majoré", "warning")

    # Dose — adulte uniquement (pas de calcul mg/kg pour alizapride)
    dose_mg = 50.0   # Litican® 50 mg/2 ml — dose standard adulte IM ou IV
    return ({
        "dose_mg":   dose_mg,
        "voie":      "IV lent (2 min) ou IM",
        "dose_note": "50 mg — répétable 1 fois après 4-6h si besoin — max 200 mg/24h",
        "freq":      "Toutes les 4-6h selon besoin — max 4 injections/24h",
        "ref":       "BCFI / RCP — Alizapride (Litican® 50 mg/2 ml)",
        "alerts":    alerts,
    }, None)


def salbutamol(poids: float, age: float, gravite: str = "moderee", atcd: list = None) -> Result:
    """Salbutamol nébulisation — Bronchospasme — BCFI."""
    atcd = atcd or []
    dose_mg = {"legere": 2.5, "moderee": 2.5, "severe": 5.0}.get(gravite, 2.5)
    return ({
        "dose_mg": dose_mg,
        "admin": "Nébulisation 15-20 min",
        "dilution": f"{dose_mg} mg dans 3-4 ml NaCl 0,9 %",
        "debit_o2": "O2 6-8 L/min",
        "rep": "Répéter toutes les 20 min si bronchospasme sévère",
        "ref": "BCFI / GINA — Salbutamol nébulisation",
        "alerts": [],
    }, None)


def furosemide(poids: float, age: float, atcd: list = None) -> Result:
    """Furosémide IV — OAP cardiogénique / Surcharge volémique — BCFI.
    
    Adaptation obligatoire en cas d'IRC :
    - DFG > 60 : dose standard 40-80 mg
    - DFG 30-60 : doubler la dose (80-160 mg)  
    - DFG < 30  : dose jusqu'à 240-320 mg (sinon inefficace — résistance diurétique)
    Source : BCFI / Kidney Disease Improving Global Outcomes (KDIGO 2020).
    """
    atcd = atcd or []
    alerts: List[Alert] = []

    irc = _has(atcd, "Insuffisance rénale chronique")
    ica = _has(atcd, "Insuffisance cardiaque")

    if irc:
        dose_min = 80.0
        dose_max = 240.0
        _add(alerts,
             "IRC — Résistance diurétique : besoins 3-5× supérieurs (KDIGO 2020). "
             "Commencer à 80 mg IV — Titrer jusqu'à 240-320 mg si diurèse < 0,5 ml/kg/h. "
             "Surveiller kaliémie et créatinine (hypokaliémie + azotémie aiguë)", "warning")
        _add(alerts,
             "Si IRC avancée (DFG < 15) : furosémide souvent inefficace seul — "
             "envisager ultrafiltration (Tolvaptan ou consultation néphro)", "info")
    else:
        dose_min = 40.0
        dose_max = 80.0
        if ica:
            _add(alerts,
                 "IC chronique sous diurétiques au long cours : "
                 "augmenter la dose à 1-2× la dose orale habituelle en IV", "info")

    if age >= 75:
        _add(alerts, "Sujet âgé ≥ 75 ans : surveiller la déshydratation et l'hypotension orthostatique", "warning")

    _add(alerts, "Surveiller K⁺, Na⁺, créatinine à 2-4 h — Objectif diurèse ≥ 0,5 ml/kg/h", "info")

    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "admin": "IV lent en 2-5 min (max 4 mg/min pour éviter ototoxicité)",
        "note": f"Répéter selon diurèse — {'IRC : titration aggressive nécessaire' if irc else 'Standard : 40-80 mg'}",
        "ref": "BCFI / KDIGO 2020 — Furosémide IV",
        "alerts": alerts,
    }, None)


def ondansetron(poids: float, age: float, atcd: list = None) -> Result:
    """Ondansétron IV — Antiémétique — BCFI."""
    atcd = atcd or []
    dose_mg = 4.0 if age >= 18 else min(0.1 * poids, 4.0)
    return ({
        "dose_mg": _r(dose_mg, 1),
        "admin": "IV lent en 2-5 min",
        "note": "Max 4 mg/dose — 8 mg/24 h",
        "ref": "BCFI — Ondansétron IV",
        "alerts": [],
    }, None)


def acide_tranexamique(poids: float, age: float, atcd: list = None) -> Result:
    """Acide tranexamique IV — Hémorragie — Protocole CRASH-2."""
    atcd = atcd or []
    return ({
        "dose_g": 1.0,
        "admin": "1 g IV en 10 min puis 1 g en 8 h si besoin",
        "note": "À administrer dans les 3 h suivant le traumatisme",
        "ref": "CRASH-2 / BCFI — Acide tranexamique IV",
        "alerts": [("Délai critique : efficacité maximale < 3h post-traumatisme", "danger")],
    }, None)


def methylprednisolone(poids: float, age: float, atcd: list = None) -> Result:
    """Méthylprednisolone IV — Antiinflammatoire — BCFI."""
    atcd = atcd or []
    dose_mg = 40.0 if age >= 18 else min(1.0 * poids, 40.0)
    alerts: List[Alert] = []
    if _has(atcd, "Diabète type 1", "Diabète type 2"):
        _add(alerts, "Diabète : surveillance glycémique renforcée sous corticoïdes", "warning")
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "IV lent en 2-5 min",
        "ref": "BCFI — Méthylprednisolone IV",
        "alerts": alerts,
    }, None)


def crise_hypertensive(pas: float, contexte: str, poids: float, atcd: list = None) -> Result:
    """Gestion crise hypertensive selon étiologie — BCFI / ESC 2023."""
    atcd = atcd or []
    cibles = {
        "Urgence hypertensive standard":       "Réduire PAS de 25 % en 1h, puis ≤ 160/100 en 6h",
        "AVC ischémique (non thrombolysé)":    "PAS cible < 220 mmHg (respecter l'hypertension réflexe)",
        "AVC ischémique (si thrombolyse)":     "PAS cible < 180/105 mmHg",
        "AVC hémorragique":                    "PAS cible 140-160 mmHg",
        "Dissection aortique":                 "PAS cible < 120 mmHg — FC < 60 bpm — Bêtabloquant IV URGENT",
        "OAP hypertensif":                     "Dérivé nitré sublingual puis IV + furosémide",
    }
    cible = cibles.get(contexte, "Cible selon contexte clinique — Avis médical")
    return ({
        "contexte": contexte,
        "cible": cible,
        "ref": "ESC 2023 / BCFI — Urgences hypertensives",
        "alerts": [("Ne jamais normaliser trop vite — risque ischémique cérébral", "danger")],
    }, None)


def neutralisation_aod(molecule: str, atcd: list = None) -> dict:
    """Neutralisation AOD — Protocoles belges — BCFI."""
    antidotes = {
        "Dabigatran (Pradaxa)":      {"mesure_avant": "Hémostase — anti-IIa", "antidote": "Idarucizumab (Praxbind) 5 g IV — 2 x 2,5 g"},
        "Apixaban (Eliquis)":         {"mesure_avant": "Hémostase — anti-Xa", "antidote": "Andexanet alfa ou FEIBA selon disponibilité locale"},
        "Rivaroxaban (Xarelto)":      {"mesure_avant": "Hémostase — anti-Xa", "antidote": "Andexanet alfa ou FEIBA selon disponibilité locale"},
        "AVK (Sintrom/Marcoumar)":    {"mesure_avant": "TP/INR urgent", "antidote": "PPSB 25-50 UI/kg + vitamine K 5-10 mg IV"},
    }
    return antidotes.get(molecule, {
        "mesure_avant": "Hémostase complète",
        "antidote": "PPSB 25-50 UI/kg + vitamine K 5-10 mg IV — valable pour AVK ou molécule inconnue",
    })


def sepsis_bundle_1h(pas: float, lactate: Optional[float], temp: float, fc: float, poids: float, atcd: list = None) -> dict:
    """Bundle Sepsis 1h — SSC 2021."""
    atcd = atcd or []
    choc = pas < 90 or (lactate is not None and lactate >= 4.0)
    remplissage_mlkg = 15 if _has(atcd, "Insuffisance cardiaque") else 30
    # Critères de choc septique affinés (SSC 2021)
    choc_lactate_haut  = lactate is not None and lactate >= 4.0
    choc_lactate_mod   = lactate is not None and 2.0 <= lactate < 4.0
    choc = pas < 90 or choc_lactate_haut
    choc_intermediaire = not choc and (choc_lactate_mod or pas < 100)

    checklist = [
        ("Lactate",       "Dosage rapide si non fait",                    "warning"),
        ("Hémocultures",  "Avant antibiothérapie si possible (2 paires)", "info"),
        ("Antibiothérapie", "Dans l'heure si sepsis suspecté",            "danger" if choc else "warning"),
        ("Remplissage",   f"{remplissage_mlkg} ml/kg cristalloïdes en 30 min",    "danger" if choc else "warning"),
        ("Vasopresseurs", "Si PAS < 65 mmHg après remplissage",           "danger" if choc else "info"),
        ("Contrôle source", "Identifier et contrôler le foyer infectieux", "warning"),
    ]
    alerts: List[Alert] = []
    if choc_lactate_haut:
        _add(alerts, f"Lactate {lactate:.1f} mmol/l ≥ 4 — CHOC SEPTIQUE — Vasopresseurs après 30 ml/kg", "danger")
    elif choc_lactate_mod:
        _add(alerts, f"Lactate {lactate:.1f} mmol/l entre 2 et 4 — Sepsis sévère — Remplissage et réévaluation", "warning")
    if choc:
        _add(alerts, "Hypotension / lactate élevé : choc septique — Réanimation immédiate", "danger")
    if temp < 36.0 or temp >= 38.3:
        _add(alerts, "Température anormale compatible avec sepsis", "warning")
    if fc >= 120:
        _add(alerts, "Tachycardie majeure : surveillance rapprochée", "warning")
    return {"choc_septique": choc, "checklist": checklist, "alerts": alerts}


def ketamine_intranasale(poids: float, age: float, atcd: list = None) -> Result:
    """Kétamine intranasale — Protocole pédiatrique urgences."""
    if age >= 18:
        return None, "Kétamine intranasale réservée au protocole pédiatrique"
    dose_mg = min(poids * 1.0, 50.0)
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "IN, répartir en 2 narines",
        "onset": "Début d'effet 5-10 min",
        "duree": "Durée 20-30 min",
        "surv": "Surveiller dissociation, vomissements et saturation",
        "ref": "Protocoles pédiatriques urgences — Kétamine IN",
        "alerts": [("Alternative avant VVP si douleur aiguë intense", "info")],
    }, None)


def vesiera(poids: float, age: float, atcd: list = None) -> Result:
    """Vesiera — Perfusion kétamine-magnésium — Protocole algologue Hainaut."""
    return ({
        "dose": "Selon protocole algologue",
        "admin": "Perfusion IV lente de kétamine sur 3 h, associée au magnésium",
        "note": "Traitement monitorisé — Hors autonomie IAO sans prescription médicale",
        "ref": "Protocole Hainaut — Perfusion kétamine Vesiera",
        "alerts": [("Surveillance monitorage, TA, FC et saturation pendant la perfusion", "warning")],
    }, None)


def clevidipine(pas: float, poids: float, contexte: str = "HTA sévère", atcd: list = None) -> Result:
    """Clévidipine IV (Vesierra®) — HTA sévère — BCFI/ESC 2023.
    Inhibiteur calcique dihydropyridine d'action ultrarapide — T½ ~1 min.
    """
    atcd = atcd or []
    if _has(atcd, "Sténose aortique sévère"):
        return None, "CONTRE-INDIQUÉ : Sténose aortique sévère"
    if _has(atcd, "Allergie soja", "Allergie œuf"):
        return None, "CONTRE-INDIQUÉ : Allergie soja/œuf (émulsion lipidique)"
    if _has(atcd, "Insuffisance cardiaque décompensée"):
        return None, "CONTRE-INDIQUÉ : Insuffisance cardiaque décompensée (shunt AV)"

    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance hépatique"):
        _add(alerts, "Insuff. hépatique : prudence — surveillance rapprochée", "warning")
    if _has(atcd, "Insuffisance rénale chronique"):
        _add(alerts, "Insuff. rénale : pas d'ajustement (métabolisme plasmatique)", "info")
    if _has(atcd, "Diabète type 1", "Diabète type 2"):
        _add(alerts, "Diabète : l'émulsion lipidique apporte ~0,2 g lipides/ml", "info")

    cibles = {
        "HTA sévère":          "PAS cible < 180 mmHg — réduction progressive 20-25 % en 1 h",
        "OAP hypertensif":     "PAS cible < 140 mmHg — vasodilatation pulmonaire bénéfique",
        "Dissection aortique": "PAS < 120 mmHg ET FC < 60/min — associer bêtabloquant IV",
        "Péri-opératoire":     "Cible définie par anesthésiste/chirurgien",
    }
    return ({
        "debit_init":  CLEV_DEBIT_INIT_MG_H,
        "debit_max":   CLEV_DEBIT_MAX_MG_H,
        "palier_s":    CLEV_PALIER_S,
        "cible":       cibles.get(contexte, "Cible selon étiologie — Avis médical"),
        "admin":       (f"IV continue : démarrer à {CLEV_DEBIT_INIT_MG_H} mg/h — "
                        f"doubler toutes les {CLEV_PALIER_S} s jusqu'à effet — "
                        f"max {CLEV_DEBIT_MAX_MG_H} mg/h"),
        "note":        "Flacon 50 mg / 2 ml (25 mg/ml) — Diluer avant administration — Agiter avant usage",
        "ref":         "BCFI / ESC 2023 — Clévidipine (Vesierra®) IV",
        "alerts":      alerts,
    }, None)


def meopa(age: float, atcd: list = None) -> Result:
    """MEOPA (Kalinox® 50/50 O₂/N₂O) — Analgésie/Anxiolyse procédurale — BCFI."""
    atcd = atcd or []
    ci = []
    if _has(atcd, "Pneumothorax"):
        ci.append("pneumothorax (expansion gazeuse N₂O)")
    if _has(atcd, "Occlusion intestinale", "Distension abdominale"):
        ci.append("distension gazeuse/occlusion")
    if _has(atcd, "Déficit vitamine B12", "Déficit folates"):
        ci.append("déficit B12/folates (inactivation méthionine-synthase)")
    if _has(atcd, "Hypertension intracrânienne"):
        ci.append("HTIC (vasodilatation cérébrale)")
    if age > 0 and age < 1:
        ci.append("nourrisson < 1 an")
    if ci:
        return None, "CONTRE-INDIQUÉ : " + " | ".join(ci)

    alerts: List[Alert] = [
        ("Consentement éclairé du patient/tuteur obligatoire", "warning"),
        ("Opérateur administrateur ≠ opérateur procédure (2 professionnels requis)", "info"),
        ("Ventilation de la pièce obligatoire — Récupération 5 min avant mobilisation", "info"),
    ]
    if _has(atcd, "BPCO"):
        _add(alerts, "BPCO : FiO₂ 50 % — Surveiller SpO₂ en continu", "warning")
    if age < 5:
        _add(alerts, "Enfant < 5 ans : coopération requise — évaluer la faisabilité", "warning")
    if _has(atcd, "Grossesse"):
        _add(alerts, "Grossesse T1 : éviter — T2/T3 : discussion spécialisée requise", "danger")

    return ({
        "melange":    "50 % O₂ / 50 % N₂O (Kalinox®)",
        "debit":      f"≥ {MEOPA_DEBIT_L_MIN} L/min",
        "duree_max":  f"≤ {MEOPA_DUREE_MAX_MIN} min par session",
        "admin":      (f"Pré-inhalation 3 min avant geste — Masque étanche — "
                       f"Débit ≥ {MEOPA_DEBIT_L_MIN} L/min — Max {MEOPA_DUREE_MAX_MIN} min"),
        "note":       "Surveillance SpO₂ + conscience — Arrêt si nausées/vomissements",
        "ref":        "BCFI / SFMU — MEOPA Kalinox® 50/50 — Analgésie procédurale",
        "alerts":     alerts,
    }, None)


def midazolam_iv(poids: float, age: float, indication: str = "sedation", atcd: list = None) -> Result:
    """Midazolam IV (Hypnovel®) — Sédation/Convulsion urgence — BCFI."""
    atcd = atcd or []
    alerts: List[Alert] = []
    if _has(atcd, "BPCO"):
        _add(alerts, "BPCO : réduire dose de 30 % — Risque dépression respiratoire", "warning")
    if _has(atcd, "Insuffisance hépatique"):
        _add(alerts, "Insuff. hépatique : demi-vie prolongée — titration très prudente", "warning")
    if _has(atcd, "Anticoagulants/AOD"):
        _add(alerts, "Anticoagulants : privilégier voie IV", "info")

    if indication == "convulsion":
        dose_mg = _r(min(MIDAZ_IV_CONVULS_KG * poids, MIDAZ_IV_CONVULS_MAX), 1)
        admin   = "IV lent 2 min — Surveillance SpO₂ continue — Répéter si nécessaire (max 2×)"
        note    = f"Crise convulsive : {_fmt(dose_mg)} mg IV — Antidote : Flumazénil 0,2 mg IV"
    else:
        dose_mg = _r(min(MIDAZ_IV_KG * poids, MIDAZ_IV_MAX_MG), 1)
        admin   = "IV lent 2 min — Titrer par bolus 1 mg/2 min — Matériel réa disponible"
        note    = f"Sédation : {_fmt(dose_mg)} mg IV — Antidote : Flumazénil (Anexate®) 0,2 mg IV"

    if _use_mg_kg(age):
        kg = MIDAZ_IV_CONVULS_KG if indication == "convulsion" else MIDAZ_IV_KG
        dose_display = f"{_fmt(kg)} mg/kg ({_fmt(dose_mg)} mg)"
    else:
        dose_display = f"{_fmt(dose_mg)} mg"

    return ({
        "dose_mg":      dose_mg,
        "dose_display": dose_display,
        "admin":        admin,
        "note":         note,
        "antidote":     "Flumazénil (Anexate®) 0,2 mg IV — répéter toutes les 60 s si besoin",
        "ref":          "BCFI — Midazolam IV (Hypnovel®)",
        "alerts":       alerts,
    }, None)


def protocole_eva(poids: float, age: float, eva: int, atcd: list = None) -> list:
    """Recommandations antalgie selon EVA — Circulaire belge 2014."""
    atcd = atcd or []
    if eva <= 3:
        return [("EVA ≤ 3 — Réévaluation à 30 min", "info")]
    elif eva <= 6:
        return [("EVA 4-6 — Paracétamol IV ou AINS si non contre-indiqué", "warning")]
    else:
        return [
            ("EVA ≥ 7 — Antalgie forte requise — Piritramide ou Morphine IV", "danger"),
            ("Réévaluation obligatoire à 30 min post-antalgie (Circulaire 2014)", "warning"),
        ]


def protocole_epilepsie_ped(poids: float, age: float, duree_min: float, en_cours: bool, atcd: list = None) -> dict:
    """
    Protocole anticonvulsivant pédiatrique — BCFI / Lignes directrices belges.
    Retourne les doses calculées pour chaque étape thérapeutique.
    """
    atcd = atcd or []
    diaz_rect  = _r(min(DIAZEPAM_RECT_KG * poids, DIAZEPAM_RECT_MAX_MG), 1)
    midaz_bucc = _r(min(MIDAZOLAM_IM_IN_KG * poids, MIDAZOLAM_BUCC_MAX_MG), 1)
    loraz_iv   = _r(min(LORAZEPAM_IV_KG * poids, LORAZEPAM_IV_MAX_MG), 1)
    clona_iv   = _r(min(CLONAZEPAM_IV_KG * poids, CLONAZEPAM_IV_MAX_MG), 2)
    diaz_iv    = _r(min(DIAZEPAM_IV_KG * poids, DIAZEPAM_IV_MAX_MG), 1)
    phenob_iv  = _r(min(PHENOBARB_IV_KG * poids, PHENOBARB_IV_MAX_MG), 0)
    leveti_iv  = _r(min(LEVETI_IV_KG * poids, LEVETI_IV_MAX_MG), 0)
    valpr_iv   = _r(min(VALPROATE_IV_KG * poids, VALPROATE_IV_MAX_MG), 0)

    eme_etabli = en_cours and duree_min >= EME_ETABLI_MIN
    eme_operationnel = en_cours and duree_min >= EME_OPERATIONNEL_MIN

    return {
        "poids": poids,
        "eme_etabli": eme_etabli,
        "eme_operationnel": eme_operationnel,
        "midazolam_buccal": {
            "dose": f"{midaz_bucc} mg buccal",
            "note": "1ère ligne si sans VVP — Répartir en 2 côtés",
            "ref": "BCFI — Midazolam buccal",
        },
        "diazepam_rectal": {
            "dose": f"{diaz_rect} mg rectal",
            "note": "Alternative si midazolam buccal non disponible",
            "ref": "BCFI — Diazépam rectal",
        },
        "lorazepam_iv": {
            "dose": f"{loraz_iv} mg IV lent",
            "note": "Avec VVP — 2e ligne ou 1ère si VVP en place",
            "ref": "BCFI — Lorazépam IV",
        },
        "clonazepam_iv": {
            "dose": f"{clona_iv} mg IV lent",
            "note": "Alternative lorazépam si disponible",
            "ref": "BCFI — Clonazépam IV",
        },
        "phenobarbital_iv": {
            "dose": f"{phenob_iv} mg IV",
            "debit": f"Max {PHENOBARB_DEBIT_MG_KG_MIN} mg/kg/min",
            "note": "EME réfractaire — Avis pédiatre/réanimateur",
            "ref": "BCFI — Phénobarbital IV",
        },
        "levetiracetam_iv": {
            "dose": f"{leveti_iv} mg IV en 15 min",
            "note": "Alternative phénobarbital — EME réfractaire",
            "ref": "BCFI — Lévétiracétam IV",
        },
        "valproate_iv": {
            "dose": f"{valpr_iv} mg IV",
            "debit": f"Min {VALPROATE_IV_DEBIT_MIN} mg/kg/min",
            "note": "Contre-indiqué si hépatopathie / mitochondriopathie",
            "ref": "BCFI — Valproate IV",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# MIDAZOLAM IM / IN — Pédiatrie et sédation procédurale
# Source : BCFI — Midazolam IM/IN
# ─────────────────────────────────────────────────────────────────────────────

def midazolam_im(poids: float, age: float = 40, atcd: list = None) -> Result:
    """Midazolam IM ou IN (Hypnovel® 5 mg/ml) — Sédation / Convulsion.
    Dose 0,2 mg/kg IM ou IN, plafond 10 mg.
    Source : BCFI — Midazolam IM/IN.
    """
    atcd = atcd or []
    dose = min(_r(0.2 * poids, 1), 10.0)
    vol  = _r(dose / 5.0, 2)   # solution 5 mg/ml
    alerts: List[Alert] = [
        ("Antidote : Flumazénil 0,2 mg IV (max 1 mg)", "info"),
        ("Surveiller SpO2 + FR — matériel de VA à portée", "warning"),
    ]
    if age > 75 or _has(atcd, "Insuffisance hépatique"):
        alerts.append(("Sujet âgé / IH : réduire la dose de 30-50 %", "warning"))
    return ({
        "medicament":    "Midazolam IM/IN (Hypnovel® 5 mg/ml)",
        "dose_mg":       dose,
        "volume_ml":     vol,
        "admin":         "IM (cuisse antéro-lat.) ou IN (atomiseur MAD — répartir en 2 narines)",
        "onset":         "IM 5-10 min / IN 3-5 min",
        "surveillance":  "SpO2, FR, conscience toutes les 5 min",
        "ref":           "BCFI — Midazolam IM/IN",
        "alerts":        alerts,
    }, None)


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLES ANTICIPÉS IAO — par motif de recours
# Source : Protocoles locaux Hainaut / SFMU
# ─────────────────────────────────────────────────────────────────────────────

PROTOCOLES_IAO: Dict[str, List[dict]] = {
    "Douleur thoracique / SCA": [
        {"med": "Aspirine",  "dose": "250 mg IV",           "voie": "IV",  "condition": lambda v: (v.get("pas") or 120) > 100},
        {"med": "Trinitrine","dose": "0,5 mg sublingual",   "voie": "SL",  "condition": lambda v: (v.get("pas") or 120) > 100},
        {"med": "O₂",        "dose": "Cible SpO2 94-98 %",  "voie": "Masque", "condition": lambda v: (v.get("spo2") or 98) < 94},
    ],
    "Allergie / anaphylaxie": [
        {"med": "Adrénaline IM", "dose_fn": lambda p: f"{min(0.5, 0.01*p):.2f} mg", "voie": "IM cuisse"},
        {"med": "NaCl 0,9 %",   "dose": "500 ml IV sur 15 min", "voie": "IV"},
    ],
    "Dyspnée / insuffisance respiratoire": [
        {"med": "Salbutamol", "dose": "5 mg nébulisation", "voie": "INH"},
        {"med": "O₂",         "dose": "Cible SpO2 94-98 %", "voie": "Masque/lunettes"},
    ],
    "Convulsions / EME": [
        {"med": "Midazolam buccal", "dose_fn": lambda p: f"{min(10.0, round(0.3*p,1)):.1f} mg", "voie": "Buccale"},
        {"med": "O₂",              "dose": "Haute concentration", "voie": "Masque"},
    ],
    "Hypoglycémie": [
        {"med": "Glucose 30 %", "dose_fn": lambda p: f"{min(15, round(0.3*p,1)):.1f} g IV", "voie": "IV lent"},
    ],
    "Pétéchie / Purpura": [
        {"med": "Ceftriaxone", "dose_fn": lambda p: f"{CEFRTRX_ADULTE_G} g IV", "voie": "IV 3-5 min"},
        {"med": "O₂ + VVP",   "dose": "Large calibre — remplissage si choc", "voie": "IV"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY CHECKS — Vérifications croisées ATCD × médicament
# Source : BCFI — Interactions médicamenteuses
# ─────────────────────────────────────────────────────────────────────────────

SAFETY_CHECKS = [
    {
        "medicament": "Tramadol",
        "condition": lambda patient, v: any("IMAO" in x for x in patient.get("atcd", [])),
        "message": "IMAO — Tramadol CONTRE-INDIQUÉ ABSOLU (risque syndrome sérotoninergique)",
        "niveau": "danger",
    },
    {
        "medicament": "Tramadol",
        "condition": lambda patient, v: any("ISRS" in x or "IRSNA" in x for x in patient.get("atcd", [])),
        "message": "ISRS/IRSNA — Tramadol déconseillé (interaction sérotoninergique)",
        "niveau": "warning",
    },
    {
        "medicament": "AINS",
        "condition": lambda patient, v: any(c in patient.get("atcd", []) for c in ["Insuffisance rénale chronique", "Ulcère gastro-duodénal", "Grossesse en cours"]),
        "message": "Contre-indication AINS — IRC / ulcère / grossesse",
        "niveau": "danger",
    },
    {
        "medicament": "Midazolam",
        "condition": lambda patient, v: (v.get("age") or 40) > 75,
        "message": "Sujet âgé > 75 ans — risque dépression respiratoire — réduire dose de 50 %",
        "niveau": "warning",
    },
    {
        "medicament": "Morphine",
        "condition": lambda patient, v: (v.get("age") or 40) > 75 or "BPCO" in patient.get("atcd", []),
        "message": "Morphine — Surveillance SpO2 / FR renforcée (âge > 75 ou BPCO)",
        "niveau": "warning",
    },
    {
        "medicament": "Morphine",
        "condition": lambda patient, v: "Insuffisance rénale chronique" in patient.get("atcd", []),
        "message": "IRC — Morphine : accumulation des métabolites actifs — réduire fréquence",
        "niveau": "warning",
    },
]


def check_safety(medicament: str, patient: dict, vitals: dict) -> List[dict]:
    """Vérifie les contre-indications croisées pour un médicament donné.
    Source : BCFI — Pharmacovigilance.
    """
    alerts = []
    for check in SAFETY_CHECKS:
        if check["medicament"] in medicament:
            try:
                if check["condition"](patient, vitals):
                    alerts.append({"message": check["message"], "niveau": check["niveau"]})
            except Exception:
                pass
    return alerts


# ─────────────────────────────────────────────────────────────────────────────
# GÉNÉRATION D'ÉTIQUETTE PSE — Pour traçabilité seringue auto-pousseuse
# ─────────────────────────────────────────────────────────────────────────────

def generer_etiquette(
    medicament: str,
    concentration: float,   # mg/ml
    debit_mlh: float,       # ml/h
    vol_total: float,       # ml
    poids: float = 70.0,
    operateur: str = "IAO",
) -> str:
    """Génère le texte d'étiquette standardisé pour une PSE.
    Format compatible avec les fiches de traçabilité belges (AR 78 AFMPS).
    """
    gouttes   = int(debit_mlh * 20 / 60)
    autonomie = round(vol_total / debit_mlh, 1) if debit_mlh > 0 else 0
    dose_mg_h = round(concentration * debit_mlh, 2)
    dose_ug_kg_min = round(dose_mg_h * 1000 / 60 / max(1, poids), 2)
    now = __import__("datetime").datetime.now().strftime("%d/%m/%Y %H:%M")

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  {medicament.upper()}\n"
        f"  {concentration * vol_total:.0f} mg / {vol_total:.0f} ml NaCl 0,9 %\n"
        f"  Concentration : {concentration} mg/ml\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Débit    : {debit_mlh} ml/h = {gouttes} gttes/min\n"
        f"  Dose     : {dose_mg_h} mg/h = {dose_ug_kg_min} µg/kg/min\n"
        f"  Autonomie: {autonomie} h ({vol_total:.0f} ml)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Préparé le : {now}\n"
        f"  Opérateur  : {operateur}\n"
        f"  Patient    : {poids:.0f} kg — Session anonyme\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
