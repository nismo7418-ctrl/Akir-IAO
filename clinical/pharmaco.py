# clinical/pharmaco.py — Pharmacologie BCFI Belgique — AKIR-IAO v18.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Références : BCFI — Répertoire Commenté des Médicaments — Belgique
#              AFMPS — RCP Belgique — SFAR 2010 — CRASH-2 Lancet 2010
#              EAACI 2023 — GINA 2023 — SFNP / ISPE 2022

from typing import Optional, Tuple, Dict
import unicodedata
from config import (
    GLYC, GLYC as _G,
    PARA_DOSE_KG, PARA_DOSE_FIXE_G, PARA_POIDS_PIVOT_KG,
    GLUCOSE_DOSE_KG, GLUCOSE_MAX_G,
    ADRE_POIDS_ADULTE_KG, ADRE_DOSE_ADULTE_MG, ADRE_DOSE_KG,
    PIRI_BOLUS_MIN, PIRI_BOLUS_MAX, PIRI_PLAFOND_LT70, PIRI_PLAFOND_GE70,
    NALOO_ADULTE_MG, NALOO_PED_KG, NALOO_DEP_MG,
    MORPH_MIN_KG, MORPH_MAX_KG, MORPH_PLAFOND_STD, MORPH_PLAFOND_GE100, MORPH_PALIER_MG,
    CEFRTRX_ADULTE_G, CEFRTRX_PED_KG,
    LITICAN_DOSE_ADULTE_MG, LITICAN_DOSE_KG_ENF, LITICAN_DOSE_MAX_ENF_MG,
    LITICAN_DOSE_MAX_JOUR, LITICAN_POIDS_PIVOT_KG,
    MIDAZOLAM_BUCC_KG, MIDAZOLAM_BUCC_MAX_MG,
    MIDAZOLAM_IM_IN_KG, MIDAZOLAM_IM_IN_MAX_MG,
    DIAZEPAM_RECT_KG, DIAZEPAM_RECT_MAX_MG,
    DIAZEPAM_IV_KG, DIAZEPAM_IV_MAX_MG,
    LORAZEPAM_IV_KG, LORAZEPAM_IV_MAX_MG,
    CLONAZEPAM_IV_KG, CLONAZEPAM_IV_MAX_MG,
    PHENOBARB_IV_KG, PHENOBARB_IV_MAX_MG, PHENOBARB_DEBIT_MG_KG_MIN,
    LEVETI_IV_KG, LEVETI_IV_MAX_MG,
    VALPROATE_IV_KG, VALPROATE_IV_MAX_MG, VALPROATE_IV_DEBIT_MIN,
    FLUMAZENIL_DOSE_MG, FLUMAZENIL_MAX_MG, FLUMAZENIL_MAX_TOTAL,
    EME_SEUIL_MIN, EME_OPERATIONNEL_MIN, EME_ETABLI_MIN,
)

Rx = Tuple[Optional[Dict], Optional[str]]


def _norm(value) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def _has_atcd(atcd: list, label: str) -> bool:
    labels = {_norm(x) for x in (atcd or [])}
    return _norm(label) in labels

# ── CI AINS communes ─────────────────────────────────────────────────────────
_CI_A = [
    "Ulcere gastro-duodenal", "Insuffisance renale chronique",
    "Insuffisance hepatique", "Grossesse en cours", "Chimiotherapie en cours",
]
def ci_ains(atcd: list) -> list:
    return [c for c in _CI_A if _has_atcd(atcd, c)]


# ═══════════════════════════════════════════════════════════════════════════════
# ANTALGIQUES — PROTOCOLE EVA OMS
# ═══════════════════════════════════════════════════════════════════════════════

def paracetamol(poids: float) -> Rx:
    """Paracétamol IV — palier I OMS. 15 mg/kg si < 50 kg, 1 g si ≥ 50 kg."""
    if poids <= 0:
        return None, "Poids invalide"
    if poids >= PARA_POIDS_PIVOT_KG:
        return {"dose_g": PARA_DOSE_FIXE_G, "vol": "100 ml NaCl 0,9 % — 15 min",
                "freq": "Toutes 6 h (max 4 g/24 h)", "ref": "BCFI — Paracétamol IV"}, None
    dg = min(round(PARA_DOSE_KG * poids / 1000, 2), PARA_DOSE_FIXE_G)
    return {"dose_g": dg, "vol": f"{dg*1000:.0f} mg dans 100 ml NaCl 0,9 %",
            "freq": "Toutes 6 h", "ref": "BCFI — Paracétamol IV"}, None


