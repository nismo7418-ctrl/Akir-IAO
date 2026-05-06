# clinical/discriminants.py — Questions discriminantes FRENCH v1.1
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Extrait de french_v12.py pour modularité (AKIR-IAO v20)
# Sources : SFMU FRENCH V1.1 2018 / SFP / GINA / ESC / ERC / ATLS
# Usage : from clinical.discriminants import DISCRIMINANTS_ENRICHIS

from __future__ import annotations
from typing import Dict, List, Any

try:
    import streamlit as st
except Exception:  # pragma: no cover - tolere les imports hors interface Streamlit
    st = None

# Type : {motif: [{"id","text","type","det_key","options"?,"auto"?}]}
DISCRIMINANTS_ENRICHIS: Dict[str, List[Dict[str, Any]]] = {}

# ─────────────────────────────────────────────────────────────────────────────
# DISCRIMINANTS ENRICHIS — Questions interactives par motif
# Compat. avec process_answers() dans streamlit_app.py
# Source : SFMU FRENCH V1.1 — Arbres décisionnels
# ─────────────────────────────────────────────────────────────────────────────

DISCRIMINANTS_ENRICHIS: dict = {
    "Douleur thoracique / SCA": [
        {
            "id": "sca_ecg",
            "text": "Aspect ECG",
            "type": "select",
            "options": [
                ("normal",             "Normal"),
                ("anormal_non_typique","Anormal non typique"),
                ("anormal_typique",    "Anormal typique SCA (sus-ST, Wellens…)"),
            ],
            "det_key": "ecg",
            "mapping": {
                "normal":              "Normal",
                "anormal_non_typique": "Anormal non typique",
                "anormal_typique":     "Anormal typique SCA",
            },
        },
        {
            "id": "sca_douleur",
            "text": "Caractère de la douleur",
            "type": "select",
            "options": [
                ("atypique",          "Atypique"),
                ("coronaire_probable","Coronaire probable"),
                ("typique",           "Typique (constrictive, irradiante, ≥ 20 min)"),
            ],
            "det_key": "douleur",
            "mapping": {
                "atypique":          "Atypique",
                "coronaire_probable":"Coronaire probable",
                "typique":           "Typique (constrictive, irradiante)",
            },
        },
        {
            "id": "sca_frcv",
            "text": "Comorbidité coronaire (diabète, ATCD familial, coronaropathie) ?",
            "type": "bool",
            "det_key": "frcv",
            "true_val": 1, "false_val": 0,
        },
    ],
    "AVC / Déficit neurologique": [
        {
            "id": "avc_delai",
            "text": "Délai début des symptômes < 4,5 h (fenêtre thrombolyse) ?",
            "type": "bool",
            "det_key": "delai",
            "true_val": 2.0, "false_val": 6.0,
        },
        {
            "id": "avc_def_prog",
            "text": "Déficit neurologique progressif ou aggravation en cours ?",
            "type": "bool",
            "det_key": "def_prog",
        },
        {
            "id": "avc_fast",
            "text": "BE-FAST positif (≥ 1 critère) ?",
            "type": "bool",
            "det_key": "fast_positif",
        },
    ],
    "Dyspnée / insuffisance respiratoire": [
        {
            "id": "dyspnee_detresse",
            "text": "FR ≥ 40/min ou SpO2 < 86 % ?",
            "type": "bool",
            "det_key": "detresse",
        },
        {
            "id": "dyspnee_parole",
            "text": "Ne peut pas parler en phrases complètes (dyspnée à la parole) ?",
            "type": "bool",
            "det_key": "parole",
            "true_val": False, "false_val": True,
        },
        {
            "id": "dyspnee_tirage",
            "text": "Tirage intercostal / orthopnée ?",
            "type": "bool",
            "det_key": "tirage",
        },
    ],
    "Hypotension artérielle": [
        {
            "id": "hypo_pas70",
            "text": "PAS ≤ 70 mmHg ?",
            "type": "bool",
            "det_key": "hypo_critique",
        },
        {
            "id": "hypo_pas90",
            "text": "PAS ≤ 90 mmHg ou (PAS ≤ 100 + FC > 100/min) ?",
            "type": "bool",
            "det_key": "hypo_severe",
        },
    ],
    "Pédiatrie - Crise épileptique": [
        {
            "id": "ped_epi_encours",
            "text": "Crise EN COURS au moment du triage ?",
            "type": "bool",
            "det_key": "en_cours",
        },
        {
            "id": "ped_epi_duree",
            "text": "Durée de la crise (minutes)",
            "type": "number",
            "det_key": "duree_min",
            "min": 0.0, "max": 120.0, "default": 0.0,
        },
        {
            "id": "ped_epi_focale",
            "text": "Crise focale (mouvements unilatéraux) ?",
            "type": "bool",
            "det_key": "focale",
        },
        {
            "id": "ped_epi_premiere",
            "text": "Première crise dans la vie de l'enfant ?",
            "type": "bool",
            "det_key": "premiere_crise",
        },
        {
            "id": "ped_epi_febrile",
            "text": "Crise fébrile (température ≥ 38°C) ?",
            "type": "bool",
            "det_key": "febrile",
        },
        {
            "id": "ped_epi_recuperee",
            "text": "Crise récupérée (enfant conscient) ?",
            "type": "bool",
            "det_key": "recuperee",
        },
    ],
    "Pédiatrie - Vomissements / Gastro-entérite": [
        {
            "id": "ped_gastro_bilieux",
            "text": "Vomissements bilieux (vert) ?",
            "type": "bool",
            "det_key": "bilieux",
        },
        {
            "id": "ped_gastro_deshydrat",
            "text": "Niveau de déshydratation",
            "type": "select",
            "options": [
                ("aucune",   "Absente"),
                ("legere",   "Légère (< 5 %)"),
                ("moderee",  "Modérée (5-10 %)"),
                ("severe",   "Sévère (> 10 %)"),
            ],
            "det_key": None,  # Traitement spécial dans process_answers
        },
        {
            "id": "ped_gastro_pleurs",
            "text": "Pleurs inconsolables (invagination ?) ?",
            "type": "bool",
            "det_key": "pleurs_inconsolables",
        },
    ],
}


