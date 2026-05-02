# clinical/french_v12.py — Données protocole FRENCH Triage V1.2
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Source : SFMU — Classification FRENCH Triage V1.1, 2018

from __future__ import annotations
from typing import Dict, List, Optional
from clinical.utils import norm

try:
    import streamlit as st
except Exception:  # pragma: no cover - tolère les imports hors interface Streamlit
    st = None

NO_CRITERION_LABEL = "Aucun critère discriminant sélectionné"
TRIAGE_ORDER = {"M": 0, "1": 1, "2": 2, "3A": 3, "3B": 4, "4": 5, "5": 6}


def _row(category: str, motif: str, default: str, criteria=(), aliases=()):
    return {
        "id": norm(motif).replace(" ", "_").replace("/", "_"),
        "category": category,
        "motif": motif,
        "default": default,
        "criteria": [{"level": level, "text": text} for level, text in criteria],
        "aliases": list(aliases),
    }


FRENCH_PROTOCOL: List[dict] = [
    # ── CARDIAQUE / VASCULAIRE ────────────────────────────────────────────
    _row("Cardiovasculaire", "Arrêt cardiorespiratoire", "M"),
    _row("Cardiovasculaire", "Douleur thoracique / SCA", "3A", [
        ("1", "Arrêt cardio-respiratoire ou instabilité hémodynamique"),
        ("2", "Douleur thoracique typique ou signes d'instabilité"),
        ("3A", "Douleur thoracique atypique"),
        ("3B", "Douleur thoracique peu évocatrice"),
    ], aliases=["Douleur thoracique / syndrome coronaire aigu (SCA)", "Douleur thoracique/syndrome coronaire aigu (SCA)", "SCA", "Infarctus"]),
    _row("Cardiovasculaire", "Tachycardie / tachyarythmie", "3A", [
        ("1", "Instabilité hémodynamique"),
        ("2", "FC > 150 bpm"),
        ("3A", "FC > 120 bpm"),
    ]),
    _row("Cardiovasculaire", "Bradycardie / bradyarythmie", "3A", [
        ("1", "Syncope / instabilité"),
        ("2", "FC < 50 bpm symptomatique"),
        ("3A", "FC < 50 bpm asymptomatique"),
    ]),
    _row("Cardiovasculaire", "Hypertension artérielle", "4", [
        ("2", "PAS > 220 mmHg ou encéphalopathie"),
        ("3A", "PAS > 180 mmHg symptomatique"),
        ("4", "HTA asymptomatique"),
    ], aliases=["HTA", "Crise hypertensive"]),
    _row("Cardiovasculaire", "Hypotension artérielle", "2", [
        ("1", "Choc / PAS < 80 mmHg"),
        ("2", "PAS < 100 mmHg"),
        ("3A", "Hypotension relative"),
    ]),
    _row("Cardiovasculaire", "Palpitations", "4", [
        ("2", "Syncope associée"),
        ("3A", "FC anormale à l'examen"),
        ("4", "Palpitations isolées"),
    ]),
    _row("Cardiovasculaire", "Allergie / anaphylaxie", "2", [
        ("1", "Choc anaphylactique / dyspnée sévère"),
        ("2", "Urticaire généralisée + instabilité"),
        ("4", "Réaction allergique légère"),
    ], aliases=["Anaphylaxie"]),

    # ── RESPIRATOIRE ──────────────────────────────────────────────────────
    _row("Respiratoire", "Dyspnée / insuffisance respiratoire", "3A", [
        ("1", "Arrêt respiratoire / SpO2 < 85 %"),
        ("2", "SpO2 < 90 % ou FR > 25/min"),
        ("3A", "SpO2 90-93 % ou FR élevée"),
        ("3B", "Dyspnée légère"),
    ], aliases=["Dyspnée", "Insuffisance respiratoire", "Dyspnee / insuffisance respiratoire"]),
    _row("Respiratoire", "Dyspnée / insuffisance cardiaque", "3A", [
        ("1", "OAP fulminant"),
        ("2", "OAP avec hypoxémie"),
        ("3A", "Décompensation modérée"),
    ], aliases=["OAP", "Insuffisance cardiaque"]),
    _row("Respiratoire", "Asthme ou aggravation BPCO", "3A", [
        ("1", "Asthme silencieux / SpO2 < 88 %"),
        ("2", "Bronchospasme sévère / SpO2 < 92 %"),
        ("3A", "Bronchospasme modéré"),
    ], aliases=["Asthme", "BPCO", "Bronchospasme", "Asthme / aggravation BPCO"]),
    _row("Respiratoire", "Hémoptysie", "3A", [
        ("2", "Hémoptysie abondante ou SpO2 < 94 %"),
        ("3A", "Hémoptysie modérée"),
        ("4", "Hémoptysie légère"),
    ]),

    # ── DIGESTIF ──────────────────────────────────────────────────────────
    _row("Digestif", "Douleur abdominale", "3B", [
        ("2", "Défense / contracture ou instabilité"),
        ("2", "Douleur irradiant dans le dos (dissection ?)"),
        ("3A", "Fièvre > 38.5 °C + tachycardie"),
        ("3B", "EVA ≥ 4"),
        ("4", "EVA < 4"),
    ]),
    _row("Digestif", "Vomissements / Diarrhée", "4", [
        ("2", "Occlusion suspectée"),
        ("3A", "Enfant ≤ 2 ans"),
        ("3B", "Douleur abdominale ou mauvaise tolérance"),
    ], aliases=["Vomissements", "Diarrhée", "Gastroentérite"]),
    _row("Digestif", "Hématémèse / Rectorragie", "2", [
        ("1", "Choc hémorragique"),
        ("2", "Saignement actif"),
        ("3A", "Saignement résolutif"),
    ], aliases=["Hématemèse", "Rectorragie", "Méléna", "Hematémèse / vomissements sanglants", "Rectorragie / méléna", "Vomissement de sang / hématémèse", "Maelena/rectorragies"]),
    _row("Digestif", "Colique néphrétique / Douleur lombaire", "3B", [
        ("2", "Fièvre + douleur lombaire — Pyélonéphrite obstructive"),
        ("3A", "EVA ≥ 7"),
        ("3B", "EVA 4-6"),
        ("4", "EVA < 4"),
    ], aliases=["Colique nephretique", "Lithiase urinaire", "Douleur de la fosse lombaire/du flanc"]),

    # ── NEUROLOGIQUE ──────────────────────────────────────────────────────
    _row("Neurologique", "AVC / Déficit neurologique", "2", [
        ("1", "GCS < 13 ou choc"),
        ("2", "Code Stroke — BE-FAST positif"),
        ("2", "Déficit focal d'installation brutale"),
    ], aliases=["AVC", "Stroke", "Code Stroke", "Déficit neurologique", "Déficit moteur sensitif sensoriel ou du langage / AVC", "Déficit moteur, sensitif, sensoriel ou du langage/AVC"]),
    _row("Neurologique", "Traumatisme crânien", "3B", [
        ("1", "GCS < 13"),
        ("2", "PDC + vomissements ou anticoagulés"),
        ("3A", "PDC brève ou GCS 13-14"),
        ("3B", "TC bénin GCS 15"),
    ], aliases=["TC", "TCC", "Traumatisme cranien"]),
    _row("Neurologique", "Altération de conscience / Coma", "2", [
        ("1", "GCS ≤ 8 / Coma"),
        ("2", "GCS 9-12"),
        ("2", "Hypoglycémie sévère"),
    ], aliases=["Coma", "Altération de la conscience / coma", "Altération de la conscience/coma", "Alteration de conscience / Coma"]),
    _row("Neurologique", "Céphalée", "3B", [
        ("1", "Céphalée en coup de tonnerre / méningisme"),
        ("2", "Déficit neurologique associé"),
        ("3A", "Céphalée intense brutale"),
        ("3B", "Céphalée modérée"),
    ], aliases=["Migraine"]),
    _row("Neurologique", "Convulsions / EME", "2", [
        ("1", "Convulsions en cours"),
        ("2", "Post-critique — GCS < 13"),
        ("2", "Première crise"),
        ("3A", "Crise résolue — GCS 15"),
    ], aliases=["Épilepsie", "Convulsions", "EME", "Crise épileptique", "Convulsion hyperthermique"]),
    _row("Neurologique", "Syndrome confusionnel", "3A", [
        ("2", "Agitation + instabilité"),
        ("3A", "Confusion modérée"),
        ("3B", "Confusion légère"),
    ], aliases=["Confusion"]),
    _row("Neurologique", "Malaise", "3B", [
        ("2", "Conscience altérée / instabilité"),
        ("3A", "Syncope avec retour rapide"),
        ("3B", "Malaise vague résolu"),
    ], aliases=["Syncope", "Lipothymie"]),

    # ── TRAUMATOLOGIE ─────────────────────────────────────────────────────
    _row("Traumatologie", "Traumatisme thorax/abdomen/rachis cervical", "3A", [
        ("1", "Instabilité hémodynamique"),
        ("2", "Haute énergie / polytraumatisme"),
        ("3A", "Traumatisme axial sans instabilité"),
    ], aliases=["Polytraumatisme", "Trauma thorax"]),
    _row("Traumatologie", "Traumatisme bassin/hanche/fémur", "3A", [
        ("1", "Instabilité hémodynamique"),
        ("2", "Fracture ouverte / lésion vasculaire"),
        ("3A", "Fracture probable"),
    ]),
    _row("Traumatologie", "Traumatisme membre / épaule", "4", [
        ("1", "Amputation / lésion vasculaire"),
        ("3A", "Fracture déplacée probable / EVA ≥ 7"),
        ("4", "Entorse / contusion"),
    ], aliases=["Fracture", "Entorse", "Plaie"]),
    _row("Traumatologie", "Hémorragie active", "2", [
        ("1", "Choc hémorragique"),
        ("2", "Hémorragie active non contrôlée"),
        ("3A", "Hémorragie contrôlée"),
    ], aliases=["Saignement"]),
    _row("Traumatologie", "Brûlure", "3A", [
        ("1", "Voies aériennes + > 25 %"),
        ("2", "Surface > 15 % ou 3e degré"),
        ("3A", "Zone fonctionnelle / visage"),
        ("4", "Brûlure mineure"),
    ]),

    # ── INFECTIEUX ────────────────────────────────────────────────────────
    _row("Infectieux", "Fièvre", "4", [
        ("1", "Purpura non effaçable + fièvre"),
        ("2", "T° ≥ 40 °C avec signe de gravité"),
        ("3A", "T° ≥ 39 °C mauvaise tolérance"),
        ("4", "Fièvre bien tolérée"),
    ]),
    _row("Infectieux", "Pétéchie / Purpura", "2", [
        ("1", "Purpura non effaçable — Ceftriaxone IMMÉDIAT"),
        ("2", "Fièvre + pétéchies"),
        ("3A", "Pétéchies sans fièvre"),
    ], aliases=["Purpura", "Purpura fulminans"]),

    # ── PÉDIATRIE ─────────────────────────────────────────────────────────
    _row("Pédiatrie", "Pédiatrie - Fièvre ≤ 3 mois", "1", [
        ("1", "Fièvre ≥ 38 °C nourrisson ≤ 3 mois"),
    ], aliases=["Pediatrie - Fievre <= 3 mois", "Fièvre nourrisson", "Fièvre ≤ 3 mois"]),
    _row("Pédiatrie", "Fièvre enfant (3 mois - 15 ans)", "4", [
        ("2", "T° ≥ 40 °C ou somnolence / geignement / marbrures"),
        ("3A", "Tachycardie pour l'âge ou mauvaise tolérance"),
    ], aliases=["Pediatrie - Fievre enfant (3 mois - 15 ans)"]),
    _row("Pédiatrie", "Pédiatrie - Vomissements / Gastro-entérite", "4", [
        ("2", "Nourrisson / déshydratation sévère"),
        ("3A", "Enfant avec sang dans selles"),
        ("4", "Gastro-entérite bien tolérée"),
    ], aliases=["Pediatrie - Vomissements / Gastro-enterite", "Diarrhée / vomissements du nourrisson (≤ 24 mois)"]),
    _row("Pédiatrie", "Pédiatrie - Crise épileptique", "2", [
        ("1", "Crise en cours"),
        ("2", "Post-critique / première crise"),
    ], aliases=["Pediatrie - Crise epileptique"]),
    _row("Pédiatrie", "Pédiatrie - Asthme / Bronchospasme", "3A", [
        ("1", "Silencieux / SpO2 < 88 %"),
        ("2", "SpO2 < 94 %"),
        ("3A", "Modéré"),
    ], aliases=["Pediatrie - Asthme / Bronchospasme"]),

    # ── GYNÉCOLOGIE ───────────────────────────────────────────────────────
    _row("Gynécologie", "Accouchement imminent", "1", aliases=["Accouchement imminent ou réalisé"]),
    _row("Gynécologie", "Complication grossesse T1/T2", "2", [
        ("1", "Choc / hémorragie abondante"),
        ("2", "GEU suspecté / douleur + métrorragies"),
        ("3A", "Métrorragies modérées"),
    ], aliases=["GEU", "Grossesse extra-utérine", "Problème de grossesse 1er et 2ème trimestre"]),
    _row("Gynécologie", "Ménorragie / Métrorragie", "3A", [
        ("2", "Instabilité hémodynamique"),
        ("3A", "Saignement abondant"),
        ("4", "Saignement modéré"),
    ], aliases=["Méno-metrorragie"]),

    # ── MÉTABOLIQUE ───────────────────────────────────────────────────────
    _row("Métabolique", "Hypoglycémie", "2", [
        ("1", "GCS < 13 ou glycémie < 2 mmol/l (36 mg/dl)"),
        ("2", "Glycémie < 3 mmol/l (54 mg/dl)"),
        ("3A", "Glycémie 3-3.9 mmol/l (54-70 mg/dl)"),
    ]),
    _row("Métabolique", "Hyperglycémie", "3A", [
        ("2", "Glycémie > 20 mmol/l (360 mg/dl) ou cétoacidose"),
        ("3A", "Glycémie 10-20 mmol/l"),
        ("4", "Hyperglycémie modérée bien tolérée"),
    ], aliases=["Hyperglycémie / Cétoacidose", "Cétoacidose"]),

    # ── PSYCHIATRIE ───────────────────────────────────────────────────────
    _row("Psychiatrie", "Idée / comportement suicidaire", "2", [
        ("1", "Tentative de suicide avec instabilité"),
        ("2", "Idées suicidaires actives"),
        ("3B", "Idées suicidaires passives"),
    ]),
    _row("Psychiatrie", "Troubles psychiatriques", "3B", [
        ("2", "Agitation sévère / violence"),
        ("3B", "Trouble modéré"),
    ]),

    # ── ORL / OPHTALMOLOGIE ───────────────────────────────────────────────
    _row("ORL", "Épistaxis", "3B", [
        ("2", "Épistaxis abondant + anticoagulés + instabilité"),
        ("2", "Épistaxis abondant actif"),
        ("3B", "Épistaxis abondant résolutif"),
        ("5", "Épistaxis peu abondant"),
    ]),
    _row("ORL", "Corps étranger / brûlure oculaire", "3A", [
        ("2", "Brûlure chimique / baisse AV brutale"),
        ("3A", "Corps étranger pénétrant"),
        ("4", "Corps étranger superficiel"),
    ]),

    # ── INTOXICATION ─────────────────────────────────────────────────────
    _row("Intoxication", "Intoxication médicamenteuse", "2", [
        ("1", "Instabilité hémodynamique / troubles de conscience"),
        ("2", "Produit cardiotoxique"),
        ("3A", "Intoxication modérée bien tolérée"),
    ]),

    # ── DIVERS ───────────────────────────────────────────────────────────
    _row("Divers", "Renouvellement ordonnance", "5"),
    _row("Divers", "Examen administratif", "5"),
    _row("Divers", "Autre motif", "4"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Index de recherche O(1)
# ─────────────────────────────────────────────────────────────────────────────
FRENCH_INDEX: Dict[str, dict] = {}
for item in FRENCH_PROTOCOL:
    FRENCH_INDEX[norm(item["motif"])] = item
    for alias in item.get("aliases", []):
        FRENCH_INDEX[norm(alias)] = item

# Dictionnaire catégorie → liste de motifs
FRENCH_MOTS_CAT: Dict[str, List[str]] = {}
for item in FRENCH_PROTOCOL:
    FRENCH_MOTS_CAT.setdefault(item["category"], []).append(item["motif"])

# Liste plate pour accès rapide en mode Tri Rapide
FRENCH_MOTIFS_RAPIDES: List[str] = [
    "Arrêt cardiorespiratoire",
    "Douleur thoracique / SCA",
    "Dyspnée / insuffisance respiratoire",
    "AVC / Déficit neurologique",
    "Altération de conscience / Coma",
    "Traumatisme crânien",
    "Hypotension artérielle",
    "Hémorragie active",
    "Tachycardie / tachyarythmie",
    "Fièvre",
    "Douleur abdominale",
    "Colique néphrétique / Douleur lombaire",
    "Allergie / anaphylaxie",
    "Hypoglycémie",
    "Convulsions / EME",
    "Céphalée",
    "Malaise",
    "Pédiatrie - Fièvre ≤ 3 mois",
    "Fièvre enfant (3 mois - 15 ans)",
    "Pédiatrie - Crise épileptique",
    "Pédiatrie - Asthme / Bronchospasme",
    "Brûlure",
    "Épistaxis",
    "Intoxication médicamenteuse",
    "Autre motif",
]


def get_protocol(motif: str) -> Optional[dict]:
    """Retourne le protocole FRENCH pour un motif donné."""
    return FRENCH_INDEX.get(norm(motif))


def get_criterion_options(motif: str) -> List[dict]:
    """Retourne la liste des critères discriminants pour un motif."""
    protocol = get_protocol(motif)
    if not protocol:
        return [{"level": None, "text": "", "label": NO_CRITERION_LABEL}]
    options = [{"level": None, "text": "", "label": NO_CRITERION_LABEL}]
    for criterion in protocol["criteria"]:
        level = criterion["level"]
        text = criterion["text"]
        options.append({"level": level, "text": text, "label": f"Tri {level} — {text}"})
    return options


def apply_discriminant_selection(
    level: str,
    justification: str,
    criterion_ref: str,
    selected: Optional[dict],
):
    """
    Applique un critère discriminant FRENCH sélectionné sans jamais downgrader le triage.
    """
    selected = selected or {}
    selected_level = selected.get("level")
    selected_text = (selected.get("text") or "").strip()
    selected_label = selected.get("label") or criterion_ref or NO_CRITERION_LABEL

    if not selected_level:
        return level, justification, criterion_ref or NO_CRITERION_LABEL

    if TRIAGE_ORDER.get(selected_level, 99) < TRIAGE_ORDER.get(level, 99):
        justification = f"{selected_text} — Critère discriminant FRENCH"
        level = selected_level

    return level, justification, selected_label


def _widget_key(motif: str, key: Optional[str] = None) -> str:
    base_key = key or f"french_disc_{norm(motif).replace(' ', '_')}"
    if st is None:
        return base_key
    prefix = str(st.session_state.get("uid") or st.session_state.get("sid") or "session")
    if base_key.startswith(f"{prefix}__"):
        return base_key
    return f"{prefix}__{base_key}"


def render_discriminants(
    motif: str,
    *,
    key: Optional[str] = None,
    label: str = "Critère discriminant",
    index: int = 0,
):
    """
    Affiche un sélecteur Streamlit des critères discriminants FRENCH.
    Retourne le critère sélectionné.
    """
    options = get_criterion_options(motif)
    if st is None:
        return options

    if not options:
        return {"level": None, "text": "", "label": NO_CRITERION_LABEL}

    index = max(0, min(index, len(options) - 1))
    selected = st.selectbox(
        label,
        options,
        index=index,
        key=_widget_key(motif, key),
        format_func=lambda opt: opt["label"],
    )
    return selected


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
