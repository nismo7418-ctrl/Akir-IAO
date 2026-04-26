# clinical/french_v12.py — Données protocole FRENCH Triage V1.2
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Source : SFMU — Classification FRENCH Triage V1.1, 2018

from __future__ import annotations
from typing import Dict, List, Optional, TypedDict
from clinical.utils import norm

NO_CRITERION_LABEL = "Aucun critère discriminant sélectionné"


class CriterionOption(TypedDict):
    level: Optional[str]
    text: str
    label: str


class CriterionEntry(TypedDict):
    level: str
    text: str


class ProtocolRow(TypedDict):
    id: str
    category: str
    motif: str
    default: str
    criteria: List[CriterionEntry]
    aliases: List[str]


class RedFlagDefinition(TypedDict, total=False):
    key: str
    label: str
    level: str
    rationale: str
    detail_key: str
    help: str


def _row(category: str, motif: str, default: str, criteria=(), aliases=()) -> ProtocolRow:
    return {
        "id": norm(motif).replace(" ", "_").replace("/", "_"),
        "category": category,
        "motif": motif,
        "default": default,
        "criteria": [{"level": level, "text": text} for level, text in criteria],
        "aliases": list(aliases),
    }


def _flag(
    *,
    key: str,
    label: str,
    level: str,
    rationale: str,
    detail_key: Optional[str] = None,
    help_text: str = "",
) -> RedFlagDefinition:
    flag: RedFlagDefinition = {
        "key": key,
        "label": label,
        "level": level,
        "rationale": rationale,
    }
    if detail_key:
        flag["detail_key"] = detail_key
    if help_text:
        flag["help"] = help_text
    return flag


FRENCH_PROTOCOL: List[ProtocolRow] = [
    # ── CARDIAQUE / VASCULAIRE ────────────────────────────────────────────
    _row("Cardiovasculaire", "Arrêt cardiorespiratoire", "M"),
    _row("Cardiovasculaire", "Douleur thoracique / SCA", "3A", [
        ("1", "Arrêt cardio-respiratoire ou instabilité hémodynamique"),
        ("2", "Douleur thoracique typique ou signes d'instabilité"),
        ("3A", "Douleur thoracique atypique"),
        ("3B", "Douleur thoracique peu évocatrice"),
    ], aliases=["Douleur thoracique / syndrome coronaire aigu (SCA)", "SCA", "Infarctus"]),
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
    ], aliases=["Hématemèse", "Rectorragie", "Méléna", "Hematémèse / vomissements sanglants", "Rectorragie / méléna"]),
    _row("Digestif", "Colique néphrétique / Douleur lombaire", "3B", [
        ("2", "Fièvre + douleur lombaire — Pyélonéphrite obstructive"),
        ("3A", "EVA ≥ 7"),
        ("3B", "EVA 4-6"),
        ("4", "EVA < 4"),
    ], aliases=["Colique nephretique", "Lithiase urinaire"]),

    # ── NEUROLOGIQUE ──────────────────────────────────────────────────────
    _row("Neurologique", "AVC / Déficit neurologique", "2", [
        ("1", "GCS < 13 ou choc"),
        ("2", "Code Stroke — BE-FAST positif"),
        ("2", "Déficit focal d'installation brutale"),
    ], aliases=["AVC", "Stroke", "Code Stroke", "Déficit neurologique", "Déficit moteur sensitif sensoriel ou du langage / AVC"]),
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
    ], aliases=["Coma", "Altération de la conscience / coma", "Alteration de conscience / Coma"]),
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
    ], aliases=["Épilepsie", "Convulsions", "EME", "Crise épileptique"]),
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
    ], aliases=["Pediatrie - Fievre <= 3 mois", "Fièvre nourrisson"]),
    _row("Pédiatrie", "Fièvre enfant (3 mois - 15 ans)", "4", [
        ("2", "T° ≥ 40 °C ou somnolence / geignement / marbrures"),
        ("3A", "Tachycardie pour l'âge ou mauvaise tolérance"),
    ], aliases=["Pediatrie - Fievre enfant (3 mois - 15 ans)"]),
    _row("Pédiatrie", "Pédiatrie - Vomissements / Gastro-entérite", "4", [
        ("2", "Nourrisson / déshydratation sévère"),
        ("3A", "Enfant avec sang dans selles"),
        ("4", "Gastro-entérite bien tolérée"),
    ], aliases=["Pediatrie - Vomissements / Gastro-enterite"]),
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
    _row("Gynécologie", "Accouchement imminent", "1"),
    _row("Gynécologie", "Complication grossesse T1/T2", "2", [
        ("1", "Choc / hémorragie abondante"),
        ("2", "GEU suspecté / douleur + métrorragies"),
        ("3A", "Métrorragies modérées"),
    ], aliases=["GEU", "Grossesse extra-utérine"]),
    _row("Gynécologie", "Ménorragie / Métrorragie", "3A", [
        ("2", "Instabilité hémodynamique"),
        ("3A", "Saignement abondant"),
        ("4", "Saignement modéré"),
    ]),

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
FRENCH_INDEX: Dict[str, ProtocolRow] = {}
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


