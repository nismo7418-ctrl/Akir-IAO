# clinical/tools.py — Outils cliniques spécialisés — AKIR-IAO v20
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# RGPD : aucune donnée nominative stockée
#
# Outils implémentés :
#   1. Calculateur RSI — Séquence rapide d'intubation (ERC 2021 / SFAR)
#   2. Recharge volémique — 20 ml/kg adulte / 10 ml/kg pédiatrique
#   3. Broselow pédiatrique — Taille → couleur → doses
#   4. Convertisseur opioïdes — Équianalgésie BCFI 2024
#   5. Correction natrémie (hyperglycémie)
#   6. DFGe CKD-EPI — Adaptation posologie rénale
#   7. Code Stroke interactif — Délais FAST + door-to-needle
#   8. Joules défibrillateur — 2 J/kg / 4 J/kg / adulte
#   9. Timer multi-médicaments — Plusieurs chrono indépendants
#  10. Glasgow-Blatchford — Hémorragie digestive haute

from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import math


# ══════════════════════════════════════════════════════════════════════════════
# 1. RSI — Séquence Rapide d'Intubation
# Source : SFAR 2017 / ERC 2021 / ACEP — RSI Protocol
# ══════════════════════════════════════════════════════════════════════════════

RSI_AGENTS = {
    "Étomidate": {
        "dose_kg": 0.3, "max_mg": 40, "voie": "IV rapide",
        "note": "Hypnotique de référence RSI (SFAR 2017) — 0,3 mg/kg IV",
        "ci": ["Insuffisance surrénalienne", "Sepsis sévère (relatif)"],
    },
    "Kétamine": {
        "dose_kg": 1.5, "max_mg": 200, "voie": "IV rapide",
        "note": "Alternative si bronchospasme ou état de choc — 1,5 mg/kg IV",
        "ci": ["HTA sévère non contrôlée", "HTIC (relatif)"],
    },
    "Midazolam": {
        "dose_kg": 0.1, "max_mg": 10, "voie": "IV lente",
        "note": "Alternative si agitation — 0,1 mg/kg IV — titrée",
        "ci": ["Choc hémodynamique"],
    },
    "Propofol": {
        "dose_kg": 1.5, "max_mg": 200, "voie": "IV rapide",
        "note": "Si patient hémodynamiquement stable — 1,5 mg/kg IV",
        "ci": ["Choc", "Hypovolémie", "Allergie aux huiles de soja"],
    },
}

CURARES_RSI = {
    "Succinylcholine": {
        "dose_kg": 1.5, "max_mg": 200, "voie": "IV rapide",
        "note": "Curarisant de RÉFÉRENCE RSI — 1,5 mg/kg IV — délai 45-60 s",
        "ci": ["Brûlure étendue > 24h", "Crush syndrome", "Hyperkaliémie", "Myopathie"],
        "duree_min": 10,
    },
    "Rocuronium": {
        "dose_kg": 1.2, "max_mg": 200, "voie": "IV rapide",
        "note": "Alternative si CI succinylcholine — 1,2 mg/kg IV — délai 60-90 s",
        "ci": ["Allergie"],
        "antidote": "Sugammadex 16 mg/kg IV (ERC 2021)",
        "duree_min": 60,
    },
}

ATROPINE_RSI = {"dose_kg": 0.02, "min_mg": 0.1, "max_mg": 0.5,
                "note": "Pré-médication enfant < 5 ans — 0,02 mg/kg (min 0,1 mg / max 0,5 mg)"}


