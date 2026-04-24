# config.py — Constantes cliniques AKIR-IAO v18.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Toutes les "magic numbers" cliniques sont nommées ici.
# Modifier une dose = modifier uniquement ce fichier.

# ── Labels de triage ─────────────────────────────────────────────────────────
LABELS = {
    "M":  "TRI M — IMMÉDIAT",
    "1":  "TRI 1 — URGENCE EXTRÊME",
    "2":  "TRI 2 — TRÈS URGENT",
    "3A": "TRI 3A — URGENT",
    "3B": "TRI 3B — URGENT DIFFÉRÉ",
    "4":  "TRI 4 — MOINS URGENT",
    "5":  "TRI 5 — NON URGENT",
}
SECTEURS = {
    "M":  "Déchocage — Immédiat",
    "1":  "Déchocage — Immédiat",
    "2":  "Soins aigus — Méd. < 20 min",
    "3A": "Soins aigus — Méd. < 30 min",
    "3B": "Polyclinique — Méd. < 1 h",
    "4":  "Consultation — Méd. < 2 h",
    "5":  "Salle d'attente — Réorientation MG",
}
DELAIS  = {"M": 5, "1": 5, "2": 15, "3A": 30, "3B": 60, "4": 120, "5": 999}
TCSS    = {"M": "tri-M", "1": "tri-1", "2": "tri-2",
           "3A": "tri-3A", "3B": "tri-3B", "4": "tri-4", "5": "tri-5"}
HBCSS   = {"M": "hb-M", "1": "hb-1", "2": "hb-2",
           "3A": "hb-3A", "3B": "hb-3B", "4": "hb-4", "5": "hb-5"}
ORD     = {"M": 0, "1": 1, "2": 2, "3A": 3, "3B": 4, "4": 5, "5": 6}

# ── Seuils glycémiques — unité mg/dl (standard belge BCFI) ───────────────────
GLYC = {
    "hs":  54,   # Hypoglycémie sévère    < 3,0 mmol/l
    "hm":  70,   # Hypoglycémie modérée  < 3,9 mmol/l
    "Hs": 180,   # Hyperglycémie          > 10,0 mmol/l
    "Hs2":360,   # Hyperglycémie sévère   > 20,0 mmol/l
}

# ── NEWS2 — RCP London 2017 ───────────────────────────────────────────────────
NEWS2_TRI_M         = 9   # Engagement vital — Tri M
NEWS2_RISQUE_ELEVE  = 7   # Appel médical immédiat
NEWS2_RISQUE_MOD    = 5   # Surveillance rapprochée

# ── SIPA — Shock Index Pédiatrique — Acker 2015 ──────────────────────────────
SIPA_0_1AN   = 2.2
SIPA_1_4ANS  = 2.0
SIPA_4_7ANS  = 1.8
SIPA_7_12ANS = 1.7

# ── AVC — Délai thrombolyse — ESO/AHA 2023 ───────────────────────────────────
AVC_DELAI_THROMBOLYSE_H = 4.5

# ── Paracétamol IV — BCFI ────────────────────────────────────────────────────
PARA_DOSE_KG        = 15.0   # mg/kg pour poids < 50 kg
PARA_DOSE_FIXE_G    = 1.0    # g — dose fixe adulte ≥ 50 kg
PARA_POIDS_PIVOT_KG = 50.0   # kg — pivot adulte/enfant

# ── Glucose 30 % — BCFI ──────────────────────────────────────────────────────
GLUCOSE_DOSE_KG  = 0.3    # g/kg
GLUCOSE_MAX_G    = 15.0   # g — plafond adulte

# ── Adrénaline IM — BCFI / EAACI 2023 ────────────────────────────────────────
ADRE_POIDS_ADULTE_KG = 30.0  # kg — seuil adulte
ADRE_DOSE_ADULTE_MG  = 0.5   # mg — adulte ≥ 30 kg
ADRE_DOSE_KG         = 0.01  # mg/kg — enfant < 30 kg

# ── Piritramide IV — BCFI / SFAR 2010 ────────────────────────────────────────
PIRI_BOLUS_MIN    = 0.03   # mg/kg — bolus minimal
PIRI_BOLUS_MAX    = 0.05   # mg/kg — bolus maximal
PIRI_PLAFOND_LT70 = 3.0    # mg — plafond bolus < 70 kg
PIRI_PLAFOND_GE70 = 6.0    # mg — plafond bolus ≥ 70 kg

