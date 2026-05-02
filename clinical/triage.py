# clinical/triage.py — Moteur de triage FRENCH V1.1 — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Référence : SFMU — Classification FRENCH Triage V1.1, 2018
# Hiérarchie : NEWS2 absolu → Priorités cliniques → Handler motif → Ajustement NEWS2

from __future__ import annotations
import unicodedata
from typing import Callable, Dict, Optional, Tuple, List
from config import (
    NEWS2_TRI_M, NEWS2_RISQUE_ELEVE, NEWS2_RISQUE_MOD,
    GLYC, AVC_DELAI_THROMBOLYSE_H,
)

TriageResult = Tuple[str, str, str]
Handler = Callable[..., TriageResult]


def _norm(value: str) -> str:
    """Normalise une chaîne pour comparaison insensible aux accents."""
    value = str(value or "").replace("≤", "<=").replace("≥", ">=").replace("/", " / ")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def _more_urgent(r1: TriageResult, r2: TriageResult) -> TriageResult:
    """Retourne le niveau le plus urgent entre deux résultats de triage."""
    ordre = {"M": 0, "1": 1, "2": 2, "3A": 3, "3B": 4, "4": 5, "5": 6}
    return r1 if ordre.get(r1[0], 9) <= ordre.get(r2[0], 9) else r2


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
    """Douleur thoracique / SCA — Discriminants ECG + douleur + FRCV.
    Source : SFMU FRENCH V1.1 / ESC 2023.
    """
    det, pas, fc, spo2, gcs = kw["det"], kw["pas"], kw["fc"], kw["spo2"], kw["gcs"]
    ecg  = det.get("ecg", "Normal")
    doul = det.get("douleur", "Atypique")
    frcv = int(det.get("frcv") or 0)
    if ecg == "Anormal typique SCA":
        return "1", "ECG typique SCA — Tri 1 immédiat", "FRENCH Tri 1"
    if det.get("syncopal") or pas < 90 or gcs < 15:
        return "1", "Douleur thoracique avec instabilité hémodynamique", "FRENCH Tri 1"
    if ecg == "Anormal non typique" and doul in ("Typique (constrictive, irradiante)", "Coronaire probable"):
        return "2", "ECG anormal + douleur typique/coronaire", "FRENCH Tri 2"
    if doul == "Typique (constrictive, irradiante)" or fc > 120 or spo2 < 94:
        return "2", "Douleur thoracique typique / instabilité relative", "FRENCH Tri 2"
    if ecg == "Normal" and frcv >= 1:
        return "3A", "ECG normal avec comorbidité coronaire", "FRENCH Tri 3A"
    if doul == "Coronaire probable":
        return "3B", "Douleur de type coronaire — ECG normal", "FRENCH Tri 3B"
    return "4", "ECG normal et douleur atypique — Évaluation", "FRENCH Tri 4"


def _h_dyspnee(**kw) -> TriageResult:
    """Dyspnée / insuffisance respiratoire — Discriminants FRENCH.
    Source : SFMU FRENCH V1.1.
    """
    spo2, fr, det = kw["spo2"], kw["fr"], kw["det"]
    # Tri 1 : Détresse respiratoire majeure
    if spo2 < 86 or fr >= 40 or det.get("cyanose") or det.get("detresse"):
        return "1", f"Détresse respiratoire — SpO2 {spo2:.0f}% / FR {fr:.0f}/min", "FRENCH Tri 1"
    # Tri 2 : Dyspnée sévère
    if spo2 <= 90 or fr >= 30 or not det.get("parole", True):
        return "2", f"Dyspnée sévère — SpO2 {spo2:.0f}% / FR {fr:.0f}/min", "FRENCH Tri 2"
    if det.get("tirage") or det.get("orth") or det.get("orthopnee"):
        return "2", "Tirage / orthopnée — Dyspnée sévère", "FRENCH Tri 2"
    # Tri 3A/3B
    if spo2 < 94 or fr > 22:
        return "3A", f"Dyspnée modérée — SpO2 {spo2:.0f}%", "FRENCH Tri 3A"
    return "3B", "Dyspnée légère — Évaluation", "FRENCH Tri 3B"


