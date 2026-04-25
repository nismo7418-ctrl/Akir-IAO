from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from clinical.utils import norm
from config import (
    ADRE_DOSE_ADULTE_MG,
    ADRE_DOSE_KG,
    ADRE_POIDS_ADULTE_KG,
    CEFRTRX_ADULTE_G,
    CEFRTRX_PED_KG,
    CLONAZEPAM_IV_KG,
    CLONAZEPAM_IV_MAX_MG,
    DIAZEPAM_IV_KG,
    DIAZEPAM_IV_MAX_MG,
    DIAZEPAM_RECT_KG,
    DIAZEPAM_RECT_MAX_MG,
    EME_ETABLI_MIN,
    EME_OPERATIONNEL_MIN,
    EME_SEUIL_MIN,
    GLUCOSE_DOSE_KG,
    GLUCOSE_MAX_G,
    LEVETI_IV_KG,
    LEVETI_IV_MAX_MG,
    LITICAN_DOSE_ADULTE_MG,
    LITICAN_DOSE_KG_ENF,
    LITICAN_DOSE_MAX_ENF_MG,
    LITICAN_DOSE_MAX_JOUR,
    LITICAN_POIDS_PIVOT_KG,
    LORAZEPAM_IV_KG,
    LORAZEPAM_IV_MAX_MG,
    MIDAZOLAM_BUCC_MAX_MG,
    MIDAZOLAM_IM_IN_KG,
    MIDAZOLAM_IM_IN_MAX_MG,
    MORPH_MAX_KG,
    MORPH_MIN_KG,
    MORPH_PALIER_MG,
    MORPH_PLAFOND_GE100,
    MORPH_PLAFOND_STD,
    NALOO_ADULTE_MG,
    NALOO_DEP_MG,
    NALOO_PED_KG,
    PARA_DOSE_FIXE_G,
    PARA_DOSE_KG,
    PARA_POIDS_PIVOT_KG,
    PHENOBARB_DEBIT_MG_KG_MIN,
    PHENOBARB_IV_KG,
    PHENOBARB_IV_MAX_MG,
    PIRI_BOLUS_MAX,
    PIRI_BOLUS_MIN,
    PIRI_PLAFOND_GE70,
    PIRI_PLAFOND_LT70,
    VALPROATE_IV_DEBIT_MIN,
    VALPROATE_IV_KG,
    VALPROATE_IV_MAX_MG,
)

Alert = Tuple[str, str]
Result = Tuple[Optional[Dict[str, object]], Optional[str]]


def _has(atcd: list, *items: str) -> bool:
    known = {norm(x) for x in (atcd or [])}
    return any(norm(item) in known for item in items)


def _add(alerts: List[Alert], message: str, level: str = "warning") -> None:
    alerts.append((message, level))


def _r(value: float, digits: int = 1) -> float:
    return round(value + 1e-9, digits)


def _fmt(value: float) -> str:
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"


def _opioid_alerts(atcd: list) -> List[Alert]:
    alerts: List[Alert] = []
    if _has(atcd, "BPCO"):
        _add(alerts, "BPCO: monitorer la ventilation et la sedation sous opioides")
    if _has(atcd, "Insuffisance hepatique"):
        _add(alerts, "Insuffisance hepatique: titration plus prudente", "warning")
    if _has(atcd, "Anticoagulants/AOD"):
        _add(alerts, "Anticoagulants/AOD: privilegier voie IV plutot qu'IM", "warning")
    return alerts


def _nsaid_error(atcd: list) -> Optional[str]:
    blockers: List[str] = []
    if _has(atcd, "Insuffisance renale chronique"):
        blockers.append("insuffisance renale chronique")
    if _has(atcd, "Ulcere gastro-duodenal"):
        blockers.append("ulcere gastro-duodenal")
    if _has(atcd, "Anticoagulants/AOD"):
        blockers.append("anticoagulants/AOD")
    if _has(atcd, "Grossesse en cours"):
        blockers.append("grossesse")
    if _has(atcd, "Insuffisance cardiaque"):
        blockers.append("insuffisance cardiaque")
    if not blockers:
        return None
    return "AINS a eviter: " + ", ".join(blockers)