# ── Naloxone IV — BCFI ───────────────────────────────────────────────────────
NALOO_ADULTE_MG = 0.4    # mg — adulte sans dépendance
NALOO_PED_KG    = 0.01   # mg/kg — pédiatrique
NALOO_DEP_MG    = 0.04   # mg — dépendance (titration douce)

# ── Morphine IV — BCFI ───────────────────────────────────────────────────────
MORPH_MIN_KG       = 0.05   # mg/kg — bolus minimal
MORPH_MAX_KG       = 0.10   # mg/kg — bolus maximal
MORPH_PLAFOND_STD  = 5.0    # mg — plafond bolus < 100 kg
MORPH_PLAFOND_GE100= 7.5    # mg — plafond bolus ≥ 100 kg
MORPH_PALIER_MG    = 2.0    # mg — palier de titration

# ── Ceftriaxone IV — BCFI / SPILF 2017 ──────────────────────────────────────
CEFRTRX_ADULTE_G  = 2.0    # g — dose adulte fixe
CEFRTRX_PED_KG    = 0.1    # g/kg — dose pédiatrique

# ── Litican IM — BCFI / Protocole local Hainaut ──────────────────────────────
LITICAN_DOSE_ADULTE_MG  = 40.0    # mg — adulte
LITICAN_DOSE_KG_ENF     = 1.0     # mg/kg — enfant
LITICAN_DOSE_MAX_ENF_MG = 40.0    # mg — plafond enfant
LITICAN_DOSE_MAX_JOUR   = 120.0   # mg/24 h — max journalier
LITICAN_POIDS_PIVOT_KG  = 15.0    # kg — pivot adulte/enfant

# ── Protocole épilepsie pédiatrique — SFNP / ISPE 2022 ───────────────────────
MIDAZOLAM_BUCC_KG       = 0.3     # mg/kg — Midazolam buccal
MIDAZOLAM_BUCC_MAX_MG   = 10.0    # mg
MIDAZOLAM_IM_IN_KG      = 0.2     # mg/kg — Midazolam IM / intranasale
MIDAZOLAM_IM_IN_MAX_MG  = 10.0    # mg
DIAZEPAM_RECT_KG        = 0.5     # mg/kg — Diazépam rectal
DIAZEPAM_RECT_MAX_MG    = 10.0    # mg
DIAZEPAM_IV_KG          = 0.3     # mg/kg — Diazépam IV
DIAZEPAM_IV_MAX_MG      = 10.0    # mg
LORAZEPAM_IV_KG         = 0.1     # mg/kg — Lorazépam IV (Temesta)
LORAZEPAM_IV_MAX_MG     = 4.0     # mg
CLONAZEPAM_IV_KG        = 0.02    # mg/kg — Clonazépam IV (Rivotril)
CLONAZEPAM_IV_MAX_MG    = 1.0     # mg
PHENOBARB_IV_KG         = 20.0    # mg/kg — Phénobarbital IV (charge)
PHENOBARB_IV_MAX_MG     = 1000.0  # mg
PHENOBARB_DEBIT_MG_KG_MIN = 1.0   # mg/kg/min — débit max
LEVETI_IV_KG            = 60.0    # mg/kg — Lévétiracétam IV (Keppra)
LEVETI_IV_MAX_MG        = 4500.0  # mg
VALPROATE_IV_KG         = 40.0    # mg/kg — Valproate IV (Dépakine)
VALPROATE_IV_MAX_MG     = 3000.0  # mg
VALPROATE_IV_DEBIT_MIN  = 6.0     # min — durée perfusion minimale
FLUMAZENIL_DOSE_MG      = 0.01    # mg/kg — Flumazénil (Anexate)
FLUMAZENIL_MAX_MG       = 0.2     # mg — dose initiale max
FLUMAZENIL_MAX_TOTAL    = 1.0     # mg — dose totale max

# ── Seuils temporels EME — ILAE 2015 ─────────────────────────────────────────
EME_SEUIL_MIN        = 5    # min — traitement actif si > 5 min
EME_OPERATIONNEL_MIN = 15   # min — risque lésionnel
EME_ETABLI_MIN       = 30   # min — réanimation pédiatrique

# ── Pédiatrie — Fièvre et déshydratation ─────────────────────────────────────
FIEVRE_TRES_HAUTE_ENFANT = 40.0   # °C — critère de gravité
FIEVRE_NOURR_SEUIL       = 38.0   # °C — seuil nourrisson < 3 mois
FIEVRE_HAUT_RISQUE_AGE   = 0.25   # ans — < 3 mois = haut risque

