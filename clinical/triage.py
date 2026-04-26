# clinical/triage.py — Moteur de triage FRENCH V1.1 — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Référence : SFMU — Classification FRENCH Triage V1.1, 2018
# Hiérarchie : NEWS2 absolu → Priorités cliniques → Handler motif → Ajustement NEWS2

from __future__ import annotations
import unicodedata
from typing import Callable, Dict, List, Optional, Tuple
from config import (
    NEWS2_TRI_M, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD,
    GLYC, AVC_DELAI_THROMBOLYSE_H, ORD,
)
from clinical.french_v12 import get_protocol
from clinical.vitaux import si, sipa

TriageResult = Tuple[str, str, str]
Handler = Callable[..., TriageResult]


def _norm(value: str) -> str:
    """Normalise une chaîne pour comparaison insensible aux accents."""
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def _more_urgent(r1: TriageResult, r2: TriageResult) -> TriageResult:
    """Retourne le niveau le plus urgent entre deux résultats de triage."""
    ordre = ORD
    return r1 if ordre.get(r1[0], 9) <= ordre.get(r2[0], 9) else r2


def _protocol_default_result(motif: str) -> TriageResult:
    """
    Niveau de base issu de la table FRENCH V1.2.
    Les discriminants affichés dans l'UI proviennent de clinical/french_v12.py.
    """
    protocol = get_protocol(motif)
    if not protocol:
        return "3B", f"Évaluation standard — {motif}", "FRENCH V1.2 défaut Tri 3B"
    level = str(protocol.get("default") or "3B")
    label = str(protocol.get("motif") or motif)
    return level, f"Motif {label} — niveau protocolaire de base", f"FRENCH V1.2 défaut Tri {level}"


def _selected_discriminant_result(motif: str, det: dict) -> Optional[TriageResult]:
    """
    Discriminant sélectionné depuis la grille FRENCH V1.2.
    Un niveau 1 ou 2 reste prioritaire sur les autres scores via _more_urgent.
    """
    try:
        selected = (det or {}).get("french_discriminant")
        if isinstance(selected, dict):
            level = str(selected.get("level") or "").strip().upper()
            text = str(selected.get("text") or "").strip()
        elif isinstance(selected, tuple) and len(selected) >= 2:
            level = str(selected[0] or "").strip().upper()
            text = str(selected[1] or "").strip()
        else:
            return None

        if level not in ORD or not text:
            return None

        protocol = get_protocol(motif)
        motif_label = protocol.get("motif") if protocol else motif
        return (
            level,
            f"Critère discriminant FRENCH V1.2 — {motif_label} — {text}",
            f"FRENCH V1.2 discriminant Tri {level}",
        )
    except Exception:
        return None


def _selected_red_flag_result(motif: str, det: dict) -> Optional[TriageResult]:
    """
    Red flags saisis via l'interface dynamique.
    Le moteur retient le plus urgent des red flags cochés.
    """
    try:
        selections = (det or {}).get("red_flags_selected")
        if not isinstance(selections, list):
            return None

        best: Optional[TriageResult] = None
        protocol = get_protocol(motif)
        motif_label = protocol.get("motif") if protocol else motif

        for item in selections:
            if not isinstance(item, dict):
                continue
            level = str(item.get("level") or "").strip().upper()
            label = str(item.get("label") or item.get("text") or "").strip()
            rationale = str(item.get("rationale") or "Red flag clinique").strip()
            if level not in ORD or not label:
                continue

            candidate = (
                level,
                f"Red flag {motif_label} — {label}",
                rationale,
            )
            best = candidate if best is None else _more_urgent(best, candidate)

        return best
    except Exception:
        return None


def _has_atcd(det: dict, *labels: str) -> bool:
    terrain = {_norm(item) for item in (det or {}).get("atcd", [])}
    return any(_norm(label) in terrain for label in labels)


def _is_trauma_motif(motif: str) -> bool:
    motif_norm = _norm(motif)
    trauma_tokens = (
        "trauma",
        "traumatisme",
        "fracture",
        "entorse",
        "plaie",
        "brulure",
    )
    return any(token in motif_norm for token in trauma_tokens)


def _sidebar_risk_adjustment(
    motif: str,
    det: dict,
    temp: float,
    pas: float,
) -> Optional[TriageResult]:
    """Majoration terrain/pharmaco issue de la sidebar contextuelle."""
    if _has_atcd(det, "Anticoagulants/AOD") and (_is_trauma_motif(motif) or bool(det.get("anticoagulants"))):
        return "2", "Terrain anticoagulé associé à un traumatisme", "Majoration terrain"

    if _has_atcd(det, "Bêta-bloquants", "Beta-bloquants") and (pas < 100 or bool(det.get("syncopal"))):
        return "2", "Bêta-bloquants avec hypoperfusion potentielle", "Majoration terrain"

    if _has_atcd(det, "Corticoïdes au long cours", "Corticoides au long cours") and temp >= 38.0 and pas <= 100:
        return "2", "Corticothérapie chronique avec syndrome infectieux mal toléré", "Majoration terrain"

    return None