def paracetamol(poids: float, age: float, atcd: list) -> Result:
    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance hepatique"):
        _add(alerts, "Insuffisance hepatique: valider la dose cumulative des 24 h", "warning")
    dose_mg = PARA_DOSE_KG * poids if poids < PARA_POIDS_PIVOT_KG else PARA_DOSE_FIXE_G * 1000.0
    dose_g = dose_mg / 1000.0
    return ({
        "dose_mg": _r(dose_mg, 0),
        "dose_g": _r(dose_g, 2),
        "admin": "IV en 15 min",
        "note": "Perfu antalgique: 15 mg/kg si < 50 kg, sinon 1 g",
        "ref": "BCFI - Paracetamol IV",
        "alerts": alerts,
    }, None)


def naproxene(poids: float, age: float, atcd: list) -> Result:
    if age < 15:
        return None, "Naproxene non automatise avant 15 ans dans ce protocole IAO"
    err = _nsaid_error(atcd)
    if err:
        return None, err
    dose_mg = 500.0 if poids >= 50 else 250.0
    alerts: List[Alert] = [("A prendre avec nourriture et hydratation correcte", "info")]
    return ({
        "dose_mg": dose_mg,
        "admin": "PO",
        "note": "250-500 mg puis 250-500 mg/12 h, max 1 g/24 h",
        "ref": "BCFI - Naproxene oral",
        "alerts": alerts,
    }, None)


def ketorolac(poids: float, age: float, atcd: list) -> Result:
    err = _nsaid_error(atcd)
    if err:
        return None, err
    dose_mg = 10.0 if age >= 75 or poids < 50 else 30.0
    return ({
        "dose_mg": dose_mg,
        "admin": "IV lent ou IM",
        "note": "Alternative AINS courte duree si protocole local disponible",
        "ref": "BCFI - Ketorolac",
        "alerts": [("Eviter > 48 h et en cas de dehydration", "warning")],
    }, None)


def tramadol(poids: float, age: float, atcd: list) -> Result:
    if age < 1:
        return None, "Tradonal contre-indique avant 1 an"
    if _has(atcd, "IMAO (inhibiteurs MAO)"):
        return None, "IMAO: Tradonal / tramadol contre-indique"
    alerts = _opioid_alerts(atcd)
    if _has(atcd, "Antidepresseurs ISRS/IRSNA"):
        _add(alerts, "ISRS/IRSNA: risque serotoninergique et convulsivant avec tramadol", "danger")

    if age < 15:
        dose_mg = min(max(poids * 1.5, 10.0), 50.0)
        note = f"Tradonal pediatrique: 1-2 mg/kg PO, ici {_fmt(dose_mg)} mg"
    else:
        dose_mg = 50.0 if age >= 75 or poids < 60 else 100.0
        note = "50-100 mg PO, max 400 mg/24 h"

    drops = int(round(dose_mg / 2.5))
    return ({
        "dose_mg": _r(dose_mg, 0),
        "drops": drops,
        "admin": "PO - gouttes Tradonal 100 mg/ml",
        "note": f"{note} ({drops} gouttes environ)",
        "ref": "BCFI - Tradonal / tramadol 100 mg/ml",
        "alerts": alerts,
    }, None)


def piritramide(poids: float, age: float, atcd: list) -> Result:
    alerts = _opioid_alerts(atcd)
    _add(alerts, "Belgique: Dipidolor / piritramide reserve a l'usage hospitalier depuis mars 2024")
    ceiling = PIRI_PLAFOND_GE70 if poids >= 70 else PIRI_PLAFOND_LT70
    dose_min = min(max(poids * PIRI_BOLUS_MIN, 1.0), ceiling)
    dose_max = min(max(poids * PIRI_BOLUS_MAX, 1.0), ceiling)
    return ({
        "dose_min": _r(dose_min),
        "dose_max": _r(dose_max),
        "admin": "IV lent titrable",
        "note": "Bolus initial 0,03-0,05 mg/kg, reevaluation toutes les 5 min",
        "ref": "BCFI / FAGG - Piritramide (Dipidolor)",
        "alerts": alerts,
    }, None)