def ketorolac(poids: float, atcd: list) -> Rx:
    """Kétorolac (Taradyl) IV — AINS palier II. 15 mg < 50 kg / 30 mg ≥ 50 kg."""
    ci = ci_ains(atcd)
    if ci:
        return None, f"Contre-indiqué : {', '.join(ci)}"
    d = 15.0 if poids < 50 else 30.0
    return {"dose_mg": d, "admin": "IV lent 15 s", "freq": "Toutes 6 h — max 5 j",
            "ref": "BCFI — Kétorolac (Taradyl)"}, None


def tramadol(poids: float, atcd: list, age: float) -> Rx:
    """Tramadol IV — opioïde faible. CI absolue : IMAO / Épilepsie."""
    als = []
    if _has_atcd(atcd, "Epilepsie"):
        als.append("CONTRE-INDIQUÉ — Épilepsie (seuil épileptogène abaissé)")
    if _has_atcd(atcd, "IMAO (inhibiteurs MAO)"):
        als.append("CONTRE-INDICATION ABSOLUE — SYNDROME SÉROTONINERGIQUE FATAL avec IMAO")
    if _has_atcd(atcd, "Antidepresseurs ISRS/IRSNA"):
        als.append("INTERACTION MAJEURE — ISRS/IRSNA — risque sérotoninergique")
    d = 100.0 if poids >= 50 else round(1.5 * poids, 0)
    return {"dose_mg": d, "admin": f"{d:.0f} mg dans 100 ml NaCl 0,9 % — IV 30 min",
            "freq": "Toutes 6 h (max 400 mg/24 h)", "alertes": als,
            "ref": "BCFI — Tramadol"}, None


def piritramide(poids: float, age: float, atcd: list) -> Rx:
    """Piritramide (Dipidolor) IV — opioïde fort — titration. Réduction 50 % si ≥ 70 ans / IRC / IH."""
    red = (age >= 70 or _has_atcd(atcd, "Insuffisance renale chronique")
           or _has_atcd(atcd, "Insuffisance hepatique"))
    f = 0.5 if red else 1.0
    plafond = (PIRI_PLAFOND_LT70 if poids < 70 else PIRI_PLAFOND_GE70) * f
    dmin = min(round(PIRI_BOLUS_MIN * poids * f, 2), plafond)
    dmax = min(round(PIRI_BOLUS_MAX * poids * f, 2), plafond)
    return {"dmin": dmin, "dmax": dmax,
            "admin": "IV lent 1-2 min — titrer si EVA > 3 après 15 min",
            "note": "Dose −50 % si âge ≥ 70 / IRC / IH" if red else "",
            "ref": "BCFI — Piritramide (Dipidolor)"}, None


def morphine(poids: float, age: float) -> Rx:
    """Morphine IV — titration 0,05-0,10 mg/kg. Réduction 50 % si ≥ 70 ans."""
    f = 0.5 if age >= 70 else 1.0
    plafond = (MORPH_PLAFOND_GE100 if poids >= 100 else MORPH_PLAFOND_STD) * f
    dmin = min(round(MORPH_MIN_KG * poids * f, 1), plafond)
    dmax = min(round(MORPH_MAX_KG * poids * f, 1), plafond)
    return {"dmin": dmin, "dmax": dmax, "palier": MORPH_PALIER_MG,
            "admin": f"IV lent 2-3 min — titrer par paliers {MORPH_PALIER_MG:.0f} mg / 5-10 min",
            "ref": "BCFI — Morphine chlorhydrate"}, None