def _h_avc(**kw) -> TriageResult:
    """AVC / Déficit neurologique — Délai thrombolyse + sévérité.
    Source : ESO 2023 / SFMU FRENCH V1.1.
    """
    det, gcs, pas = kw["det"], kw["gcs"], kw["pas"]
    delai = float(det.get("delai") or 99)
    # Tri 1 : Sévérité ou instabilité majeure
    if gcs < 13 or pas > 220 or det.get("hemiplegique"):
        return "1", f"AVC sévère — GCS {gcs}/15", "FRENCH Tri 1"
    # Tri 2 : Fenêtre thrombolyse
    if delai <= AVC_DELAI_THROMBOLYSE_H:
        return "2", f"AVC — délai {delai:.1f}h ≤ 4,5h — FENÊTRE THROMBOLYSE", "ESO 2023"
    if det.get("def_prog"):
        return "2", "Déficit neurologique progressif", "FRENCH Tri 2"
    if det.get("fast_positif") or det.get("avc_suspect"):
        return "2", "Code Stroke — BE-FAST positif — Imagerie URGENTE", "FRENCH Tri 2"
    if delai >= 24:
        return "4", f"AVC > 24 h — avis MAO/MCO", "FRENCH Tri 4"
    return "3A", "AVC > 4,5 h — bilan urgent", "FRENCH Tri 3A"


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
    if fc >= 130:
        return "2", f"Tachycardie sévère — FC {fc:.0f}", "FRENCH Tri 2"
    if fc > 110:
        return "3A", f"Tachycardie — FC {fc:.0f} — Évaluation ECG urgente", "FRENCH Tri 3A"
    return "3B", "Tachycardie résolutive ou sans signe de gravité", "FRENCH Tri 3B"


def _h_bradycardie(**kw) -> TriageResult:
    """Bradycardie / bradyarythmie."""
    fc, pas, det = kw["fc"], kw["pas"], kw["det"]
    if fc <= 40 or pas < 90 or det.get("syncope"):
        return "1", f"Bradycardie instable — FC {fc:.0f}", "FRENCH Tri 1"
    if fc < 50 and det.get("mauvaise_tolerance"):
        return "2", f"Bradycardie mal tolérée — FC {fc:.0f}", "FRENCH Tri 2"
    if fc < 50:
        return "3A", f"Bradycardie — FC {fc:.0f} — ECG urgent", "FRENCH Tri 3A"
    return "3B", "Bradycardie résolutive ou sans signe de gravité", "FRENCH Tri 3B"


def _h_palpitations(**kw) -> TriageResult:
    """Palpitations."""
    fc, det = kw["fc"], kw["det"]
    if det.get("syncope") or det.get("malaise") or fc >= 130:
        return "2", "Palpitations avec malaise / fréquence très élevée", "FRENCH Tri 2"
    if fc > 110:
        return "3A", f"Palpitations avec FC {fc:.0f} bpm", "FRENCH Tri 3A"
    return "4", "Palpitations isolées", "FRENCH Tri 4"


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



# ── Seuils FC pédiatriques par tranche d'âge (AAP / SFNP) ────────────────────
_FC_TACHY_NOURR  = 160   # < 1 mois
_FC_TACHY_BEBE   = 150   # 1-12 mois
_FC_TACHY_ENFANT = 140   # 1-5 ans
_FC_TACHY_GRAND  = 120   # > 5 ans
_VOMISS_FREQ_SEVERE = 6  # vomissements/heure — seuil d'alerte


def _fc_tachy_ped(fc: float, age: float) -> bool:
    """Retourne True si FC supérieure au seuil pédiatrique pour l'âge."""
    if age < 1/12:  seuil = _FC_TACHY_NOURR
    elif age < 1.0: seuil = _FC_TACHY_BEBE
    elif age < 5.0: seuil = _FC_TACHY_ENFANT
    else:           seuil = _FC_TACHY_GRAND
    return fc > seuil


def _h_ped_fievre_nourr(**kw) -> TriageResult:
    """Fièvre nourrisson ≤ 3 mois — Bilan sepsis systématique.
    Source : SFP / SFMU — Fièvre du nourrisson.
    """
    temp, age = kw["temp"], kw["age"]
    if temp >= 38.0 and age <= 3/12:
        return "1", f"Fièvre {temp:.1f}°C nourrisson ≤ 3 mois — Bilan sepsis IMMÉDIAT", "SFP/SFMU"
    return "2", "Nourrisson fébrile ≤ 3 mois — Évaluation urgente", "FRENCH Tri 2"