def morphine(poids: float, age: float, atcd: list) -> Result:
    alerts = _opioid_alerts(atcd)
    ceiling = MORPH_PLAFOND_GE100 if poids >= 100 else MORPH_PLAFOND_STD
    dose_min = min(max(poids * MORPH_MIN_KG, 1.0), ceiling)
    dose_max = min(max(poids * MORPH_MAX_KG, 1.0), ceiling)
    return ({
        "dose_min": _r(dose_min),
        "dose_max": _r(dose_max),
        "palier_mg": MORPH_PALIER_MG,
        "admin": "IV lent titrable",
        "note": f"Bolus 0,05-0,1 mg/kg puis paliers de {MORPH_PALIER_MG:.0f} mg toutes les 5 min",
        "ref": "BCFI - Morphine IV",
        "alerts": alerts,
    }, None)


def naloxone(poids: float, age: float, dependant: bool, atcd: list) -> Result:
    dose = NALOO_DEP_MG if dependant else (min(NALOO_ADULTE_MG, max(NALOO_PED_KG * poids, NALOO_DEP_MG)) if age < 15 else NALOO_ADULTE_MG)
    return ({
        "dose": _r(dose, 2),
        "admin": "IV lent, repeter selon ventilation",
        "note": "Objectif: reprise ventilatoire, pas reveil brutal si patient dependant",
        "ref": "BCFI - Naloxone IV",
        "alerts": [("Surveiller recurarisation apres opioide a demi-vie longue", "warning")],
    }, None)


def adrenaline(poids: float, atcd: list) -> Result:
    dose_mg = ADRE_DOSE_ADULTE_MG if poids >= ADRE_POIDS_ADULTE_KG else min(ADRE_DOSE_KG * poids, ADRE_DOSE_ADULTE_MG)
    return ({
        "dose_mg": _r(dose_mg, 2),
        "voie": "IM cuisse antero-laterale",
        "note": "Sterop 1 mg/ml => volume en ml = dose en mg",
        "rep": "A repeter toutes les 5-10 min si choc persistant",
        "ref": "BCFI / EAACI - Adrenaline IM",
        "alerts": [("Ne jamais retarder l'injection si anaphylaxie", "danger")],
    }, None)


def glucose(poids: float, glycemie_mgdl: Optional[float], atcd: list) -> Result:
    if glycemie_mgdl is None:
        return None, "Glycemie capillaire manquante"
    if glycemie_mgdl >= 70:
        return None, f"Hypoglycemie non documentee ({glycemie_mgdl:.0f} mg/dl)"
    dose_g = min(GLUCOSE_DOSE_KG * poids, GLUCOSE_MAX_G)
    vol_ml = dose_g / 0.3
    return ({
        "dose_g": _r(dose_g, 1),
        "vol": f"{_fmt(vol_ml)} ml de glucose 30 %",
        "ctrl": "Recontroler la glycemie a 15 min",
        "ref": "BCFI - Glucose hypertonique IV",
        "alerts": [("Perfusion sur voie veineuse fiable: risque d'extravasation", "warning")],
    }, None)


def ceftriaxone(poids: float, age: float, atcd: list) -> Result:
    dose_g = CEFRTRX_ADULTE_G if age >= 15 or poids >= 50 else min(CEFRTRX_PED_KG * poids, CEFRTRX_ADULTE_G)
    alerts: List[Alert] = []
    if _has(atcd, "Insuffisance hepatique"):
        _add(alerts, "Insuffisance hepatique: verifier protocole local et bilan associe", "warning")
    return ({
        "dose_g": _r(dose_g, 2),
        "admin": "IV lent 3-5 min ou perfusion selon dilution locale",
        "note": "Purpura / sepsis / meningite: ne pas retarder si indication forte",
        "ref": "BCFI / SPILF - Ceftriaxone IV",
        "alerts": alerts,
    }, None)


