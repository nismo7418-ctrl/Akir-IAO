# config.py — Constantes cliniques AKIR-IAO

LABELS = {
    "M":"TRI M — IMMÉDIAT","1":"TRI 1 — URGENCE EXTRÊME","2":"TRI 2 — TRÈS URGENT",
    "3A":"TRI 3A — URGENT","3B":"TRI 3B — URGENT DIFFÉRÉ",
    "4":"TRI 4 — MOINS URGENT","5":"TRI 5 — NON URGENT"
}
SECTEURS = {
    "M":"Déchocage — Immédiat","1":"Déchocage — Immédiat",
    "2":"Soins aigus — Méd. <20 min","3A":"Soins aigus — Méd. <30 min",
    "3B":"Polyclinique — Méd. <1 h","4":"Consultation — Méd. <2 h",
    "5":"Salle d'attente — Réorientation MG"
}
DELAIS   = {"M":5,"1":5,"2":15,"3A":30,"3B":60,"4":120,"5":999}
TCSS     = {"M":"tri-M","1":"tri-1","2":"tri-2","3A":"tri-3A","3B":"tri-3B","4":"tri-4","5":"tri-5"}
HBCSS    = {"M":"hb-M","1":"hb-1","2":"hb-2","3A":"hb-3A","3B":"hb-3B","4":"hb-4","5":"hb-5"}
ORD      = {"M":0,"1":1,"2":2,"3A":3,"3B":4,"4":5,"5":6}

GLYC = {
    "hs":  54,   # Hypoglycémie sévère    < 3,0 mmol/l
    "hm":  70,   # Hypoglycémie modérée  < 3,9 mmol/l
    "Hs": 180,   # Hyperglycémie          > 10,0 mmol/l
    "Hs2":360,   # Hyperglycémie sévère   > 20,0 mmol/l
}

NEWS2_TRI_M         = 9
NEWS2_RISQUE_ELEVE  = 7
NEWS2_RISQUE_MOD    = 5

SIPA_0_1AN  = 2.2
SIPA_1_4ANS = 2.0
SIPA_4_7ANS = 1.8
SIPA_7_12ANS= 1.7

AVC_DELAI_THROMBOLYSE_H = 4.5

PARA_DOSE_KG          = 15.0
PARA_DOSE_FIXE_G      = 1.0
PARA_POIDS_PIVOT_KG   = 50.0
GLUCOSE_DOSE_KG       = 0.3
GLUCOSE_MAX_G         = 15.0
ADRE_POIDS_ADULTE_KG  = 30.0
ADRE_DOSE_ADULTE_MG   = 0.5
ADRE_DOSE_KG          = 0.01
PIRI_BOLUS_MIN        = 0.03
PIRI_BOLUS_MAX        = 0.05
PIRI_PLAFOND_LT70     = 3.0
PIRI_PLAFOND_GE70     = 6.0
NALOO_ADULTE_MG       = 0.4
NALOO_PED_KG          = 0.01
NALOO_DEP_MG          = 0.04
MORPH_MIN_KG          = 0.05
MORPH_MAX_KG          = 0.10
MORPH_PLAFOND_STD     = 5.0
MORPH_PLAFOND_GE100   = 7.5
MORPH_PALIER_MG       = 2.0
CEFRTRX_ADULTE_G      = 2.0
CEFRTRX_PED_KG        = 0.1

LITICAN_DOSE_ADULTE_MG  = 40.0
LITICAN_DOSE_KG_ENF     = 1.0
LITICAN_DOSE_MAX_ENF_MG = 40.0
LITICAN_DOSE_MAX_JOUR   = 120.0
LITICAN_POIDS_PIVOT_KG  = 15.0

MIDAZOLAM_BUCC_KG      = 0.3
MIDAZOLAM_BUCC_MAX_MG  = 10.0
DIAZEPAM_RECT_KG       = 0.5
DIAZEPAM_RECT_MAX_MG   = 10.0
DIAZEPAM_IV_KG         = 0.3
DIAZEPAM_IV_MAX_MG     = 10.0
LORAZEPAM_IV_KG        = 0.1
LORAZEPAM_IV_MAX_MG    = 4.0
CLONAZEPAM_IV_KG       = 0.02
CLONAZEPAM_IV_MAX_MG   = 1.0
PHENOBARB_IV_KG        = 20.0
PHENOBARB_IV_MAX_MG    = 1000.0
LEVETI_IV_KG           = 60.0
LEVETI_IV_MAX_MG       = 4500.0
VALPROATE_IV_KG        = 40.0
VALPROATE_IV_MAX_MG    = 3000.0
VALPROATE_IV_DEBIT_MIN = 6.0
PHENOBARB_DEBIT_MG_KG_MIN = 1.0
FLUMAZENIL_DOSE_MG     = 0.01
FLUMAZENIL_MAX_MG      = 0.2
FLUMAZENIL_MAX_TOTAL   = 1.0
EME_SEUIL_MIN          = 5
EME_ETABLI_MIN         = 30
EME_OPERATIONNEL_MIN   = 15