FRENCH_RED_FLAGS: Dict[str, List[RedFlagDefinition]] = {
    norm("Céphalée"): [
        _flag(
            key="cephalee_debut_brutal",
            label="Début brutal ?",
            level="3A",
            rationale="Céphalée d'installation brutale",
            detail_key="brutal",
        ),
        _flag(
            key="cephalee_coup_tonnerre",
            label="Céphalée en coup de tonnerre ?",
            level="1",
            rationale="HSA ou urgence neurovasculaire à exclure",
            detail_key="explosif",
        ),
        _flag(
            key="cephalee_signes_neuro",
            label="Signes neurologiques ?",
            level="2",
            rationale="Céphalée avec déficit neurologique associé",
            detail_key="neurologique",
        ),
        _flag(
            key="cephalee_fievre",
            label="Fièvre ?",
            level="3A",
            rationale="Cause infectieuse ou inflammatoire à documenter",
            detail_key="fievre_associee",
        ),
        _flag(
            key="cephalee_raideur_nuque",
            label="Raideur de nuque ?",
            level="1",
            rationale="Méningisme associé",
            detail_key="raideur_nuque",
        ),
    ],
    norm("Douleur abdominale"): [
        _flag(
            key="abdomen_defense",
            label="Défense abdominale ?",
            level="2",
            rationale="Abdomen chirurgical suspecté",
            detail_key="defense",
        ),
        _flag(
            key="abdomen_contracture",
            label="Contracture ?",
            level="2",
            rationale="Irritation péritonéale",
            detail_key="contracture",
        ),
        _flag(
            key="abdomen_douleur_dorsale",
            label="Irradiation dorsale ?",
            level="2",
            rationale="Dissection ou atteinte rétro-péritonéale à exclure",
            detail_key="irradiation_dorsale",
        ),
        _flag(
            key="abdomen_syncope",
            label="Malaise ou syncope ?",
            level="2",
            rationale="Instabilité potentielle",
            detail_key="syncopal",
        ),
        _flag(
            key="abdomen_metrorragies",
            label="Métrorragies associées ?",
            level="2",
            rationale="Urgence gynécologique possible",
            detail_key="metrorragies",
        ),
    ],
    norm("Traumatisme crânien"): [
        _flag(
            key="tc_pdc",
            label="Perte de connaissance ?",
            level="2",
            rationale="Traumatisme crânien avec PDC",
            detail_key="perte_connaissance",
        ),
        _flag(
            key="tc_pdc_prolongee",
            label="Perte de connaissance prolongée ?",
            level="1",
            rationale="Traumatisme crânien grave",
            detail_key="perte_connaissance_prolongee",
        ),
        _flag(
            key="tc_vomissements",
            label="Vomissements ?",
            level="2",
            rationale="Risque intracrânien accru",
            detail_key="vomissements",
        ),
        _flag(
            key="tc_anticoagulants",
            label="Sous anticoagulants ?",
            level="2",
            rationale="Risque neuro-hémorragique majoré",
            detail_key="anticoagulants",
        ),
        _flag(
            key="tc_cephalee",
            label="Céphalée post-traumatique ?",
            level="3A",
            rationale="Surveillance neurologique nécessaire",
            detail_key="cephalee_post_tc",
        ),
    ],
    norm("Dyspnée / insuffisance respiratoire"): [
        _flag(
            key="dyspnee_cyanose",
            label="Cyanose ?",
            level="2",
            rationale="Défaillance respiratoire",
            detail_key="cyanose",
        ),
        _flag(
            key="dyspnee_tirage",
            label="Tirage ou lutte respiratoire ?",
            level="2",
            rationale="Travail respiratoire majeur",
            detail_key="tirage",
        ),
        _flag(
            key="dyspnee_parole_limitee",
            label="Impossible de parler en phrases complètes ?",
            level="2",
            rationale="Tolérance respiratoire altérée",
            detail_key="parole_limitee",
        ),
        _flag(
            key="dyspnee_orthopnee",
            label="Orthopnée ?",
            level="3A",
            rationale="Congestion ou décompensation cardiaque possible",
            detail_key="orthopnee",
        ),
    ],
    norm("AVC / Déficit neurologique"): [
        _flag(
            key="avc_fast",
            label="BE-FAST positif ?",
            level="2",
            rationale="Code stroke à déclencher",
            detail_key="fast_positif",
        ),
        _flag(
            key="avc_deficit_brutal",
            label="Déficit focal brutal ?",
            level="2",
            rationale="Déficit neurologique d'installation brutale",
            detail_key="avc_suspect",
        ),
        _flag(
            key="avc_hemiplegie",
            label="Hémiplégie franche ?",
            level="1",
            rationale="Déficit neurologique sévère",
            detail_key="hemiplegique",
        ),
        _flag(
            key="avc_aphasie",
            label="Aphasie ou trouble du langage ?",
            level="2",
            rationale="Atteinte neurologique focale",
            detail_key="aphasie",
        ),
    ],
    norm("Fièvre"): [
        _flag(
            key="fievre_purpura",
            label="Purpura non effaçable ?",
            level="1",
            rationale="Purpura fulminans suspecté",
            detail_key="purpura",
        ),
        _flag(
            key="fievre_raideur_nuque",
            label="Raideur de nuque ?",
            level="1",
            rationale="Méningite à exclure",
            detail_key="raideur_nuque",
        ),
        _flag(
            key="fievre_confusion",
            label="Confusion ou désorientation ?",
            level="2",
            rationale="Signe de gravité infectieux",
            detail_key="confusion",
        ),
        _flag(
            key="fievre_mauvaise_tolerance",
            label="Mauvaise tolérance hémodynamique ?",
            level="2",
            rationale="Risque de sepsis sévère",
            detail_key="mauvaise_tolerance",
        ),
    ],
    norm("Allergie / anaphylaxie"): [
        _flag(
            key="ana_dyspnee",
            label="Dyspnée ou stridor ?",
            level="1",
            rationale="Anaphylaxie sévère",
            detail_key="dyspnee",
        ),
        _flag(
            key="ana_hypotension",
            label="Hypotension, malaise ou collapsus ?",
            level="1",
            rationale="Choc anaphylactique possible",
            detail_key="mauvaise_tolerance",
        ),
        _flag(
            key="ana_urticaire",
            label="Urticaire généralisée ?",
            level="2",
            rationale="Réaction allergique systémique",
            detail_key="urticaire_generalisee",
        ),
        _flag(
            key="ana_oedeme",
            label="Oedème facial ou lingual ?",
            level="2",
            rationale="Atteinte des voies aériennes supérieures",
            detail_key="angioedeme",
        ),
    ],
    norm("Hémorragie active"): [
        _flag(
            key="hemorragie_active",
            label="Saignement actif non contrôlé ?",
            level="2",
            rationale="Hémorragie active",
            detail_key="active",
        ),
        _flag(
            key="hemorragie_abondante",
            label="Saignement abondant ?",
            level="2",
            rationale="Perte sanguine importante",
            detail_key="abondante",
        ),
        _flag(
            key="hemorragie_anticoagulants",
            label="Sous anticoagulants ?",
            level="2",
            rationale="Risque de saignement majoré",
            detail_key="anticoagulants",
        ),
    ],
    norm("Traumatisme thorax/abdomen/rachis cervical"): [
        _flag(
            key="trauma_axial_haute_energie",
            label="Mécanisme à haute énergie ?",
            level="2",
            rationale="Traumatisme axial à haut risque",
            detail_key="haute_energie",
        ),
        _flag(
            key="trauma_axial_sangle",
            label="Signe de ceinture ou impact axial ?",
            level="2",
            rationale="Lésions internes possibles",
            detail_key="sangle",
        ),
        _flag(
            key="trauma_axial_dyspnee",
            label="Dyspnée ou douleur thoracique post-trauma ?",
            level="2",
            rationale="Atteinte thoracique associée",
            detail_key="dyspnee_post_trauma",
        ),
    ],
}