def litican(poids: float, age: float, atcd: list) -> Result:
    alerts: List[Alert] = []
    if _has(atcd, "Glaucome"):
        _add(alerts, "Glaucome: prudence avec l'effet anticholinergique")
    if _has(atcd, "Adenome prostatique", "Retention urinaire"):
        _add(alerts, "Adenome prostatique / retention urinaire: risque de retention")
    dose_mg = LITICAN_DOSE_ADULTE_MG if poids >= LITICAN_POIDS_PIVOT_KG else min(LITICAN_DOSE_KG_ENF * poids, LITICAN_DOSE_MAX_ENF_MG)
    return ({
        "dose_mg": _r(dose_mg, 0),
        "voie": "IM",
        "dose_note": f"Max {LITICAN_DOSE_MAX_JOUR:.0f} mg/24 h",
        "freq": "Repetition selon protocole local",
        "ref": "BCFI / protocole local Hainaut - Tiemonium (Litican)",
        "alerts": alerts,
    }, None)


def salbutamol(poids: float, age: float, gravite: str, atcd: list) -> Result:
    if gravite == "severe":
        dose_mg = 5.0
        rep = "A repeter toutes les 20 min x 3 en attente du medecin"
    elif gravite == "legere":
        dose_mg = 2.5 if poids < 20 else 5.0
        rep = "A reevaluer a 20 min"
    else:
        dose_mg = 2.5 if poids < 20 else 5.0
        rep = "2 a 3 nebs la premiere heure selon la reponse"
    return ({
        "dose_mg": dose_mg,
        "admin": "Nebulisation",
        "dilution": "Diluer a 4-5 ml NaCl 0,9 %",
        "debit_o2": "O2 6-8 l/min",
        "rep": rep,
        "ref": "GINA / BCFI - Salbutamol nebulise",
        "alerts": [("Si SpO2 < 92 % ou epuisement: triage critique", "danger" if gravite == "severe" else "warning")],
    }, None)


def furosemide(poids: float, age: float, atcd: list) -> Result:
    if age < 15:
        dose_min = min(max(poids * 1.0, 10.0), 40.0)
        dose_max = min(max(poids * 1.0, 10.0), 40.0)
    else:
        dose_min = 40.0 if _has(atcd, "Insuffisance cardiaque") else 20.0
        dose_max = 80.0 if _has(atcd, "Insuffisance cardiaque") else 40.0
    return ({
        "dose_min": dose_min,
        "dose_max": dose_max,
        "admin": "IV lent",
        "ref": "BCFI - Furosemide IV",
        "alerts": [("Surveiller TA, diurese et kaliemie", "warning")],
    }, None)


def ondansetron(poids: float, age: float, atcd: list) -> Result:
    dose_mg = min(max(0.15 * poids, 2.0), 8.0) if age < 15 else 4.0
    return ({
        "dose_mg": _r(dose_mg, 1),
        "admin": "IV lent ou PO orodispersible",
        "note": "Dose usuelle adulte 4 mg",
        "ref": "BCFI - Ondansetron",
        "alerts": [("Prudence si QT long connu", "warning")],
    }, None)


def acide_tranexamique(poids: float, age: float, atcd: list) -> Result:
    dose_mg = min(1000.0, max(15.0 * poids, 500.0)) if age < 15 else 1000.0
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "IV en 10 min",
        "note": "Penser a l'hemostase mecanique en parallele",
        "ref": "BCFI / trauma - Acide tranexamique",
        "alerts": [("Trauma severes: benefice si precoce", "warning")],
    }, None)


def methylprednisolone(poids: float, age: float, atcd: list) -> Result:
    dose_mg = min(max(1.0 * poids, 40.0), 125.0) if age < 15 else 125.0
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "IV",
        "note": "A visee anti-inflammatoire / anaphylaxie en relais",
        "ref": "BCFI - Methylprednisolone",
        "alerts": [],
    }, None)