def _terrain_adjustment(
    motif: str,
    det: dict,
    age: float,
    temp: float,
    pas: float,
    gcs: int,
) -> Optional[TriageResult]:
    """
    Pondération du terrain :
    nourrisson fébrile, immunodépression, grossesse, anticoagulants, fragilité gériatrique.
    """
    motif_norm = _norm(motif)

    if age <= (3 / 12) and temp >= 38.0:
        return "1", f"Nourrisson ≤ 3 mois fébrile ({temp:.1f}°C)", "Terrain pédiatrique"

    if _has_atcd(det, "Immunodépression", "Chimiothérapie en cours") and temp >= 38.3:
        return "2", f"Terrain immunodéprimé + fièvre {temp:.1f}°C", "Terrain infectieux"

    if _has_atcd(det, "Grossesse") and (pas >= 160 or pas < 90 or det.get("metrorragies")):
        return "2", "Grossesse avec instabilité tensionnelle / métrorragies", "Terrain obstétrical"

    if _has_atcd(det, "Anticoagulants/AOD") and (
        "traumatisme cranien" in motif_norm
        or "cephalee" in motif_norm
        or bool(det.get("perte_connaissance"))
        or bool(det.get("trauma_cranien"))
    ):
        return "2", "Terrain anticoagulé avec risque neuro-hémorragique", "Terrain hémorragique"

    if age >= 75 and gcs < 15:
        return "2", f"Terrain gériatrique fragile avec GCS {gcs}/15", "Terrain gériatrique"

    return None


def _vital_adjustment(fc: float, pas: float, spo2: float, fr: float, gcs: int, age: float) -> Optional[TriageResult]:
    """
    Pondération par constantes vitales :
      - Shock Index adulte
      - SIPA pédiatrique
    """
    try:
        shock_index = si(fc, pas)
        if age < 18:
            sipa_val, _, sipa_alert = sipa(fc, age)
            if sipa_alert and (pas < 90 or gcs < 15):
                return "2", f"SIPA {sipa_val:.2f} au-dessus du seuil d'âge", "Vitaux/SIPA"

        if shock_index >= 1.0:
            return "2", f"Shock Index {shock_index:.2f} — instabilité hémodynamique", "Vitaux/SI"

        if spo2 < 92 or fr >= 26 or gcs <= 12:
            return "2", f"Dégradation vitale — SpO2 {spo2:.0f}% / FR {fr:.0f} / GCS {gcs}", "Vitaux FRENCH"
    except Exception:
        return None

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PRIORITÉS ABSOLUES (verrouillage clinique indépendant du motif)
# ═══════════════════════════════════════════════════════════════════════════════

def _check_priorites_absolues(det: dict, gcs: int, pas: float, spo2: float, fr: float) -> Optional[TriageResult]:
    """
    Vérifie les priorités absolues transversales.
    Ces critères verrouillent le triage quel que soit le motif.
    Source : SFMU FRENCH V1.1 — Critères de danger immédiat.
    """
    # Purpura fulminans — urgence absolue
    if det.get("purpura") or det.get("neff") or det.get("non_effacable"):
        return "1", "Purpura non effaçable — Purpura fulminans suspecté — Ceftriaxone IMMÉDIAT", "FRENCH Critère Absolu"

    # Arrêt cardio-respiratoire
    if det.get("acr") or det.get("arret"):
        return "M", "Arrêt cardio-respiratoire — RCP immédiate", "FRENCH Tri M"

    # Détresse respiratoire sévère
    if spo2 < 88 or fr > 30 or fr < 8:
        return "1", f"Détresse respiratoire sévère — SpO2 {spo2:.0f}% / FR {fr:.0f}/min", "FRENCH Critère Absolu"

    # Choc hémodynamique
    if pas < 80:
        return "1", f"Choc hémodynamique — PAS {pas:.0f} mmHg", "FRENCH Critère Absolu"

    # Coma
    if gcs <= 8:
        return "1", f"Altération profonde conscience — GCS {gcs}/15", "FRENCH Critère Absolu"

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS PAR MOTIF (logique FRENCH V1.1 spécifique à chaque motif)
# ═══════════════════════════════════════════════════════════════════════════════

def _h_acr(**kw) -> TriageResult:
    return "M", "Arrêt cardio-respiratoire — Déchocage immédiat", "FRENCH Tri M"


def _h_thoracique(**kw) -> TriageResult:
    """Douleur thoracique / SCA."""
    det, pas, fc, spo2, gcs = kw["det"], kw["pas"], kw["fc"], kw["spo2"], kw["gcs"]
    if det.get("syncopal") or pas < 90 or gcs < 15:
        return "1", "Douleur thoracique avec instabilité — Tri 1", "FRENCH Tri 1"
    if det.get("typique") or fc > 120 or spo2 < 94:
        return "2", "Douleur thoracique typique / instabilité relative", "FRENCH Tri 2"
    return "3A", "Douleur thoracique atypique — Évaluation rapide", "FRENCH Tri 3A"


def _h_dyspnee(**kw) -> TriageResult:
    """Dyspnée / insuffisance respiratoire."""
    spo2, fr, det = kw["spo2"], kw["fr"], kw["det"]
    if spo2 < 90 or fr > 25 or det.get("cyanose"):
        return "2", f"Dyspnée sévère — SpO2 {spo2:.0f}% / FR {fr:.0f}/min", "FRENCH Tri 2"
    if spo2 < 94 or fr > 20:
        return "3A", f"Dyspnée modérée — SpO2 {spo2:.0f}%", "FRENCH Tri 3A"
    return "3B", "Dyspnée légère — Évaluation", "FRENCH Tri 3B"