def get_protocol(motif: str) -> Optional[ProtocolRow]:
    """Retourne le protocole FRENCH pour un motif donné."""
    return FRENCH_INDEX.get(norm(motif))


def get_criterion_options(motif: str) -> List[CriterionOption]:
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


def get_red_flag_definitions(motif: str) -> List[RedFlagDefinition]:
    """Retourne la checklist de red flags pour un motif, avec fallback générique FRENCH."""
    protocol = get_protocol(motif)
    if not protocol:
        return []

    custom_flags = FRENCH_RED_FLAGS.get(norm(protocol["motif"]))
    if custom_flags:
        return custom_flags

    generated_flags: List[RedFlagDefinition] = []
    for index, criterion in enumerate(protocol.get("criteria", []), start=1):
        level = str(criterion.get("level") or protocol.get("default") or "3B")
        text = str(criterion.get("text") or "").strip()
        if not text:
            continue
        generated_flags.append(
            _flag(
                key=f"{protocol['id']}_rf_{index}",
                label=text,
                level=level,
                rationale=f"Discriminant FRENCH V1.2 Tri {level}",
            )
        )
    return generated_flags


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
    try:
        import streamlit as st
    except Exception:
        return options

    if not options:
        return {"level": None, "text": "", "label": NO_CRITERION_LABEL}

    index = max(0, min(index, len(options) - 1))
    selected = st.selectbox(
        label,
        options,
        index=index,
        key=key,
        format_func=lambda opt: opt["label"],
    )
    return selected