FC_TACHY_NOURR  = 160  # bpm — nourrisson 0-1 mois
FC_TACHY_BEBE   = 150  # bpm — bébé 1-12 mois
FC_TACHY_ENFANT = 140  # bpm — enfant 1-5 ans
FC_TACHY_GRAND  = 120  # bpm — enfant 5-12 ans

VOMISS_FREQ_SEVERE = 6  # > 6/h — vomissements très fréquents

# ── Persistance RGPD ─────────────────────────────────────────────────────────
REGISTRE_CAP = 500  # nb max d'entrées conservées (rotation FIFO)

# ── Antécédents disponibles en multiselect ───────────────────────────────────
ATCD = [
    "HTA", "Diabète type 1", "Diabète type 2", "Tabagisme actif", "Dyslipidémie",
    "ATCD familial coronarien", "Insuffisance cardiaque", "BPCO",
    "Anticoagulants/AOD", "Grossesse en cours", "Immunodépression",
    "Néoplasie évolutive", "Épilepsie", "Insuffisance rénale chronique",
    "Ulcère gastro-duodénal", "Insuffisance hépatique",
    "Déficit vitamine B12", "Drépanocytose", "Chimiothérapie en cours",
    "IMAO (inhibiteurs MAO)", "Antidépresseurs ISRS/IRSNA",
    "Glaucome", "Adénome prostatique", "Rétention urinaire",
]

# ── CFS — Clinical Frailty Scale ─────────────────────────────────────────────
CFS_LBL = {
    1: "Très en forme", 2: "En forme", 3: "Bien portant", 4: "Vulnérable",
    5: "Fragilité légère", 6: "Fragilité modérée", 7: "Fragilité sévère",
    8: "Fragilité très sévère", 9: "Maladie terminale",
}

# ── Motifs de triage — FRENCH V1.1 ───────────────────────────────────────────
MOTS_CAT = {
    "Cardio": [
        "Arret cardio-respiratoire", "Hypotension arterielle",
        "Douleur thoracique / SCA", "Tachycardie / tachyarythmie",
        "Bradycardie / bradyarythmie", "Palpitations",
        "Hypertension arterielle", "Allergie / anaphylaxie",
    ],
    "Respiratoire": [
        "Dyspnee / insuffisance respiratoire",
        "Dyspnee / insuffisance cardiaque",
    ],
    "Digestif": [
        "Douleur abdominale", "Vomissements / Diarrhee",
        "Hematemese / Rectorragie",
        "Colique nephretique / Douleur lombaire",
    ],
    "Neuro": [
        "AVC / Deficit neurologique", "Traumatisme cranien",
        "Alteration de conscience / Coma", "Cephalee",
        "Convulsions / EME", "Syndrome confusionnel", "Malaise",
    ],
    "Trauma": [
        "Traumatisme thorax/abdomen/rachis cervical",
        "Traumatisme bassin/hanche/femur",
        "Traumatisme membre / epaule",
        "Hemorragie active",
    ],
    "Infectio": ["Fievre"],
    "Pediatrie": [
        "Pediatrie - Fievre <= 3 mois",
        "Pediatrie - Fievre enfant (3 mois - 15 ans)",
        "Pediatrie - Vomissements / Gastro-enterite",
        "Pediatrie - Crise epileptique",
        "Pediatrie - Asthme / Bronchospasme",
    ],
    "Peau":       ["Petechie / Purpura", "Erytheme etendu"],
    "Gyneco":     ["Accouchement imminent", "Complication grossesse T1/T2",
                   "Menorragie / Metrorragie"],
    "Metabolique":["Hypoglycemie", "Hyperglycemie / Cetoacidose"],
    "Divers":     ["Renouvellement ordonnance", "Examen administratif"],
}

MOTIFS_RAPIDES = [
    "Douleur thoracique / SCA",
    "Dyspnee / insuffisance respiratoire",
    "AVC / Deficit neurologique",
    "Alteration de conscience / Coma",
    "Traumatisme cranien",
    "Hypotension arterielle",
    "Hemorragie active",
    "Tachycardie / tachyarythmie",
    "Fievre",
    "Douleur abdominale",
    "Colique nephretique / Douleur lombaire",
    "Allergie / anaphylaxie",
    "Hypoglycemie",
    "Convulsions / EME",
    "Pediatrie - Fievre <= 3 mois",
    "Pediatrie - Fievre enfant (3 mois - 15 ans)",
    "Pediatrie - Vomissements / Gastro-enterite",
    "Pediatrie - Crise epileptique",
    "Pediatrie - Asthme / Bronchospasme",
    "Autre motif",
]