def process_answers(motif: str, answers: dict) -> dict:
    """
    Transforme les réponses aux discriminants enrichis en un dict compatible
    avec les handlers de triage (SS.det).
    Source : SFMU FRENCH V1.1.
    """
    det_updates: dict = {}
    questions = DISCRIMINANTS_ENRICHIS.get(motif, [])

    for q in questions:
        qid    = q["id"]
        val    = answers.get(qid)
        dk     = q.get("det_key")

        if val is None:
            continue

        if q["type"] == "bool":
            if dk:
                stored = q.get("true_val", True) if val else q.get("false_val", False)
                det_updates[dk] = stored
        elif q["type"] == "select":
            mapping = q.get("mapping") or {}
            if dk:
                det_updates[dk] = mapping.get(val, val)
            # Cas spécial : déshydratation pédiatrique
            if qid == "ped_gastro_deshydrat":
                det_updates["deshydrat_legere"]   = val == "legere"
                det_updates["deshydrat_moderee"]  = val == "moderee"
                det_updates["deshydrat_severe"]   = val == "severe"
        elif q["type"] == "number":
            if dk:
                try:
                    det_updates[dk] = float(val)
                except (TypeError, ValueError):
                    pass

    return det_updates


def render_discriminants_enrichis(motif: str, key_prefix: str = "disc") -> dict:
    """
    Affiche les questions discriminantes enrichies pour un motif donné
    et retourne les réponses sous forme de dict {qid: valeur}.
    Utilisable en remplacement ou complément de render_discriminants().
    """
    if st is None:
        return {}

    questions = DISCRIMINANTS_ENRICHIS.get(motif)
    if not questions:
        return {}

    answers: dict = {}
    for q in questions:
        qid = q["id"]
        if q["type"] == "bool":
            answers[qid] = st.checkbox(q["text"], key=f"{key_prefix}_{qid}")
        elif q["type"] == "select":
            opts = q["options"]
            answers[qid] = st.selectbox(
                q["text"],
                options=[o[0] for o in opts],
                format_func=lambda v, opts=opts: next((lbl for k, lbl in opts if k == v), v),
                key=f"{key_prefix}_{qid}",
            )
        elif q["type"] == "number":
            answers[qid] = st.number_input(
                q["text"],
                min_value=q.get("min", 0.0),
                max_value=q.get("max", 100.0),
                value=q.get("default", 0.0),
                step=0.5,
                key=f"{key_prefix}_{qid}",
            )
    return answers