def _h_avc(**kw) -> TriageResult:
    """AVC / Déficit neurologique."""
    det, gcs, pas = kw["det"], kw["gcs"], kw["pas"]
    if gcs < 13 or pas > 220 or det.get("hemiplegique"):
        return "1", "AVC sévère — Déficit majeur — Tri 1", "FRENCH Tri 1"
    if det.get("fast_positif") or det.get("avc_suspect"):
        return "2", "Code Stroke — BE-FAST positif — Imagerie URGENTE", "FRENCH Tri 2"
    return "2", "Déficit neurologique focal — Bilan urgent", "FRENCH Tri 2"


def _h_conscience(**kw) -> TriageResult:
    """Altération de conscience / coma."""
    gcs, gl = kw["gcs"], kw.get("gl")
    if gcs <= 8:
        return "1", f"Coma — GCS {gcs}/15 — Protection VA indispensable", "FRENCH Tri 1"
    if gcs <= 12:
        return "2", f"Altération conscience modérée — GCS {gcs}/15", "FRENCH Tri 2"
    # Hypoglycémie sévère comme cause probable
    if gl and gl < GLYC["hs"]:
        return "2", f"Hypoglycémie sévère {gl:.0f} mg/dl — GCS {gcs}", "FRENCH Tri 2"
    return "2", f"Altération conscience — GCS {gcs}/15 — Évaluation urgente", "FRENCH Tri 2"


def _h_tc(**kw) -> TriageResult:
    """Traumatisme crânien."""
    gcs, det = kw["gcs"], kw["det"]
    if gcs < 13 or det.get("perte_connaissance_prolongee"):
        return "1", "TC grave — GCS < 13 — Déchocage", "FRENCH Tri 1"
    if det.get("perte_connaissance") or det.get("vomissements") or gcs == 13:
        return "2", "TC avec PDC ou vomissements — Imagerie urgente", "FRENCH Tri 2"
    if gcs == 14 or det.get("cephalee_post_tc"):
        return "3A", "TC modéré — Surveillance neurologique", "FRENCH Tri 3A"
    return "3B", "TC bénin — Surveillance clinique", "FRENCH Tri 3B"


def _h_hypotension(**kw) -> TriageResult:
    """Hypotension artérielle."""
    pas, fc, det = kw["pas"], kw["fc"], kw["det"]
    si_val = fc / pas if pas > 0 else 2.0
    if pas < 80 or si_val >= 1.5:
        return "1", f"Choc — PAS {pas:.0f} mmHg / SI {si_val:.1f}", "FRENCH Tri 1"
    if pas < 100 or si_val >= 1.0:
        return "2", f"Hypotension sévère — PAS {pas:.0f} mmHg", "FRENCH Tri 2"
    return "2", f"Hypotension — PAS {pas:.0f} mmHg — Évaluation urgente", "FRENCH Tri 2"


def _h_tachycardie(**kw) -> TriageResult:
    """Tachycardie / tachyarythmie."""
    fc, pas, det = kw["fc"], kw["pas"], kw["det"]
    if fc > 180 or pas < 90 or det.get("instable"):
        return "1", f"Tachycardie instable — FC {fc:.0f} / PAS {pas:.0f}", "FRENCH Tri 1"
    if fc > 150:
        return "2", f"Tachycardie sévère — FC {fc:.0f}", "FRENCH Tri 2"
    return "3A", f"Tachycardie — FC {fc:.0f} — Évaluation ECG urgente", "FRENCH Tri 3A"


def _h_bradycardie(**kw) -> TriageResult:
    """Bradycardie / bradyarythmie."""
    fc, pas, det = kw["fc"], kw["pas"], kw["det"]
    if fc < 40 or pas < 90 or det.get("syncope"):
        return "1", f"Bradycardie instable — FC {fc:.0f}", "FRENCH Tri 1"
    if fc < 50:
        return "2", f"Bradycardie sévère — FC {fc:.0f}", "FRENCH Tri 2"
    return "3A", f"Bradycardie — FC {fc:.0f} — ECG urgent", "FRENCH Tri 3A"


def _h_hta(**kw) -> TriageResult:
    """Hypertension artérielle."""
    pas, det, gcs = kw["pas"], kw["det"], kw["gcs"]
    if pas > 220 or det.get("encephalopathie") or gcs < 15:
        return "2", f"Urgence hypertensive — PAS {pas:.0f} mmHg", "FRENCH Tri 2"
    if pas > 180 or det.get("symptomes"):
        return "3A", f"HTA sévère symptomatique — PAS {pas:.0f} mmHg", "FRENCH Tri 3A"
    return "4", f"HTA — PAS {pas:.0f} mmHg — Évaluation", "FRENCH Tri 4"


def _h_abdomen(**kw) -> TriageResult:
    """Douleur abdominale."""
    det, fc, pas, temp = kw["det"], kw["fc"], kw["pas"], kw["temp"]
    eva = int(det.get("eva") or 0)
    if det.get("defense") or det.get("contracture") or pas < 100 or fc > 120:
        return "2", "Abdomen chirurgical suspecté — Défense / Instabilité", "FRENCH Tri 2"
    if eva >= 7 or det.get("irradiation_dorsale"):
        return "2", f"Douleur abdominale sévère EVA {eva}", "FRENCH Tri 2"
    if temp >= 38.5 and fc > 100:
        return "3A", "Douleur abdominale fébrile — Sepsis abdominal suspecté", "FRENCH Tri 3A"
    if eva >= 4:
        return "3B", f"Douleur abdominale modérée EVA {eva}", "FRENCH Tri 3B"
    return "4", "Douleur abdominale légère", "FRENCH Tri 4"