def _h_ped_fievre(**kw) -> TriageResult:
    """Fièvre enfant 3 mois – 15 ans — Arbre décisionnel complet.
    Source : SFMU / SFP 2017 — Critères de gravité pédiatrique.
    """
    temp, fc, det, age, spo2 = kw["temp"], kw["fc"], kw["det"], kw["age"], kw["spo2"]
    tachy = _fc_tachy_ped(fc, age)

    # ── Tri 1 : Signes vitaux critiques ─────────────────────────────────────
    if det.get("purpura") and temp >= 38.0:
        return "1", "Fièvre + purpura — Ceftriaxone 2 g IV IMMÉDIAT", "SPILF/SFP 2017"
    if det.get("convulsion_prolongee") or det.get("convulsion_focale"):
        return "1", "Convulsion fébrile prolongée ou focale", "SFNP Tri 1"

    # ── Tri 2 : Signes de gravité ────────────────────────────────────────────
    if temp >= 40.0:
        return "2", f"Fièvre {temp:.1f}°C ≥ 40°C", "FRENCH Pédiatrie"
    if det.get("nuque") or det.get("kernig"):
        return "2", "Fièvre avec signes méningés", "FRENCH Pédiatrie"
    if det.get("encephalopathie") or det.get("agitation") or det.get("somnolence"):
        return "2", "Fièvre avec encéphalopathie", "FRENCH Pédiatrie"
    if age <= 0.5 and temp >= 38.0:
        return "2", f"Fièvre nourrisson {int(age*12)} mois — bilan urgent", "SFP/SFMU"
    if tachy and det.get("mauvaise_tolerance"):
        return "2", f"Fièvre + tachycardie FC {fc:.0f} — mauvaise tolérance", "FRENCH Pédiatrie"
    if det.get("immunodepression") or det.get("cardiopathie"):
        return "2", "Fièvre — terrain à risque (immunodépression/cardiopathie)", "FRENCH Pédiatrie"

    # ── Tri 3A : Signes modérés ──────────────────────────────────────────────
    if tachy or det.get("mauvaise_tolerance"):
        return "3A", f"Fièvre {temp:.1f}°C — mauvaise tolérance", "FRENCH Tri 3A"

    # ── Tri 3B / 4 : Bien toléré ─────────────────────────────────────────────
    if temp >= 38.5:
        return "3B", f"Fièvre {temp:.1f}°C — bonne tolérance", "FRENCH Tri 3B"
    return "4", f"Fièvre {temp:.1f}°C — bonne tolérance", "FRENCH Tri 4"


def _h_ped_gastro(**kw) -> TriageResult:
    """Pédiatrie — Vomissements / Gastro-entérite — Arbre décisionnel ESPGHAN.
    Source : ESPGHAN 2014 / FRENCH Pédiatrie.
    """
    det, age, fc, pas, temp = kw["det"], kw["age"], kw["fc"], kw["pas"], kw["temp"]
    tachy = _fc_tachy_ped(fc, age)
    sh = fc / max(1.0, pas)

    # ── Tri 1 : Urgences chirurgicales / choc ────────────────────────────────
    if det.get("bilieux"):
        return "1", "Vomissements bilieux — occlusion à exclure", "FRENCH Pédiatrie"
    if det.get("fontanelle_bombante"):
        return "1", "Fontanelle bombante — HTIC", "FRENCH Pédiatrie"
    if det.get("pleurs_inconsolables"):
        return "1", "Pleurs inconsolables — invagination intestinale", "FRENCH Pédiatrie"
    if det.get("convulsions"):
        return "1", "Vomissements + convulsions", "FRENCH Pédiatrie"
    if sh >= 1.0 or pas < 90 or det.get("deshydrat_severe"):
        return "1", f"Choc hypovolémique — SI {sh:.2f}", "FRENCH Pédiatrie"

    # ── Tri 2 : Déshydratation modérée / signes de gravité ──────────────────
    if det.get("deshydrat_moderee"):
        return "2", "Déshydratation modérée — réhydratation urgente", "ESPGHAN 2014"
    if age < 0.25 and temp >= 38.0:
        return "2", f"Nourrisson {int(age*12)} mois — vomissements + fièvre", "FRENCH Pédiatrie"
    if tachy and temp >= 38.5:
        return "2", f"Tachycardie FC {fc:.0f} + fièvre {temp:.1f}°C", "FRENCH Pédiatrie"
    if (det.get("vomiss_freq") or 0) >= _VOMISS_FREQ_SEVERE:
        return "2", f"Vomissements ≥ {_VOMISS_FREQ_SEVERE}/h", "FRENCH Pédiatrie"
    if det.get("refus_alimentation") and (tachy or det.get("deshydrat_legere")):
        return "2", "Refus alimentaire + déshydratation", "FRENCH Pédiatrie"

    # ── Tri 3A / 3B ───────────────────────────────────────────────────────────
    if det.get("deshydrat_legere") or tachy:
        return "3A", "Déshydratation légère", "ESPGHAN 2014"
    if age < 2 or det.get("sang"):
        return "3A", "Gastro-entérite pédiatrique avec signe de gravité", "FRENCH Pédiatrie"
    return "3B", "Gastro-entérite bien tolérée", "FRENCH Tri 3B"


