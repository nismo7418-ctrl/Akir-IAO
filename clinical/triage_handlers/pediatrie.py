# clinical/triage_handlers/pediatrie.py — Triage pédiatrique — AKIR-IAO v19.0
# Référence : FRENCH V1.1 — Protocoles pédiatriques SFMU / ESPGHAN

def _triage_ped_generique(age: float, fc: float, spo2: float, temp: float, gcs: int, det: dict, **_) -> tuple:
    """
    Handler pédiatrique générique — appliqué si aucun handler spécifique.
    Source : FRENCH V1.1 — Seuils pédiatriques ajustés à l'âge.
    """
    # Seuils tachycardie selon âge (APLS 2021)
    if   age < 1/12:  seuil_fc = 160
    elif age < 1.0:   seuil_fc = 150
    elif age < 5.0:   seuil_fc = 140
    elif age < 12.0:  seuil_fc = 130
    else:             seuil_fc = 120

    tachy = fc > seuil_fc

    # Critères Tri M
    if gcs <= 8:
        return "M", f"GCS {gcs} — Détresse neurologique majeure", "FRENCH Tri M"
    if spo2 < 85:
        return "M", f"SpO2 {spo2}% — Détresse respiratoire critique", "FRENCH Tri M"

    # Critères Tri 1
    if spo2 < 92:
        return "1", f"SpO2 {spo2}% — Détresse respiratoire sévère", "FRENCH Tri 1"
    if tachy and spo2 < 95:
        return "1", f"FC {fc:.0f} + SpO2 {spo2}% — Instabilité hémodynamique", "FRENCH Tri 1"
    if gcs < 14:
        return "1", f"GCS {gcs} — Altération conscience", "FRENCH Tri 1"

    # Critères Tri 2
    if age < 1/12 and temp >= 38.0:
        return "2", f"Nourrisson < 1 mois — fièvre {temp:.1f}°C", "FRENCH Pédiatrie"
    if age < 0.25 and temp >= 38.0:
        return "2", f"Nourrisson {int(age*12)} mois — fièvre {temp:.1f}°C", "FRENCH Pédiatrie"
    if tachy and temp >= 38.5:
        return "2", f"Tachycardie FC {fc:.0f} + fièvre {temp:.1f}°C", "FRENCH Pédiatrie"
    if det.get("cri_aigu") or det.get("hypotonie"):
        return "2", "Signe de gravité pédiatrique — hypotonie / cri aigu", "FRENCH Pédiatrie"

    # Critères Tri 3A
    if temp >= 39.5:
        return "3A", f"Fièvre élevée {temp:.1f}°C", "FRENCH Tri 3A"
    if tachy:
        return "3A", f"Tachycardie FC {fc:.0f} bpm", "FRENCH Tri 3A"
    if age < 3.0 / 12:
        return "3A", f"Nourrisson {int(age*12)} mois < 3 mois", "FRENCH Tri 3A"

    return "3B", "Pédiatrie stable", "FRENCH Tri 3B"