def _h_colique(**kw) -> TriageResult:
    """Colique néphrétique / douleur lombaire."""
    det, temp = kw["det"], kw["temp"]
    eva = int(det.get("eva") or 0)
    if temp >= 38.0 and det.get("douleur_lombaire"):
        return "2", "Colique fébrile — Pyélonéphrite obstructive à exclure", "FRENCH Tri 2"
    if eva >= 7:
        return "3A", f"Colique sévère EVA {eva}", "FRENCH Tri 3A"
    if eva >= 4:
        return "3B", f"Colique modérée EVA {eva}", "FRENCH Tri 3B"
    return "4", "Colique légère", "FRENCH Tri 4"


def _h_fievre(**kw) -> TriageResult:
    """Fièvre."""
    temp, det, age, gcs = kw["temp"], kw["det"], kw["age"], kw["gcs"]
    if det.get("purpura") or det.get("raideur_nuque"):
        return "1", "Fièvre + purpura/méningisme — Méningite suspecté — Ceftriaxone IMMÉDIAT", "FRENCH Tri 1"
    if temp >= 40.0 or gcs < 15:
        return "2", f"Fièvre élevée {temp:.1f}°C avec signe de gravité", "FRENCH Tri 2"
    if temp >= 39.0 or (age < 3/12 and temp >= 38.0):
        return "3A", f"Fièvre {temp:.1f}°C — Évaluation rapide", "FRENCH Tri 3A"
    if temp >= 38.0:
        return "4", f"Fièvre {temp:.1f}°C — Évaluation", "FRENCH Tri 4"
    return "4", "Fièvre légère", "FRENCH Tri 4"


def _h_hemorragie(**kw) -> TriageResult:
    """Hémorragie active."""
    det, pas, fc = kw["det"], kw["pas"], kw["fc"]
    si_val = fc / pas if pas > 0 else 2.0
    if si_val >= 1.0 or pas < 90 or det.get("abondante"):
        return "1", f"Hémorragie active avec instabilité — SI {si_val:.1f}", "FRENCH Tri 1"
    if det.get("active"):
        return "2", "Hémorragie active — Contrôle hémorragique urgent", "FRENCH Tri 2"
    return "3A", "Hémorragie contrôlée — Évaluation", "FRENCH Tri 3A"


def _h_trauma_axial(**kw) -> TriageResult:
    """Traumatisme thorax/abdomen/rachis cervical ou bassin."""
    det, pas, fc, spo2 = kw["det"], kw["pas"], kw["fc"], kw["spo2"]
    if pas < 90 or fc > 130 or spo2 < 94:
        return "1", "Traumatisme axial avec instabilité — Déchocage", "FRENCH Tri 1"
    if det.get("haute_energie") or det.get("sangle"):
        return "2", "Traumatisme haute énergie — Bilan corps entier", "FRENCH Tri 2"
    return "3A", "Traumatisme axial — Évaluation lésionnelle", "FRENCH Tri 3A"


def _h_trauma_distal(**kw) -> TriageResult:
    """Traumatisme membre / épaule."""
    det = kw["det"]
    eva = int(det.get("eva") or 0)
    if det.get("amputation") or det.get("vasculaire") or det.get("ouvert"):
        return "1", "Traumatisme membre — Lésion vasculaire / Amputation", "FRENCH Tri 1"
    if det.get("deformation") or det.get("impotence_complete") or eva >= 7:
        return "3A", "Fracture probable — Immobilisation urgente", "FRENCH Tri 3A"
    return "4", "Traumatisme distal — Évaluation clinique", "FRENCH Tri 4"


def _h_hypoglycemie(**kw) -> TriageResult:
    """Hypoglycémie."""
    gl, gcs, det = kw.get("gl"), kw["gcs"], kw["det"]
    if gl is not None:
        if gl < GLYC["hs"] or gcs < 13:
            return "1", f"Hypoglycémie sévère {gl:.0f} mg/dl — GCS {gcs} — Glucose IV IMMÉDIAT", "FRENCH Tri 1"
        if gl < GLYC["hm"]:
            return "2", f"Hypoglycémie {gl:.0f} mg/dl — Correction urgente", "FRENCH Tri 2"
    if gcs < 15:
        return "2", "Hypoglycémie suspecté — Conscience altérée", "FRENCH Tri 2"
    return "3A", "Hypoglycémie légère — Correction per os / IV", "FRENCH Tri 3A"


def _h_hyperglycemie(**kw) -> TriageResult:
    """Hyperglycémie / Cétoacidose."""
    gl, det, fc, pas = kw.get("gl"), kw["det"], kw["fc"], kw["pas"]
    if gl is not None and gl > GLYC["Hs2"]:
        return "2", f"Hyperglycémie sévère {gl:.0f} mg/dl — Cétoacidose / coma hyperosm.", "FRENCH Tri 2"
    if det.get("cetoacidose") or det.get("vomissements_diabete"):
        return "2", "Cétoacidose probable — Bilan urgent", "FRENCH Tri 2"
    if gl is not None and gl > GLYC["Hs"]:
        return "3A", f"Hyperglycémie {gl:.0f} mg/dl — Évaluation", "FRENCH Tri 3A"
    return "4", "Hyperglycémie modérée", "FRENCH Tri 4"


def _h_purpura(**kw) -> TriageResult:
    """Pétéchie / Purpura."""
    det, temp = kw["det"], kw["temp"]
    if det.get("non_effacable") or det.get("purpura"):
        return "1", "Purpura non effaçable — Ceftriaxone IMMÉDIAT — Tri 1", "FRENCH Tri 1"
    if temp >= 38.5:
        return "2", "Fièvre + pétéchies — Purpura fulminans à exclure", "FRENCH Tri 2"
    return "3A", "Pétéchies — Évaluation hématologique", "FRENCH Tri 3A"