FIEVRE_TRES_HAUTE_ENFANT = 40.0
FIEVRE_NOURR_SEUIL       = 38.0
FIEVRE_HAUT_RISQUE_AGE   = 0.25
FC_TACHY_NOURR    = 160
FC_TACHY_BEBE     = 150
FC_TACHY_ENFANT   = 140
FC_TACHY_GRAND    = 120
VOMISS_FREQ_SEVERE = 6

REGISTRE_CAP = 500

ATCD = [
    "HTA","Diabète type 1","Diabète type 2","Tabagisme actif","Dyslipidémie",
    "ATCD familial coronarien","Insuffisance cardiaque","BPCO","Anticoagulants/AOD",
    "Grossesse en cours","Immunodépression","Néoplasie évolutive","Épilepsie",
    "Insuffisance rénale chronique","Ulcère gastro-duodénal","Insuffisance hépatique",
    "Déficit vitamine B12","Drépanocytose","Chimiothérapie en cours",
    "IMAO (inhibiteurs MAO)","Antidépresseurs ISRS/IRSNA"
]
CFS_LBL  = {1:"Très en forme",2:"En forme",3:"Bien portant",4:"Vulnérable",
            5:"Fragilité légère",6:"Fragilité modérée",7:"Fragilité sévère",
            8:"Fragilité très sévère",9:"Maladie terminale"}
MOTS_CAT = {
  "Cardio":["Arrêt cardio-respiratoire","Hypotension artérielle","Douleur thoracique / SCA",
            "Tachycardie / tachyarythmie","Bradycardie / bradyarythmie","Palpitations",
            "Hypertension artérielle","Allergie / anaphylaxie"],
  "Respiratoire":["Dyspnée / insuffisance respiratoire","Dyspnée / insuffisance cardiaque"],
  "Digestif":["Douleur abdominale","Vomissements / Diarrhée","Hématémèse / Rectorragie"],
  "Neuro":["AVC / Déficit neurologique","Traumatisme crânien","Altération de conscience / Coma",
           "Céphalée","Convulsions / EME","Syndrome confusionnel","Malaise"],
  "Trauma":["Traumatisme thorax/abdomen/rachis cervical","Traumatisme bassin/hanche/fémur",
            "Traumatisme membre / épaule"],
  "Infectio":["Fièvre"],
  "Pédiatrie":[
    "Pédiatrie - Fièvre <= 3 mois",
    "Pédiatrie - Fièvre enfant (3 mois - 15 ans)",
    "Pédiatrie - Vomissements / Gastro-entérite",
    "Pédiatrie - Crise épileptique",
  ],
  "Peau":["Pétéchie / Purpura","Érythème étendu"],
  "Gynéco":["Accouchement imminent","Complication grossesse T1/T2","Ménorragie / Métrorragie"],
  "Métabolique":["Hypoglycémie","Hyperglycémie / Cétoacidose"],
  "Divers":["Renouvellement ordonnance","Examen administratif"],
}
MOTIFS_RAPIDES = [
    "Douleur thoracique / SCA",
    "Dyspnée / insuffisance respiratoire",
    "AVC / Déficit neurologique",
    "Altération de conscience / Coma",
    "Traumatisme crânien",
    "Hypotension artérielle",
    "Tachycardie / tachyarythmie",
    "Fièvre",
    "Douleur abdominale",
    "Allergie / anaphylaxie",
    "Hypoglycémie",
    "Convulsions / EME",
    "Pédiatrie - Fièvre <= 3 mois",
    "Pédiatrie - Fièvre enfant (3 mois - 15 ans)",
    "Pédiatrie - Vomissements / Gastro-entérite",
    "Pédiatrie - Crise épileptique",
    "Autre motif",
]