def crise_hypertensive(pas: float, contexte: str, poids: float, atcd: list) -> Dict[str, object]:
    ci_labetalol = _has(atcd, "BPCO")
    ref = "ESC / protocoles hospitaliers - crise hypertensive"
    if "Dissection aortique" in contexte:
        objectif = "PAS < 120 mmHg rapidement et FC < 60/min"
        med1 = {"nom": "Labetalol", "dose": "20 mg IV puis titration"}
        med2 = {"nom": "Nicardipine", "dose": "5 mg/h puis titration"}
        priorite = "danger"
    elif "OAP hypertensif" in contexte:
        objectif = "Reduction prudente de la PAS et soulagement de l'OAP"
        med1 = {"nom": "Nitroglycerine", "dose": "Selon protocole local / avis medical"}
        med2 = {"nom": "Furosemide", "dose": "40-80 mg IV lent"}
        priorite = "warning"
    elif "thrombolyse" in contexte:
        objectif = "PAS < 185 mmHg et PAD < 110 mmHg"
        med1 = {"nom": "Labetalol", "dose": "10-20 mg IV lent"}
        med2 = {"nom": "Nicardipine", "dose": "5 mg/h puis titration"}
        priorite = "warning"
    elif "hemorragique" in contexte:
        objectif = "PAS cible 140-160 mmHg selon tolerance"
        med1 = {"nom": "Nicardipine", "dose": "5 mg/h puis titration"}
        med2 = {"nom": "Labetalol", "dose": "10-20 mg IV lent"}
        priorite = "danger"
    else:
        objectif = "Baisser MAP d'environ 20-25 % sur la 1re heure"
        med1 = {"nom": "Urapidil", "dose": "10-25 mg IV lent"}
        med2 = {"nom": "Nicardipine", "dose": "5 mg/h puis titration"}
        priorite = "warning"
    return {
        "objectif": objectif,
        "med1": med1,
        "med2": med2,
        "priorite": priorite,
        "ref": ref,
        "ci_labetalol": ci_labetalol,
    }


def neutralisation_aod(molecule: str, contexte: str, poids: float, atcd: list) -> Dict[str, object]:
    lower = norm(molecule)
    measure = "Contacter le medecin, dater la derniere prise et verifier la fonction renale"
    if "dabigatran" in lower:
        antidote = {
            "nom": "Idarucizumab",
            "dose": "5 g IV (2 x 2,5 g)",
            "dispo": "Antidote specifique",
            "ref": "BCFI / protocole AOD",
        }
    elif any(x in lower for x in ("rivaroxaban", "apixaban", "edoxaban")):
        antidote = {
            "nom": "CCP 4 facteurs",
            "dose": "25-50 UI/kg IV selon gravite",
            "dispo": "Andexanet selon disponibilite locale",
            "ref": "BCFI / protocole AOD",
        }
    else:
        antidote = {
            "nom": "PPSB + vitamine K",
            "dose": "PPSB 25-50 UI/kg + vitamine K 5-10 mg IV",
            "dispo": "Valable pour AVK ou molecule inconnue",
            "ref": "BCFI / protocole AVK",
        }
    return {
        "mesure_avant": measure,
        "antidote": antidote,
    }


def sepsis_bundle_1h(pas: float, lactate: Optional[float], temp: float, fc: float, poids: float, atcd: list) -> Dict[str, object]:
    choc = pas < 90 or (lactate is not None and lactate >= 4.0)
    remplissage_mlkg = 15 if _has(atcd, "Insuffisance cardiaque") else 30
    checklist = [
        ("Lactate", "Dosage rapide si non fait", "warning"),
        ("Hemocultures", "Avant antibiotherapie si possible", "info"),
        ("Antibiotherapie", "Dans l'heure si sepsis suspect", "danger" if choc else "warning"),
        ("Remplissage", f"{remplissage_mlkg} ml/kg cristalloides", "warning"),
        ("Vasopresseurs", "Si hypotension persistante apres remplissage", "danger" if choc else "info"),
    ]
    alerts: List[Alert] = []
    if choc:
        _add(alerts, "Hypotension / lactate eleve: sepsis severe ou choc septique", "danger")
    if temp < 36.0 or temp >= 38.3:
        _add(alerts, "Temperature anormale compatible avec sepsis", "warning")
    if fc >= 120:
        _add(alerts, "Tachycardie majeure: surveillance rapprochee", "warning")
    return {
        "choc_septique": choc,
        "checklist": checklist,
        "alerts": alerts,
    }