def _h_anaphylaxie(**kw) -> TriageResult:
    """Allergie / Anaphylaxie."""
    det, spo2, pas, fc = kw["det"], kw["spo2"], kw["pas"], kw["fc"]
    if det.get("dyspnee") or pas < 90 or spo2 < 94 or det.get("mauvaise_tolerance"):
        return "1", "Anaphylaxie sévère — Adrénaline IM IMMÉDIAT", "FRENCH Tri 1"
    if det.get("urticaire_generalisee") or fc > 110:
        return "2", "Réaction allergique sévère — Surveillance continue", "FRENCH Tri 2"
    return "4", "Réaction allergique légère", "FRENCH Tri 4"


def _h_cephalee(**kw) -> TriageResult:
    """Céphalée."""
    det, temp, gcs = kw["det"], kw["temp"], kw["gcs"]
    if det.get("brutal") or det.get("explosif") or det.get("raideur_nuque"):
        return "1", "Céphalée en coup de tonnerre / méningisme — HSA suspecté", "FRENCH Tri 1"
    if temp >= 38.5 and det.get("raideur_nuque"):
        return "1", "Céphalée + raideur nuque + fièvre — Méningite", "FRENCH Tri 1"
    if gcs < 15 or det.get("neurologique"):
        return "2", "Céphalée avec signes neurologiques", "FRENCH Tri 2"
    if det.get("eva_eleve") or det.get("brutale"):
        return "3A", "Céphalée intense — Évaluation rapide", "FRENCH Tri 3A"
    return "3B", "Céphalée modérée", "FRENCH Tri 3B"


def _h_convulsions(**kw) -> TriageResult:
    """Convulsions / EME."""
    det, gcs, temp, age = kw["det"], kw["gcs"], kw["temp"], kw["age"]
    if det.get("en_cours") or det.get("eme_etabli"):
        return "1", "Convulsions en cours / EME — Anticonvulsivant IMMÉDIAT", "FRENCH Tri 1"
    if gcs < 13:
        return "2", f"Post-critique — GCS {gcs}/15", "FRENCH Tri 2"
    if det.get("premiere_crise") or temp >= 38.5:
        return "2", "Première crise / crise fébrile — Bilan étiologique urgent", "FRENCH Tri 2"
    return "3A", "Crise épileptique résolue — Évaluation neurologique", "FRENCH Tri 3A"


def _h_psychiatrie(**kw) -> TriageResult:
    """Trouble psychiatrique."""
    det, gcs = kw["det"], kw["gcs"]
    if det.get("agitation_severe") or det.get("violence") or gcs < 15:
        return "2", "Agitation psychiatrique sévère — Sécurisation", "FRENCH Tri 2"
    if det.get("suicidaire") or det.get("idees_suicidaires"):
        return "2", "Idées suicidaires actives — Évaluation psychiatrique urgente", "FRENCH Tri 2"
    return "3B", "Trouble psychiatrique — Évaluation", "FRENCH Tri 3B"


def _h_ped_fievre_nourr(**kw) -> TriageResult:
    """Fièvre nourrisson ≤ 3 mois."""
    temp, age = kw["temp"], kw["age"]
    if temp >= 38.0 and age <= 3/12:
        return "1", f"Fièvre {temp:.1f}°C nourrisson ≤ 3 mois — Bilan sepsis IMMÉDIAT", "FRENCH Tri 1"
    return "2", "Nourrisson fébrile ≤ 3 mois — Évaluation urgente", "FRENCH Tri 2"


def _h_ped_fievre(**kw) -> TriageResult:
    """Fièvre enfant 3 mois — 15 ans."""
    temp, fc, det, age = kw["temp"], kw["fc"], kw["det"], kw["age"]
    if temp >= 40.0 or det.get("somnolence") or det.get("purpura"):
        return "2", f"Fièvre élevée {temp:.1f}°C enfant — Signe de gravité", "FRENCH Tri 2"
    if fc > 150 or det.get("mauvaise_tolerance"):
        return "3A", f"Fièvre {temp:.1f}°C enfant — Mauvaise tolérance", "FRENCH Tri 3A"
    return "4", f"Fièvre {temp:.1f}°C enfant — Bonne tolérance", "FRENCH Tri 4"


def _h_ped_gastro(**kw) -> TriageResult:
    """Pédiatrie — Vomissements / Gastro-entérite."""
    det, age = kw["det"], kw["age"]
    if age < 3/12 or det.get("deshydratation_severe"):
        return "2", "Nourrisson / déshydratation sévère — Hydratation urgente", "FRENCH Tri 2"
    if age < 2 or det.get("occlusion") or det.get("sang"):
        return "3A", "Gastro-entérite pédiatrique avec signe de gravité", "FRENCH Tri 3A"
    return "4", "Gastro-entérite pédiatrique — Surveillance", "FRENCH Tri 4"


def _h_ped_epilepsie(**kw) -> TriageResult:
    """Pédiatrie — Crise épileptique."""
    det, gcs = kw["det"], kw["gcs"]
    if det.get("en_cours") or det.get("eme_etabli"):
        return "1", "Crise pédiatrique en cours — Anticonvulsivant IMMÉDIAT", "FRENCH Tri 1"
    if gcs < 13:
        return "2", f"Post-critique pédiatrique — GCS {gcs}/15", "FRENCH Tri 2"
    return "2", "Crise pédiatrique résolue — Évaluation", "FRENCH Tri 2"