# Compléter les motifs les plus fréquents sans discriminants
_DISC_COMPLEMENT = {
    "Tachycardie / tachyarythmie": [
        {"id": "tachy_toleree",   "text": "Tachycardie mal tolérée (hypotension, lipothymie, dyspnée) ?",
         "type": "bool", "det_key": "tol_mal"},
        {"id": "tachy_supra",     "text": "FC > 150 bpm ?",
         "type": "bool", "det_key": "fc_extreme"},
    ],
    "Bradycardie / bradyarythmie": [
        {"id": "brady_toleree",   "text": "Bradycardie mal tolérée (PA basse, syncope, dyspnée) ?",
         "type": "bool", "det_key": "tol_mal"},
        {"id": "brady_extreme",   "text": "FC < 40 bpm ?",
         "type": "bool", "det_key": "fc_extreme"},
    ],
    "Hypertension artérielle": [
        {"id": "hta_sf",          "text": "Signes fonctionnels (céphalée, phosphènes, dyspnée) ?",
         "type": "bool", "det_key": "sf"},
        {"id": "hta_neurologique","text": "Trouble neurologique associé (confusion, déficit focal) ?",
         "type": "bool", "det_key": "neuro"},
    ],
    "Allergie / anaphylaxie": [
        {"id": "anaph_choc",      "text": "Choc : hypotension / perte de conscience ?",
         "type": "bool", "det_key": "choc_anaph"},
        {"id": "anaph_dyspnee",   "text": "Dyspnée / stridor / angio-œdème laryngé ?",
         "type": "bool", "det_key": "dyspnee"},
        {"id": "anaph_urticaire", "text": "Urticaire généralisée seule (sans choc) ?",
         "type": "bool", "det_key": "urticaire"},
    ],
    "Convulsions / EME": [
        {"id": "conv_encours",    "text": "Crise EN COURS au triage ?",
         "type": "bool", "det_key": "en_cours"},
        {"id": "conv_multi",      "text": "Crises multiples ou EME (> 5 min) ?",
         "type": "bool", "det_key": "multi"},
        {"id": "conv_deficit",    "text": "Déficit neurologique post-critique persistant ?",
         "type": "bool", "det_key": "def_post"},
    ],
    "Céphalée": [
        {"id": "ceph_brutal",     "text": "Céphalée d'installation brutale en coup de tonnerre ?",
         "type": "bool", "det_key": "brutal"},
        {"id": "ceph_nuque",      "text": "Raideur de nuque / fièvre associée ?",
         "type": "bool", "det_key": "nuque"},
        {"id": "ceph_deficit",    "text": "Déficit neurologique associé ?",
         "type": "bool", "det_key": "deficit"},
    ],
    "Douleur abdominale": [
        {"id": "abdo_defense",    "text": "Défense / contracture musculaire ?",
         "type": "bool", "det_key": "defense"},
        {"id": "abdo_grossesse",  "text": "Grossesse connue ?",
         "type": "bool", "det_key": "grossesse"},
        {"id": "abdo_sang",       "text": "Sang dans les selles / rectorragie ?",
         "type": "bool", "det_key": "sang"},
        {"id": "abdo_tol",        "text": "Douleur mal tolérée (EVA ≥ 7) ?",
         "type": "bool", "det_key": "tol_mal"},
    ],
    "Malaise": [
        {"id": "malaise_pdc",     "text": "Perte de conscience complète ?",
         "type": "bool", "det_key": "pdc"},
        {"id": "malaise_trauma",  "text": "Traumatisme lors de la chute ?",
         "type": "bool", "det_key": "trauma_chute"},
        {"id": "malaise_anomalie","text": "Anomalie vitale au triage (FC < 50, PAS < 90…) ?",
         "type": "bool", "det_key": "anomalie_vitale"},
    ],
    "Fièvre": [
        {"id": "fievre_purpura",  "text": "Purpura / pétéchies non effaçables ?",
         "type": "bool", "det_key": "purpura"},
        {"id": "fievre_nuque",    "text": "Raideur de nuque ?",
         "type": "bool", "det_key": "nuque"},
        {"id": "fievre_immu",     "text": "Patient immunodéprimé / chimiothérapie ?",
         "type": "bool", "det_key": "immunodepression"},
    ],
    "Traumatisme crânien": [
        {"id": "tc_pdc",          "text": "Perte de conscience même brève ?",
         "type": "bool", "det_key": "pdc"},
        {"id": "tc_anticoag",     "text": "Anticoagulants (AVK/AOD) ?",
         "type": "bool", "det_key": "aod"},
        {"id": "tc_vomiss",       "text": "Vomissements répétés (≥ 2) ?",
         "type": "bool", "det_key": "vomissements"},
        {"id": "tc_amnesia",      "text": "Amnésie > 5 min ?",
         "type": "bool", "det_key": "amnesia"},
    ],
}