def ketamine_intranasale(poids: float, age: float, atcd: list) -> Result:
    if age >= 18:
        return None, "Ketamine intranasale reservee ici au protocole pediatrique"
    dose_mg = min(poids * 1.0, 50.0)
    return ({
        "dose_mg": _r(dose_mg, 0),
        "admin": "IN, repartir en 2 narines",
        "onset": "Debut d'effet 5-10 min",
        "duree": "Duree 20-30 min",
        "surv": "Surveiller dissociation, vomissements et saturation",
        "ref": "Protocoles pediatriques urgences - ketamine IN",
        "alerts": [("Alternative avant VVP si douleur aigue intense", "info")],
    }, None)


def vesiera(poids: float, age: float, atcd: list) -> Result:
    return ({
        "dose": "Selon protocole algologue",
        "admin": "Perfusion IV lente de ketamine sur 3 h, associee au magnesium",
        "note": "Traitement antalgique monitorise; hors autonomie IAO sans prescription medicale",
        "ref": "CHR Huy - brochure perfusion de ketamine Vesiera",
        "alerts": [
            ("Surveillance monitorage, TA, FC et saturation pendant la perfusion", "warning"),
            ("Retour accompagne et pas de conduite pendant 24 h", "warning"),
        ],
    }, None)


def protocole_eva(eva: int, poids: float, age: float, atcd: list, gl: Optional[float] = None) -> Dict[str, object]:
    recs: List[Dict[str, object]] = []
    als: List[Alert] = []

    if eva <= 0:
        return {"als": [("EVA 0/10: pas d'antalgie immediate, poursuivre la surveillance", "success")], "recs": []}

    para_r, _ = paracetamol(poids, age, atcd)
    if para_r:
        recs.append({
            "nom": "Perfu - Paracetamol IV",
            "dose": f"{para_r['dose_g']} g",
            "admin": para_r["admin"],
            "note": para_r["note"],
            "ref": para_r["ref"],
            "palier": "1",
            "alerts": para_r.get("alerts", []),
        })

    if eva <= 6:
        nap_r, nap_err = naproxene(poids, age, atcd)
        if nap_r:
            recs.append({
                "nom": "Naproxene PO",
                "dose": f"{_fmt(float(nap_r['dose_mg']))} mg",
                "admin": nap_r["admin"],
                "note": nap_r["note"],
                "ref": nap_r["ref"],
                "palier": "1",
                "alerts": nap_r.get("alerts", []),
            })
        elif nap_err:
            als.append((nap_err, "warning"))

    if 4 <= eva <= 6:
        tram_r, tram_err = tramadol(poids, age, atcd)
        if tram_r:
            recs.append({
                "nom": "Tradonal - Tramadol",
                "dose": f"{_fmt(float(tram_r['dose_mg']))} mg",
                "admin": tram_r["admin"],
                "note": tram_r["note"],
                "ref": tram_r["ref"],
                "palier": "2",
                "alerts": tram_r.get("alerts", []),
            })
        elif tram_err:
            als.append((tram_err, "danger" if "contre-indique" in norm(tram_err) else "warning"))

        lit_r, _ = litican(poids, age, atcd)
        if lit_r:
            recs.append({
                "nom": "Litican IM",
                "dose": f"{_fmt(float(lit_r['dose_mg']))} mg",
                "admin": lit_r["voie"],
                "note": "Adjuvant anti-spasmodique / antiemetique",
                "ref": lit_r["ref"],
                "palier": "2",
                "alerts": lit_r.get("alerts", []),
            })

    if eva >= 7:
        dip_r, dip_err = piritramide(poids, age, atcd)
        if dip_r:
            recs.append({
                "nom": "Dipidolor - Piritramide",
                "dose": f"{_fmt(float(dip_r['dose_min']))}-{_fmt(float(dip_r['dose_max']))} mg",
                "admin": dip_r["admin"],
                "note": dip_r["note"],
                "ref": dip_r["ref"],
                "palier": "3",
                "alerts": dip_r.get("alerts", []),
            })
        elif dip_err:
            als.append((dip_err, "warning"))

        morph_r, morph_err = morphine(poids, age, atcd)
        if morph_r:
            recs.append({
                "nom": "Morphine IV titree",
                "dose": f"{_fmt(float(morph_r['dose_min']))}-{_fmt(float(morph_r['dose_max']))} mg",
                "admin": morph_r["admin"],
                "note": morph_r["note"],
                "ref": morph_r["ref"],
                "palier": "3",
                "alerts": morph_r.get("alerts", []),
            })
        elif morph_err:
            als.append((morph_err, "warning"))

        lit_r, _ = litican(poids, age, atcd)
        if lit_r:
            recs.append({
                "nom": "Litican IM",
                "dose": f"{_fmt(float(lit_r['dose_mg']))} mg",
                "admin": lit_r["voie"],
                "note": "Adjuvant utile si nausees sous opioides",
                "ref": lit_r["ref"],
                "palier": "2",
                "alerts": lit_r.get("alerts", []),
            })

    if age < 18 and eva >= 6:
        ket_r, _ = ketamine_intranasale(poids, age, atcd)
        if ket_r:
            recs.append({
                "nom": "Ketamine intranasale pediatrique",
                "dose": f"{_fmt(float(ket_r['dose_mg']))} mg",
                "admin": ket_r["admin"],
                "note": "Alternative avant VVP si douleur intense",
                "ref": ket_r["ref"],
                "palier": "2",
                "alerts": ket_r.get("alerts", []),
            })

    if eva >= 6:
        als.append(("EVA >= 6: reevaluation de la douleur a 30 min obligatoire", "warning"))
    if _has(atcd, "Drepanocytose") and eva >= 6:
        als.append(("Drepanocytose: morphine titree precoce recommandee", "danger"))
    return {"als": als, "recs": recs}


