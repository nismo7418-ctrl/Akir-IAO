from typing import Optional, Dict, Tuple
from config import *

_CI_A = ["Ulcère gastro-duodénal","Insuffisance rénale chronique","Insuffisance hépatique",
         "Grossesse en cours","Chimiothérapie en cours"]

def ci_ains(atcd: list) -> list:
    return [c for c in _CI_A if c in atcd]

def paracetamol(poids: float) -> Tuple[Optional[Dict], Optional[str]]:
    if poids <= 0: return None, "Poids invalide"
    if poids >= PARA_POIDS_PIVOT_KG:
        return {"dose_g": PARA_DOSE_FIXE_G, "vol": "100 ml NaCl 0.9% sur 15 min", "freq": "Toutes les 6h (max 4g/24h)", "ref": "BCFI — Paracétamol IV"}, None
    dg = min(round(PARA_DOSE_KG * poids / 1000, 2), 1.0)
    return {"dose_g": dg, "vol": f"{dg*1000:.0f} mg dans 100 ml NaCl 0.9%", "freq": "Toutes les 6h", "ref": "BCFI — Paracétamol IV"}, None

def ketorolac(poids: float, atcd: list) -> Tuple[Optional[Dict], Optional[str]]:
    ci = ci_ains(atcd)
    if ci: return None, f"Contre-indiqué : {', '.join(ci)}"
    d = 15.0 if poids < 50 else 30.0
    return {"dose_mg": d, "admin": "IV lent 15s", "freq": "Toutes 6h — max 5j", "ref": "BCFI — Kétorolac (Taradyl)"}, None

def tramadol(poids: float, atcd: list, age: float) -> Tuple[Optional[Dict], Optional[str]]:
    alerts = []
    if "Épilepsie" in atcd: alerts.append("CONTRE-INDIQUÉ — Épilepsie (seuil épileptogène)")
    if "IMAO (inhibiteurs MAO)" in atcd: alerts.append("CONTRE-INDICATION ABSOLUE — IMAO")
    if "Antidépresseurs ISRS/IRSNA" in atcd: alerts.append("INTERACTION MAJEURE — ISRS/IRSNA")
    d = 100.0 if poids >= 50 else round(1.5 * poids, 0)
    return {"dose_mg": d, "admin": f"{d:.0f} mg dans 100 ml NaCl 0.9% — IV 30 min", "freq": "Toutes 6h (max 400 mg/24h)", "alertes": alerts, "ref": "BCFI — Tramadol"}, None

def piritramide(poids: float, age: float, atcd: list) -> Tuple[Optional[Dict], Optional[str]]:
    red = (age >= 70 or "Insuffisance rénale chronique" in atcd or "Insuffisance hépatique" in atcd)
    f = 0.5 if red else 1.0
    plafond = (PIRI_PLAFOND_LT70 if poids < 70 else PIRI_PLAFOND_GE70) * f
    dmin = min(round(PIRI_BOLUS_MIN * poids * f, 2), plafond)
    dmax = min(round(PIRI_BOLUS_MAX * poids * f, 2), plafond)
    note = "Dose -50% si âge≥70/IRC/IH" if red else ""
    return {"dmin": dmin, "dmax": dmax, "admin": "IV lent 1-2 min — titrer si EVA>3 après 15 min", "note": note, "ref": "BCFI — Piritramide (Dipidolor)"}, None

