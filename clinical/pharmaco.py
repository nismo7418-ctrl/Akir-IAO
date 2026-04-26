# clinical/pharmaco.py — Protocoles pharmacologiques — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Référence : BCFI Belgique, protocoles locaux Hainaut

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from clinical.utils import norm
from config import (
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


# ─────────────────────────────────────────────────────────────────────────────
# ANTALGIQUES
# ─────────────────────────────────────────────────────────────────────────────

def paracetamol(poids: float, age: float, atcd: list) -> Result:
    """Paracétamol IV — BCFI Belgique."""
    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance hépatique"):
        _add(alerts, "Insuffisance hépatique : valider la dose cumulative des 24 h", "warning")
    dose_mg = PARA_DOSE_KG * poids if poids < PARA_POIDS_PIVOT_KG else PARA_DOSE_FIXE_G * 1000.0
    dose_g = dose_mg / 1000.0
    return ({
        "dose_mg": _r(dose_mg, 0),
        "dose_g": _r(dose_g, 2),
        "admin": "IV en 15 min",
        "note": f"15 mg/kg si < {PARA_POIDS_PIVOT_KG} kg, sinon 1 g fixe",
        "ref": "BCFI — Paracétamol IV",
        "alerts": alerts,
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


def tramadol(poids: float, age: float, atcd: list) -> Result:
    """Tramadol PO — BCFI / Hainaut."""
    if age < 1:
        return None, "Tramadol contre-indiqué avant 1 an"
    if _has(atcd, "IMAO (inhibiteurs MAO)"):
        return None, "IMAO : Tramadol / Tradonal contre-indiqué"
    alerts = _opioid_alerts(atcd)
    if age < 15:
        dose_mg = min(max(poids * 1.5, 25.0), 50.0)
    else:
        dose_mg = 50.0
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "PO ou IV lent 100 mg/250 ml NaCl en 30 min",
        "note": f"Max 400 mg/24 h adulte — attention tolérance digestive",
        "ref": "BCFI — Tramadol",
        "alerts": alerts,
    }, None)


def piritramide(poids: float, age: float, atcd: list) -> Result:
    """Piritramide IV (Dipidolor) — BCFI / SFAR 2010."""
    alerts = _opioid_alerts(atcd)
    dose_min = _r(min(PIRI_BOLUS_MIN * poids, PIRI_PLAFOND_LT70 if poids < 70 else PIRI_PLAFOND_GE70), 1)
    dose_max = _r(min(PIRI_BOLUS_MAX * poids, PIRI_PLAFOND_LT70 if poids < 70 else PIRI_PLAFOND_GE70), 1)
    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "admin": "IV lent en 2-3 min",
        "note": f"Titration : bolus {dose_min}-{dose_max} mg — répéter si EVA > 3",
        "ref": "BCFI / SFAR — Piritramide IV",
        "alerts": alerts,
    }, None)


def morphine(poids: float, age: float, atcd: list) -> Result:
    """Morphine IV titrée — SFAR / BCFI."""
    alerts = _opioid_alerts(atcd)
    plafond = MORPH_PLAFOND_GE100 if poids >= 100 else MORPH_PLAFOND_STD
    dose_min = _r(MORPH_MIN_KG * poids, 1)
    dose_max = _r(min(MORPH_MAX_KG * poids, plafond), 1)
    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "palier_mg": MORPH_PALIER_MG,
        "admin": f"IV titration : {MORPH_PALIER_MG} mg/5 min jusqu'à EVA ≤ 3",
        "note": f"Dose initiale {dose_min} mg — plafond {dose_max} mg",
        "ref": "SFAR / BCFI — Morphine titrée",
        "alerts": alerts,
    }, None)


def naloxone(poids: float, age: float, dependant: bool = False, atcd: list = None) -> Result:
    """Naloxone IV — antidote opioïdes — BCFI."""
    atcd = atcd or []
    if dependant:
        dose = 0.04
        note = "Patient dépendant : diluer 0,4 mg dans 10 ml NaCl → 0,04 mg/ml — titrer 1 ml/2 min"
    elif age < 18:
        dose = _r(NALOO_PED_KG * poids, 2)
        note = f"Pédiatrique : {dose} mg IV — répéter si besoin"
    else:
        dose = NALOO_ADULTE_MG
        note = "Adulte : 0,4 mg IV — répéter toutes les 2-3 min si nécessaire"
    return ({
        "dose": dose,
        "admin": note,
        "note": "Durée d'action courte (30-90 min) : surveiller récidive",
        "ref": "BCFI — Naloxone (Narcan)",
        "alerts": [("Demi-vie plus courte que l'opioïde : réévaluation rapprochée", "warning")],
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
    """Litican IM (Tiémonium) — Antispasmodique — Protocole Hainaut."""
    atcd = atcd or []
    alerts: List[Alert] = []
    if _has(atcd, "Glaucome"):
        _add(alerts, "Glaucome : prudence avec l'effet anticholinergique")
    if _has(atcd, "Adénome prostatique", "Rétention urinaire"):
        _add(alerts, "Adénome prostatique / rétention urinaire : risque de rétention")
    dose_mg = LITICAN_DOSE_ADULTE_MG if poids >= LITICAN_POIDS_PIVOT_KG else min(LITICAN_DOSE_KG_ENF * poids, LITICAN_DOSE_MAX_ENF_MG)
    return ({
        "dose_mg": _r(dose_mg, 0),
        "voie": "IM",
        "dose_note": f"Max {LITICAN_DOSE_MAX_JOUR:.0f} mg/24 h",
        "freq": "Répétition selon protocole local",
        "ref": "BCFI / protocole Hainaut — Tiémonium (Litican)",
        "alerts": alerts,
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
    """Furosémide IV — OAP cardiogénique — BCFI."""
    atcd = atcd or []
    dose_min = 40.0
    dose_max = 80.0
    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance rénale chronique"):
        dose_max = 120.0
        _add(alerts, "Insuffisance rénale : dose plus élevée possible selon protocole", "warning")
    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "admin": "IV lent en 2-5 min",
        "ref": "BCFI — Furosémide IV",
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
    checklist = [
        ("Lactate", "Dosage rapide si non fait", "warning"),
        ("Hémocultures", "Avant antibiothérapie si possible", "info"),
        ("Antibiothérapie", "Dans l'heure si sepsis suspecté", "danger" if choc else "warning"),
        ("Remplissage", f"{remplissage_mlkg} ml/kg cristalloïdes", "warning"),
        ("Vasopresseurs", "Si hypotension persistante après remplissage", "danger" if choc else "info"),
    ]
    alerts: List[Alert] = []
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