def protocole_eva(eva: int, poids: float, age: float, atcd: list,
                  gl: Optional[float] = None) -> dict:
    """Protocole antalgique OMS adapté à l'EVA (0-10)."""
    als = []
    recs = []
    pr, _ = paracetamol(poids)
    if pr:
        recs.append({"nom": "Paracétamol IV", "dose": f"{pr['dose_g']} g",
                     "d": pr["vol"], "note": pr["freq"], "ref": pr["ref"], "p": "1"})
    if eva >= 4:
        kr, ke = ketorolac(poids, atcd)
        if kr:
            recs.append({"nom": "Kétorolac IV (Taradyl)", "dose": f"{kr['dose_mg']} mg",
                         "d": kr["admin"], "note": kr["freq"], "ref": kr["ref"], "p": "2"})
        elif ke:
            als.append(ke)
        tr, _ = tramadol(poids, atcd, age)
        if tr:
            al_t = tr.get("alertes", [])
            if not any("ABSOLU" in a or "INDIQUÉ" in a for a in al_t):
                recs.append({"nom": "Tramadol IV", "dose": f"{tr['dose_mg']:.0f} mg",
                             "d": tr["admin"], "note": tr["freq"], "ref": tr["ref"],
                             "p": "2", "al": al_t})
    if eva >= 7:
        pi, _ = piritramide(poids, age, atcd)
        if pi:
            recs.append({"nom": "Piritramide IV (Dipidolor)",
                         "dose": f"{pi['dmin']}-{pi['dmax']} mg",
                         "d": pi["admin"], "note": pi["note"], "ref": pi["ref"], "p": "3"})
    return {"als": als, "recs": recs}


# ═══════════════════════════════════════════════════════════════════════════════
# URGENCES VITALES
# ═══════════════════════════════════════════════════════════════════════════════

def naloxone(poids: float, age: float, dep: bool = False) -> Rx:
    """Naloxone (Narcan) IV — antidote opioïdes. 3 protocoles : adulte / pédiatrique / dépendance."""
    als = []
    if dep:
        d = NALOO_DEP_MG
        a = f"{d} mg IV / 2 min — titration douce"
        n = "Dépendance — objectif : ventilation, pas levée totale"
        als.append("Risque de syndrome de sevrage si surdosage")
    elif age < 18:
        d = min(round(NALOO_PED_KG * poids, 3), NALOO_ADULTE_MG)
        a = f"{d} mg IV (0,01 mg/kg)"
        n = f"Pédiatrique : {d} mg pour {poids} kg"
    else:
        d = NALOO_ADULTE_MG
        a = f"{d} mg IV — répéter / 2-3 min (max 10 mg)"
        n = "Si pas de réponse à 10 mg : reconsidérer le diagnostic"
    return {"dose": d, "admin": a, "note": n, "alertes": als,
            "surv": "Demi-vie courte 30-90 min — surveiller resédation",
            "ref": "BCFI — Naloxone (Narcan)"}, None


def adrenaline(poids: float) -> Rx:
    """Adrénaline IM — anaphylaxie. Face antéro-latérale cuisse."""
    if poids <= 0:
        return None, "Poids invalide"
    d = ADRE_DOSE_ADULTE_MG if poids >= ADRE_POIDS_ADULTE_KG else min(
        round(ADRE_DOSE_KG * poids, 3), ADRE_DOSE_ADULTE_MG)
    n = "0,5 ml sol 1 mg/ml" if poids >= ADRE_POIDS_ADULTE_KG else f"0,01 mg/kg = {d} mg"
    return {"dose_mg": d, "voie": "IM face antéro-lat cuisse", "note": n,
            "rep": "Répéter 5-15 min si pas d'amélioration",
            "ref": "BCFI — Adrénaline Sterop 1 mg/ml — EAACI 2023"}, None


def glucose(poids: float, gl: Optional[float] = None) -> Rx:
    """Glucose 30 % IV — hypoglycémie sévère. Désactivé si glycémie None."""
    if gl is None:
        return None, "Glycémie non mesurée — protocole désactivé"
    dg = min(round(GLUCOSE_DOSE_KG * poids, 1), GLUCOSE_MAX_G)
    dm = round(dg / GLUCOSE_DOSE_KG, 0)
    return {"dose_g": dg, "vol": f"{dm:.0f} ml Glucose 30 % IV lent 5 min",
            "ctrl": "Glycémie de contrôle à 15 min",
            "ref": "BCFI — Glucose 30 % (Glucosie)"}, None


