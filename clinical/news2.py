# clinical/news2.py — Score NEWS2 (National Early Warning Score 2)
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Source : Royal College of Physicians London, 2017.
# Pondération BPCO selon échelle SpO2-2 (Eccles SE, 2017).

from typing import Tuple, List
from config import NEWS2_TRI_M, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD


def calculer_news2(
    fr: float, spo2: float, supp_o2: bool,
    temp: float, pas: float, fc: float,
    gcs: int, bpco: bool = False,
) -> Tuple[int, List[str]]:
    """
    Calcule le score NEWS2 et retourne (score, liste_avertissements).
    Prend en compte l'échelle SpO2-2 pour les patients BPCO.
    """
    alertes: List[str] = []
    s = 0

    try:
        # ── Fréquence respiratoire ────────────────────────────────────────
        if fr <= 8:       s += 3
        elif fr <= 11:    s += 1
        elif fr <= 20:    s += 0
        elif fr <= 24:    s += 2
        else:             s += 3

        # ── SpO2 — échelle 1 (défaut) ou échelle 2 (BPCO) ────────────────
        if not bpco:
            # Échelle 1 — standard
            if spo2 <= 91:   s += 3
            elif spo2 <= 93: s += 2
            elif spo2 <= 95: s += 1
            else:            s += 0
        else:
            # Échelle 2 — BPCO (cible SpO2 88-92 %)
            if spo2 <= 83:   s += 3
            elif spo2 <= 85: s += 2
            elif spo2 <= 87: s += 1
            elif spo2 <= 92: s += 0
            elif spo2 <= 94: s += 1
            elif spo2 <= 96: s += 2
            else:            s += 3  # hyperoxie BPCO = dangereux

        # ── O2 supplémentaire ─────────────────────────────────────────────
        if supp_o2:
            s += 2

        # ── Température ───────────────────────────────────────────────────
        if temp <= 35.0:   s += 3
        elif temp <= 36.0: s += 1
        elif temp <= 38.0: s += 0
        elif temp <= 39.0: s += 1
        else:              s += 2

        # ── Pression artérielle systolique ────────────────────────────────
        if pas <= 90:    s += 3
        elif pas <= 100: s += 2
        elif pas <= 110: s += 1
        elif pas <= 219: s += 0
        else:            s += 3

        # ── Fréquence cardiaque ───────────────────────────────────────────
        if fc <= 40:    s += 3
        elif fc <= 50:  s += 1
        elif fc <= 90:  s += 0
        elif fc <= 110: s += 1
        elif fc <= 130: s += 2
        else:           s += 3

        # ── Conscience (GCS < 15 = altération) ───────────────────────────
        if gcs < 15:
            s += 3

        # ── Alertes cliniques selon niveau ────────────────────────────────
        if s >= NEWS2_TRI_M:
            alertes.append(f"NEWS2 {s} ≥ {NEWS2_TRI_M} — ENGAGEMENT VITAL — TRI M DÉCHOCAGE IMMÉDIAT")
        elif s >= NEWS2_RISQUE_ELEVE:
            alertes.append(f"NEWS2 {s} ≥ {NEWS2_RISQUE_ELEVE} — APPEL MÉDICAL IMMÉDIAT")
        elif s >= NEWS2_RISQUE_MOD:
            alertes.append(f"NEWS2 {s} ≥ {NEWS2_RISQUE_MOD} — Surveillance rapprochée")

        # Alerte BPCO hyperoxie
        if bpco and spo2 > 96 and supp_o2:
            alertes.append("BPCO — SpO2 > 96 % sous O2 : risque d'hypercapnie — Titrer O2 cible 88-92 %")

    except (TypeError, ValueError) as e:
        alertes.append(f"Erreur calcul NEWS2 — Vérifier les constantes ({e})")

    return s, alertes