def _h_ped_asthme(**kw) -> TriageResult:
    """Pédiatrie — Asthme / Bronchospasme."""
    spo2, fr, det = kw["spo2"], kw["fr"], kw["det"]
    if spo2 < 90 or det.get("silencieux"):
        return "1", "Asthme pédiatrique sévère / silencieux — Tri 1", "FRENCH Tri 1"
    if spo2 < 94 or fr > 30:
        return "2", f"Asthme pédiatrique — SpO2 {spo2:.0f}%", "FRENCH Tri 2"
    return "3A", "Asthme pédiatrique modéré — Salbutamol", "FRENCH Tri 3A"


def _h_malaise(**kw) -> TriageResult:
    """Malaise / Syncope."""
    det, gcs, pas, fc = kw["det"], kw["gcs"], kw["pas"], kw["fc"]
    if gcs < 13 or det.get("prolonge") or pas < 90:
        return "2", "Malaise avec instabilité / conscience altérée", "FRENCH Tri 2"
    if det.get("syncope") or fc > 130 or fc < 45:
        return "3A", "Syncope — ECG urgent — Bilan étiologique", "FRENCH Tri 3A"
    return "3B", "Malaise résolu — Évaluation", "FRENCH Tri 3B"


def _h_brulure(**kw) -> TriageResult:
    """Brûlure."""
    det = kw["det"]
    surface = det.get("surface_pct", 0) or 0
    if det.get("voies_aeriennes") or surface > 25:
        return "1", f"Brûlure grave — Surface {surface}% / Voies aériennes", "FRENCH Tri 1"
    if surface > 15 or det.get("troisieme_degre"):
        return "2", f"Brûlure étendue {surface}%", "FRENCH Tri 2"
    if surface > 5 or det.get("main") or det.get("visage"):
        return "3A", f"Brûlure localisée zone fonctionnelle", "FRENCH Tri 3A"
    return "4", "Brûlure mineure", "FRENCH Tri 4"


def _h_epistaxis(**kw) -> TriageResult:
    """Épistaxis."""
    det, pas = kw["det"], kw["pas"]
    if pas < 90 or det.get("abondant_actif") and det.get("anticoagulants"):
        return "2", "Épistaxis sévère — Instabilité / anticoagulés", "FRENCH Tri 2"
    if det.get("abondant_actif"):
        return "2", "Épistaxis abondant actif", "FRENCH Tri 2"
    if det.get("abondant_resolutif"):
        return "3B", "Épistaxis abondant résolutif", "FRENCH Tri 3B"
    return "5", "Épistaxis peu abondant", "FRENCH Tri 5"


def _h_non_urgent(**kw) -> TriageResult:
    """Motif non urgent / administratif."""
    return "5", "Motif non urgent — Réorientation possible", "FRENCH Tri 5"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DE DISPATCH (lookup O(1) normalisé)
# ═══════════════════════════════════════════════════════════════════════════════

_TRIAGE_DISPATCH: Dict[str, Handler] = {
    "arret cardiorespiratoire":                      _h_acr,
    "douleur thoracique / sca":                      _h_thoracique,
    "douleur thoracique / syndrome coronaire aigu (sca)": _h_thoracique,
    "douleur thoracique":                            _h_thoracique,
    "dyspnee / insuffisance respiratoire":           _h_dyspnee,
    "dyspnee / insuffisance cardiaque":              _h_dyspnee,
    "asthme ou aggravation bpco":                    _h_dyspnee,
    "asthme / aggravation bpco":                     _h_dyspnee,
    "hemoptysie":                                    _h_dyspnee,
    "avc / deficit neurologique":                    _h_avc,
    "deficit moteur sensitif sensoriel ou du langage / avc": _h_avc,
    "alteration de la conscience / coma":            _h_conscience,
    "alteration de conscience / coma":               _h_conscience,
    "traumatisme cranien":                           _h_tc,
    "hypotension arterielle":                        _h_hypotension,
    "tachycardie / tachyarythmie":                   _h_tachycardie,
    "bradycardie / bradyarythmie":                   _h_bradycardie,
    "hypertension arterielle":                       _h_hta,
    "palpitations":                                  _h_tachycardie,
    "allergie / anaphylaxie":                        _h_anaphylaxie,
    "douleur abdominale":                            _h_abdomen,
    "colique nephretique / douleur lombaire":        _h_colique,
    "vomissements / diarrhee":                       _h_abdomen,
    "hematemese / vomissements sanglants":           _h_hemorragie,
    "rectorragie / melena":                          _h_hemorragie,
    "fievre":                                        _h_fievre,
    "hemorragie active":                             _h_hemorragie,
    "traumatisme thorax/abdomen/rachis cervical":    _h_trauma_axial,
    "traumatisme bassin/hanche/femur":               _h_trauma_axial,
    "traumatisme membre / epaule":                   _h_trauma_distal,
    "hypoglycemie":                                  _h_hypoglycemie,
    "hyperglycemie / cetoacidose":                   _h_hyperglycemie,
    "hyperglycemie":                                 _h_hyperglycemie,
    "petechie / purpura":                            _h_purpura,
    "cephalee":                                      _h_cephalee,
    "convulsions / eme":                             _h_convulsions,
    "convulsions":                                   _h_convulsions,
    "syndrome confusionnel":                         _h_conscience,
    "malaise":                                       _h_malaise,
    "brulure":                                       _h_brulure,
    "epistaxis":                                     _h_epistaxis,
    "troubles psychiatriques":                       _h_psychiatrie,
    "idee / comportement suicidaire":                _h_psychiatrie,
    "pediatrie - fievre <= 3 mois":                  _h_ped_fievre_nourr,
    "pediatrie - fievre enfant (3 mois - 15 ans)":   _h_ped_fievre,
    "pediatrie - vomissements / gastro-enterite":    _h_ped_gastro,
    "pediatrie - crise epileptique":                 _h_ped_epilepsie,
    "pediatrie - asthme / bronchospasme":            _h_ped_asthme,
    "renouvellement ordonnance":                     _h_non_urgent,
    "examen administratif":                          _h_non_urgent,
    "autre motif":                                   _h_non_urgent,
}

