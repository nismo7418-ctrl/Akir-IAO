"""FRENCH triage v1.2 protocol data.

Structured from the local SFMU PDF supplied with the project migration work.
The criteria are intentionally short labels for decision support, not a full
replacement for clinical judgement or the official reference document.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import unicodedata


NO_CRITERION_LABEL = "Aucun critere discriminant selectionne"


def norm(value) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def _row(category: str, motif: str, default: str, criteria=(), aliases=()):
    return {
        "id": norm(motif).replace(" ", "_").replace("/", "_"),
        "category": category,
        "motif": motif,
        "default": default,
        "criteria": [{"level": level, "text": text} for level, text in criteria],
        "aliases": list(aliases),
    }


FRENCH_PROTOCOL = [
    _row("Cardio-circulatoire", "Arret cardiorespiratoire", "1"),
    _row("Cardio-circulatoire", "Hypotension arterielle", "2", [
        ("1", "PAS <= 70 mmHg"),
        ("2", "PAS <= 90 mmHg ou PAS <= 100 mmHg avec FC > 100/min"),
        ("3B", "PAS 90-100 mmHg avec FC <= 100/min"),
    ]),
    _row("Cardio-circulatoire", "Membre douloureux froid pale ischemie", "2", [
        ("2", "Duree <= 24 h, cyanose ou deficit moteur"),
        ("3B", "Duree >= 24 h"),
    ], aliases=["Membre douloureux/froid ou pale/ischemie"]),
    _row("Cardio-circulatoire", "Douleur thoracique / syndrome coronaire aigu (SCA)", "3B", [
        ("1", "ECG anormal typique de SCA"),
        ("2", "ECG anormal non typique ou douleur typique persistante/intense"),
        ("3A", "ECG normal avec comorbidite coronaire"),
        ("3B", "ECG normal avec douleur de type coronaire"),
        ("4", "ECG normal et douleur atypique"),
    ], aliases=["Douleur thoracique / SCA"]),
    _row("Cardio-circulatoire", "Malaise", "3B", [
        ("3B", "Pas d'anomalie notable des parametres vitaux ni de la glycemie"),
    ]),
    _row("Cardio-circulatoire", "Tachycardie / tachyarythmie", "3B", [
        ("1", "FC >= 180/min"),
        ("2", "FC >= 130/min"),
        ("3B", "FC > 110/min"),
        ("4", "Episode resolutif"),
    ], aliases=["Tachycardie/tachyarythmie"]),
    _row("Cardio-circulatoire", "Bradycardie / bradyarythmie", "3B", [
        ("1", "FC <= 40/min"),
        ("2", "FC 40-50/min avec mauvaise tolerance"),
        ("3B", "FC 40-50/min sans mauvaise tolerance"),
    ], aliases=["Bradycardie/bradyarythmie"]),
    _row("Cardio-circulatoire", "Dyspnee / insuffisance cardiaque", "3B", [
        ("1", "Detresse respiratoire, FR >= 40/min ou SpO2 < 86%"),
        ("2", "Dyspnee a la parole, tirage, orthopnee, FR 30-40/min ou SpO2 86-90%"),
    ]),
    _row("Cardio-circulatoire", "Dysfonction stimulateur / defibrillateur cardiaque", "3B", [
        ("2", "Choc(s) electrique(s) ressenti(s)"),
        ("3B", "Avis referent"),
    ]),
    _row("Cardio-circulatoire", "Oedeme des membres inferieurs / insuffisance cardiaque", "3B", [
        ("3B", "FR < 30/min et SpO2 > 90%"),
        ("4", "OMI chronique"),
    ]),
    _row("Cardio-circulatoire", "Palpitations", "4", [
        ("1", "FC >= 180/min"),
        ("2", "FC >= 130/min"),
        ("3B", "Malaise ou FC > 110/min"),
    ]),
    _row("Cardio-circulatoire", "Hypertension arterielle", "4", [
        ("2", "PAS IOA >= 220 mmHg ou >= 180 mmHg avec signes fonctionnels"),
        ("3B", "PAS IOA >= 180 mmHg sans signes fonctionnels"),
        ("4", "PAS < 180 mmHg"),
    ]),
    _row("Cardio-circulatoire", "Membre douloureux chaud rouge phlebite", "4", [
        ("3B", "Signes locaux francs ou siege proximal sur echographie"),
        ("4", "Signes locaux moderes ou siege distal sur echographie"),
    ], aliases=["Membre douloureux/chaud ou rouge/phlebite"]),

    _row("Infectiologie", "AES et/ou liquide biologique", "4", [
        ("2", "Sujet contact VIH avere et exposition <= 48 h"),
        ("5", "Exposition >= 48 h"),
    ]),
    _row("Infectiologie", "Fievre", "5", [
        ("2", "Temperature >= 40 C ou <= 35,2 C, confusion, cephalee ou purpura"),
        ("3B", "Mauvaise tolerance, hypotension ou shock index >= 1"),
    ]),
    _row("Infectiologie", "Exposition a une maladie contagieuse", "5", [
        ("3B", "Risque vital de contage"),
        ("5", "Sans risque vital de contage"),
    ]),

    _row("Abdominal", "Vomissement de sang / hematemese", "2", [
        ("2", "Hematemese abondante"),
        ("3B", "Vomissement(s) strie(s) de sang"),
    ], aliases=["Vomissement de sang/hematemese", "Hematemese / Rectorragie"]),
    _row("Abdominal", "Maelena / rectorragies", "2", [
        ("2", "Rectorragie abondante"),
        ("3B", "Selles souillees de sang"),
    ]),
    _row("Abdominal", "Douleur abdominale", "3B", [
        ("2", "Douleur severe et/ou mauvaise tolerance"),
        ("5", "Douleur regressive ou indolore"),
    ]),
    _row("Abdominal", "Ictere", "3B"),
    _row("Abdominal", "Probleme technique stomie cicatrices post-op", "3B", [
        ("3B", "Avis referent"),
    ], aliases=["Probleme technique (stomie, cicatrices post op...)"]),
    _row("Abdominal", "Hernie masse ou distension abdominale", "4", [
        ("2", "Douleur severe et/ou symptomes d'occlusion"),
    ], aliases=["Hernie, masse ou distension abdominale"]),
    _row("Abdominal", "Corps etranger oesophage estomac intestins", "4", [
        ("2", "Aphagie, hypersialorrhee ou autres signes fonctionnels"),
        ("3B", "Objet tranchant ou pointu"),
    ], aliases=["Corps etranger dans oesophage/estomac/intestins"]),
    _row("Abdominal", "Corps etranger dans le rectum", "4", [
        ("2", "Douleur severe et/ou rectorragie"),
    ]),
    _row("Abdominal", "Constipation", "5", [
        ("2", "Symptomes d'occlusion"),
        ("3B", "Douleur abdominale"),
    ]),
    _row("Abdominal", "Vomissements", "5", [
        ("2", "Symptomes d'occlusion"),
        ("3A", "Enfant <= 2 ans"),
        ("3B", "Douleur abdominale ou vomissements abondants"),
    ]),
    _row("Abdominal", "Diarrhee", "5", [
        ("3A", "Enfant <= 2 ans"),
        ("3B", "Diarrhee abondante et/ou mauvaise tolerance"),
    ]),
    _row("Abdominal", "Douleur anale", "5", [
        ("3B", "Suspicion abces ou fissure"),
    ]),
    _row("Abdominal", "Hoquet", "5", [
        ("3B", "Hoquet incessant >= 12 h"),
    ]),

    _row("Genito-urinaire", "Douleur de la fosse lombaire / du flanc", "3B", [
        ("2", "Douleur intense"),
        ("5", "Douleur regressive ou indolore"),
    ], aliases=["Douleur de la fosse lombaire/du flanc", "Colique nephretique / Douleur lombaire"]),
    _row("Genito-urinaire", "Retention d'urine / anurie", "3B", [
        ("2", "Douleur intense ou agitation"),
    ], aliases=["Retention d'urine/anurie"]),
    _row("Genito-urinaire", "Douleur de bourse / orchite / torsion testicule", "3B", [
        ("2", "Douleur intense ou suspicion de torsion"),
        ("3B", "Avis referent"),
    ]),
    _row("Genito-urinaire", "Dysfonction de sonde urinaire / sonde JJ / stomie", "3B", [
        ("2", "Douleur intense, fievre ou mauvaise tolerance"),
        ("3B", "Avis referent"),
    ]),
    _row("Genito-urinaire", "Hematurie", "3B", [
        ("2", "Saignement abondant actif"),
    ]),
    _row("Genito-urinaire", "Dysurie / brulure mictionnelle / infection", "5", [
        ("3B", "Fievre"),
        ("4", "Enfant"),
    ]),
    _row("Genito-urinaire", "Ecoulement ou lesion cutaneo-muqueuse genitale", "5", [
        ("3B", "Fievre"),
    ]),

    _row("Gyneco-obstetrique", "Accouchement imminent ou realise", "1", aliases=["Accouchement imminent"]),
    _row("Gyneco-obstetrique", "Probleme de grossesse 1er et 2eme trimestre", "3A", [
        ("3A", "Metrorragies ou douleur"),
    ], aliases=["Complication grossesse T1/T2"]),
    _row("Gyneco-obstetrique", "Probleme de grossesse 3eme trimestre", "3A", [
        ("3A", "Metrorragies, douleur, HTA ou perte de liquide amniotique"),
    ]),
    _row("Gyneco-obstetrique", "Meno-metrorragie", "3B", [
        ("2", "Grossesse connue/suspectee ou saignement abondant"),
    ], aliases=["Menorragie / Metrorragie"]),
    _row("Gyneco-obstetrique", "Probleme de post partum", "4", [
        ("3A", "Allaitement et fievre"),
    ]),
    _row("Gyneco-obstetrique", "Anomalie du sein", "5", [
        ("3B", "Mastite ou abces"),
    ]),
    _row("Gyneco-obstetrique", "Anomalie vulvo-vaginale / corps etranger", "5"),

    _row("Intoxication", "Intoxication medicamenteuse", "3B", [
        ("2", "Mauvaise tolerance, intention suicidaire ou toxique cardiotrope/lesionnel"),
        ("3A", "Enfant"),
        ("3B", "Avis referent"),
        ("5", "Pas de mauvaise tolerance et consultation tardive"),
    ]),
    _row("Intoxication", "Intoxication non medicamenteuse", "3B", [
        ("2", "Mauvaise tolerance ou toxique lesionnel"),
        ("3A", "Enfant"),
        ("3B", "Avis referent"),
        ("5", "Pas de mauvaise tolerance et consultation tardive"),
    ]),
    _row("Intoxication", "Demande de sevrage / toxicomanie", "4", [
        ("2", "Agitation, violence ou etat de manque"),
        ("3A", "Enfant"),
        ("5", "Demande d'ordonnance pour substitution"),
    ]),
    _row("Intoxication", "Comportement ebrieux / ivresse", "4", [
        ("1", "GCS <= 8"),
        ("2", "Agitation, violence ou GCS 9-13"),
        ("3A", "Enfant"),
        ("3B", "Demande des forces de l'ordre"),
    ]),

    _row("Neurologie", "Alteration de la conscience / coma", "2", [
        ("1", "GCS <= 8"),
        ("2", "GCS 9-13 ou avis referent"),
    ], aliases=["Alteration de conscience / Coma"]),
    _row("Neurologie", "Deficit moteur sensitif sensoriel ou du langage / AVC", "2", [
        ("1", "Delai <= 4 h 30"),
        ("3B", "Delai >= 24 h avec avis referent"),
    ], aliases=["AVC / Deficit neurologique"]),
    _row("Neurologie", "Convulsions", "3B", [
        ("2", "Crises multiples/en cours, confusion, TC, deficit ou fievre"),
        ("3B", "Recuperation complete post-critique"),
    ], aliases=["Convulsions / EME"]),
    _row("Neurologie", "Confusion / desorientation temporo-spatiale", "3B", [
        ("2", "Fievre"),
    ], aliases=["Syndrome confusionnel"]),
    _row("Neurologie", "Cephalee", "3B", [
        ("2", "Inhabituelle, premier episode, brutale, intense ou fievre"),
        ("3B", "Habituelle ou migraine"),
    ]),
    _row("Neurologie", "Vertiges / trouble de l'equilibre", "3B", [
        ("2", "Signes neurologiques associes ou cephalee brutale"),
        ("5", "Troubles anciens et stables"),
    ]),

    _row("Ophtalmologie", "Corps etranger / brulure oculaire", "3B", [
        ("2", "Douleur intense ou brulure chimique"),
        ("3B", "Avis referent"),
    ]),
    _row("Ophtalmologie", "Trouble visuel / oeil douloureux / cecite", "3B", [
        ("2", "Debut brutal"),
        ("3B", "Avis referent"),
    ]),
    _row("Ophtalmologie", "Demangeaison / oeil rouge", "5"),

    _row("ORL / Stomatologie", "Epistaxis", "3B", [
        ("2", "Saignement abondant actif"),
        ("3B", "Saignement abondant resolutif"),
        ("5", "Saignement peu abondant resolutif"),
    ]),
    _row("ORL / Stomatologie", "Trouble de l'audition / acouphenes", "4", [
        ("2", "Surdite brutale"),
    ]),
    _row("ORL / Stomatologie", "Tumefaction ORL ou cervicale", "4", [
        ("3B", "Fievre ou signes locaux importants"),
    ]),
    _row("ORL / Stomatologie", "Corps etranger ORL", "4", [
        ("2", "Dyspnee inspiratoire"),
    ]),
    _row("ORL / Stomatologie", "Pathologie de l'oreille / otite", "5"),
    _row("ORL / Stomatologie", "Douleur de gorge / angine / stomatite", "5", [
        ("3B", "Mauvaise tolerance ou aphagie"),
    ]),
    _row("ORL / Stomatologie", "Obstruction nasale / rhinite / sinusite", "5", [
        ("3B", "Sinusite febrile"),
    ]),
    _row("ORL / Stomatologie", "Probleme de dent ou de gencive", "5", [
        ("3B", "Signes locaux importants ou douleur resistante aux antalgiques"),
    ]),

    _row("Peau", "Ecchymose / hematome spontane", "3B"),
    _row("Peau", "Abces ou infection localisee de la peau", "4", [
        ("3B", "Fievre ou abces volumineux"),
    ]),
    _row("Peau", "Erytheme etendu et autres eruptions / oedeme spontane", "5", [
        ("2", "Anaphylaxie"),
        ("3B", "Fievre ou mauvaise tolerance"),
        ("4", "Etendu"),
        ("5", "Localise"),
    ], aliases=["Erytheme etendu"]),
    _row("Peau", "Morsure piqure prurit parasitose", "5", [
        ("2", "Morsure de serpent/scorpion"),
        ("3B", "Fievre ou signes locaux importants"),
        ("4", "Etendu"),
        ("5", "Localise"),
    ], aliases=["Morsure, piqure, prurit, parasitose"]),
    _row("Peau", "Corps etranger sous la peau", "5", [
        ("3B", "Corps etrangers multiples ou complexes"),
    ]),

    _row("Pediatrie <= 2 ans", "Dyspnee avec sifflement respiratoire", "2", [
        ("3A", "Sifflement sans dyspnee"),
    ], aliases=["Pediatrie - Asthme / Bronchospasme"]),
    _row("Pediatrie <= 2 ans", "Fievre <= 3 mois", "2", aliases=["Pediatrie - Fievre <= 3 mois"]),
    _row("Pediatrie <= 2 ans", "Convulsion hyperthermique", "3B", [
        ("2", "Recidive, duree >= 10 min ou hypotonie"),
        ("3A", "Recuperation complete"),
    ], aliases=["Pediatrie - Crise epileptique"]),
    _row("Pediatrie <= 2 ans", "Diarrhee / vomissements du nourrisson <= 24 mois", "3B", [
        ("2", "Perte de poids >= 10% ou hypotonie"),
        ("3A", "Age <= 6 mois"),
    ], aliases=["Pediatrie - Vomissements / Gastro-enterite"]),
    _row("Pediatrie <= 2 ans", "Troubles alimentaires du nourrisson <= 6 mois", "4", [
        ("2", "Perte de poids >= 10% ou hypotonie"),
        ("3A", "Perte de poids <= 10%"),
    ]),
    _row("Pediatrie <= 2 ans", "Bradycardie pediatrique", "4", [
        ("2", "Avant 1 an FC <= 80/min, apres 1 an FC <= 60/min"),
    ]),
    _row("Pediatrie <= 2 ans", "Ictere neonatal", "4", [
        ("2", "Perte de poids <= 10% ou selles decolorees"),
    ]),
    _row("Pediatrie <= 2 ans", "Tachycardie pediatrique", "4", [
        ("2", "Avant 1 an FC >= 180/min, apres 1 an FC >= 160/min"),
    ]),
    _row("Pediatrie <= 2 ans", "Hypotension pediatrique", "4", [
        ("2", "1-10 ans: PAS <= 70 + age x 2"),
    ]),
    _row("Pediatrie <= 2 ans", "Pleurs incoercibles", "4", [
        ("3A", "Pleurs dans le box de l'IOA"),
    ]),

    _row("Psychiatrie", "Idee / comportement suicidaire", "2"),
    _row("Psychiatrie", "Troubles du comportement / psychiatrie", "3B", [
        ("2", "Agitation, violence, delire ou hallucinations"),
        ("3A", "Enfant"),
    ]),
    _row("Psychiatrie", "Anxiete / depression / consultation psychiatrique", "4", [
        ("2", "Anxiete majeure ou attaque de panique"),
        ("3A", "Enfant"),
        ("3B", "Demande d'hospitalisation"),
    ]),

    _row("Respiratoire", "Dyspnee / insuffisance respiratoire", "3B", [
        ("1", "Detresse respiratoire, FR >= 40/min ou SpO2 < 86%"),
        ("2", "Dyspnee a la parole, tirage, orthopnee, FR 30-40/min ou SpO2 86-90%"),
    ]),
    _row("Respiratoire", "Asthme ou aggravation BPCO", "3B", [
        ("1", "Detresse respiratoire"),
        ("2", "DEP <= 200 ou dyspnee a la parole/tirage/orthopnee"),
        ("4", "DEP >= 300 l/min et asthme"),
    ]),
    _row("Respiratoire", "Hemoptysie", "3B", [
        ("1", "Detresse respiratoire"),
        ("2", "Hemoptysie repetee ou abondante"),
    ]),
    _row("Respiratoire", "Douleur thoracique / embolie / pneumopathie / pneumothorax", "3B", [
        ("1", "Detresse respiratoire"),
        ("2", "Dyspnee a la parole, tirage ou orthopnee"),
    ]),
    _row("Respiratoire", "Corps etranger voies aeriennes", "3B", [
        ("1", "Detresse respiratoire"),
        ("2", "Dyspnee a la parole, tirage ou orthopnee"),
        ("3A", "Enfant"),
        ("3B", "Pas de dyspnee"),
    ]),
    _row("Respiratoire", "Toux / bronchite", "5", [
        ("3B", "Fievre ou signes respiratoires associes"),
    ]),

    _row("Rhumatologie", "Douleur articulaire / arthrose / arthrite", "4", [
        ("3B", "Fievre ou signes locaux importants"),
    ]),
    _row("Rhumatologie", "Douleur rachidienne cervicale dorsale lombaire", "5", [
        ("2", "Deficit sensitif ou moteur associe"),
        ("3B", "Fievre ou paresthesies"),
    ], aliases=["Douleur rachidienne (cervicale, dorsale ou lombaire)"]),
    _row("Rhumatologie", "Douleur de membre / sciatique", "5", [
        ("3B", "Fievre ou impotence du membre"),
    ]),

    _row("Traumatologie", "Traumatisme avec amputation", "1"),
    _row("Traumatologie", "Traumatisme abdomen thorax cervical", "2", [
        ("1", "Penetrant"),
        ("2", "Haute velocite"),
        ("3B", "Faible velocite et mauvaise tolerance"),
        ("4", "Faible velocite sans mauvaise tolerance ou gene limitee"),
    ], aliases=["Traumatisme abdomen/thorax/cervical", "Traumatisme thorax/abdomen/rachis cervical"]),
    _row("Traumatologie", "Agression sexuelle et sevices", "2"),
    _row("Traumatologie", "Brulure", "3B", [
        ("2", "Brulure etendue, main ou visage"),
        ("3A", "Age <= 24 mois et brulure peu etendue"),
        ("3B", "Avis referent"),
        ("5", "Brulure peu etendue, consultation tardive"),
    ]),
    _row("Traumatologie", "Traumatisme bassin hanche femur rachis", "3B", [
        ("2", "Haute velocite"),
        ("3B", "Faible velocite et mauvaise tolerance"),
        ("4", "Faible velocite sans mauvaise tolerance ou gene limitee"),
    ], aliases=["Traumatisme bassin/hanche/femur"]),
    _row("Traumatologie", "Traumatisme oculaire", "3B", [
        ("2", "Haute velocite"),
        ("3B", "Faible velocite et mauvaise tolerance"),
        ("4", "Faible velocite sans mauvaise tolerance ou gene limitee"),
    ]),
    _row("Traumatologie", "Traumatisme maxillo-facial / oreille", "3B", [
        ("2", "Haute velocite"),
        ("3B", "Faible velocite et mauvaise tolerance"),
        ("4", "Faible velocite sans mauvaise tolerance ou gene limitee"),
    ]),
    _row("Traumatologie", "Plaie", "4", [
        ("2", "Plaie delabrante ou saignement actif"),
        ("3B", "Plaie large, complexe ou de la main"),
        ("4", "Plaie superficielle hors main"),
        ("5", "Excoriation"),
    ]),
    _row("Traumatologie", "Traumatisme d'epaule ou distal de membre", "4", [
        ("2", "Haute velocite, grande deformation ou ischemie"),
        ("3B", "Impotence totale ou deformation"),
        ("4", "Impotence moderee ou petite deformation"),
        ("5", "Ni impotence ni deformation"),
    ], aliases=["Traumatisme membre / epaule"]),
    _row("Traumatologie", "Electrisation", "4", [
        ("2", "Perte de connaissance, brulure ou foudre"),
        ("3B", "Haute tension ou temps de contact long"),
        ("4", "Courant domestique"),
    ]),
    _row("Traumatologie", "Traumatisme cranien", "5", [
        ("1", "Coma GCS <= 8"),
        ("2", "GCS 9-13, deficit neurologique, convulsion, otorragie, AOD/AVK ou vomissements repetes"),
        ("3B", "Perte de connaissance avant ou apres"),
        ("4", "Plaie ou hematome"),
    ]),

    _row("Divers", "Pathologie rare et grave en poussee", "2", [
        ("3B", "Avis referent"),
    ]),
    _row("Divers", "Hypothermie", "2", [
        ("1", "Temperature <= 32 C"),
        ("2", "Temperature 32-35,2 C"),
    ]),
    _row("Divers", "Hyperglycemie", "3B", [
        ("2", "Cetose elevee ou trouble de conscience"),
        ("3B", "Glycemie >= 20 mmol/l ou cetose positive"),
        ("4", "Glycemie <= 20 mmol/l et cetose negative"),
    ], aliases=["Hyperglycemie / Cetoacidose"]),
    _row("Divers", "Hypoglycemie", "3B", [
        ("1", "Coma GCS <= 8"),
        ("2", "Mauvaise tolerance ou GCS 9-13"),
    ]),
    _row("Divers", "Anomalie de resultat biologique", "3B", [
        ("2", "Symptomatique"),
        ("3B", "Avis referent"),
    ]),
    _row("Divers", "AEG / Asthenie", "3B", [
        ("3B", "Signes objectifs d'alteration de l'etat general"),
        ("5", "Ni comorbidites ni signes objectifs"),
    ]),
    _row("Divers", "Coup de chaleur / insolation", "3B", [
        ("1", "Coma GCS <= 8"),
        ("2", "Temperature >= 40 C ou GCS 9-13"),
    ]),
    _row("Divers", "Gelure / lesions liees au froid", "3B", [
        ("2", "Necrose, deficit sensitif ou moteur"),
    ]),
    _row("Divers", "Allergie", "4", [
        ("2", "Dyspnee, risque d'obstruction ou mauvaise tolerance"),
    ], aliases=["Allergie / anaphylaxie"]),
    _row("Divers", "Probleme suite de soins", "5"),
    _row("Divers", "Renouvellement ordonnance", "5"),
    _row("Divers", "Examen administratif / certificat / requisition", "5", [
        ("3B", "Demande des forces de l'ordre"),
    ], aliases=["Examen administratif"]),
    _row("Divers", "Demande d'hebergement pour raison sociale", "5"),
    _row("Divers", "Autre motif", "5"),
]


FRENCH_INDEX: Dict[str, dict] = {}
for item in FRENCH_PROTOCOL:
    FRENCH_INDEX[norm(item["motif"])] = item
    for alias in item.get("aliases", []):
        FRENCH_INDEX[norm(alias)] = item

FRENCH_MOTS_CAT: Dict[str, List[str]] = {}
for item in FRENCH_PROTOCOL:
    FRENCH_MOTS_CAT.setdefault(item["category"], []).append(item["motif"])

FRENCH_MOTIFS_RAPIDES = [
    "Arret cardiorespiratoire",
    "Douleur thoracique / syndrome coronaire aigu (SCA)",
    "Dyspnee / insuffisance respiratoire",
    "Deficit moteur sensitif sensoriel ou du langage / AVC",
    "Alteration de la conscience / coma",
    "Traumatisme cranien",
    "Hypotension arterielle",
    "Fievre",
    "Hypoglycemie",
    "Hyperglycemie",
    "Convulsions",
    "Hemoptysie",
    "Asthme ou aggravation BPCO",
    "Brulure",
    "Traumatisme abdomen thorax cervical",
    "Pediatrie - Fievre <= 3 mois",
    "Autre motif",
]


def get_protocol(motif: str) -> Optional[dict]:
    return FRENCH_INDEX.get(norm(motif))


def get_criterion_options(motif: str) -> List[dict]:
    protocol = get_protocol(motif)
    if not protocol:
        return [{"level": None, "text": "", "label": NO_CRITERION_LABEL}]
    options = [{"level": None, "text": "", "label": NO_CRITERION_LABEL}]
    for criterion in protocol["criteria"]:
        level = criterion["level"]
        text = criterion["text"]
        options.append({"level": level, "text": text, "label": f"Tri {level} - {text}"})
    return options
