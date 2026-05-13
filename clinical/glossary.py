"""
clinical/glossary.py — Glossaire pédagogique des outils cliniques.

Explique en langage accessible :
- Ce qu'est l'outil
- À quoi il sert concrètement
- Comment lire le résultat

Chaque entrée a :
    title  — titre court
    tldr   — résumé en 1 phrase (affiché replié)
    body   — explication détaillée (3-6 phrases, accessible)
    source — référence académique

Utilisation côté UI :
    from ui.explainer import explain
    explain("news2")
"""
from __future__ import annotations


GLOSSARY: dict[str, dict[str, str]] = {

    # ══════════════════════════════════════════════════════════════════════
    # SCORES CLINIQUES
    # ══════════════════════════════════════════════════════════════════════

    "news2": {
        "title": "NEWS2 — Score d'alerte précoce",
        "tldr": "Score 0-20 qui résume la gravité d'un patient à partir de 6 mesures vitales.",
        "body": (
            "NEWS2 (National Early Warning Score 2) combine 6 paramètres : "
            "fréquence respiratoire, SpO2, oxygène supplémentaire, température, "
            "pression artérielle, fréquence cardiaque et état de conscience. "
            "Chaque paramètre rapporte 0 à 3 points selon sa déviation. "
            "Plus le score est haut, plus le risque vital est important. "
            "**Au-delà de 5 : un médecin doit voir le patient sous 30 minutes.** "
            "**Au-delà de 7 : urgence vitale immédiate.** "
            "Les patients BPCO utilisent une échelle SpO2 ajustée (cible 88-92 %)."
        ),
        "source": "Royal College of Physicians, London 2017",
    },

    "pews": {
        "title": "PEWS — Score d'alerte précoce pédiatrique",
        "tldr": "Équivalent du NEWS2 pour les enfants de 0 à 16 ans.",
        "body": (
            "PEWS (Paediatric Early Warning Score) évalue 3 dimensions : "
            "comportement/conscience, cardiovasculaire (FC, TRC), respiratoire "
            "(FR, SpO2, O2 supplémentaire). Les seuils s'adaptent à l'âge "
            "car un nouveau-né a normalement une FC de 140 et une FR de 50. "
            "**Score ≥ 5 : appel médecin immédiat. ≥ 7 : appel réanimation pédiatrique.** "
            "NEWS2 n'est PAS validé avant 16 ans, c'est pourquoi PEWS existe."
        ),
        "source": "Monaghan A, Nurs Stand 2005 / Parshuram CS, JAMA 2011",
    },

    "qsofa": {
        "title": "qSOFA — Screening rapide de sepsis",
        "tldr": "3 critères pour détecter rapidement une infection sévère.",
        "body": (
            "qSOFA (quick Sepsis-related Organ Failure Assessment) note 1 point pour : "
            "**tension systolique ≤ 100 mmHg**, **fréquence respiratoire ≥ 22/min**, "
            "**état mental altéré (GCS < 15)**. "
            "Score ≥ 2 sur 3 = risque élevé d'infection sévère et de mortalité. "
            "Action attendue : démarrer le **bundle sepsis 1h** (lactates + 2 hémocultures + "
            "antibiothérapie probabiliste IV < 1h)."
        ),
        "source": "Surviving Sepsis Campaign 2021",
    },

    "gcs": {
        "title": "GCS — Glasgow Coma Scale",
        "tldr": "Mesure standardisée de l'état de conscience, de 3 à 15.",
        "body": (
            "Le GCS évalue 3 réactions : **ouverture des yeux** (1-4 points), "
            "**réponse verbale** (1-5), **réponse motrice** (1-6). "
            "Total = 3 (coma profond) à 15 (alerte). "
            "**GCS ≤ 8** : coma — protection des voies aériennes indispensable (intubation à discuter). "
            "**GCS 9-12** : altération modérée. "
            "**GCS 13-14** : altération légère. "
            "**GCS 15** : alerte normal."
        ),
        "source": "Teasdale & Jennett, Lancet 1974",
    },

    "avpu": {
        "title": "AVPU — Évaluation rapide de la conscience",
        "tldr": "Version simplifiée du GCS en 4 lettres.",
        "body": (
            "AVPU est un screening en 4 niveaux : "
            "**A — Alerte** : le patient parle normalement. "
            "**V — répond à la Voix** : il faut l'appeler pour qu'il réagisse. "
            "**P — répond à la douleur (Pain)** : seule la stimulation douloureuse provoque une réponse. "
            "**U — inconscient (Unresponsive)** : aucune réponse. "
            "Mapping approximatif avec GCS : A=15, V=13-14, P=9-12, U≤8. "
            "C'est plus rapide à évaluer que le GCS complet, utile en pré-hospitalier."
        ),
        "source": "Kelly CA et al., Resuscitation 2004",
    },

    "shock_index": {
        "title": "Index de choc — Signal d'alerte précoce",
        "tldr": "Pouls divisé par tension systolique. Au-delà de 0.9, suspicion de choc.",
        "body": (
            "Calcul : **FC ÷ PAS**. "
            "Valeur normale : 0.5 à 0.7. "
            "**> 0.9** : suspicion de choc compensé, même si FC et PAS prises séparément paraissent normales. "
            "**> 1.0** : choc franc probable. "
            "Particulièrement utile chez les patients sous **bêtabloquants** qui peuvent garder "
            "une FC normale alors qu'ils sont en train de décompenser hémodynamiquement."
        ),
        "source": "Allgöwer & Burri, Dtsch Med Wochenschr 1967",
    },

    "lace": {
        "title": "Score LACE — Risque de réadmission J30",
        "tldr": "Estime le risque qu'un patient revienne aux urgences dans les 30 jours.",
        "body": (
            "LACE combine 4 facteurs : "
            "**L** = Length of stay (durée du séjour). "
            "**A** = Acuity (admission via urgences ou non). "
            "**C** = Comorbidities (index de Charlson). "
            "**E** = Emergency visits (passages aux urgences dans les 6 mois). "
            "Score 0-19. **≥ 10** : risque élevé de réadmission — discussion équipe, "
            "follow-up rapproché, voire ré-examen médical avant sortie."
        ),
        "source": "van Walraven C et al., CMAJ 2010;182(6):551-7",
    },

    "charlson": {
        "title": "Index de Charlson — Comorbidités",
        "tldr": "Liste pondérée des maladies chroniques pesant sur le pronostic vital.",
        "body": (
            "Chaque maladie chronique reçoit 1 à 6 points selon sa gravité : "
            "infarctus passé, insuffisance cardiaque, AVC, BPCO, diabète, cancer, démence... "
            "Plus le score est haut, plus la mortalité à 10 ans augmente. "
            "Dans AKIR-IAO, Charlson alimente le LACE et permet aussi d'estimer le risque "
            "de complications péri-opératoires."
        ),
        "source": "Charlson ME et al., J Chronic Dis 1987",
    },

    "heart": {
        "title": "Score HEART — Risque coronarien aux urgences",
        "tldr": "Évalue le risque d'événement cardiaque chez un patient avec douleur thoracique.",
        "body": (
            "HEART combine 5 critères, chacun de 0 à 2 points : "
            "**H**istoire (douleur typique ?), **E**CG, **A**ge, **R**isk factors (tabac, HTA...), "
            "**T**roponine. Score total 0-10. "
            "**≤ 3** : risque faible (~ 1.7 %), sortie envisageable. "
            "**4-6** : risque modéré, hospitalisation pour surveillance. "
            "**≥ 7** : risque élevé (~ 50 %), prise en charge cardiologique urgente."
        ),
        "source": "Six AJ et al., Neth Heart J 2008",
    },

    "nihss": {
        "title": "NIHSS — Sévérité de l'AVC",
        "tldr": "Score 0-42 qui quantifie l'importance d'un déficit neurologique.",
        "body": (
            "NIHSS (NIH Stroke Scale) évalue 11 items : conscience, oculomotricité, "
            "champ visuel, paralysie faciale, motricité membres, ataxie, sensibilité, langage, "
            "dysarthrie, négligence. "
            "**0** : pas de déficit. **1-4** : AVC mineur. **5-15** : modéré. "
            "**16-20** : modéré à sévère. **> 20** : sévère. "
            "Détermine l'éligibilité à la thrombolyse et à la thrombectomie."
        ),
        "source": "Brott T et al., Stroke 1989",
    },

    "ciwa": {
        "title": "CIWA-Ar — Sévérité du sevrage alcoolique",
        "tldr": "Score 0-67 qui guide la dose de benzodiazépine en sevrage.",
        "body": (
            "CIWA évalue 10 symptômes : nausées, tremblements, sueurs, anxiété, agitation, "
            "trouble tactile/auditif/visuel, céphalée, désorientation. "
            "**< 8** : sevrage léger, surveillance simple. "
            "**8-15** : sevrage modéré, benzodiazépine. "
            "**≥ 16** : sévère, risque de delirium tremens. "
            "Important : toujours administrer **thiamine 500 mg IV avant tout glucosé** "
            "pour éviter l'encéphalopathie de Wernicke."
        ),
        "source": "Sullivan JT et al., Br J Addict 1989",
    },

    "wells": {
        "title": "Score de Wells — Probabilité TVP/EP",
        "tldr": "Évalue la probabilité clinique de thrombose veineuse ou embolie pulmonaire.",
        "body": (
            "Wells combine signes cliniques (gonflement mollet, douleur, ATCD cancer/chirurgie...) "
            "et calcule une probabilité de TVP ou d'EP. "
            "**Bas** : D-dimères suffisent souvent à exclure. "
            "**Modéré/élevé** : imagerie indiquée (échodoppler veineux pour TVP, "
            "angio-TDM pour EP)."
        ),
        "source": "Wells PS et al., NEJM 2003",
    },

    "perc": {
        "title": "Règle PERC — Exclusion d'EP",
        "tldr": "Critères qui permettent d'écarter l'embolie pulmonaire sans imagerie.",
        "body": (
            "PERC (Pulmonary Embolism Rule-out Criteria) : 8 critères négatifs simultanés "
            "(âge < 50 ans, FC < 100, SpO2 > 94 %, pas d'œdème unilatéral, pas d'hémoptysie, "
            "pas de chirurgie/trauma récent, pas d'ATCD TVP/EP, pas de contraception orale) "
            "permettent d'exclure une EP avec une probabilité < 2 % chez un patient à faible risque. "
            "Évite les D-dimères et l'imagerie chez les patients clairement non-EP."
        ),
        "source": "Kline JA et al., J Thromb Haemost 2008",
    },

    # ══════════════════════════════════════════════════════════════════════
    # TRIAGE & WORKFLOW
    # ══════════════════════════════════════════════════════════════════════

    "french": {
        "title": "FRENCH V1.1 — Grille officielle de triage",
        "tldr": "Système belge/français à 5 niveaux + niveau M (déchocage).",
        "body": (
            "FRENCH V1.1 classe le patient selon le délai maximum acceptable avant prise en charge : "
            "**Tri M** : déchocage immédiat (ACR, choc, détresse vitale). "
            "**Tri 1** : prise en charge sous 5 minutes. "
            "**Tri 2** : sous 15 minutes. "
            "**Tri 3A** : sous 30 minutes. "
            "**Tri 3B** : sous 60 minutes. "
            "**Tri 4** : sous 2 heures. "
            "**Tri 5** : non urgent. "
            "L'IAO valide ce niveau en combinant motif, vitaux, antécédents et NEWS2."
        ),
        "source": "SFMU — Classification FRENCH Triage V1.1, 2018",
    },

    "sbar": {
        "title": "SBAR — Format de transmission standardisé",
        "tldr": "Méthode pour transmettre un patient en 30 secondes sans rien oublier.",
        "body": (
            "SBAR structure la passation orale ou écrite : "
            "**S — Situation** : qui est le patient, où, pourquoi il est là. "
            "**B — Background** : antécédents pertinents, traitements. "
            "**A — Assessment** : ce que tu observes, scores, ton hypothèse. "
            "**R — Recommendation** : ce que tu proposes (examens, transfert, surveillance). "
            "Utilisé pour transmettre IAO → médecin, équipe → équipe, et entre services."
        ),
        "source": "ISBAR — Joint Commission International",
    },

    "5b": {
        "title": "Règle des 5B — Sécurité d'injection",
        "tldr": "5 vérifications avant toute administration médicamenteuse.",
        "body": (
            "**Bon patient** (vérifier identité + bracelet). "
            "**Bon médicament** (lire l'étiquette, pas la couleur). "
            "**Bonne dose** (calcul vérifié pour pédiatrie, IR). "
            "**Bonne voie** (IV, IM, SC, PO, IN...). "
            "**Bon moment** (timing par rapport au repas, antibiothérapie, etc.). "
            "Standard belge AFMPS — réduit les erreurs médicamenteuses de 50 %."
        ),
        "source": "AR 78 AFMPS 2019, Belgique",
    },

    # ══════════════════════════════════════════════════════════════════════
    # IA & MODÈLES ML
    # ══════════════════════════════════════════════════════════════════════

    "ia_triage": {
        "title": "IA Triage — Modèle de classification ML",
        "tldr": "Random Forest qui prédit la priorité 1-5 à partir de 13 paramètres.",
        "body": (
            "Modèle entraîné sur **1 267 cas KTAS coréens** validés par des experts urgentistes, "
            "augmenté de **70 séjours réels MIMIC-III** (ICU MIT) marqués P1/P2. "
            "Features utilisées : 6 vitaux + AVPU + douleur NRS + arrivée ambulance + traumatisme + 3 dérivés "
            "(shock index, pression moyenne, pression pulsée). "
            "Le modèle renvoie une priorité **et** la probabilité de chaque classe. "
            "**Alerte P1** déclenchée si probabilité P1 ≥ 25 %. "
            "F1 weighted = 0.68 — c'est un avis algorithmique, pas une décision."
        ),
        "source": "AKIR-IAO v2 — entraîné mai 2026",
    },

    "ia_mortalite": {
        "title": "Mortalité ICU — Modèle MIMIC-III",
        "tldr": "Ensemble ML qui estime le risque de décès hospitalier à partir des vitaux agrégés.",
        "body": (
            "Combine 3 modèles en soft-voting : GradientBoosting + RandomForest + Régression Logistique. "
            "Entraîné sur **70 séjours ICU réels** de MIMIC-III (base publique du MIT, Beth Israel). "
            "Utilise 21 features dérivées des vitaux (mean/min/max sur la durée du séjour) + démographie + type d'admission. "
            "**AUC-ROC = 0.83** en cross-validation. "
            "⚠️ Dataset petit : à utiliser comme aide à la discussion senior, pas comme décision finale."
        ),
        "source": "MIMIC-III v1.4 — MIT Lab for Computational Physiology",
    },

    "ia_readmission": {
        "title": "Réadmission J30 — Modèle RandomForest",
        "tldr": "Prédit la probabilité qu'un patient revienne aux urgences dans 30 jours.",
        "body": (
            "Entraîné sur **30 000 patients** avec issue de réadmission connue (taux 12.2 %). "
            "Combine 11 features : âge, sexe, tension, cholestérol, BMI, diabète, HTA, "
            "nombre de médicaments, durée du séjour, destination de sortie. "
            "Renvoie une probabilité 0-100 % + un niveau (Faible/Modéré/Élevé) + les 3 facteurs les plus influents. "
            "Complémentaire du score LACE qui est, lui, basé sur des règles explicites."
        ),
        "source": "AKIR-IAO — Random Forest, balanced class weight",
    },

    "mimic": {
        "title": "MIMIC-III — Base de données ICU publique",
        "tldr": "60 millions de mesures cliniques anonymisées disponibles pour la recherche.",
        "body": (
            "MIMIC-III (Medical Information Mart for Intensive Care) est une base publiée par le MIT. "
            "Elle contient **40 000 patients réels** passés en USI à Beth Israel Deaconess Medical Center (Boston) "
            "entre 2001 et 2012, anonymisés selon HIPAA. "
            "Standard de l'industrie pour entraîner et benchmarker des modèles ML cliniques. "
            "Dans AKIR-IAO, on utilise un sous-ensemble (100 patients, 130 admissions, 758 k mesures vitaux)."
        ),
        "source": "Johnson AEW et al., Scientific Data 2016",
    },

    "ktas": {
        "title": "KTAS — Référentiel coréen de triage",
        "tldr": "Équivalent coréen de FRENCH, à 5 niveaux similaires.",
        "body": (
            "KTAS (Korean Triage and Acuity Scale) classe également les patients en 5 niveaux. "
            "Notre dataset KTAS contient **1 267 cas réels** annotés par des urgentistes coréens "
            "(gold standard expert). C'est sur ces données que le modèle IA Triage a été entraîné. "
            "Pourquoi pas FRENCH directement ? Parce que **les datasets FRENCH labellisés publics "
            "n'existent pas**. KTAS est la meilleure approximation publique disponible."
        ),
        "source": "Lim T et al., Clin Exp Emerg Med 2017",
    },

    "sofa_proxy": {
        "title": "SOFA proxy — Estimation rapide de défaillance d'organes",
        "tldr": "Approximation du SOFA basée uniquement sur les vitaux disponibles.",
        "body": (
            "Le score SOFA complet (Sequential Organ Failure Assessment) évalue 6 systèmes : "
            "respiratoire (PaO2/FiO2), coagulation (plaquettes), foie (bilirubine), "
            "cardiovasculaire (PAM + amines), neurologique (GCS), rénal (créatinine + diurèse). "
            "Notre **proxy** estime à partir des seuls paramètres dispo aux urgences (vitaux + GCS), "
            "sans biologie. C'est **indicatif** — à confirmer par un SOFA complet quand les résultats arrivent."
        ),
        "source": "Vincent JL et al., Intensive Care Med 1996",
    },

    # ══════════════════════════════════════════════════════════════════════
    # PHARMACOLOGIE & OUTILS
    # ══════════════════════════════════════════════════════════════════════

    "rsi": {
        "title": "RSI — Induction en séquence rapide",
        "tldr": "Procédure d'urgence pour endormir et intuber un patient à estomac plein.",
        "body": (
            "RSI (Rapid Sequence Intubation) est utilisée quand on doit intuber rapidement "
            "un patient qui n'est pas à jeun (urgence). Risque principal : inhalation. "
            "Combine **hypnotique** (kétamine 1-2 mg/kg ou étomidate 0.3 mg/kg) "
            "+ **curare** (succinylcholine 1 mg/kg ou rocuronium 1.2 mg/kg). "
            "Doses précises selon poids — pondération par poids idéal théorique pour les obèses."
        ),
        "source": "Walls RM, Manual of Emergency Airway Management",
    },

    "broselow": {
        "title": "Règle de Broselow — Poids pédiatrique sans balance",
        "tldr": "Estime le poids d'un enfant à partir de sa taille.",
        "body": (
            "En urgence pédiatrique, on n'a pas toujours le temps de peser. "
            "Broselow donne **poids = formule(taille)** ou utilise des bandelettes colorées. "
            "Permet de calculer rapidement les doses (en mg/kg) sans erreur de zéro. "
            "Méthode complémentaire : **âge** : poids (kg) ≈ (âge × 2) + 8 entre 1 et 10 ans."
        ),
        "source": "Broselow JB, Pediatrics 1988",
    },

    "code_stroke": {
        "title": "Code Stroke — AVC ischémique aigu",
        "tldr": "Protocole chronométré pour la thrombolyse / thrombectomie.",
        "body": (
            "Objectifs **temps-cibles** validés ESO 2021 : "
            "**porte → scanner ≤ 25 min**. "
            "**porte → thrombolyse ≤ 60 min** (door-to-needle). "
            "**Fenêtre thrombolyse** : ≤ 4h30 après début des symptômes (ou ≤ 9h si imagerie de perfusion favorable). "
            "**Thrombectomie** : jusqu'à 6h voire 24h selon critères DAWN/DEFUSE-3. "
            "Time is brain : chaque minute = 1.9 million de neurones perdus."
        ),
        "source": "ESO 2021 / Saver JL, Stroke 2006",
    },

    "dfge": {
        "title": "DFGe CKD-EPI — Fonction rénale",
        "tldr": "Estime la filtration glomérulaire à partir de la créatinine sanguine.",
        "body": (
            "Le débit de filtration glomérulaire estimé (DFGe) reflète la capacité des reins à "
            "épurer le sang. Formule CKD-EPI utilise créatinine, âge, sexe (ethnie supprimée en 2021). "
            "**> 90** : normal. **60-89** : légère diminution. **30-59** : IR modérée. "
            "**15-29** : IR sévère. **< 15** : insuffisance rénale terminale (dialyse). "
            "Indispensable pour adapter les doses des médicaments éliminés par les reins."
        ),
        "source": "Levey AS et al., NEJM 2021",
    },

    "aod": {
        "title": "AOD vs AVK — Anticoagulants oraux",
        "tldr": "Deux familles avec antidotes différents.",
        "body": (
            "**AOD (Anticoagulants Oraux Directs)** : Eliquis (apixaban), Xarelto (rivaroxaban), "
            "Pradaxa (dabigatran), Lixiana (edoxaban). Plus stables, pas de surveillance INR. "
            "**AVK (Antivitamine K)** : Sintrom (acénocoumarol), Coumadine (warfarine). Surveillance INR. "
            "**En urgence hémorragique** : "
            "Pradaxa → **Idarucizumab (Praxbind®) 5 g IV**. "
            "Xa-inh (Eliquis, Xarelto) → **Andexanet alfa** ou PPSB. "
            "AVK → **Vitamine K 10 mg IV + PPSB 25-50 UI/kg**."
        ),
        "source": "SFMU 2023 — AOD reversal guidelines",
    },

    "bpco_spo2": {
        "title": "Échelle SpO2-2 BPCO — Cible 88-92 %",
        "tldr": "Les patients BPCO sont sensibles à l'hyperoxie : O2 trop généreux peut tuer.",
        "body": (
            "Chez un patient BPCO, la commande respiratoire dépend de l'hypoxémie chronique. "
            "Donner trop d'O2 supprime cette commande → hypoventilation → rétention de CO2 → narcose → "
            "arrêt respiratoire. "
            "**Cible SpO2 : 88-92 %** chez le patient BPCO connu (pas le standard 94-98 %). "
            "NEWS2 utilise une **échelle spécifique** : pénalité si SpO2 > 96 % sous oxygène. "
            "L'app force automatiquement cette échelle si BPCO en antécédent."
        ),
        "source": "Royal College of Physicians 2017 / Eccles SE 2017",
    },

    "poids_ideal": {
        "title": "Poids idéal théorique — Pour les opioïdes et BZD",
        "tldr": "Dose adaptée à la masse maigre pour éviter les surdosages chez l'obèse.",
        "body": (
            "Formule de Devine 1974 : "
            "**Hommes** : 50 + 2.3 × (taille en pouces − 60). "
            "**Femmes** : 45.5 + 2.3 × (taille en pouces − 60). "
            "**Pourquoi ?** Les opioïdes (morphine, fentanyl) et BZD (midazolam) sont **lipophiles** : "
            "chez l'obèse, doser sur le poids réel = surdosage avec dépression respiratoire. "
            "Utiliser le poids idéal théorique réduit ce risque."
        ),
        "source": "Devine BJ, Drug Intell Clin Pharm 1974",
    },

    "sepsis_bundle": {
        "title": "Bundle Sepsis 1 heure",
        "tldr": "5 actions à compléter dans la première heure du diagnostic de sepsis.",
        "body": (
            "Surviving Sepsis Campaign 2021 : "
            "**1.** Mesurer les lactates. "
            "**2.** Prélever 2 paires d'hémocultures avant antibiothérapie. "
            "**3.** Démarrer antibiothérapie probabiliste IV à large spectre. "
            "**4.** Remplissage cristalloïde 30 ml/kg si hypotension ou lactates > 4. "
            "**5.** Démarrer noradrénaline si hypotension persistante (objectif PAM ≥ 65 mmHg). "
            "Chaque heure de retard = + 7 % de mortalité."
        ),
        "source": "Surviving Sepsis Campaign Guidelines 2021",
    },

    # ══════════════════════════════════════════════════════════════════════
    # GÉNÉRAL
    # ══════════════════════════════════════════════════════════════════════

    "icd10": {
        "title": "ICD-10 — Codification internationale des maladies",
        "tldr": "Codes standardisés pour décrire chaque diagnostic (E11, I50, J44...).",
        "body": (
            "La CIM-10 (ICD-10 en anglais) est le système de classification utilisé dans tous les DPI "
            "et statistiques de santé. Chaque code commence par une lettre (E = endocrinien, "
            "I = circulatoire, J = respiratoire...) suivi de chiffres précisant la pathologie. "
            "Exemples : **E11.9** = diabète T2 non compliqué, **I50** = insuffisance cardiaque, "
            "**N18.3** = IRC stade 3. AKIR-IAO les utilise pour auto-détecter les comorbidités Charlson."
        ),
        "source": "WHO ICD-10 — révision 2019",
    },

    "next_action": {
        "title": "Next-Best-Action — Guidage proactif",
        "tldr": "L'app analyse l'état clinique et te dit la prochaine action prioritaire.",
        "body": (
            "Un moteur de règles évalue en continu 12 conditions cliniques : "
            "vitaux invalides, NEWS2 critique, AVC en fenêtre thrombolyse, qSOFA + fièvre = sepsis, "
            "AOD + traumatisme, P1 sans SBAR, délai triage dépassé, EVA élevée sans antalgie... "
            "La carte change de couleur selon l'urgence (violet=critique, rouge=haute, orange=modérée). "
            "Cite toujours la source clinique. Chaque règle a un test pytest associé."
        ),
        "source": "AKIR-IAO — moteur clinique inter-modules",
    },

    "audit_log": {
        "title": "Audit log — Trace clinique inaltérable",
        "tldr": "Chaque décision IAO est enregistrée avec un hash chaîné.",
        "body": (
            "Toutes les actions enregistrées (triage validé, réévaluation, prescription) sont stockées "
            "dans un fichier local avec une **chaîne de hachage** type blockchain légère. "
            "Toute altération a posteriori est détectable. "
            "Utile en cas de litige : la trace prouve quelle décision a été prise, quand, avec quels paramètres. "
            "Bouton d'intégrité dans l'onglet Suivi → Historique."
        ),
        "source": "AKIR-IAO — persistence/audit.py",
    },
}


def get(key: str) -> dict[str, str] | None:
    """Retourne l'entrée du glossaire, ou None si introuvable."""
    return GLOSSARY.get(key)


def keys() -> list[str]:
    """Liste toutes les clés disponibles."""
    return sorted(GLOSSARY.keys())