def n2_meta(score: int, bpco: bool = False) -> dict:
    """
    Retourne les métadonnées NEWS2 : niveau de risque, couleur, recommandation.
    Source : RCP 2017 — Tableau 2.
    """
    if score >= NEWS2_TRI_M:
        return {
            "label": f"NEWS2 {score} — CRITIQUE",
            "color": "#7C3AED",
            "risk": "Engagement vital",
            "reco": "Tri M — Appel équipe déchocage IMMÉDIAT",
        }
    elif score >= NEWS2_RISQUE_ELEVE:
        return {
            "label": f"NEWS2 {score} — ÉLEVÉ",
            "color": "#EF4444",
            "risk": "Risque élevé",
            "reco": "Appel médical immédiat — Réévaluation continue",
        }
    elif score >= NEWS2_RISQUE_MOD:
        return {
            "label": f"NEWS2 {score} — MODÉRÉ",
            "color": "#F59E0B",
            "risk": "Risque modéré",
            "reco": "Surveillance rapprochée — Réévaluation < 30 min",
        }
    elif score >= 1:
        return {
            "label": f"NEWS2 {score} — BAS",
            "color": "#22C55E",
            "risk": "Risque faible",
            "reco": "Surveillance standard",
        }
    else:
        return {
            "label": "NEWS2 0 — STABLE",
            "color": "#3B82F6",
            "risk": "Stable",
            "reco": "Surveillance de routine",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PÉDIATRIE — PEWS + Valeurs normales par âge
# NEWS2 est NON VALIDÉ avant 16 ans (RCP 2017).
# Pour la pédiatrie, utiliser le PEWS (Paediatric Early Warning Score)
# ou les seuils normaux par âge pour interpréter les constantes.
#
# Références :
#   - Monaghan A, "Detecting and managing deterioration in children", 2005
#   - Sécurité Sanitaire SPF Santé Publique (Belgique) — Signes vitaux normaux
#   - PEWS : Parshuram CS et al., Arch Pediatr Adolesc Med 2011
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Dict

# Valeurs normales pédiatriques par tranche d'âge (en années)
# Format : (fc_min, fc_max, pas_min, pas_max, fr_min, fr_max, spo2_min)
# Sources : SPF Santé Publique Belgique / Flemish Paediatric Society /
#            PEWS Monaghan 2005 / SFP 2020
_NORMALES_PED: Dict[str, tuple] = {
    "nourr_0_1m":  (100, 180, 55,  80,  30, 60, 95),   # 0-1 mois  (<1/12 an)
    "nourr_1_12m": (90,  160, 65,  100, 25, 55, 95),   # 1-12 mois
    "enf_1_5a":    (75,  140, 75,  110, 20, 40, 95),   # 1-5 ans
    "enf_5_12a":   (60,  120, 80,  120, 15, 30, 96),   # 5-12 ans
    "ado_12_16a":  (55,  110, 85,  130, 12, 25, 96),   # 12-16 ans
}


def seuils_normaux_ped(age_ans: float) -> dict:
    """Retourne les plages normales pour un enfant d'âge donné.
    Source : SPF Santé Publique Belgique / PEWS Monaghan 2005.
    """
    if age_ans < 1/12:      # < 1 mois (< 0.0833 an)
        fc_min,fc_max,pas_min,pas_max,fr_min,fr_max,spo2 = _NORMALES_PED["nourr_0_1m"]
        label = "Nouveau-né / nourrisson < 1 mois"
    elif age_ans < 1:
        fc_min,fc_max,pas_min,pas_max,fr_min,fr_max,spo2 = _NORMALES_PED["nourr_1_12m"]
        label = f"Nourrisson {int(age_ans*12)} mois"
    elif age_ans < 5:
        fc_min,fc_max,pas_min,pas_max,fr_min,fr_max,spo2 = _NORMALES_PED["enf_1_5a"]
        label = f"Enfant {age_ans:.0f} an{'s' if age_ans >= 2 else ''}"
    elif age_ans < 12:
        fc_min,fc_max,pas_min,pas_max,fr_min,fr_max,spo2 = _NORMALES_PED["enf_5_12a"]
        label = f"Enfant {age_ans:.0f} ans"
    else:
        fc_min,fc_max,pas_min,pas_max,fr_min,fr_max,spo2 = _NORMALES_PED["ado_12_16a"]
        label = f"Adolescent {age_ans:.0f} ans"
    return {
        "label": label,
        "fc": (fc_min, fc_max),
        "pas": (pas_min, pas_max),
        "fr": (fr_min, fr_max),
        "spo2_min": spo2,
    }


def calculer_pews(
    fc: float, fr: float, spo2: float, gcs: int,
    temp: float, age_ans: float, supp_o2: bool = False,
    vomissements: bool = False, agitation: bool = False,
) -> Tuple[int, List[str], dict]:
    """
    PEWS — Paediatric Early Warning Score.
    Validé pour les enfants de 0 à 16 ans.
    Score > 4 = risque élevé de détérioration / appel médical urgent.

    Critères scorés (0-3 par paramètre) :
      - Comportement (agitation/somnolence)
      - Cardiovasculaire (FC, TRC)
      - Respiratoire (FR, SpO2, O2 supp.)

    Source : Monaghan A, Nurs Stand 2005 — adapté Parshuram CS, JAMA 2011.
    """
    alertes: List[str] = []
    s = 0
    norm = seuils_normaux_ped(age_ans)
    fc_min, fc_max = norm["fc"]
    fr_min, fr_max = norm["fr"]
    spo2_min       = norm["spo2_min"]

    # ── Score comportement / conscience ──────────────────────────────────────
    if gcs <= 8:
        s += 3; alertes.append(f"GCS {gcs}/15 — Coma/stupeur")
    elif gcs <= 12:
        s += 2; alertes.append(f"GCS {gcs}/15 — Altération modérée")
    elif gcs < 15 or agitation:
        s += 1

    # ── Score cardiovasculaire (FC par tranche d'âge) ────────────────────────
    if fc < fc_min - 30 or fc > fc_max + 50:
        s += 3; alertes.append(f"FC {fc:.0f} bpm — hors plage critique (normale {fc_min}-{fc_max})")
    elif fc < fc_min - 15 or fc > fc_max + 30:
        s += 2; alertes.append(f"FC {fc:.0f} bpm — hors plage modérée (normale {fc_min}-{fc_max})")
    elif fc < fc_min or fc > fc_max:
        s += 1

    # ── Score respiratoire (FR + SpO2) ───────────────────────────────────────
    if fr < fr_min - 10 or fr > fr_max + 20 or spo2 < 85:
        s += 3; alertes.append(f"FR {fr:.0f}/min ou SpO2 {spo2:.0f}% — détresse respiratoire")
    elif fr < fr_min - 5 or fr > fr_max + 10 or spo2 < 90:
        s += 2; alertes.append(f"FR {fr:.0f}/min ou SpO2 {spo2:.0f}% (normale FR {fr_min}-{fr_max})")
    elif fr < fr_min or fr > fr_max or spo2 < spo2_min or supp_o2:
        s += 1
        if supp_o2:
            alertes.append("O2 supplémentaire administré")

    # ── Vomissements post-opératoires ─────────────────────────────────────────
    if vomissements:
        s += 1

    # ── Hyperthermie sévère ───────────────────────────────────────────────────
    if temp >= 40.0:
        s += 1; alertes.append(f"Hyperthermie {temp:.1f}°C ≥ 40°C")
    elif temp <= 35.5:
        s += 1; alertes.append(f"Hypothermie {temp:.1f}°C")

    # ── Alertes PEWS ──────────────────────────────────────────────────────────
    if s >= 7:
        alertes.insert(0, f"PEWS {s} ≥ 7 — APPEL ÉQUIPE RÉANIMATION PÉDIATRIQUE IMMÉDIAT")
    elif s >= 5:
        alertes.insert(0, f"PEWS {s} ≥ 5 — APPEL MÉDECIN IMMÉDIAT")
    elif s >= 3:
        alertes.insert(0, f"PEWS {s} ≥ 3 — Surveillance rapprochée — réévaluation < 30 min")

    return s, alertes, {
        "seuils": norm,
        "fc_anormale":  fc < fc_min or fc > fc_max,
        "fr_anormale":  fr < fr_min or fr > fr_max,
        "spo2_anormale": spo2 < spo2_min,
    }


def pews_meta(score: int) -> dict:
    """Métadonnées PEWS : couleur et recommandation."""
    if score >= 7:
        return {"label": f"PEWS {score} — CRITIQUE",   "color": "#7C3AED",
                "reco": "Appel réanimation pédiatrique immédiat"}
    elif score >= 5:
        return {"label": f"PEWS {score} — ÉLEVÉ",      "color": "#EF4444",
                "reco": "Appel médecin immédiat"}
    elif score >= 3:
        return {"label": f"PEWS {score} — MODÉRÉ",     "color": "#F59E0B",
                "reco": "Surveillance rapprochée — réévaluation < 30 min"}
    elif score >= 1:
        return {"label": f"PEWS {score} — BAS",        "color": "#22C55E",
                "reco": "Surveillance standard"}
    return {"label": "PEWS 0 — STABLE", "color": "#3B82F6", "reco": "Surveillance de routine"}