# Fusionner dans DISCRIMINANTS_ENRICHIS
DISCRIMINANTS_ENRICHIS.update(_DISC_COMPLEMENT)

# ─────────────────────────────────────────────────────────────────────────────
# DISCRIMINANTS SUPPLÉMENTAIRES — Motifs fréquents IAO (Audit v19.3)
# Sources : SFMU FRENCH V1.1 / ERC 2021 / ESC 2023 / GINA 2023 / ATLS 11th
# ─────────────────────────────────────────────────────────────────────────────
_DISC_URGENT = {
    "Arrêt cardiorespiratoire": [
        {"id": "acr_type",    "text": "Type d'arrêt ?",
         "type": "radio",    "det_key": "acr_type",
         "options": ["Témoin","Non témoin","FV défibrillé","Asystole/AESP"]},
        {"id": "acr_rcp_ok",  "text": "RCP en cours / efficace (pouls revenu) ?",
         "type": "bool",     "det_key": "rcp_ok"},
        {"id": "acr_cause",   "text": "Cause suspectée ?",
         "type": "radio",    "det_key": "cause",
         "options": ["Cardiaque","Hypoxique","Trauma","Intox","Inconnue"]},
    ],
    "Palpitations": [
        {"id": "palp_fc",     "text": "FC > 150 bpm ou < 40 bpm ?",
         "type": "bool",     "det_key": "fc_extreme"},
        {"id": "palp_tol",    "text": "Mal tolérées (lipothymie, douleur thoracique, dyspnée) ?",
         "type": "bool",     "det_key": "tol_mal"},
        {"id": "palp_ecg",    "text": "Anomalie ECG vue (WPW, QRS large, FA) ?",
         "type": "bool",     "det_key": "ecg_anormal"},
    ],
    "Dyspnée / insuffisance cardiaque": [
        {"id": "dysp_spo2",   "text": "SpO2 < 92 % ?",
         "type": "bool",     "det_key": "spo2_basse",
         "auto": lambda ss: (ss.get("v_spo2") or 98) < 92},
        {"id": "dysp_ortho",  "text": "Orthopnée (ne peut pas s'allonger) ?",
         "type": "bool",     "det_key": "orthopnee"},
        {"id": "dysp_rale",   "text": "Crépitants bilatéraux / OAP ?",
         "type": "bool",     "det_key": "oap"},
        {"id": "dysp_stridor","text": "Stridor inspiratoire (obstruction VAS) ?",
         "type": "bool",     "det_key": "stridor"},
    ],
    "Asthme ou aggravation BPCO": [
        {"id": "asthme_sil",  "text": "Silence auscultatoire (asthme quasi-fatal) ?",
         "type": "bool",     "det_key": "silencieux"},
        {"id": "asthme_parole","text": "Incapacité à parler en phrase entière ?",
         "type": "bool",     "det_key": "parole_impossible"},
        {"id": "asthme_epuis","text": "Épuisement respiratoire / tirage sévère ?",
         "type": "bool",     "det_key": "epuisement"},
    ],
    "Hémoptysie": [
        {"id": "hemop_abond", "text": "Hémoptysie abondante (> 200 ml ou active) ?",
         "type": "bool",     "det_key": "abondante"},
        {"id": "hemop_atcd",  "text": "ATCD TBC, cancer bronchique, anticoagulants ?",
         "type": "bool",     "det_key": "atcd_hemop"},
        {"id": "hemop_choc",  "text": "Instabilité hémodynamique associée ?",
         "type": "bool",     "det_key": "choc"},
    ],
    "Vomissements / Diarrhée": [
        {"id": "vomi_sang",   "text": "Présence de sang (hématémèse / rectorragies) ?",
         "type": "bool",     "det_key": "sang"},
        {"id": "vomi_deshy",  "text": "Signes de déshydratation sévère (yeux creux, pli cutané) ?",
         "type": "bool",     "det_key": "deshydratation"},
        {"id": "vomi_choc",   "text": "Tachycardie + hypotension associées ?",
         "type": "bool",     "det_key": "choc"},
    ],
    "Hématémèse / Rectorragie": [
        {"id": "hemato_abond","text": "Hémorragie active / abondante en cours ?",
         "type": "bool",     "det_key": "active"},
        {"id": "hemato_choc", "text": "Choc hémodynamique (PAS < 90, FC > 110) ?",
         "type": "bool",     "det_key": "choc"},
        {"id": "hemato_anti", "text": "Anticoagulants / AINS en cours ?",
         "type": "bool",     "det_key": "anticoag"},
    ],
    "Colique néphrétique / Douleur lombaire": [
        {"id": "cn_fievre",   "text": "Fièvre ≥ 38,5°C (pyélonéphrite / sepsis urinaire) ?",
         "type": "bool",     "det_key": "fievre",
         "auto": lambda ss: (ss.get("v_temp") or 37) >= 38.5},
        {"id": "cn_rein_u",   "text": "Rein unique ou transplanté ?",
         "type": "bool",     "det_key": "rein_unique"},
        {"id": "cn_eva",      "text": "EVA ≥ 7 résistante aux antalgiques ?",
         "type": "bool",     "det_key": "eva_severe",
         "auto": lambda ss: (ss.get("eva") or 0) >= 7},
    ],
    "Altération de conscience / Coma": [
        {"id": "coma_glyc",   "text": "Glycémie capillaire mesurée ?",
         "type": "bool",     "det_key": "glycemie_faite"},
        {"id": "coma_trauma", "text": "Traumatisme crânien associé ?",
         "type": "bool",     "det_key": "trauma"},
        {"id": "coma_gcs8",   "text": "GCS ≤ 8 (protection des voies aériennes requise) ?",
         "type": "bool",     "det_key": "gcs_severe",
         "auto": lambda ss: (ss.get("v_gcs") or 15) <= 8},
    ],
    "Syndrome confusionnel": [
        {"id": "conf_brutal", "text": "Installation brutale (< 24h) ?",
         "type": "bool",     "det_key": "brutal"},
        {"id": "conf_sepsis", "text": "Fièvre / suspicion infectieuse ?",
         "type": "bool",     "det_key": "fievre",
         "auto": lambda ss: (ss.get("v_temp") or 37) >= 38.0},
        {"id": "conf_med",    "text": "Médicament suspect récent (BZD, morphine, anticholinergique) ?",
         "type": "bool",     "det_key": "iatrogene"},
    ],
    "Hémorragie active": [
        {"id": "hemo_site",   "text": "Site saignement ?",
         "type": "radio",    "det_key": "site",
         "options": ["Extérieur compressible","Thorax","Abdomen","Pelvis","Intracrânien"]},
        {"id": "hemo_ctrl",   "text": "Saignement contrôlé / comprimé ?",
         "type": "bool",     "det_key": "controle"},
        {"id": "hemo_anti",   "text": "Anticoagulants / AOD en cours ?",
         "type": "bool",     "det_key": "anticoag"},
    ],
    "Traumatisme thorax/abdomen/rachis cervical": [
        {"id": "tt_penetrant","text": "Mécanisme pénétrant (arme blanche / feu) ?",
         "type": "bool",     "det_key": "penetrant"},
        {"id": "tt_rachis",   "text": "Douleur rachis cervical + mécanisme flexion/extension ?",
         "type": "bool",     "det_key": "rachis_instable"},
        {"id": "tt_pneu",     "text": "Détresse respi + tympanisme — pneumothorax compressif ?",
         "type": "bool",     "det_key": "pneumothorax_compressif"},
    ],
    "Traumatisme bassin/hanche/fémur": [
        {"id": "tb_instab",   "text": "Instabilité pelvienne (compression latérale douloureuse) ?",
         "type": "bool",     "det_key": "instabilite_pelvienne"},
        {"id": "tb_anticoag", "text": "Anticoagulants (AVK / AOD) ?",
         "type": "bool",     "det_key": "anticoag"},
        {"id": "tb_impot",    "text": "Impotence fonctionnelle totale ?",
         "type": "bool",     "det_key": "impotence_totale"},
    ],
    "Traumatisme membre / épaule": [
        {"id": "tm_deform",   "text": "Déformation visible / fracture ouverte ?",
         "type": "bool",     "det_key": "deformation"},
        {"id": "tm_neuro",    "text": "Déficit neuro-vasculaire distal (pouls, sensibilité) ?",
         "type": "bool",     "det_key": "deficit_nv"},
        {"id": "tm_anti",     "text": "Anticoagulants (risque hémorragie) ?",
         "type": "bool",     "det_key": "anticoag"},
    ],
    "Brûlure": [
        {"id": "brul_pct",    "text": "Surface corporelle estimée ?",
         "type": "radio",    "det_key": "surface_pct",
         "options": ["< 10%","10-20%","20-40%","> 40%"]},
        {"id": "brul_face",   "text": "Brûlure face / cou / mains / parties génitales ?",
         "type": "bool",     "det_key": "localisation_crit"},
        {"id": "brul_inh",    "text": "Inhalation de fumée / brûlure voies aériennes ?",
         "type": "bool",     "det_key": "inhalation"},
    ],
}