def _h_ped_epilepsie(**kw) -> TriageResult:
    """Pédiatrie — Crise épileptique — Algorithme SFNP 2023 / ILAE.
    Source : SFNP 2023, ILAE 2015, ISPE 2022.
    """
    det, gcs, spo2, temp, age, gl = (
        kw["det"], kw["gcs"], kw["spo2"], kw["temp"], kw["age"],
        kw.get("gl"),
    )
    duree = float(det.get("duree_min") or 0)

    # ── Tri 1 : EME / situations critiques ───────────────────────────────────
    if det.get("eme_etabli") or duree > 30:
        return "1", f"EME établi > 30 min", "ISPE 2022"
    if duree > 15:
        return "1", f"EME opérationnel {duree:.0f} min", "ILAE 2015"
    if spo2 < 92:
        return "1", f"Crise + SpO2 {spo2:.0f}%", "FRENCH Pédiatrie"
    if age < 1/12:
        return "1", "Convulsion néonatale", "SFNP Tri 1"
    if det.get("tc_associe"):
        return "1", "Crise + TC associé", "FRENCH Tri 1"
    if det.get("signes_meninges") and temp >= 38.0:
        return "1", "Crise fébrile + signes méningés — méningite", "FRENCH Pédiatrie"
    if gl is not None and gl < 54 and det.get("conscience_incomplete"):
        return "1", f"Hypoglycémie sévère {gl:.0f} mg/dl + crise", "FRENCH Tri 1"

    # ── Tri 2 : Crise en cours / première crise / complexe ───────────────────
    if det.get("en_cours"):
        return "2", "Crise EN COURS — anticonvulsivant IMMÉDIAT", "SFNP 2023"
    if duree > 5:
        return "2", f"Crise prolongée {duree:.0f} min", "SFNP 2023"
    if det.get("premiere_crise") and "Épilepsie" not in (det.get("atcd") or []):
        return "2", "Première crise non fébrile", "FRENCH Pédiatrie"
    if det.get("focale") or det.get("repetee_24h"):
        return "2", "Crise fébrile complexe (focale ou répétée)", "SFNP 2023"
    if det.get("conscience_incomplete") or det.get("avpu") in ("V", "P", "U"):
        return "2", "Conscience altérée post-critique", "FRENCH Pédiatrie"

    # ── Tri 3A / 3B : Épilepsie connue récupérée ─────────────────────────────
    if det.get("febrile") and not det.get("focale") and det.get("recuperee"):
        return "3A", "Crise fébrile simple récupérée", "SFNP 2023"
    if "Épilepsie" in (det.get("atcd") or []) and det.get("recuperee") and det.get("habituelle"):
        return "3A", "Épilepsie connue — crise habituelle récupérée", "FRENCH Tri 3A"
    if "Épilepsie" in (det.get("atcd") or []) and det.get("recuperee") and det.get("plan_urgence"):
        return "3B", "Épilepsie connue — plan urgences personnalisé", "FRENCH Tri 3B"
    return "2", "Crise pédiatrique — évaluation urgente", "SFNP 2023"


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


def _h_accouchement(**kw) -> TriageResult:
    """Accouchement imminent."""
    return "1", "Accouchement imminent ou réalisé — Prise en charge obstétricale immédiate", "FRENCH Tri 1"


