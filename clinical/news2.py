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