def ceftriaxone(poids: float, age: float) -> Rx:
    """Ceftriaxone IV — purpura fulminans / méningite. Ne pas attendre si purpura."""
    dg = (CEFRTRX_ADULTE_G if age >= 18
          else min(round(CEFRTRX_PED_KG * poids, 1), CEFRTRX_ADULTE_G))
    n = "Ne pas attendre le médecin si purpura" if age >= 18 else f"100 mg/kg = {dg*1000:.0f} mg"
    return {"dose_g": dg, "admin": "IV 3-5 min ou IM si VVP impossible", "note": n,
            "ref": "BCFI — Ceftriaxone — SPILF/SFP 2017"}, None


def litican(poids: float, age: float, atcd: list) -> Rx:
    """Litican IM — tiémonium méthylsulfate — antispasmodique. PROTOCOLE LOCAL HAINAUT."""
    if poids <= 0:
        return None, "Poids invalide"
    ci = []
    if _has_atcd(atcd, "Glaucome") or _has_atcd(atcd, "Glaucome par fermeture de l'angle"):
        ci.append("Glaucome (CI absolue)")
    if _has_atcd(atcd, "Adenome prostatique") or _has_atcd(atcd, "Retention urinaire"):
        ci.append("Rétention urinaire")
    if _has_atcd(atcd, "Grossesse en cours"):
        ci.append("Grossesse — données insuffisantes")
    if ci:
        return None, f"Contre-indication : {' | '.join(ci)}"
    if poids >= LITICAN_POIDS_PIVOT_KG and age >= 15:
        dose = LITICAN_DOSE_ADULTE_MG
        note = "1 ampoule 2 ml (40 mg/2 ml)"
    else:
        dose = min(round(LITICAN_DOSE_KG_ENF * poids, 1), LITICAN_DOSE_MAX_ENF_MG)
        note = f"1 mg/kg = {dose} mg pour {poids} kg"
    return {"dose_mg": dose, "dose_note": note,
            "voie": "IM profond — quadrant supéro-externe fessier ou cuisse",
            "volume": f"{dose/20:.1f} ml de solution 20 mg/ml",
            "freq": f"Si besoin après 4-6 h — max {LITICAN_DOSE_MAX_JOUR:.0f} mg/24 h",
            "attention": "NE PAS INJECTER EN IV — risque de bradycardie",
            "ref": "BCFI — Tiémonium (Litican) — Protocole local Hainaut"}, None


# ═══════════════════════════════════════════════════════════════════════════════
# NOUVEAUX PROTOCOLES (session 2025)
# ═══════════════════════════════════════════════════════════════════════════════

def salbutamol(poids: float, age: float, gravite: str = "moderee") -> Rx:
    """Salbutamol (Ventolin) nébulisation — bronchospasme / asthme. GINA 2023."""
    if poids <= 0:
        return None, "Poids invalide"
    if age >= 18:
        dose = 5.0 if gravite == "severe" else 2.5
        note = f"{dose} mg ({dose/5:.1f} ml sol 5 mg/ml) + NaCl 0,9 % qs 3 ml"
    else:
        dose = min(max(round(0.15 * poids, 2), 1.25), 5.0 if age >= 2 else 2.5)
        note = f"0,15 mg/kg = {dose} mg ({dose/5:.2f} ml sol 5 mg/ml) + NaCl 0,9 % qs 3 ml"
    return {"dose_mg": dose, "volume": round(dose/5.0, 2),
            "dilution": "Compléter à 3-4 ml avec NaCl 0,9 %",
            "debit_o2": "6-8 l/min — 15-20 min",
            "admin": note,
            "rep": "Répéter toutes les 20-30 min si besoin (max 3 doses)",
            "ref": "BCFI — Salbutamol (Ventolin) — GINA 2023"}, None