def _h_grossesse_t1t2(**kw) -> TriageResult:
    """Complication grossesse T1/T2."""
    det, pas = kw["det"], kw["pas"]
    if pas < 90 or det.get("abondante") or det.get("hemorragie"):
        return "1", "Grossesse T1/T2 avec instabilité ou hémorragie abondante", "FRENCH Tri 1"
    if det.get("grossesse") or det.get("saignement") or det.get("douleur_severe"):
        return "2", "Grossesse T1/T2 compliquée — GEU / hémorragie à exclure", "FRENCH Tri 2"
    return "3A", "Complication de grossesse T1/T2 — Évaluation prioritaire", "FRENCH Tri 3A"


def _h_metrorragie(**kw) -> TriageResult:
    """Ménorragie / Métrorragie."""
    det, pas = kw["det"], kw["pas"]
    if pas < 90 or det.get("grossesse") or det.get("abondante"):
        return "2", "Métrorragie abondante ou grossesse associée", "FRENCH Tri 2"
    if det.get("active"):
        return "3A", "Métrorragie active — Surveillance rapprochée", "FRENCH Tri 3A"
    return "3B", "Saignement gynécologique modéré", "FRENCH Tri 3B"


def _h_oeil(**kw) -> TriageResult:
    """Corps étranger / brûlure oculaire."""
    det = kw["det"]
    if det.get("brulure_chimique") or det.get("baisse_av") or det.get("douleur_severe"):
        return "2", "Brûlure chimique ou baisse visuelle brutale", "FRENCH Tri 2"
    if det.get("penetrant") or det.get("haute_energie"):
        return "3A", "Corps étranger oculaire pénétrant suspecté", "FRENCH Tri 3A"
    return "3A", "Corps étranger / brûlure oculaire — Évaluation ophtalmologique", "FRENCH Tri 3A"


def _h_intoxication(**kw) -> TriageResult:
    """Intoxication médicamenteuse."""
    det, gcs, pas, age = kw["det"], kw["gcs"], kw["pas"], kw["age"]
    if gcs < 15 or pas < 90 or det.get("intention_suicidaire") or det.get("toxique_cardiotrope"):
        return "2", "Intoxication médicamenteuse avec mauvaise tolérance ou risque suicidaire", "FRENCH Tri 2"
    if age < 18:
        return "2", "Intoxication pédiatrique — Avis urgent", "FRENCH Tri 2"
    return "3B", "Intoxication médicamenteuse bien tolérée", "FRENCH Tri 3B"


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
    "deficit moteur, sensitif, sensoriel ou du langage/avc": _h_avc,
    "alteration de la conscience / coma":            _h_conscience,
    "alteration de la conscience/coma":              _h_conscience,
    "alteration de conscience / coma":               _h_conscience,
    "traumatisme cranien":                           _h_tc,
    "hypotension arterielle":                        _h_hypotension,
    "tachycardie / tachyarythmie":                   _h_tachycardie,
    "bradycardie / bradyarythmie":                   _h_bradycardie,
    "hypertension arterielle":                       _h_hta,
    "palpitations":                                  _h_palpitations,
    "allergie / anaphylaxie":                        _h_anaphylaxie,
    "douleur abdominale":                            _h_abdomen,
    "colique nephretique / douleur lombaire":        _h_colique,
    "vomissements / diarrhee":                       _h_abdomen,
    "hematemese / rectorragie":                      _h_hemorragie,
    "hematemese / vomissements sanglants":           _h_hemorragie,
    "vomissement de sang / hematemese":              _h_hemorragie,
    "maelena/rectorragies":                          _h_hemorragie,
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
    "accouchement imminent":                         _h_accouchement,
    "accouchement imminent ou realise":              _h_accouchement,
    "complication grossesse t1/t2":                  _h_grossesse_t1t2,
    "probleme de grossesse 1er et 2eme trimestre":   _h_grossesse_t1t2,
    "menorragie / metrorragie":                      _h_metrorragie,
    "meno-metrorragie":                              _h_metrorragie,
    "corps etranger / brulure oculaire":             _h_oeil,
    "intoxication medicamenteuse":                   _h_intoxication,
    "pediatrie - fievre <= 3 mois":                  _h_ped_fievre_nourr,
    "fievre <= 3 mois":                              _h_ped_fievre_nourr,
    "fievre enfant (3 mois - 15 ans)":              _h_ped_fievre,
    "pediatrie - fievre enfant (3 mois - 15 ans)":   _h_ped_fievre,
    "pediatrie - vomissements / gastro-enterite":    _h_ped_gastro,
    "diarrhee / vomissements du nourrisson (<= 24 mois)": _h_ped_gastro,
    "pediatrie - crise epileptique":                 _h_ped_epilepsie,
    "convulsion hyperthermique":                     _h_ped_epilepsie,
    "pediatrie - asthme / bronchospasme":            _h_ped_asthme,
    "renouvellement ordonnance":                     _h_non_urgent,
    "examen administratif":                          _h_non_urgent,
    "autre motif":                                   _h_non_urgent,
}