# Fusionner dans DISCRIMINANTS_ENRICHIS
DISCRIMINANTS_ENRICHIS.update(_DISC_URGENT)



# ─────────────────────────────────────────────────────────────────────────────
# DISCRIMINANTS PÉDIATRIE + MOTIFS SPÉCIAUX (Audit v19.3 — second lot)
# Sources : SFP/SFMU 2017 / HAS 2019 Bronchiolite / SFMU 2021 / OMS ATIH
# ─────────────────────────────────────────────────────────────────────────────
_DISC_PED_SPEC = {
    "Pétéchie / Purpura": [
        {"id": "pur_neff",    "text": "Purpura NON EFFAÇABLE à la vitropression ?",
         "type": "bool",     "det_key": "neff"},
        {"id": "pur_fievre",  "text": "Fièvre associée ?",
         "type": "bool",     "det_key": "fievre",
         "auto": lambda ss: (ss.get("v_temp") or 37) >= 38.0},
        {"id": "pur_choc",    "text": "Instabilité hémodynamique (FC↑, PAS↓) ?",
         "type": "bool",     "det_key": "choc"},
    ],
    "Pédiatrie - Fièvre ≤ 3 mois": [
        {"id": "pf1_age",     "text": "Âge exact (mois) ?",
         "type": "number",   "det_key": "age_mois", "min": 0, "max": 3},
        {"id": "pf1_tempe",   "text": "Température rectale ≥ 38,0°C confirmée ?",
         "type": "bool",     "det_key": "temp_confirmee",
         "auto": lambda ss: (ss.get("v_temp") or 37) >= 38.0},
        {"id": "pf1_alerte",  "text": "Signes de gravité (mauvaise couleur, hypotonie, pleurs inconsolables) ?",
         "type": "bool",     "det_key": "signes_gravite"},
    ],
    "Fièvre enfant (3 mois - 15 ans)": [
        {"id": "pf2_bruyan",  "text": "Raideur de nuque / photophobie ?",
         "type": "bool",     "det_key": "nuque"},
        {"id": "pf2_purp",    "text": "Purpura / pétéchies ?",
         "type": "bool",     "det_key": "purpura"},
        {"id": "pf2_dur",     "text": "Fièvre > 5 jours (maladie de Kawasaki ?) ?",
         "type": "bool",     "det_key": "fievre_prolongee"},
        {"id": "pf2_immu",    "text": "Enfant immunodéprimé / chimiothérapie ?",
         "type": "bool",     "det_key": "immunodepression"},
    ],
    "Pédiatrie - Asthme / Bronchospasme": [
        {"id": "pa_sil",      "text": "Silence auscultatoire (asthme quasi-fatal) ?",
         "type": "bool",     "det_key": "silencieux"},
        {"id": "pa_parole",   "text": "Incapacité à parler en phrase entière ?",
         "type": "bool",     "det_key": "parole"},
        {"id": "pa_tirage",   "text": "Tirage sévère visible ?",
         "type": "bool",     "det_key": "tirage_severe"},
        {"id": "pa_spo2",     "text": "SpO2 < 92% malgré O2 ?",
         "type": "bool",     "det_key": "spo2_basse",
         "auto": lambda ss: (ss.get("v_spo2") or 98) < 92},
    ],
    "Pédiatrie - Bronchiolite": [
        {"id": "pb_apn",      "text": "Apnée(s) observée(s) ?",
         "type": "bool",     "det_key": "apnee"},
        {"id": "pb_age",      "text": "Nourrisson < 6 semaines OU prématuré < 36 SA ?",
         "type": "bool",     "det_key": "premature"},
        {"id": "pb_alim",     "text": "Alimentation impossible (< 50% des biberons) ?",
         "type": "bool",     "det_key": "alimentation_impossible"},
        {"id": "pb_spo2",     "text": "SpO2 < 92% en air ambiant ?",
         "type": "bool",     "det_key": "spo2_basse",
         "auto": lambda ss: (ss.get("v_spo2") or 98) < 92},
    ],
    "Pédiatrie - Déshydratation": [
        {"id": "pd_pct",      "text": "Perte de poids estimée > 10% ?",
         "type": "bool",     "det_key": "deshydrat_severe"},
        {"id": "pd_yeux",     "text": "Yeux creux + pli cutané persistant ?",
         "type": "bool",     "det_key": "deshydrat_moderee"},
        {"id": "pd_urine",    "text": "Anurie depuis > 8h ?",
         "type": "bool",     "det_key": "anurie"},
    ],
    "Pédiatrie - Douleur abdominale": [
        {"id": "pda_def",     "text": "Défense abdominale à la palpation ?",
         "type": "bool",     "det_key": "defense_musculaire"},
        {"id": "pda_bili",    "text": "Vomissements bilieux (vert) ?",
         "type": "bool",     "det_key": "bilieux"},
        {"id": "pda_pleurs",  "text": "Pleurs inconsolables en crise (< 2 ans) ?",
         "type": "bool",     "det_key": "pleurs_inconsolables"},
        {"id": "pda_fid",     "text": "Douleur fosse iliaque droite (appendicite ?) ?",
         "type": "bool",     "det_key": "douleur_fosse_iliaque_droite"},
    ],
    "Pédiatrie - Traumatisme": [
        {"id": "pt_gcs",      "text": "GCS ≤ 14 OU perte de conscience même brève ?",
         "type": "bool",     "det_key": "pdc",
         "auto": lambda ss: (ss.get("v_gcs") or 15) < 15},
        {"id": "pt_meca",     "text": "Haute cinétique (chute > 3m, AVP, piéton) ?",
         "type": "bool",     "det_key": "haute_cinetique"},
        {"id": "pt_deform",   "text": "Déformation visible / fracture ouverte ?",
         "type": "bool",     "det_key": "deformation"},
    ],
    "Accouchement imminent": [
        {"id": "acc_dilat",   "text": "Présentation visible ou expulsion imminente ?",
         "type": "bool",     "det_key": "expulsion_imminente"},
        {"id": "acc_semaines","text": "Terme de la grossesse (SA) ?",
         "type": "number",   "det_key": "terme_sa", "min": 20, "max": 42},
        {"id": "acc_colore",  "text": "Liquide amniotique teinté / méconial ?",
         "type": "bool",     "det_key": "liquide_meconial"},
    ],
    "Complication grossesse T1/T2": [
        {"id": "cg_douleur",  "text": "Douleur pelvienne + métrorragies ?",
         "type": "bool",     "det_key": "geu_suspectee"},
        {"id": "cg_choc",     "text": "Instabilité hémodynamique (PAS < 90 / FC > 110) ?",
         "type": "bool",     "det_key": "choc",
         "auto": lambda ss: (ss.get("v_pas") or 120) < 90 or (ss.get("v_fc") or 80) > 110},
        {"id": "cg_betahcg",  "text": "βHCG positif / grossesse confirmée ?",
         "type": "bool",     "det_key": "beta_hcg_pos"},
    ],
    "Ménorragie / Métrorragie": [
        {"id": "mm_abond",    "text": "Hémorragie abondante (> 1 protection/h) ?",
         "type": "bool",     "det_key": "abondante"},
        {"id": "mm_choc",     "text": "Malaise / hypotension associés ?",
         "type": "bool",     "det_key": "choc"},
        {"id": "mm_grossesse","text": "Grossesse possible (test non réalisé) ?",
         "type": "bool",     "det_key": "grossesse_possible"},
    ],
    "Hypoglycémie": [
        {"id": "hg_coma",     "text": "Coma / GCS ≤ 8 ?",
         "type": "bool",     "det_key": "coma",
         "auto": lambda ss: (ss.get("v_gcs") or 15) <= 8},
        {"id": "hg_val",      "text": "Glycémie capillaire mesurée (mg/dl) ?",
         "type": "number",   "det_key": "gl", "min": 10, "max": 500},
        {"id": "hg_diab",     "text": "Patient diabétique / insulino-traité ?",
         "type": "bool",     "det_key": "diabetique"},
    ],
    "Hyperglycémie": [
        {"id": "hgly_cetose", "text": "Nausées / vomissements / douleur abdominale (acidocétose) ?",
         "type": "bool",     "det_key": "acidocetose"},
        {"id": "hgly_val",    "text": "Glycémie capillaire > 3 g/l (300 mg/dl) ?",
         "type": "bool",     "det_key": "hyperglycemie_severe"},
        {"id": "hgly_neuro",  "text": "Trouble neurologique / coma hyperosmolaire ?",
         "type": "bool",     "det_key": "neuro"},
    ],
    "Idée / comportement suicidaire": [
        {"id": "sui_moyen",   "text": "Moyen létal disponible (médicaments, arme) ?",
         "type": "bool",     "det_key": "moyen_letal"},
        {"id": "sui_intox",   "text": "Prise médicamenteuse / intoxication déjà réalisée ?",
         "type": "bool",     "det_key": "intox_realise"},
        {"id": "sui_urg",     "text": "Idéation active avec intention immédiate ?",
         "type": "bool",     "det_key": "intention_immediate"},
    ],
    "Troubles psychiatriques": [
        {"id": "psy_agit",    "text": "Agitation / violence envers autrui ?",
         "type": "bool",     "det_key": "agitation"},
        {"id": "psy_disso",   "text": "État dissociatif / déconnexion de la réalité ?",
         "type": "bool",     "det_key": "dissociation"},
        {"id": "psy_med",     "text": "Médicament ou substance suspecté ?",
         "type": "bool",     "det_key": "substance"},
    ],
    "Épistaxis": [
        {"id": "ep_abond",    "text": "Saignement actif abondant non contrôlable ?",
         "type": "bool",     "det_key": "abondant_actif"},
        {"id": "ep_anti",     "text": "Anticoagulants (AVK / AOD) ?",
         "type": "bool",     "det_key": "anticoagulants"},
        {"id": "ep_bilat",    "text": "Épistaxis bilatérale ou postérieure ?",
         "type": "bool",     "det_key": "posterieure"},
    ],
    "Corps étranger / brûlure oculaire": [
        {"id": "oc_chim",     "text": "Brûlure chimique (acide / base) ?",
         "type": "bool",     "det_key": "chimique"},
        {"id": "oc_vision",   "text": "Baisse d'acuité visuelle associée ?",
         "type": "bool",     "det_key": "bav"},
        {"id": "oc_metal",    "text": "Corps étranger métallique projeté (meuleuse, marteau) ?",
         "type": "bool",     "det_key": "metal"},
    ],
    "Intoxication médicamenteuse": [
        {"id": "intox_mol",   "text": "Molécule(s) ingérée(s) ?",
         "type": "radio",    "det_key": "molecule",
         "options": ["Inconnue","Paracétamol","BZD","Tricycliques","Opioïdes","Autre"]},
        {"id": "intox_qty",   "text": "Quantité importante / dose inconnue ?",
         "type": "bool",     "det_key": "dose_inconnue"},
        {"id": "intox_cbp",   "text": "CBP appelé (070/245.245) ?",
         "type": "bool",     "det_key": "cbp_appele"},
    ],
}

# Fusionner dans DISCRIMINANTS_ENRICHIS
DISCRIMINANTS_ENRICHIS.update(_DISC_PED_SPEC)


# Motifs administratifs/divers — Tri 5 systématique, pas de discriminant clinique
_DISC_ADMIN = {
    "Renouvellement ordonnance": [
        {"id": "ren_urgence", "text": "Médicament VITAL manquant (insuline, anticoagulant, antihypertenseur) ?",
         "type": "bool", "det_key": "urgent"},
    ],
    "Examen administratif": [
        {"id": "adm_symptome","text": "Symptôme clinique découvert à l'accueil ?",
         "type": "bool", "det_key": "symptome_decouverte"},
    ],
    "Autre motif": [
        {"id": "autre_desc",  "text": "Décrire le motif brièvement",
         "type": "text",     "det_key": "description_libre"},
    ],
}
DISCRIMINANTS_ENRICHIS.update(_DISC_ADMIN)
