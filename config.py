# config.py — Constantes cliniques AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# Toutes les "magic numbers" cliniques sont nommées ici.
# Modifier une dose = modifier uniquement ce fichier.

# ── Labels de triage FRENCH ──────────────────────────────────────────────────
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
    "hs":  54,    # Hypoglycémie sévère   < 3,0 mmol/l
    "hm":  70,    # Hypoglycémie modérée < 3,9 mmol/l
    "Hs": 180,    # Hyperglycémie        > 10,0 mmol/l
    "Hs2":360,    # Hyperglycémie sévère > 20,0 mmol/l
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

# ── Naloxone — BCFI ───────────────────────────────────────────────────────────
NALOO_ADULTE_MG = 0.4    # mg — bolus IV adulte
NALOO_PED_KG    = 0.01   # mg/kg — enfant
NALOO_DEP_MG    = 2.0    # mg — dépression respiratoire sévère

# ── Morphine IV — BCFI / SFAR ────────────────────────────────────────────────
MORPH_MIN_KG     = 0.05   # mg/kg — dose initiale
MORPH_MAX_KG     = 0.1    # mg/kg — plafond par bolus
MORPH_PALIER_MG  = 2.0    # mg — palier titrée adulte
MORPH_PLAFOND_STD = 10.0  # mg — plafond standard
MORPH_PLAFOND_GE100 = 15.0 # mg — plafond patient > 100 kg

# ── Ceftriaxone IV — BCFI ────────────────────────────────────────────────────
CEFRTRX_ADULTE_G = 2.0    # g — dose adulte
CEFRTRX_PED_KG   = 0.05   # g/kg — enfant (50 mg/kg)

# ── Litican (kétoprofène lysine) — BCFI ──────────────────────────────────────
LITICAN_DOSE_ADULTE_MG  = 80.0   # mg — adulte ≥ 50 kg
LITICAN_DOSE_KG_ENF     = 1.0    # mg/kg — enfant < 50 kg
LITICAN_DOSE_MAX_ENF_MG = 80.0   # mg — plafond enfant
LITICAN_POIDS_PIVOT_KG  = 50.0   # kg
LITICAN_DOSE_MAX_JOUR   = 240.0  # mg/jour

# ── Anticonvulsivants — BCFI / Lignes directrices belges ─────────────────────
# Diazépam rectal
DIAZEPAM_RECT_KG     = 0.5    # mg/kg
DIAZEPAM_RECT_MAX_MG = 10.0   # mg
# Diazépam IV
DIAZEPAM_IV_KG       = 0.2    # mg/kg
DIAZEPAM_IV_MAX_MG   = 10.0   # mg
# Midazolam buccal
MIDAZOLAM_BUCC_MAX_MG = 10.0  # mg
# Midazolam IM/IN
MIDAZOLAM_IM_IN_KG    = 0.2   # mg/kg
MIDAZOLAM_IM_IN_MAX_MG = 10.0 # mg
# Lorazépam IV
LORAZEPAM_IV_KG       = 0.1   # mg/kg
LORAZEPAM_IV_MAX_MG   = 4.0   # mg
# Clonazépam IV
CLONAZEPAM_IV_KG      = 0.02  # mg/kg
CLONAZEPAM_IV_MAX_MG  = 1.0   # mg
# Phénobarbital IV
PHENOBARB_IV_KG        = 20.0  # mg/kg
PHENOBARB_IV_MAX_MG    = 1000.0
PHENOBARB_DEBIT_MG_KG_MIN = 1.0 # mg/kg/min
# Lévétiracétam IV
LEVETI_IV_KG           = 60.0  # mg/kg
LEVETI_IV_MAX_MG       = 4500.0
# Valproate IV
VALPROATE_IV_KG        = 40.0  # mg/kg
VALPROATE_IV_MAX_MG    = 3000.0
VALPROATE_IV_DEBIT_MIN = 6.0   # mg/kg/min

# ── Seuils EME ────────────────────────────────────────────────────────────────
EME_SEUIL_MIN       = 5    # minutes — définition EME
EME_OPERATIONNEL_MIN = 30  # minutes — EME opérationnel
EME_ETABLI_MIN      = 5    # minutes — critère triage

# ── Registre patients — anonymisé RGPD ───────────────────────────────────────
REGISTRE_CAP = 200  # nombre max d'entrées en mémoire

# ── Antécédents connus ────────────────────────────────────────────────────────
ATCD = [
    "HTA", "Diabète type 1", "Diabète type 2",
    "Coronaropathie / SCA antérieur", "Insuffisance cardiaque",
    "BPCO", "Asthme", "Insuffisance rénale chronique",
    "Insuffisance hépatique", "Épilepsie",
    "AVC / AIT antérieur", "Fibrillation atriale",
    "Anticoagulants/AOD", "Antiagrégants plaquettaires",
    "Bêta-bloquants", "Corticoïdes au long cours",
    "IMAO (inhibiteurs MAO)", "Immunodépression",
    "Chimiothérapie en cours", "Grossesse",
    "Ulcère gastro-duodénal", "Drépanocytose",
    "Troubles psychiatriques", "Démence",
    "Obésité morbide (IMC ≥ 40)",
]