def furosemide(poids: float, age: float, atcd: list) -> Rx:
    """Furosémide (Lasix) IV — OAP cardiogénique. 0,5-1 mg/kg."""
    ci = []
    if _has_atcd(atcd, "Insuffisance renale chronique"):
        ci.append("IRC — adapter la dose (risque ototoxicité)")
    dose_min = min(round(0.5 * poids, 0), 100.0)
    dose_max = min(round(1.0 * poids, 0), 200.0)
    return {"dose_min": dose_min, "dose_max": dose_max,
            "admin": f"{dose_min:.0f}-{dose_max:.0f} mg IV lent 2-5 min",
            "surv": "Diurèse attendue 5-15 min — surveiller kaliémie",
            "ci_list": ci,
            "ref": "BCFI — Furosémide (Lasix)"}, None


def ondansetron(poids: float, age: float) -> Rx:
    """Ondansétron (Zofran) IV/IM — antiémétique. 0,1 mg/kg enfant / 4 mg adulte."""
    if age >= 18:
        dose = 4.0
        note = "4 mg IV lent ou IM — répéter 8 mg si besoin après 4 h"
    else:
        dose = min(round(0.1 * poids, 2), 4.0)
        note = f"0,1 mg/kg = {dose} mg IV lent (dilué dans 50 ml NaCl 0,9 %)"
    return {"dose_mg": dose, "admin": note,
            "qt": "Attention allongement QT — ECG si ATCD arythmie",
            "ref": "BCFI — Ondansétron (Zofran)"}, None


def acide_tranexamique(poids: float, delai_h: float = 0.0) -> Rx:
    """Acide tranexamique (Exacyl) IV — hémorragie active. Fenêtre < 3 h (CRASH-2)."""
    if delai_h > 3.0:
        return None, f"Délai {delai_h:.1f} h > 3 h — fenêtre thérapeutique dépassée (CRASH-2)"
    return {"dose_charge": "1 g IV en 10 min",
            "dose_entretien": "1 g IV en 8 h (médecin)",
            "admin": "Diluer 1 g dans 100 ml NaCl 0,9 % — perfuser en 10 min",
            "fenetre": f"Délai depuis traumatisme : {delai_h:.1f} h — bénéfice si < 3 h",
            "surv": "Surveiller signes thrombotiques — PA — diurèse",
            "ref": "CRASH-2 — Lancet 2010 — BCFI — Acide tranexamique (Exacyl)"}, None