def morphine(poids: float, age: float) -> Tuple[Optional[Dict], Optional[str]]:
    f = 0.5 if age >= 70 else 1.0
    plafond = (MORPH_PLAFOND_GE100 if poids >= 100 else MORPH_PLAFOND_STD) * f
    dmin = min(round(MORPH_MIN_KG * poids * f, 1), plafond)
    dmax = min(round(MORPH_MAX_KG * poids * f, 1), plafond)
    return {"dmin": dmin, "dmax": dmax, "palier": MOR
cat <<EOF > clinical/pharmaco.py
from typing import Optional, Dict, Tuple
from config import *

_CI_A = ["Ulcère gastro-duodénal","Insuffisance rénale chronique","Insuffisance hépatique",
         "Grossesse en cours","Chimiothérapie en cours"]

def ci_ains(atcd: list) -> list:
    return [c for c in _CI_A if c in atcd]

def paracetamol(poids: float) -> Tuple[Optional[Dict], Optional[str]]:
    if poids <= 0: return None, "Poids invalide"
    if poids >= PARA_POIDS_PIVOT_KG:
        return {"dose_g": PARA_DOSE_FIXE_G, "vol": "100 ml NaCl 0.9% sur 15 min", "freq": "Toutes les 6h (max 4g/24h)", "ref": "BCFI — Paracétamol IV"}, None
    dg = min(round(PARA_DOSE_KG * poids / 1000, 2), 1.0)
    return {"dose_g": dg, "vol": f"{dg*1000:.0f} mg dans 100 ml NaCl 0.9%", "freq": "Toutes les 6h", "ref": "BCFI — Paracétamol IV"}, None

def ketorolac(poids: float, atcd: list) -> Tuple[Optional[Dict], Optional[str]]:
    ci = ci_ains(atcd)
    if ci: return None, f"Contre-indiqué : {', '.join(ci)}"
    d = 15.0 if poids < 50 else 30.0
    return {"dose_mg": d, "admin": "IV lent 15s", "freq": "Toutes 6h — max 5j", "ref": "BCFI — Kétorolac (Taradyl)"}, None

def tramadol(poids: float, atcd: list, age: float) -> Tuple[Optional[Dict], Optional[str]]:
    alerts = []
    if "Épilepsie" in atcd: alerts.append("CONTRE-INDIQUÉ — Épilepsie (seuil épileptogène)")
    if "IMAO (inhibiteurs MAO)" in atcd: alerts.append("CONTRE-INDICATION ABSOLUE — IMAO")
    if "Antidépresseurs ISRS/IRSNA" in atcd: alerts.append("INTERACTION MAJEURE — ISRS/IRSNA")
    d = 100.0 if poids >= 50 else round(1.5 * poids, 0)
    return {"dose_mg": d, "admin": f"{d:.0f} mg dans 100 ml NaCl 0.9% — IV 30 min", "freq": "Toutes 6h (max 400 mg/24h)", "alertes": alerts, "ref": "BCFI — Tramadol"}, None

def piritramide(poids: float, age: float, atcd: list) -> Tuple[Optional[Dict], Optional[str]]:
    red = (age >= 70 or "Insuffisance rénale chronique" in atcd or "Insuffisance hépatique" in atcd)
    f = 0.5 if red else 1.0
    plafond = (PIRI_PLAFOND_LT70 if poids < 70 else PIRI_PLAFOND_GE70) * f
    dmin = min(round(PIRI_BOLUS_MIN * poids * f, 2), plafond)
    dmax = min(round(PIRI_BOLUS_MAX * poids * f, 2), plafond)
    note = "Dose -50% si âge≥70/IRC/IH" if red else ""
    return {"dmin": dmin, "dmax": dmax, "admin": "IV lent 1-2 min — titrer si EVA>3 après 15 min", "note": note, "ref": "BCFI — Piritramide (Dipidolor)"}, None

def morphine(poids: float, age: float) -> Tuple[Optional[Dict], Optional[str]]:
    f = 0.5 if age >= 70 else 1.0
    plafond = (MORPH_PLAFOND_GE100 if poids >= 100 else MORPH_PLAFOND_STD) * f
    dmin = min(round(MORPH_MIN_KG * poids * f, 1), plafond)
    dmax = min(round(MORPH_MAX_KG * poids * f, 1), plafond)
    return {"dmin": dmin, "dmax": dmax, "palier": MORPH_PALIER_MG, "admin": f"IV lent 2-3 min — titrer par paliers {MORPH_PALIER_MG:.0f} mg / 5-10 min", "ref": "BCFI — Morphine"}, None

def naloxone(poids: float, age: float, dep: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
    if dep:
        d = NALOO_DEP_MG; a = f"{NALOO_DEP_MG}mg IV/2min — titration douce"; n = "Dépendance — objectif ventilation"
    elif age < 18:
        d = min(round(NALOO_PED_KG * poids, 3), NALOO_ADULTE_MG)
        a = f"{d}mg IV (0.01mg/kg)"; n = f"Pédiatrique {d} mg pour {poids} kg"
    else:
        d = NALOO_ADULTE_MG; a = f"{NALOO_ADULTE_MG}mg IV — répéter 2-3 min (max 10mg)"; n = ""
    return {"dose": d, "admin": a, "note": n, "surv": "Monitor SpO2+FR — demi-vie courte 30-90 min", "ref": "BCFI — Naloxone"}, None

def adrenaline(poids: float) -> Tuple[Optional[Dict], Optional[str]]:
    if poids <= 0: return None, "Poids invalide"
    d = 0.5 if poids >= ADRE_POIDS_ADULTE_KG else min(round(ADRE_DOSE_KG * poids, 3), ADRE_DOSE_ADULTE_MG)
    return {"dose_mg": d, "voie": "IM face antéro-latérale cuisse", "note": "0.5 ml sol 1mg/ml" if poids>=30 else f"0.01mg/kg = {d}mg", "rep": "Répéter 5-15 min si pas d'amélioration", "ref": "BCFI — Adrénaline"}, None

def glucose(poids: float, gl: Optional[float] = None) -> Tuple[Optional[Dict], Optional[str]]:
    if gl is None: return None, "Glycémie non mesurée — protocole désactivé"
    dg = min(round(GLUCOSE_DOSE_KG * poids, 1), GLUCOSE_MAX_G)
    dm = round(dg / 0.3, 0)  # Pour du G30% (0.3g/ml)
    return {"dose_g": dg, "vol": f"{dm:.0f} ml Glucose 30% IV lent 5 min", "ctrl": "Glycémie de contrôle à 15 min", "ref": "BCFI — Glucose 30%"}, None

def ceftriaxone(poids: float, age: float) -> Tuple[Optional[Dict], Optional[str]]:
    dg = CEFRTRX_ADULTE_G if age >= 18 else min(round(CEFRTRX_PED_KG * poids, 1), CEFRTRX_ADULTE_G)
    return {"dose_g": dg, "admin": "IV 3-5 min ou IM si VVP impossible", "note": "Ne pas attendre le médecin si purpura", "ref": "BCFI — Ceftriaxone"}, None

def litican(poids: float, age: float, atcd: list) -> Tuple[Optional[Dict], Optional[str]]:
    if poids <= 0: return None, "Poids invalide"
    ci = []
    if "Glaucome" in atcd: ci.append("Glaucome")
    if "Adénome prostatique" in atcd: ci.append("Rétention urinaire")
    if ci: return None, f"Contre-indication : {' | '.join(ci)}"
    if poids >= LITICAN_POIDS_PIVOT_KG and age >= 15:
        dose = LITICAN_DOSE_ADULTE_MG; note = "1 ampoule 2 ml (40 mg/2 ml)"
    else:
        dose = min(round(LITICAN_DOSE_KG_ENF * poids, 1), LITICAN_DOSE_MAX_ENF_MG)
        note = f"1 mg/kg = {dose} mg pour {poids} kg"
    return {"dose_mg": dose, "dose_note": note, "voie": "IM profond", "freq": f"Si besoin après 4-6 h — max {LITICAN_DOSE_MAX_JOUR} mg/24h", "attention": "NE PAS INJECTER EN IV", "ref": "BCFI — Litican"}, None

def protocole_eva(eva, poids, age, atcd, gl=None):
    als, recs = [], []
    imao = "IMAO (inhibiteurs MAO)" in atcd
    isrs = "Antidépresseurs ISRS/IRSNA" in atcd
    if imao: als.append("IMAO — Tramadol contre-indiqué")
    if isrs: als.append("ISRS/IRSNA — Tramadol déconseillé")
    r, _ = paracetamol(poids)
    if r: recs.append({"p":"1","nom":"Paracétamol IV","dose":f"{r['dose_g']}g","d":r["vol"],"al":[],"ref":r["ref"]})
    if eva >= 4:
        if not ci_ains(atcd):
            r2, _ = ketorolac(poids, atcd)
            if r2: recs.append({"p":"2","nom":"Kétorolac IV","dose":f"{r2['dose_mg']}mg","d":r2["admin"],"al":[],"ref":r2["ref"]})
        if not imao and "Épilepsie" not in atcd:
            r3, _ = tramadol(poids, atcd, age)
            if r3: recs.append({"p":"2","nom":"Tramadol IV","dose":f"{r3['dose_mg']:.0f}mg","d":r3["admin"],"al":r3.get("alertes",[]),"ref":r3["ref"]})
    if eva >= 7:
        r4, _ = piritramide(poids, age, atcd)
        if r4: recs.append({"p":"3","nom":"Piritramide (Dipidolor) IV","dose":f"{r4['dmin']}-{r4['dmax']}mg","d":r4["admin"],"al":[],"ref":r4["ref"]})
    return {"als": als, "recs": recs}

def protocole_epilepsie_ped(poids, age, duree_min, en_cours, atcd, gl=None):
    return {"glycemie_alerte": None, "ligne1a": {}, "ligne1b": {}, "ligne1c": {}, "ligne2_lora": {}, "ligne2_clona": {}, "ligne2_diaz": {}, "ligne3_leveti": {}, "ligne3_valp": {}, "ligne3_phenob": {}, "antidote": {}, "chrono": {}, "surveillance": [], "ref": "..."}