_MOTIF_INDEX: Dict[str, Handler] = {_norm(k): v for k, v in _TRIAGE_DISPATCH.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR PRINCIPAL DE TRIAGE
# ═══════════════════════════════════════════════════════════════════════════════

def french_triage(
    motif: str,
    det: Optional[dict],
    fc: Optional[float]   = None,
    pas: Optional[float]  = None,
    spo2: Optional[float] = None,
    fr: Optional[float]   = None,
    gcs: Optional[int]    = None,
    temp: Optional[float] = None,
    age: Optional[float]  = None,
    n2: Optional[int]     = None,
    gl: Optional[float]   = None,
) -> TriageResult:
    """
    Moteur FRENCH V1.1 — Système Expert à 4 niveaux de décision.

    Hiérarchie :
      0. NEWS2 ≥ 9 → Tri M (absolu)
      1. Priorités absolues (verrouillage clinique)
      2. Arbre de décision du handler motif
      3. Ajustement NEWS2 (jamais downgrade)
      4. Fallback sécurisé Tri 3B

    Source : SFMU — Classification FRENCH Triage V1.1, 2018.
    """
    # Valeurs par défaut sécurisées
    fc   = float(fc   or 80)
    pas  = float(pas  or 120)
    spo2 = float(spo2 or 98)
    fr   = float(fr   or 16)
    gcs  = int(gcs    or 15)
    temp = float(temp or 37.0)
    age  = float(age  or 45)
    n2   = int(n2     or 0)
    det  = det or {}

    try:
        # ── Niveau 0 : NEWS2 ≥ 9 → Tri M absolu ──────────────────────────
        if n2 >= NEWS2_TRI_M:
            return "M", f"NEWS2 {n2} ≥ {NEWS2_TRI_M} — Engagement vital immédiat", "NEWS2 Tri M"

        # ── Niveau 1 : Priorités absolues verrouillées ────────────────────
        priorite = _check_priorites_absolues(det, gcs, pas, spo2, fr)
        if priorite:
            return priorite

        # ── Niveau 2 : Arbre de décision motif ───────────────────────────
        handler = _MOTIF_INDEX.get(_norm(motif))
        if handler is not None:
            result = handler(
                fc=fc, pas=pas, spo2=spo2, fr=fr,
                gcs=gcs, temp=temp, age=age, n2=n2,
                gl=gl, det=det, motif=motif,
            )
        else:
            result = ("3B", f"Évaluation standard — {motif}", "FRENCH Tri 3B")

        # ── Niveau 3 : Ajustement NEWS2 (jamais downgrade) ───────────────
        if n2 >= NEWS2_RISQUE_ELEVE:
            result = _more_urgent(result, ("2", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_ELEVE} — Risque élevé", "NEWS2"))
        elif n2 >= NEWS2_RISQUE_MOD:
            result = _more_urgent(result, ("3A", f"NEWS2 {n2} ≥ {NEWS2_RISQUE_MOD} — Risque modéré", "NEWS2"))

        return result

    except Exception as e:
        # Failsafe : ne jamais laisser planter — triage conservateur Tri 2
        return "2", f"Erreur moteur triage — Évaluation médicale urgente ({e})", "Sécurité Tri 2"


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTES CLINIQUES TRANSVERSALES
# ═══════════════════════════════════════════════════════════════════════════════

def verifier_coherence(
    fc: float, pas: float, spo2: float, fr: float,
    gcs: int, temp: float, eva: int,
    motif: str, atcd: list, det: dict,
    n2: int, gl: Optional[float] = None,
) -> Tuple[List[str], List[str]]:
    """
    Alertes transversales post-triage.
    Retourne (alertes_danger, alertes_warning).
    Source : SFMU / BCFI — Critères de vigilance IAO.
    """
    danger: List[str]  = []
    warning: List[str] = []

    try:
        # ── Shock Index ────────────────────────────────────────────────────
        si_val = fc / pas if pas > 0 else 0
        if si_val >= 1.5:
            danger.append(f"🔴 Shock Index {si_val:.2f} ≥ 1.5 — Choc décompensé")
        elif si_val >= 1.0:
            warning.append(f"🟠 Shock Index {si_val:.2f} ≥ 1.0 — Instabilité hémodynamique")

        # ── Triade létale trauma ───────────────────────────────────────────
        if "trauma" in _norm(motif):
            if temp < 36.0 and si_val >= 1.0 and det.get("anticoagulants"):
                danger.append("🔴 Triade létale suspecte : hypothermie + choc + anticoagulants")

        # ── Hypoglycémie ───────────────────────────────────────────────────
        if gl is not None:
            if gl < 54:
                danger.append(f"🔴 Hypoglycémie sévère {gl:.0f} mg/dl ({gl/18.016:.1f} mmol/l) — Glucose IV IMMÉDIAT")
            elif gl < 70:
                warning.append(f"🟠 Hypoglycémie modérée {gl:.0f} mg/dl — Correction urgente")
            elif gl > 360:
                danger.append(f"🔴 Hyperglycémie sévère {gl:.0f} mg/dl — Cétoacidose à exclure")
            elif gl > 180:
                warning.append(f"🟠 Hyperglycémie {gl:.0f} mg/dl — Bilan")

        # ── Douleur non traitée ────────────────────────────────────────────
        if eva >= 8:
            danger.append(f"🔴 EVA {eva}/10 — Douleur sévère non contrôlée — Antalgie urgente")
        elif eva >= 5:
            warning.append(f"🟠 EVA {eva}/10 — Antalgie à initier")

        # ── Sepsis (critères croisés) ──────────────────────────────────────
        q_criteria = sum([fr >= 22, gcs < 15, pas <= 100])
        if q_criteria >= 2 and temp >= 38.0:
            danger.append("🔴 qSOFA ≥ 2 + fièvre — SEPSIS SUSPECTÉ — Bundle 1h")

        # ── Alertes ATCD critiques ─────────────────────────────────────────
        atcd_norm = {_norm(a) for a in (atcd or [])}
        if "anticoagulants/aod" in atcd_norm and eva >= 5:
            warning.append("🟠 Anticoagulants + douleur — Risque hémorragique à évaluer")
        if "immunodepression" in atcd_norm or "chimiotherapie en cours" in atcd_norm:
            if temp >= 38.3:
                danger.append("🔴 Immunodéprimé + fièvre ≥ 38.3°C — Aplasie fébrile à exclure")
        if "grossesse" in atcd_norm:
            if pas > 160:
                danger.append("🔴 HTA sévère chez femme enceinte — Pré-éclampsie")
            if pas < 90:
                danger.append("🔴 Hypotension chez femme enceinte — Urgence obstétricale")
        if "beta-bloquants" in atcd_norm and fc > 90:
            warning.append("🟠 Bêtabloquants : tachycardie relative masquée — FC peut être sous-estimée")

    except Exception as e:
        warning.append(f"Erreur vérification cohérence : {e}")

    return danger, warning


def french_triage(
    motif: str,
    det: Optional[dict],
    fc: Optional[float] = None,
    pas: Optional[float] = None,
    spo2: Optional[float] = None,
    fr: Optional[float] = None,
    gcs: Optional[int] = None,
    temp: Optional[float] = None,
    age: Optional[float] = None,
    n2: Optional[int] = None,
    gl: Optional[float] = None,
) -> TriageResult:
    """
    Moteur FRENCH V1.2 central.
    Les discriminants viennent de clinical/french_v12.py, les indices vitaux de clinical/vitaux.py.
    """
    fc = float(fc or 80)
    pas = float(pas or 120)
    spo2 = float(spo2 or 98)
    fr = float(fr or 16)
    gcs = int(gcs or 15)
    temp = float(temp or 37.0)
    age = float(age or 45)
    n2 = int(n2 or 0)
    det = det or {}

    try:
        if n2 >= NEWS2_TRI_M:
            return "M", f"NEWS2 {n2} â‰¥ {NEWS2_TRI_M} â€” Engagement vital immÃ©diat", "NEWS2 Tri M"

        priorite = _check_priorites_absolues(det, gcs, pas, spo2, fr)
        if priorite:
            return priorite

        result = _protocol_default_result(motif)

        discriminant = _selected_discriminant_result(motif, det)
        if discriminant:
            result = _more_urgent(result, discriminant)

        red_flag_result = _selected_red_flag_result(motif, det)
        if red_flag_result:
            result = _more_urgent(result, red_flag_result)

        protocol = get_protocol(motif)
        handler_key = protocol.get("motif") if protocol else motif
        handler = _MOTIF_INDEX.get(_norm(handler_key)) or _MOTIF_INDEX.get(_norm(motif))
        if handler is not None:
            handler_result = handler(
                fc=fc, pas=pas, spo2=spo2, fr=fr,
                gcs=gcs, temp=temp, age=age, n2=n2,
                gl=gl, det=det, motif=motif,
            )
            result = _more_urgent(result, handler_result)

        terrain_result = _terrain_adjustment(motif, det, age, temp, pas, gcs)
        if terrain_result:
            result = _more_urgent(result, terrain_result)

        sidebar_result = _sidebar_risk_adjustment(motif, det, temp, pas)
        if sidebar_result:
            result = _more_urgent(result, sidebar_result)

        vital_result = _vital_adjustment(fc, pas, spo2, fr, gcs, age)
        if vital_result:
            result = _more_urgent(result, vital_result)

        if n2 >= NEWS2_RISQUE_ELEVE:
            result = _more_urgent(result, ("2", f"NEWS2 {n2} â‰¥ {NEWS2_RISQUE_ELEVE} â€” Risque Ã©levÃ©", "NEWS2"))
        elif n2 >= NEWS2_RISQUE_MOD:
            result = _more_urgent(result, ("3A", f"NEWS2 {n2} â‰¥ {NEWS2_RISQUE_MOD} â€” Risque modÃ©rÃ©", "NEWS2"))

        return result

    except Exception as e:
        return "2", f"Erreur moteur triage V1.2 â€” Ã‰valuation mÃ©dicale urgente ({e})", "SÃ©curitÃ© Tri 2"