_MOTIF_INDEX: Dict[str, Handler] = {_norm(k): v for k, v in _TRIAGE_DISPATCH.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# RÈGLE WORST-CASE SCENARIO — Majoration terrain
# ═══════════════════════════════════════════════════════════════════════════════

def _worst_case_terrain(
    motif: str, det: dict, age: float,
    fc: float, pas: float, temp: float, gcs: int,
) -> Optional[TriageResult]:
    """
    Règle "Worst-Case Scenario" — Majoration automatique selon le terrain.
    Le niveau final est TOUJOURS le plus urgent entre le motif et le terrain.
    Source : SFMU — Critères de sur-risque terrain IAO.
    """
    atcd_norm = {_norm(a) for a in (det or {}).get("atcd", [])}
    m = _norm(motif)

    # Trauma + anticoagulants → Tri 2 minimum
    is_trauma = any(t in m for t in ("trauma", "traumatisme", "fracture", "brulure", "chute"))
    has_anticoag = any(a in atcd_norm for a in (
        "anticoagulants/aod", "anticoagulants", "aod", "avk",
        "antiagrégants plaquettaires", "antiagrégants",
    ))
    if is_trauma and has_anticoag:
        return "2", "Traumatisme + anticoagulants — Risque hémorragique majeur", "Worst-Case Terrain"

    # Bêtabloquants + hypotension → tachycardie masquée, Tri 2
    has_beta = any(a in atcd_norm for a in (
        "beta-bloquants", "betabloquants", "bêta-bloquants",
        "bêtabloquants", "beta bloquants",
    ))
    if has_beta and pas < 100:
        return "2", "Bêta-bloquants + hypotension — Tachycardie réflexe masquée", "Worst-Case Terrain"

    # Immunodéprimé + fièvre → aplasie fébrile, Tri 2
    has_immuno = any(a in atcd_norm for a in (
        "immunodepression", "immunodépression",
        "chimiotherapie en cours", "chimiothérapie en cours",
    ))
    if has_immuno and temp >= 38.3:
        return "2", "Immunodéprimé + fièvre ≥ 38.3°C — Aplasie fébrile à exclure", "Worst-Case Terrain"

    # Grossesse + douleur abdominale/pelvienne → GEU, Tri 2
    has_grossesse = "grossesse" in atcd_norm
    if has_grossesse and any(t in m for t in ("abdomen", "douleur", "colique")):
        return "2", "Grossesse + douleur abdominale — GEU à exclure", "Worst-Case Terrain"

    # Nourrisson ≤ 3 mois + tout motif → Tri 1
    if age > 0 and age <= 0.25:  # 3 mois = 0.25 an
        return "1", "Nourrisson ≤ 3 mois — Tri 1 systématique (immunité immature)", "Worst-Case Terrain"

    # Gériatrie ≥ 80 ans + chute/syncope → Tri 3A minimum
    if age >= 80 and any(t in m for t in ("chute", "malaise", "syncope", "fracture")):
        return "3A", "Patient ≥ 80 ans + chute/syncope — Bilan étiologique prioritaire", "Worst-Case Terrain"

    return None


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

        # ── Niveau 4 : Worst-Case Scenario terrain (jamais downgrade) ────
        terrain = _worst_case_terrain(motif, det, age, fc, pas, temp, gcs)
        if terrain:
            result = _more_urgent(result, terrain)

        return result

    except Exception as e:
        # Failsafe : sur-triage conservateur — mieux Tri M que sous-estimer
        return "M", f"Erreur moteur triage — Évaluation médicale IMMÉDIATE ({e})", "Sécurité Tri M"


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