def methylprednisolone(poids: float, indication: str = "anaphylaxie") -> Rx:
    """Méthylprednisolone (Solu-Médrol) IV — corticoïde d'urgence."""
    ind = indication.lower()
    if "anaph" in ind:
        dose = min(round(1.5 * poids, 0), 125.0)
        note = f"Anaphylaxie — {dose:.0f} mg IV lent 5 min (adjuvant adrénaline)"
    elif "asthme" in ind:
        dose = min(round(1.5 * poids, 0), 80.0)
        note = f"Asthme — {dose:.0f} mg IV lent 5 min (effets en 4-6 h)"
    elif "bpco" in ind:
        dose = 40.0
        note = "Exacerbation BPCO — 40 mg IV / 6 h — 5 jours"
    else:
        dose = min(round(1.5 * poids, 0), 125.0)
        note = f"{dose:.0f} mg IV lent 5 min"
    return {"dose_mg": dose, "admin": note,
            "delai": "Effets anti-inflammatoires en 4-6 h",
            "ref": "BCFI — Méthylprednisolone (Solu-Médrol) — EAACI 2023"}, None


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOLE ÉPILEPSIE PÉDIATRIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def protocole_epilepsie_ped(
    poids: float, age: float, duree_min: float,
    en_cours: bool, atcd: list,
    gl: Optional[float] = None,
) -> dict:
    """
    Protocole EME pédiatrique 4 lignes — SFNP / ISPE 2022 / EpiCARE 2023.

    Ligne 1 : Midazolam buccal / IM-IN / Diazépam rectal (IAO autonome)
    Ligne 2 : Lorazépam / Clonazépam / Diazépam IV (médecin + VVP)
    Ligne 3 : Lévétiracétam / Valproate / Phénobarbital IV (réanimation)
    Antidote : Flumazénil
    """
    # Alerte glycémie — prioritaire
    glycemie_alerte = None
    if gl is None:
        glycemie_alerte = ("Glycémie NON MESURÉE — Réaliser IMMÉDIATEMENT "
                           "(hypoglycémie = cause curable)")
    elif gl < 54:
        glycemie_alerte = (f"HYPOGLYCÉMIE SÉVÈRE {gl} mg/dl "
                           "— Glucose 30 % IV AVANT tout antiépileptique")

    # Buccolam® — volumes par tranche d'âge AMM
    if   age < 1:   buccolam_vol = "2,5 mg / 0,5 ml"
    elif age < 5:   buccolam_vol = "5 mg / 1 ml"
    elif age < 10:  buccolam_vol = "7,5 mg / 1,5 ml"
    else:           buccolam_vol = "10 mg / 2 ml"

    # Ligne 1a — Midazolam buccal
    d_mb = min(round(MIDAZOLAM_BUCC_KG * poids, 1), MIDAZOLAM_BUCC_MAX_MG)
    ligne1a = {"med": "Midazolam buccal (Buccolam®)", "dose_mg": d_mb,
               "volume": buccolam_vol,
               "admin": "Déposer entre la gencive et la joue",
               "delai": "Effet en 5-10 min", "peut_repeter": "1 seule dose",
               "ref": "BCFI — Midazolam buccal (Buccolam)"}

    # Ligne 1b — Midazolam IM / intranasale
    d_mi = min(round(MIDAZOLAM_IM_IN_KG * poids, 1), MIDAZOLAM_IM_IN_MAX_MG)
    vol_in = round(d_mi / 5.0, 2)
    ligne1b = {"med": "Midazolam IM / Intranasale", "dose_mg": d_mi,
               "voie_im": f"IM cuisse — {round(d_mi/5,1)} ml sol 5 mg/ml",
               "voie_in": (f"IN : {round(vol_in/2,2)} ml / narine — atomiseur MAD"),
               "delai": "Effet en 5-10 min",
               "ref": "BCFI — Midazolam (Dormicum)"}

    # Ligne 1c — Diazépam rectal
    d_dr = min(round(DIAZEPAM_RECT_KG * poids, 1), DIAZEPAM_RECT_MAX_MG)
    ligne1c = {"med": "Diazépam rectal (Stesolid®)", "dose_mg": d_dr,
               "admin": "Tube rectal préchauffé — maintien 2 min",
               "delai": "Effet en 5-15 min", "ref": "BCFI — Diazépam rectal"}

    # Ligne 2 — Benzodiazépines IV
    d_lo = min(round(LORAZEPAM_IV_KG * poids, 2), LORAZEPAM_IV_MAX_MG)
    d_cl = min(round(CLONAZEPAM_IV_KG * poids, 3), CLONAZEPAM_IV_MAX_MG)
    d_di = min(round(DIAZEPAM_IV_KG * poids, 1), DIAZEPAM_IV_MAX_MG)
    ligne2_lora  = {"med": "Lorazépam IV (Temesta®)", "dose_mg": d_lo,
                    "admin": f"{d_lo} mg IV lent 2-3 min — rincer NaCl 0,9 %",
                    "delai": "Effet en 2-5 min", "attention": "Surveiller SpO2 + FR",
                    "ref": "BCFI — Lorazépam (Temesta)"}
    ligne2_clona = {"med": "Clonazépam IV (Rivotril®)", "dose_mg": d_cl,
                    "admin": f"{d_cl} mg dans 10 ml NaCl 0,9 % — IV lent 2-5 min",
                    "delai": "Effet en 1-3 min", "ref": "BCFI — Clonazépam (Rivotril)"}
    ligne2_diaz  = {"med": "Diazépam IV (Valium®)", "dose_mg": d_di,
                    "admin": f"{d_di} mg IV lent — max 2 mg/min",
                    "ref": "BCFI — Diazépam IV"}

    # Ligne 3 — Antiépileptiques IV
    d_lev = min(round(LEVETI_IV_KG * poids, 0), LEVETI_IV_MAX_MG)
    d_valp = min(round(VALPROATE_IV_KG * poids, 0), VALPROATE_IV_MAX_MG)
    d_ph  = min(round(PHENOBARB_IV_KG * poids, 0), PHENOBARB_IV_MAX_MG)
    duree_ph = round(d_ph / (PHENOBARB_DEBIT_MG_KG_MIN * poids), 1)
    ci_valp = ("CI formelle : enfant < 2 ans avec retard développement"
               if age < 2 else "")
    ligne3_leveti = {"med": "Lévétiracétam IV (Keppra®) — 1er choix",
                     "dose_mg": d_lev,
                     "volume": f"{round(d_lev/100,1)} ml sol 100 mg/ml",
                     "admin": f"{d_lev:.0f} mg dans 100 ml NaCl 0,9 % — 15 min",
                     "avantage": "Pas de sédation — monitoring minimal",
                     "ref": "BCFI — Lévétiracétam (Keppra)"}
    ligne3_valp   = {"med": "Valproate IV (Dépakine®) — 2e choix",
                     "dose_mg": d_valp,
                     "admin": (f"{d_valp:.0f} mg dans 100 ml NaCl 0,9 % — "
                               f"perfusion ≥ {VALPROATE_IV_DEBIT_MIN:.0f} min"),
                     "ci": ci_valp, "ref": "BCFI — Acide valproïque (Dépakine IV)"}
    ligne3_phenob = {"med": "Phénobarbital IV — 3e choix",
                     "dose_mg": d_ph,
                     "admin": (f"{d_ph:.0f} mg IV — max {PHENOBARB_DEBIT_MG_KG_MIN} mg/kg/min "
                               f"→ durée min {duree_ph} min"),
                     "attention": "Risque dépression respiratoire — Monitoring ECG",
                     "ref": "BCFI — Phénobarbital IV"}

    # Flumazénil
    d_fl = min(round(FLUMAZENIL_DOSE_MG * poids, 3), FLUMAZENIL_MAX_MG)
    antidote = {"med": "Flumazénil (Anexate®)",
                "indication": "Dépression respiratoire sévère post-benzodiazépine",
                "dose_mg": d_fl, "dose_total": FLUMAZENIL_MAX_TOTAL,
                "admin": (f"{d_fl} mg IV lent 15 s — "
                          f"répétable / 60 s jusqu'à max {FLUMAZENIL_MAX_TOTAL} mg"),
                "attention": "Demi-vie courte (1 h) — surveiller resédation",
                "ref": "BCFI — Flumazénil (Anexate)"}

    # Chronomètre clinique
    chrono = {
        "T0":     "Arrivée — PLS — VAS libres — O2 — Glycémie",
        f"T+{EME_SEUIL_MIN} min": "Si crise persiste → LIGNE 2 IV (médecin)",
        f"T+{EME_OPERATIONNEL_MIN} min": "Si crise persiste → LIGNE 3 (réanimation)",
        f"T+{EME_ETABLI_MIN} min": "EME établi — Intubation à discuter",
    }

    surveillance = [
        "Position latérale de sécurité (PLS) si inconscient",
        "SpO2 en continu — O2 si < 95 %",
        f"FR toutes les 2 min post-benzodiazépine — alarme si < 12/min",
        "AVPU toutes les 5 min — noter l'heure de reprise de conscience",
        "Glycémie capillaire — répéter si non faite",
        "Température — antipyrétique si fièvre",
        "VVP dès que possible",
        f"APPEL MÉDECIN si crise persiste > {EME_SEUIL_MIN} min après ligne 1",
    ]

    return {
        "glycemie_alerte": glycemie_alerte,
        "ligne1a": ligne1a, "ligne1b": ligne1b, "ligne1c": ligne1c,
        "ligne2_lora": ligne2_lora, "ligne2_clona": ligne2_clona, "ligne2_diaz": ligne2_diaz,
        "ligne3_leveti": ligne3_leveti, "ligne3_valp": ligne3_valp, "ligne3_phenob": ligne3_phenob,
        "antidote": antidote, "chrono": chrono, "surveillance": surveillance,
        "ref": "SFNP / EpiCARE 2023 — ISPE 2022 — BCFI Belgique — Urgences Hainaut",
    }