def protocole_epilepsie_ped(
    poids: float,
    age: float,
    duree_min: float,
    en_cours: bool,
    atcd: list,
    gl: Optional[float] = None,
) -> Dict[str, object]:
    alerts: List[Alert] = []

    if gl is not None and gl < 70:
        _add(alerts, f"Hypoglycemie concomitante ({gl:.0f} mg/dl): corriger immediatement", "danger")
    if age < 0.25:
        _add(alerts, "Age < 3 mois: convulsion neonatale = triage critique / reanimation", "danger")
    if duree_min >= EME_ETABLI_MIN:
        _add(alerts, f"EME etabli >= {EME_ETABLI_MIN} min: reanimation pediatrique", "danger")
    elif duree_min >= EME_OPERATIONNEL_MIN:
        _add(alerts, f"EME operationnel >= {EME_OPERATIONNEL_MIN} min: risque lesionnel", "danger")
    elif en_cours or duree_min >= EME_SEUIL_MIN:
        _add(alerts, f"Crise > {EME_SEUIL_MIN} min: benzodiazepine immediate", "warning")

    if 0.25 <= age < 1:
        bucc_mg, bucc_ml = 2.5, "0,5 ml"
    elif 1 <= age < 5:
        bucc_mg, bucc_ml = 5.0, "1 ml"
    elif 5 <= age < 10:
        bucc_mg, bucc_ml = 7.5, "1,5 ml"
    elif 10 <= age < 18:
        bucc_mg, bucc_ml = 10.0, "2 ml"
    else:
        bucc_mg, bucc_ml = min(MIDAZOLAM_BUCC_MAX_MG, max(5.0, poids * 0.2)), "solution buccale selon seringue disponible"

    midazolam_buccal = {
        "med": "Midazolam buccal (Buccolam)",
        "dose_mg": _r(bucc_mg, 1),
        "volume": bucc_ml,
        "dose": f"{_fmt(bucc_mg)} mg ({bucc_ml})",
        "admin": "Entre gencive et joue, 1 seule dose",
        "note": "Dose AMM par age chez l'enfant; si adulte: viser 10 mg buccal",
        "ref": "BCFI - Buccolam / Folia convulsions tonico-cloniques",
    }

    midazolam_im_in_mg = min(MIDAZOLAM_IM_IN_KG * poids, MIDAZOLAM_IM_IN_MAX_MG)
    diazepam_rect_mg = min(DIAZEPAM_RECT_KG * poids, DIAZEPAM_RECT_MAX_MG)
    diazepam_iv_mg = min(DIAZEPAM_IV_KG * poids, DIAZEPAM_IV_MAX_MG)
    clonazepam_iv_mg = min(CLONAZEPAM_IV_KG * poids, CLONAZEPAM_IV_MAX_MG)
    lorazepam_iv_mg = min(LORAZEPAM_IV_KG * poids, LORAZEPAM_IV_MAX_MG)

    levetiracetam_mg = min(LEVETI_IV_KG * poids, LEVETI_IV_MAX_MG)
    valproate_mg = min(VALPROATE_IV_KG * poids, VALPROATE_IV_MAX_MG)
    phenobarbital_mg = min(PHENOBARB_IV_KG * poids, PHENOBARB_IV_MAX_MG)

    if duree_min >= EME_ETABLI_MIN:
        stage = "EME etabli"
    elif duree_min >= EME_OPERATIONNEL_MIN:
        stage = "EME operationnel"
    elif en_cours or duree_min >= EME_SEUIL_MIN:
        stage = "Crise prolongee active"
    else:
        stage = "Post-critique / surveillance"

    return {
        "stage": stage,
        "alerts": alerts,
        "midazolam_buccal": midazolam_buccal,
        "alternatives": [
            {
                "med": "Midazolam IM / intranasal",
                "dose": f"{_fmt(midazolam_im_in_mg)} mg",
                "admin": "IM ou IN",
                "note": "0,2 mg/kg si voie buccale impossible",
                "ref": "SFNP / BCFI",
            },
            {
                "med": "Diazepam rectal",
                "dose": f"{_fmt(diazepam_rect_mg)} mg",
                "admin": "Rectal",
                "note": "0,5 mg/kg, max 10 mg",
                "ref": "BCFI - Valium rectal",
            },
            {
                "med": "Clonazepam IV",
                "dose": f"{_fmt(clonazepam_iv_mg)} mg",
                "admin": "IV lent",
                "note": "Alternative IV 0,02 mg/kg, max 1 mg",
                "ref": "Protocoles EME pediatrique",
            },
            {
                "med": "Lorazepam IV",
                "dose": f"{_fmt(lorazepam_iv_mg)} mg",
                "admin": "IV lent",
                "note": "0,1 mg/kg, max 4 mg",
                "ref": "BCFI - Temesta IV",
            },
            {
                "med": "Diazepam IV",
                "dose": f"{_fmt(diazepam_iv_mg)} mg",
                "admin": "IV lent",
                "note": "0,1-0,3 mg/kg selon reponse",
                "ref": "BCFI - Valium IV",
            },
        ],
        "second_line": [
            {
                "med": "Levetiracetam IV",
                "dose": f"{_fmt(levetiracetam_mg)} mg",
                "admin": "Perfusion IV",
                "note": "Charge 60 mg/kg, max 4 500 mg",
                "ref": "Protocoles EME pediatrique",
            },
            {
                "med": "Valproate IV",
                "dose": f"{_fmt(valproate_mg)} mg",
                "admin": "Perfusion IV",
                "note": f"Charge 40 mg/kg, max 3 000 mg, sur >= {VALPROATE_IV_DEBIT_MIN:.0f} min",
                "ref": "Protocoles EME pediatrique",
            },
            {
                "med": "Phenobarbital IV",
                "dose": f"{_fmt(phenobarbital_mg)} mg",
                "admin": "Perfusion IV",
                "note": f"Charge 20 mg/kg, max 1 000 mg, debit <= {PHENOBARB_DEBIT_MG_KG_MIN:.0f} mg/kg/min",
                "ref": "Protocoles EME pediatrique",
            },
        ],
        "timeline": [
            ("0-5 min", "ABC, PLS, aspiration si besoin, O2, scope, glycémie capillaire"),
            (f"> {EME_SEUIL_MIN} min", "Midazolam buccal immediat; 1 seule dose par voie buccale"),
            ("5-10 min", "Si persistance: voie IV ou alternative IM/IN/rectale"),
            (f"{EME_OPERATIONNEL_MIN}-{EME_ETABLI_MIN} min", "Charge anti-epileptique de 2e ligne et appel senior"),
            (f">= {EME_ETABLI_MIN} min", "EME etabli: reanimation pediatrique, voie aerienne, sedation continue"),
        ],
    }