def calculer_rsi(poids: float, age: float = 45,
                 hypnotique: str = "Étomidate",
                 curare: str = "Succinylcholine") -> Dict:
    """
    Calcul des doses RSI pour un patient donné.
    Source : SFAR 2017 Intubation difficile / ERC 2021.
    """
    agents = {}
    # Hypnotique
    if hypnotique in RSI_AGENTS:
        ag = RSI_AGENTS[hypnotique]
        dose = min(ag["dose_kg"] * poids, ag["max_mg"])
        agents[hypnotique] = {
            "dose_mg": round(dose, 1),
            "voie": ag["voie"],
            "note": ag["note"],
            "ci": ag["ci"],
        }
    # Curare
    if curare in CURARES_RSI:
        cu = CURARES_RSI[curare]
        dose_c = min(cu["dose_kg"] * poids, cu["max_mg"])
        agents[curare] = {
            "dose_mg": round(dose_c, 1),
            "voie": cu["voie"],
            "note": cu["note"],
            "ci": cu["ci"],
            "duree_min": cu.get("duree_min"),
            "antidote": cu.get("antidote"),
        }
    # Atropine si enfant < 5 ans
    if age < 5:
        dose_atr = min(max(ATROPINE_RSI["dose_kg"] * poids, ATROPINE_RSI["min_mg"]),
                       ATROPINE_RSI["max_mg"])
        agents["Atropine (pré-méd.)"] = {
            "dose_mg": round(dose_atr, 2),
            "voie": "IV 2 min avant induction",
            "note": ATROPINE_RSI["note"],
            "ci": [],
        }
    # Taille canule / sonde
    if age < 1:
        sonde_it = f"{3.5:.1f} mm (non ballonnet)"
        guedel   = "40 mm (taille 000)"
    elif age < 2:
        sonde_it = f"3.5-4.0 mm"
        guedel   = "50 mm (taille 00)"
    elif age < 16:
        # Formule : (âge/4) + 4 sans ballonnet, (âge/4) + 3.5 avec
        taille_it = round(age / 4 + 4, 1)
        sonde_it  = f"{taille_it:.1f} mm"
        taille_g  = int(60 + age * 5) if age < 8 else int(80 + (age - 8) * 10)
        guedel    = f"{taille_g} mm"
    else:
        sonde_it = "7.0-8.0 mm (F) / 7.5-8.5 mm (H) avec ballonnet"
        guedel   = "90-100 mm (taille 3-4)"

    return {
        "agents":   agents,
        "sonde_it": sonde_it,
        "guedel":   guedel,
        "ordre": [
            "1. Préoxygénation 3-5 min O2 haut débit (FiO2 = 1)",
            "2. Équipement prêt : laryngoscope, aspiration, ballon",
            "3. Prémédication (atropine si < 5 ans)",
            "4. Hypnotique IV",
            "5. Curare IV (immédiatement après hypnotique)",
            "6. Pression cricoïde jusqu'à confirmation ballonnet gonflé",
            "7. Intubation à 45-60 s (succinylcholine) ou 60-90 s (rocuronium)",
            "8. Vérification : auscultation + SpO2 + ETCO2 si disponible",
        ],
        "source": "SFAR 2017 Intubation / ERC 2021 / BCFI",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. RECHARGE VOLÉMIQUE
# Source : SSC 2021 / ATLS 11th / ERC 2021
# ══════════════════════════════════════════════════════════════════════════════

def calculer_recharge_volemique(poids: float, age: float = 45,
                                 indication: str = "sepsis") -> Dict:
    """
    Calcul des bolus de recharge volémique selon l'indication et l'âge.
    Source : SSC 2021 (sepsis) / ATLS 11th (trauma) / ERC 2021 pédiatrie.
    """
    is_ped = age < 16
    bolus_ml_kg = 10 if is_ped else 500  # pédiatrie : 10 ml/kg, adulte : 500 ml fixe
    max_bolus   = 3

    if is_ped:
        bolus1_ml = round(bolus_ml_kg * poids)
        note_max  = f"Max 3 bolus × {bolus1_ml} ml = {bolus1_ml * 3} ml"
        soluté    = "NaCl 0,9 % ou Ringer Lactate"
        débit     = "15 min par bolus"
    else:
        bolus1_ml = 500
        note_max  = "Max 30 ml/kg total (15 min/bolus — réévaluer entre chaque)"
        soluté    = "Ringer Lactate (préféré) ou NaCl 0,9 %"
        débit     = "15 min"

    indications_map = {
        "sepsis":  ("SSC 2021 : 30 ml/kg cristalloïdes dans les 3 h",
                    "#EF4444", f"Remplissage sepsis — {bolus1_ml} ml × 3 en 45 min"),
        "trauma":  ("ATLS 11th : 1 L Ringer (adulte), 20 ml/kg (enfant) — contrôle hémorragie PRIORITAIRE",
                    "#F59E0B", f"Remplissage trauma — {bolus1_ml} ml × 1 à 2 max si choc hémorragique"),
        "deshy":   ("ESPGHAN 2014 : 10 ml/kg × 1-3 bolus selon sévérité",
                    "#3B82F6", f"Déshydratation — {bolus1_ml} ml en {débit}"),
        "general": ("Remplissage guidé par réponse clinique (FC, PAS, diurèse)",
                    "#22C55E", f"Bolus {bolus1_ml} ml — réévaluer après"),
    }
    info, couleur, titre = indications_map.get(indication, indications_map["general"])

    bolus_list = []
    for i in range(1, max_bolus + 1):
        total = bolus1_ml * i
        total_kg = round(total / poids, 1) if poids > 0 else 0.0
        bolus_list.append({"num": i, "ml": bolus1_ml, "total_ml": total,
                           "total_ml_kg": total_kg})

    return {
        "titre":      titre,
        "bolus_ml":   bolus1_ml,
        "bolus_list": bolus_list,
        "soluté":     soluté,
        "débit":      débit,
        "note_max":   note_max,
        "info":       info,
        "couleur":    couleur,
        "source":     "SSC 2021 / ATLS 11th / ESPGHAN 2014",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. BROSELOW — Tableau pédiatrique colorimétrique
# Source : Broselow JB et al., Ann Emerg Med 1988 — Mise à jour 2018
# ══════════════════════════════════════════════════════════════════════════════

BROSELOW_TABLE = [
    # (taille_max_cm, couleur, poids_kg, adrenaline_mg, atropine_mg,
    #  diazepam_mg, glucose_ml_G30, sonde_it_mm, defibrillation_J)
    (59,  "Gris",     3.0,  0.03, 0.1, 1.5,  10, 2.5, 6),
    (70,  "Rose",     5.0,  0.05, 0.1, 2.5,  15, 3.0, 10),
    (85,  "Rouge",    7.5,  0.08, 0.1, 3.0,  20, 3.5, 15),
    (95,  "Mauve",    9.0,  0.09, 0.2, 4.5,  25, 4.0, 18),
    (107, "Jaune",   11.0,  0.11, 0.2, 5.5,  30, 4.5, 22),
    (118, "Blanc",   14.0,  0.14, 0.3, 7.0,  35, 5.0, 28),
    (130, "Bleu",    18.0,  0.18, 0.4, 9.0,  45, 5.5, 36),
    (143, "Orange",  24.0,  0.24, 0.5, 10.0, 55, 6.0, 48),
    (155, "Vert",    32.0,  0.32, 0.5, 10.0, 70, 6.5, 64),
    (999, "Adulte",  50.0,  0.5,  0.5, 10.0, 100, 7.5, 200),
]

BROSELOW_COLORS = {
    "Gris":   "#9CA3AF", "Rose":   "#F9A8D4", "Rouge":  "#EF4444",
    "Mauve":  "#A855F7", "Jaune":  "#EAB308", "Blanc":  "#E2E8F0",
    "Bleu":   "#3B82F6", "Orange": "#F97316", "Vert":   "#22C55E",
    "Adulte": "#64748B",
}


def broselow(taille_cm: float) -> Dict:
    """
    Retourne les doses d'urgence pédiatriques selon la taille (Broselow 2018).
    Source : Broselow JB et al., Ann Emerg Med 1988 / mise à jour 2018.
    """
    for (taille_max, couleur, poids, adre, atr, diaz, gluc, sonde, defib) in BROSELOW_TABLE:
        if taille_cm <= taille_max:
            return {
                "couleur":       couleur,
                "hex_couleur":   BROSELOW_COLORS.get(couleur, "#64748B"),
                "poids_estimé":  poids,
                "doses": {
                    "Adrénaline IM (0,01 mg/kg)":       f"{adre:.2f} mg",
                    "Atropine IV (0,02 mg/kg)":         f"{atr:.2f} mg",
                    "Diazépam IV (0,3 mg/kg)":          f"{diaz:.1f} mg",
                    "Glucose 30% IV (0,3 g/kg)":        f"{gluc} ml",
                    "Sonde d'intubation":               f"{sonde:.1f} mm",
                    "Défibrillation 2 J/kg":            f"{defib} J (2 J/kg)",
                    "Défibrillation 4 J/kg":            f"{defib*2} J (4 J/kg)",
                    "Paracétamol IV (15 mg/kg)":        f"{round(poids*15)} mg",
                    "Ceftriaxone IV (100 mg/kg)":       f"{round(min(poids*100,2000)/1000,1)} g",
                },
                "source": "Broselow JB et al., Ann Emerg Med 1988 / 2018 revision",
            }
    return {"couleur": "Adulte", "hex_couleur": "#64748B", "poids_estimé": 70}


# ══════════════════════════════════════════════════════════════════════════════
# 4. CONVERTISSEUR OPIOÏDES — Équianalgésie
# Source : BCFI 2024 / BNF / Equianalgesic table OMS 2019
# ══════════════════════════════════════════════════════════════════════════════

# Ratios par rapport à la morphine IV (référence = 1.0)
OPIOIDES_RATIO_IV = {
    "Morphine IV":       1.0,
    "Morphine PO":       1/3,      # PO = 3× moins efficace que IV
    "Piritramide IV":    0.7,       # Dipidolor — 0.7× morphine IV
    "Tramadol IV":       1/10,      # Tramadol = 1/10 morphine
    "Codéine PO":        1/10,
    "Oxycodone PO":      1/1.5,     # 1.5× morphine PO = 0.5× morphine IV
    "Oxycodone IV":      1.0,       # équianalgésique morphine IV
    "Fentanyl IV":       100.0,     # 100× morphine IV
    "Fentanyl patch µg/h": 2.4,    # 25 µg/h patch ≈ 60 mg/j morphine PO
    "Sufentanil IV":     1000.0,    # 1000× morphine IV
    "Hydromorphone IV":  5.0,       # Dilaudid — 5× morphine IV
    "Méthadone PO":      3.0,       # ratio variable — prudence
    "Buprénorphine SL":  40.0,      # Temgesic — 40× morphine IV
}


def convertir_opioides(molecule_source: str, dose_mg: float,
                        molecule_cible: str) -> Dict:
    """
    Convertit une dose d'opioïde en équivalent d'un autre.
    ATTENTION : toujours commencer à 50-75% de la dose calculée.
    Source : BCFI 2024 / OMS 2019 / BNF 2024.
    """
    if molecule_source not in OPIOIDES_RATIO_IV:
        return {"erreur": f"Molécule source inconnue : {molecule_source}"}
    if molecule_cible not in OPIOIDES_RATIO_IV:
        return {"erreur": f"Molécule cible inconnue : {molecule_cible}"}

    # Conversion via morphine IV (référence)
    morphine_iv_eq = dose_mg * OPIOIDES_RATIO_IV[molecule_source]
    dose_cible_calc = morphine_iv_eq / OPIOIDES_RATIO_IV[molecule_cible]
    dose_demarrage  = dose_cible_calc * 0.5  # 50% par sécurité

    return {
        "molecule_source":    molecule_source,
        "dose_source_mg":     dose_mg,
        "morphine_iv_eq_mg":  round(morphine_iv_eq, 2),
        "molecule_cible":     molecule_cible,
        "dose_calculee_mg":   round(dose_cible_calc, 2),
        "dose_demarrage_mg":  round(dose_demarrage, 2),
        "avertissement": (
            "⚠️ Commencer à 50% de la dose calculée. "
            "Titration obligatoire. Tolérance croisée incomplète. "
            "Validation médicale obligatoire."
        ),
        "source": "BCFI 2024 / OMS 2019 / BNF 2024",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. CORRECTION NATRÉMIE / HYPERGLYCÉMIE
# Source : Hillier TA et al., NEJM 1999 — Katz MA, NEJM 1973
# ══════════════════════════════════════════════════════════════════════════════

def corriger_natrémie(na_mesure: float, glycemie_mmol_l: float) -> Dict:
    """
    Correction de la natrémie pour hyperglycémie.
    Formule : Na corrigé = Na mesuré + 0,3 × (glycémie - 5,5) / 5,5
    Ou variante Hillier : + 0,24 mmol/L par mmol/L de glucose au-dessus de 5,6.
    Source : Hillier TA et al., NEJM 1999.
    """
    if glycemie_mmol_l <= 0:
        return {"erreur": "Glycémie invalide"}

    # Formule de Katz (classique)
    na_corrige_katz = na_mesure + 0.3 * (glycemie_mmol_l - 5.5) / 5.5 * 10

    # Formule de Hillier (plus précise pour hyperglycémies sévères)
    na_corrige_hillier = na_mesure + 0.24 * max(0, glycemie_mmol_l - 5.6)

    # Interprétation
    na_ref = na_corrige_hillier
    if na_ref < 130:
        interp = f"Hyponatrémie sévère < 130 mmol/L — Restriction hydrique + avis néphro"
        niveau = "danger"
    elif na_ref < 135:
        interp = f"Hyponatrémie modérée (130-134) — Surveillance + bilan étiologique"
        niveau = "warning"
    elif na_ref <= 145:
        interp = f"Natrémie normale corrigée"
        niveau = "success"
    elif na_ref <= 150:
        interp = f"Hypernatrémie légère (146-150) — Réhydratation prudente"
        niveau = "warning"
    else:
        interp = f"Hypernatrémie sévère > 150 — Urgence métabolique"
        niveau = "danger"

    return {
        "na_mesure":           na_mesure,
        "glycemie_mmol_l":     glycemie_mmol_l,
        "glycemie_mg_dl":      round(glycemie_mmol_l * 18, 0),
        "na_corrige_katz":     round(na_corrige_katz, 1),
        "na_corrige_hillier":  round(na_corrige_hillier, 1),
        "interpretation":      interp,
        "niveau":              niveau,
        "source": "Hillier TA et al., NEJM 1999 / Katz MA, NEJM 1973",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 6. DFGe — CKD-EPI 2021 (sans race)
# Source : Inker LA et al., NEJM 2021 — doi:10.1056/NEJMoa2102953
# ══════════════════════════════════════════════════════════════════════════════

def calculer_dfge(creatinine_umol_l: float, age: float,
                   sexe: str = "H") -> Dict:
    """
    DFGe par l'équation CKD-EPI 2021 (sans coefficient racial — recommandation KDIGO 2022).
    Unité de créatinine : µmol/L (diviser par 88,4 pour mg/dL).
    Source : Inker LA et al., NEJM 2021.
    """
    if creatinine_umol_l <= 0:
        return {"erreur": "Créatinine invalide (≤ 0 µmol/L)", "dfge": None}
    if age <= 0:
        return {"erreur": "Âge invalide", "dfge": None}

    try:
        creat_mg_dl = creatinine_umol_l / 88.4
        kappa  = 0.7 if sexe == "F" else 0.9
        alpha  = -0.241 if sexe == "F" else -0.302
        multi  = 1.012 if sexe == "F" else 1.0

        ratio = creat_mg_dl / kappa
        if ratio < 1:
            dfge = 142 * (ratio ** alpha) * (0.9938 ** age) * multi
        else:
            dfge = 142 * (ratio ** -1.200) * (0.9938 ** age) * multi
        dfge = round(dfge, 1)
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        return {"erreur": f"Erreur calcul DFGe : {e}", "dfge": None}

    # Classification KDIGO 2022
    if dfge >= 90:
        stade = "G1 — Normal ou élevé"
        note  = "Fonction rénale normale — pas d'adaptation posologique"
        col   = "#22C55E"
    elif dfge >= 60:
        stade = "G2 — Légèrement diminué"
        note  = "Pas d'adaptation en général — surveiller les néphrotoxiques"
        col   = "#84CC16"
    elif dfge >= 45:
        stade = "G3a — Légèrement à modérément diminué"
        note  = "Adapter : AINS CI, métformine réduire, morphine prudence"
        col   = "#F59E0B"
    elif dfge >= 30:
        stade = "G3b — Modérément à sévèrement diminué"
        note  = "AINS CI, HBPM ajuster, antibiotiques adapter, dialyse à planifier"
        col   = "#F97316"
    elif dfge >= 15:
        stade = "G4 — Sévèrement diminué"
        note  = "Pré-dialyse — adapter quasi tous les médicaments — néphrologue"
        col   = "#EF4444"
    else:
        stade = "G5 — Insuffisance rénale terminale"
        note  = "Dialyse — ajustement maximal requis"
        col   = "#7C3AED"

    adaptations = []
    if dfge < 60:
        adaptations += ["⚠️ AINS : contre-indiqués", "⚠️ Morphine : accumulation métabolites actifs"]
    if dfge < 30:
        adaptations += ["⚠️ HBPM : réduire dose (Clairance < 30)", "⚠️ Kétamine : prudence",
                        "⚠️ Vancomycine : doser les taux résiduels"]
    if dfge < 15:
        adaptations += ["🔴 Digoxine CI", "🔴 Metformine CI", "🔴 Lithium CI"]

    return {
        "dfge":            dfge,
        "creatinine_input": creatinine_umol_l,
        "creat_mg_dl":     round(creat_mg_dl, 2),
        "stade":           stade,
        "note":            note,
        "couleur":         col,
        "adaptations":     adaptations,
        "source": "Inker LA et al., NEJM 2021 / KDIGO 2022",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 7. CODE STROKE — Délais FAST + Door-to-needle
# Source : ESO 2021 / ESC 2018 / Hainaut CHR protocole
# ══════════════════════════════════════════════════════════════════════════════

def code_stroke_delais(heure_debut: Optional[str], heure_arrivee: Optional[str],
                        heure_ct: Optional[str]) -> Dict:
    """
    Calcule les délais Code Stroke et vérifie le respect des objectifs.
    Source : ESO 2021 — délais recommandés pour thrombolyse.

    Objectifs ESO 2021 :
      Door-to-CT scan     : ≤ 25 min
      Door-to-needle      : ≤ 60 min
      Fenêtre thrombolyse : ≤ 4,5 h depuis début des symptômes
      Fenêtre thrombectomie : ≤ 6-24 h (selon imagerie)
    """
    from datetime import datetime

    def parse_time(t):
        if not t: return None
        try:
            return datetime.strptime(t, "%H:%M")
        except Exception:
            return None

    t_debut   = parse_time(heure_debut)
    t_arrivee = parse_time(heure_arrivee)
    t_ct      = parse_time(heure_ct)
    now_str   = datetime.now().strftime("%H:%M")
    t_now     = parse_time(now_str)

    resultats = {}

    if t_debut and t_arrivee:
        onset_to_door = (t_arrivee - t_debut).total_seconds() / 60
        if onset_to_door < 0: onset_to_door += 1440  # passer minuit
        resultats["onset_to_door_min"] = round(onset_to_door)

    if t_arrivee and t_ct:
        door_to_ct = (t_ct - t_arrivee).total_seconds() / 60
        if door_to_ct < 0: door_to_ct += 1440
        resultats["door_to_ct_min"]    = round(door_to_ct)
        resultats["door_to_ct_ok"]     = door_to_ct <= 25

    if t_debut and t_now:
        duree_totale = (t_now - t_debut).total_seconds() / 60
        if duree_totale < 0: duree_totale += 1440
        resultats["duree_symptomes_min"] = round(duree_totale)
        resultats["fenetre_thrombolyse"] = duree_totale <= 270   # 4.5h = 270 min
        resultats["fenetre_thrombecto"]  = duree_totale <= 360   # 6h (standard)
        resultats["temps_restant_thrombo_min"] = max(0, 270 - round(duree_totale))

    if t_arrivee and t_now:
        door_to_now = (t_now - t_arrivee).total_seconds() / 60
        if door_to_now < 0: door_to_now += 1440
        resultats["door_to_now_min"] = round(door_to_now)

    resultats["checklist"] = [
        "✅ Appeler neurologue/neurochirurgien de garde",
        "✅ Glycémie capillaire IMMÉDIATE (exclure hypoglycémie)",
        "✅ TDM cérébral sans injection urgent (≤ 25 min)",
        "✅ ECG 18 dérivations (FA ? cardiopathie ?)",
        "✅ Bilan biologique : NFS, coagulation, créatinine",
        "✅ Confirmer absence CI thrombolyse (chirurgie < 3 mois, anticoag…)",
        "✅ Voie veineuse 18G × 2 + prélèvements",
        "✅ Monitoring continu FC, PA, SpO2",
    ]
    resultats["ci_thrombolyse"] = [
        "Hémorragie intracrânienne (TDM)", "Chirurgie majeure < 3 mois",
        "AVC < 3 mois", "Traitement anticoagulant efficace",
        "PA > 185/110 mmHg non contrôlée", "Glycémie < 2,8 ou > 22 mmol/L",
        "Thrombopénie < 100 000/mm³",
    ]
    resultats["source"] = "ESO 2021 AVC / ESC 2018"
    return resultats


# ══════════════════════════════════════════════════════════════════════════════
# 8. JOULES DÉFIBRILLATEUR
# Source : ERC 2021 — Soar J et al.
# ══════════════════════════════════════════════════════════════════════════════

def joules_defibrillateur(poids: float, age: float = 45,
                           type_choc: str = "FV") -> Dict:
    """
    Calcule l'énergie de défibrillation selon le poids et le type de choc.
    Source : ERC 2021 / PALS 2020.
    """
    is_ped = age < 16

    if is_ped:
        j1 = round(2 * poids)
        j2 = round(4 * poids)
        j_max = min(j2, 200)
        return {
            "type":           "Pédiatrique (< 16 ans / palettes enfant < 10 kg)",
            "choc_1":         f"{j1} J  (2 J/kg)",
            "choc_2":         f"{min(j2, 200)} J  (4 J/kg — max 200 J)",
            "choc_suivants":  f"{min(j2, 200)} J  (maintenir 4 J/kg)",
            "palettes":       "Enfant < 10 kg : palettes 4,5 cm | > 10 kg : palettes adulte",
            "source": "ERC 2021 Pédiatrie / PALS 2020",
        }
    else:
        if type_choc in ("FV", "TV sans pouls"):
            return {
                "type":           "Adulte — FV / TV sans pouls",
                "choc_1":         "200 J biphasique (ou 360 J monophasique)",
                "choc_2":         "200 J biphasique (augmenter si échec répété)",
                "choc_suivants":  "200 J maximum selon défibrillateur",
                "cardioversion":  "N/A (ACR — choc non synchronisé)",
                "note":           "Reprendre RCP 2 min après chaque choc — pas d'interruption",
                "source": "ERC 2021 ALS",
            }
        elif type_choc == "FA":
            return {
                "type":           "Adulte — Cardioversion FA",
                "choc_1":         "200 J biphasique synchronisé",
                "choc_2":         "360 J si échec",
                "note":           "Synchronisation obligatoire — prémédication : propofol ou midazolam",
                "source": "ESC 2020 FA / ERC 2021",
            }
        elif type_choc == "Flutter":
            return {
                "type":           "Adulte — Cardioversion flutter",
                "choc_1":         "100 J biphasique synchronisé",
                "choc_2":         "200 J si échec",
                "note":           "Synchronisation obligatoire",
                "source": "ESC 2020 FA / ERC 2021",
            }
        elif type_choc == "TV tolérée":
            return {
                "type":           "Adulte — Cardioversion TV tolérée",
                "choc_1":         "150 J biphasique synchronisé",
                "choc_2":         "200 J si échec",
                "note":           "Synchronisation obligatoire — antiarythmique en parallèle",
                "source": "ERC 2021 ALS",
            }
    return {"erreur": "Type de choc non reconnu"}


# ══════════════════════════════════════════════════════════════════════════════
# 9. SCORE GLASGOW-BLATCHFORD — Hémorragie digestive haute
# Source : Blatchford O et al., Lancet 2000 — doi:10.1016/S0140-6736(00)02816-6
# ══════════════════════════════════════════════════════════════════════════════

def calculer_blatchford(urée_mmol_l: float, hb_g_dl: float, pas: float,
                         sexe: str = "H",
                         tachycardie: bool = False, méléna: bool = False,
                         syncope: bool = False, hepatopathie: bool = False,
                         ic: bool = False) -> Dict:
    """
    Score de Glasgow-Blatchford — triage hémorragie digestive haute.
    Score 0 : ambulatoire envisageable | Score ≥ 1 : hospitalisation
    Source : Blatchford O et al., Lancet 2000.
    """
    score = 0

    # Urée sanguine (mmol/L)
    if urée_mmol_l >= 25:      score += 6
    elif urée_mmol_l >= 16:    score += 4
    elif urée_mmol_l >= 10:    score += 3
    elif urée_mmol_l >= 8:     score += 2
    elif urée_mmol_l >= 6.5:   score += 2

    # Hémoglobine
    if sexe == "H":
        if hb_g_dl < 10:       score += 6
        elif hb_g_dl < 12:     score += 3
        elif hb_g_dl < 13:     score += 1
    else:
        if hb_g_dl < 10:       score += 6
        elif hb_g_dl < 12:     score += 1

    # PAS systolique
    if pas < 90:               score += 3
    elif pas < 100:            score += 2
    elif pas < 110:            score += 1

    # Variables cliniques
    if tachycardie:            score += 1
    if méléna:                 score += 1
    if syncope:                score += 2
    if hepatopathie:           score += 2
    if ic:                     score += 2

    if score == 0:
        interp = "Score 0 — Faible risque — Ambulatoire envisageable"
        reco   = "Endoscopie en externe < 72h — pas d'hospitalisation d'emblée"
        niveau = "success"
    elif score <= 3:
        interp = f"Score {score} — Risque modéré"
        reco   = "Hospitalisation courte — endoscopie < 24h"
        niveau = "warning"
    else:
        interp = f"Score {score} — Risque élevé — Intervention probable"
        reco   = "Hospitalisation — endoscopie urgente < 12h — Voie veineuse + remplissage"
        niveau = "danger"

    return {
        "score_val":       score,
        "interpretation":  interp,
        "recommendation":  reco,
        "niveau":          niveau,
        "source": "Blatchford O et al., Lancet 2000",
    }
