# AKIR-IAO — Analyse experte

> **Auteur de l'analyse** : audit indépendant, profil hybride engineering + clinical informatics
> **Date** : 13 mai 2026
> **Périmètre** : 20 328 lignes Python, 9 onglets fonctionnels, 4 modèles ML, 260 tests pytest
> **Référence projet** : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique

---

## 1. Synthèse exécutive

AKIR-IAO est une **application Streamlit d'aide à la décision pour l'Infirmier d'Accueil et d'Orientation (IAO) aux urgences**, structurée autour de trois piliers : la grille de triage FRENCH V1.1 (SFMU), les scores cliniques standards (NEWS2, qSOFA, LACE, NIHSS, GCS), et des modèles de machine learning entraînés sur des données réelles (KTAS coréen, MIMIC-III du MIT).

C'est un **projet rare** dans le paysage francophone de la HealthTech d'urgences pour quatre raisons :

1. **Précision clinique** : 38 fonctions de calcul cliniquement sourcées, citation systématique des références (SFMU, RCP 2017, ESC 2023, ESO 2023, Surviving Sepsis Campaign 2021, JCI, HAS…).
2. **Ancrage terrain** : conçu pour l'usage smartphone BYOD d'un IAO en flux tendu, avec mobile-first absolu, bottom nav, anti-zoom iOS, safe-area, presets vitaux, navigation par tap.
3. **Intelligence inter-modules** : moteur "Next-Best-Action" + pré-remplissage automatique inter-modules (ATCD → Charlson, GCS → AVPU, motif → injury/AVC). L'app ne demande jamais deux fois la même information.
4. **Sécurité patient native** : fail-loud sur les vitaux invalides (un score NEWS2 ne retourne jamais "0 silencieux"), priorités absolues verrouillées (purpura, ACR, choc, coma), anonymisation RGPD avant tout appel API externe.

Le projet est, dans son état actuel, **à mi-chemin entre prototype avancé et MVP production-ready**. Son potentiel est significatif si certaines limites sont adressées : taille du dataset mortalité (70 patients), absence d'export HL7/FHIR vers les DPI, modèles ML non versionnés.

---

## 2. Identité du projet

### Ce que c'est

Une **application d'aide à la décision IAO**, web-based (Streamlit), conçue pour :

- Sécuriser le triage aux urgences en s'appuyant sur la grille FRENCH V1.1 (référence française/belge officielle).
- Calculer en temps réel les scores cliniques pertinents (NEWS2, qSOFA, LACE, HEART, NIHSS, etc.).
- Suggérer des doses pharmaceutiques ajustées au poids, à la fonction rénale, à l'âge.
- Prédire via ML : la priorité KTAS/FRENCH (1-5), le risque de réadmission à J30 (LACE + RandomForest), la mortalité hospitalière en ICU (ensemble GBM+RF+LR sur MIMIC-III).
- Structurer la transmission via SBAR.
- Maintenir une trace clinique locale (audit log persistant).

### Ce que ce n'est pas

- **Ce n'est pas un dispositif médical (DM) certifié CE.** L'app affiche d'ailleurs clairement *"Le modèle de triage par IA est expérimental et ne remplace pas le jugement clinique"*. Toute évolution vers la prise de décision autonome déclencherait un classement DM IIa minimum (MDR EU 2017/745).
- **Ce n'est pas un substitut au DPI** (Dossier Patient Informatisé). L'usage cible confirmé est **hybride** : transmission rapide vers le DPI + trace locale pour audit qualité.
- **Ce n'est pas une marketplace ou un SaaS.** C'est un outil opérationnel pour un service donné, déployable en local ou sur Streamlit Cloud.

### Pour qui

Profil utilisateur cible confirmé :

- **IAO en garde aux urgences** (Belgique francophone, Hainaut au départ).
- Device principal : **smartphone personnel (BYOD)** — contrainte UX absolue.
- Workflow : **1 patient principal en profondeur + réévaluations courtes en parallèle**.
- Compétences SI : variables. L'outil doit être utilisable sans formation longue.

---

## 3. Métriques objectives

| Indicateur | Valeur |
|---|---|
| Lignes Python (modules métier + UI) | 20 328 |
| Tests pytest (passing) | **260/260** |
| Modules cliniques | 16 (clinical/) |
| Modules UI | 11 (ui/) |
| Modules ML | 7 (ml/) |
| Onglets Streamlit | 10 |
| Handlers de motif FRENCH | 44 (cardio, neuro, pédiatrie, autres…) |
| Médicaments avec calcul de dose | 42 (clinical/pharmaco.py) |
| Modèles ML entraînés | 3 actifs (triage, réadmission, mortalité) |
| Datasets intégrés | 8 fichiers (≈ 96 Mo cumulés) |
| Sources cliniques citées | 20+ (SFMU, FRENCH, RCP, ESC, ESO, JAMA, HAS, AFMPS, JCI, Surviving Sepsis, LACE, Walraven, MIMIC, etc.) |

### Architecture

```
streamlit_app.py (orchestrateur, 1400+ lignes)
├── clinical/         (moteur métier, sourcé, testé)
│   ├── triage.py     (FRENCH V1.1, 44 handlers motif, 1700+ lignes)
│   ├── news2.py      (RCP 2017, échelles SpO2-1/2 BPCO, PEWS pédiatrique)
│   ├── scores.py     (qSOFA, LACE, HEART, NIHSS, GCS, Charlson…)
│   ├── pharmaco.py   (42 médicaments, dosage poids/âge/IR)
│   ├── perfusion.py  (12 protocoles SAP : noradrénaline, kétamine, etc.)
│   ├── next_action.py  (moteur règles "Next-Best-Action", testé)
│   ├── prefill.py    (helpers pré-remplissage inter-modules)
│   ├── semantic_engine.py (Claude API + Pydantic, RGPD)
│   └── triage_handlers/ (handlers spécialisés par organe)
├── ml/               (modèles + prédicteurs)
│   ├── triage_predictor.py   (RF v2, 13 features, KTAS+MIMIC)
│   ├── readmission_predictor.py (RF, 11 features, 30k patients)
│   ├── mortality_predictor.py (ensemble GBM+RF+LR, 21 features MIMIC)
│   └── prepare_mimic_data.py (pipeline ETL MIMIC-III)
├── ui/               (composants Streamlit, mobile-first)
│   ├── triage_tab.py, mortality_tab.py, readmission_tab.py
│   ├── pharmacie_tab.py, scores_tab.py
│   ├── components.py (cartes, gauges, alerts)
│   ├── eva_pqrst.py  (composants EVA + discriminants)
│   └── styles.py     (CSS responsive, tokens design)
├── persistence/      (registre patients + audit hash chainé)
├── data/             (KTAS, MIMIC-III, réadmissions, ICD-9, pharmacie)
└── tests/            (260 tests : médical, triage, scores, voice, prefill, next_action)
```

---

## 4. Observations d'expert (4 angles)

### 4.1. Angle clinique

**Forces remarquables** :

1. **Fidélité au RCP 2017 pour NEWS2** — chaque seuil (FR, SpO2, Temp, PAS, FC, GCS) est vérifiable contre la source originale. L'échelle SpO2-2 pour BPCO est correctement implémentée (cible 88-92%, +3 si SpO2 > 96% sous O2). Couverture pédiatrique via PEWS (Monaghan 2005, Parshuram JAMA 2011) — chose rare dans les apps grand public.

2. **Hiérarchie de triage robuste** : `_check_priorites_absolues()` ([clinical/triage.py:490](clinical/triage.py#L490)) verrouille les drapeaux rouges absolus (ACR, purpura, choc, coma) **indépendamment du motif**. C'est la défense en profondeur correcte pour un outil de triage.

3. **`verifier_coherence()`** : 12+ règles de cohérence croisées (AOD+TC → antidote, sepsis bundle qSOFA+fièvre, bêtabloquant masquant choc, drépanocytose, grossesse pré-éclampsie…). Chaque règle est sourcée. C'est le cœur de la valeur clinique.

4. **Pharmacie ajustée au contexte** : doses pédiatriques par poids Broselow, ajustement insuffisance rénale (DFGe CKD-EPI), poids idéal théorique pour les opioïdes/BZD chez l'obèse, conversion d'opioïdes entre molécules.

5. **Sécurité saisie après audit** : NEWS2 lève désormais `ValueError` sur entrée non numérique ou hors plage physiologique. Cela élimine la classe d'erreur la plus dangereuse (faux 0 silencieux).

**Risques cliniques résiduels** :

1. **Pas de signature électronique** sur les décisions IAO. En cas de litige, la trace existe (audit log) mais pas d'opposabilité juridique forte.
2. **Pas d'export structuré** vers le DPI (HL7 v2/FHIR R4). Le copier-coller manuel reste la solution actuelle.
3. **PEWS validé jusqu'à 16 ans seulement** — l'app applique NEWS2 dès 16 ans, ce qui est conforme RCP mais peut nécessiter discussion avec l'urgentiste pédiatre.

### 4.2. Angle technique / architecture

**Forces** :

1. **Séparation propre des couches** : `clinical/` (logique métier pure, testable), `ml/` (modèles + inférence), `ui/` (Streamlit), `persistence/` (audit). Cette discipline est rare dans les apps Streamlit qui finissent typiquement en monolithe.

2. **Tests unitaires cliniques** : 260 tests qui ne valident pas seulement le code mais aussi la **règle clinique** (`test_news2_critique`, `test_triage_acr_tri_M`, `test_news2_bpco_hyperoxie`…). C'est le bon niveau d'abstraction pour une app médicale.

3. **Cache Streamlit correctement utilisé** : `@st.cache_resource` pour les modèles (chargement 1x), `@st.cache_data` pour les calculs purs cacheables. Pas d'abus.

4. **Audit log avec hash chainé** : `persistence/audit.py` implémente une chaîne de hash type blockchain légère pour détecter toute altération a posteriori des décisions.

**Faiblesses techniques** :

1. **`streamlit_app.py` est devenu monolithique** : ~1500 lignes après les ajouts récents. Risque de dette technique si non découpé en sous-modules `ui/patient_tab.py`, `ui/tools_tab.py`, `ui/followup_tab.py`.

2. **Modèles ML non versionnés** dans le bundle joblib : pas de `version`, `trained_at`, `dataset_hash`, `sklearn_version` sérialisés. Reproductibilité incomplète.

3. **Pas de CI/CD configurée** dans le repo. Les tests sont locaux uniquement. Pas de pipeline GitHub Actions.

4. **Dépendance Streamlit** : framework excellent pour le prototypage et l'usage interne, mais limitations connues sur le multi-utilisateur concurrent, les Web Components, les notifications push.

5. **Pas d'observabilité** : aucun logging structuré (Loguru, JSON logs), pas de tracing distribué, pas de métriques d'utilisation. Difficile de comprendre comment l'app est réellement utilisée en production.

### 4.3. Angle produit / UX

**Forces** :

1. **Mobile-first authentique** : 7 media queries, safe-area iOS, anti-zoom 16px sur inputs, tap targets 48×48px WCAG AA, bottom nav 4 actions sticky avec scroll smooth. Pas du mobile "bricolé" mais réfléchi.

2. **Next-Best-Action card** : approche très moderne. Au lieu d'un menu, l'app dit *"voici ce que tu dois faire maintenant"* avec justification clinique. Réduit la charge cognitive en flux tendu.

3. **Presets vitaux** : 6 scénarios courants (Stable, Fièvre, Tachycardie, Choc compensé, Hypoxie, GCS bas) en 1 tap. C'est l'astuce qui fait gagner 20 secondes par patient.

4. **Sticky bar contextuelle** : âge/poids/ATCD critique/triage/NEWS2/chrono toujours visibles. Lisible à 1 mètre.

5. **Code couleur strict** : palette FRENCH triage (M=violet, 1=rouge, 2=orange, 3=jaune, 4=vert, 5=gris) jamais détournée. Cohérence visuelle complète.

**Frustrations probables résiduelles** :

1. **9 onglets en haut** : malgré la bottom nav, les onglets supérieurs scroll horizontalement < 480px. Pas idéal pour l'orientation cognitive.

2. **Ordre des onglets** : Patient en T[0] alors que l'IAO veut souvent saisir les vitaux d'abord. Workflow inversé.

3. **Pas d'état "Patient suivant"** clair après validation triage. Le bouton existe en sidebar (cachée mobile). Risque de mélange entre dossiers.

4. **Pas de feedback haptique** sur actions critiques (vibration légère via Web Vibration API serait un gain perceptif).

5. **Pas encore d'export SBAR 1-tap vers DPI** (prévu en Étape 4).

### 4.4. Angle données / IA

**Forces** :

1. **Datasets réels et hétérogènes** : KTAS coréen (1 267 patients, gold standard expert), MIMIC-III complet (130 admissions ICU réelles + 758 k mesures vitaux), réadmissions (30 k patients). C'est plus que ce que beaucoup de papiers cliniques publient.

2. **Pipeline ETL MIMIC reproductible** : `ml/prepare_mimic_data.py` filtre outliers via `VALID_RANGES`, agrège par hadm_id, produit `mimic_mortality_features.csv` + `mimic_triage_enrichment.csv`. Documenté.

3. **Modèle triage v2 enrichi MIMIC** : combine KTAS réel (1 267) + augmentation synthétique P1/P5 (400) + 70 séjours ICU réels marqués P1/P2. Distribution finale équilibrée. F1 weighted = 0.68, P1 recall = 0.91 — meilleur que la version v1.

4. **Modèle mortalité ensemble** : GBM + RF + LogisticRegression en soft voting, AUC CV-5 = 0.83. C'est cohérent avec la littérature sur petits datasets ICU.

5. **Prédictions explicables** : tous les modèles renvoient probabilités par classe + features influentes (top-3 via `feature_importances_`). Le clinicien voit *pourquoi* le modèle prédit P1.

**Limites majeures** :

1. **Dataset mortalité = 70 patients seulement**. AUC = 0.83 ± 0.116 d'écart-type CV-5. Le modèle est dans la bonne direction mais **trop petit pour un usage clinique sérieux**. Nécessite minimum 1000-5000 séjours pour stabiliser.

2. **MIMIC-III est américain** (Beth Israel Deaconess Medical Center, Boston). Population, prises en charge, organisation des soins **diffèrent** d'un hôpital wallon. Risque de drift démographique.

3. **Pas de validation prospective** : aucun modèle n'a été testé sur les données du service cible. Risque de surprise lors du déploiement réel.

4. **Pas d'apprentissage continu** : modèles entraînés une fois, sauvegardés. Aucun re-training automatique sur les nouvelles données saisies par l'IAO. Opportunité manquée.

5. **`diagnoses.csv` (100 k patients, 274 k visites, 7 ans)** n'est **pas encore exploité**. Mine d'or pour entraîner des modèles de séjour/parcours patient.

---

## 5. Fonctionnement actuel

### Parcours utilisateur typique

```
1. IAO arrive au box → ouvre AKIR-IAO sur smartphone
   ↓
2. Sticky bar haut : âge/poids vides → Card Next-Action : "Saisir les vitaux"
   ↓
3. Tap "📊 VITAUX" (bottom nav) → scroll vers section vitaux
   ↓
4. Saisie FC, PAS, SpO2, FR, T°, GCS (ou preset 1-tap)
   ↓
5. NEWS2 calculé instantanément, sticky bar mise à jour
   ↓
6. Card Next-Action change : "Valider triage (NEWS2 6)"
   ↓
7. Tap "⚡ TRIAGE" → motif + discriminants
   ↓
8. Validation : moteur french_triage() applique FRENCH V1.1
   - Vérifie priorités absolues
   - Applique handler motif
   - Ajuste selon NEWS2
   ↓
9. Card Next-Action : "Générer SBAR pour appel équipe"
   ↓
10. Tap "📡 SBAR" → texte structuré + checklist 5B injection
    ↓
11. Réévaluation à 30 min → tap "🔄 RÉÉV." → delta NEWS2 + alertes
    ↓
12. Audit log local stocké (hash chainé, exportable CSV)
```

### Modèles ML en pratique

Les 3 modèles ML s'insèrent **à la demande**, pas en bloquage du workflow :

| Module | Quand l'IAO l'utilise | Donnée d'entrée | Sortie |
|---|---|---|---|
| **IA Triage v2** | Avis algorithmique sur cas ambigu (P3 vs P2) | 13 features (vitaux + AVPU + dérivés) | Priorité 1-5 + probabilités + alerte P1 ≥ 25 % |
| **Mortalité ICU** | Discussion avec médecin senior sur cas critique | Vitaux agrégés + démographie | Risque 0-100 % + SOFA proxy + signes d'alarme |
| **Réadmission J30** | Avant la sortie pour orienter follow-up | Démographie + comorbidités + LOS | Risque Faible/Modéré/Élevé + score LACE |

### Intelligence inter-modules (nouveauté Étape 3)

```
saisie vitaux ─┬──→ NEWS2 + french_triage    [Tri 2 / NEWS2 6]
               │
               ├──→ build_triage_payload      [IA Triage 1-clic]
               │
               ├──→ build_mortality_payload   [Mortalité 1-clic]
               │
               └──→ Next-Best-Action engine   [card dynamique]

profil ATCD ───┬──→ verifier_coherence        [12 règles cliniques]
               │
               ├──→ build_readmission_prefill [Charlson pré-coché]
               │
               └──→ pharmacie filtering       [antidote AOD si trauma]
```

L'IAO ne saisit chaque information **qu'une seule fois**. C'est le principal différenciateur produit.

---

## 6. Forces distinctives

Synthèse des éléments qui mettent AKIR-IAO dans une catégorie à part dans le paysage des outils IAO :

### Differentiator 1 — Couplage FRENCH V1.1 + IA explicable

Aucune autre app publique francophone à ma connaissance n'offre simultanément :

- Implémentation fidèle de FRENCH V1.1 (référence officielle SFMU/SBMU)
- Validation par grille KTAS étendue (1 267 cas réels coréens, gold standard)
- Modèle ML avec probabilités par priorité + alerte P1 explicite
- Source clinique citée à chaque règle (audit traçable)

### Differentiator 2 — Mobile-first pour IAO BYOD

La plupart des outils urgences sont conçus pour **PC fixe** (logiciel métier hospitalier). Quelques-uns tournent sur tablette dédiée. **Très rares** sont ceux pensés pour le smartphone personnel d'un infirmier en garde — qui est pourtant la réalité quotidienne :

- Safe-area iOS, anti-zoom, tap targets WCAG
- Bottom nav fixe, scroll smooth vers ancres
- Presets vitaux 1-tap
- Card Next-Action proactive

### Differentiator 3 — Cohérence inter-modules

Le moteur `verifier_coherence` + `next_action` + `prefill` forme un **graphe de décision** qui dépasse l'aide à la saisie : c'est une intelligence clinique distribuée.

### Differentiator 4 — Données MIMIC-III intégrées + sourcées

Très peu d'apps d'urgence intègrent **directement** un sous-ensemble MIMIC-III avec pipeline ETL reproductible. C'est un standard académique. Cela ouvre des perspectives de comparaison/benchmarking publication scientifique.

### Differentiator 5 — Tests cliniques sourcés

260 tests pytest qui valident des **règles cliniques** (pas juste du code) : `test_news2_bpco_hyperoxie`, `test_sepsis_qsofa2_fievre_declenche_bundle`, `test_triage_avc_fenetre_thrombolyse`. C'est rare et c'est précieux pour la confiance.

---

## 7. Faiblesses, risques et limites

Honnête, sans complaisance.

### Risques cliniques

| # | Risque | Sévérité | Mitigation actuelle | Action recommandée |
|---|---|---|---|---|
| R1 | Faux négatif sur cas atypique non couvert par les 44 handlers | Haute | Fallback Tri 3B + verifier_coherence | Tests sur 500+ cas réels du service cible avant déploiement |
| R2 | Modèle mortalité ICU sur 70 patients seulement | Haute | Bannière "Indicatif" + AUC ± 0.12 affichée | Refaire entraînement sur dataset local (1000+ séjours) |
| R3 | Dépendance API Claude pour dictée vocale | Moyenne | Fallback local _fallback_voice_parse | Garantir mode offline complet (Whisper local) |
| R4 | Cas pédiatriques pre-PEWS (< 1 mois) sous-couverts | Moyenne | Renvoi vers urgentiste pédiatre | Co-conception avec service de néonatalogie |

### Risques techniques

| # | Risque | Mitigation |
|---|---|---|
| T1 | `streamlit_app.py` monolithique → dette technique | Découpage en modules `ui/*_tab.py` |
| T2 | Pas de CI/CD | Ajouter GitHub Actions : lint + pytest + bandit |
| T3 | Modèles non versionnés | Wrapper `save_model_versioned()` avec hash dataset |
| T4 | Pas de monitoring production | Ajouter logs JSON + métriques d'usage anonymes |

### Risques réglementaires (Belgique + EU)

| # | Question | État |
|---|---|---|
| LR1 | Statut CE du logiciel | Probablement **DM IIa** selon MDR 2017/745 (assistance au triage = aide à la décision médicale) |
| LR2 | RGPD | Anonymisation côté Claude OK. Mais audit log local stocke des données patient — base légale ? |
| LR3 | Responsabilité juridique | App = aide. Décision = IAO + médecin. Mais en cas de mauvais triage suite à recommandation IA, qui répond ? Couverture assurance à clarifier |
| LR4 | Conservation des données | Quelle durée pour `data/audit_log.jsonl` ? RGPD impose une politique explicite |

### Risques d'adoption

- **Concurrence avec le DPI** : si l'app duplique des saisies déjà faites dans le DPI, elle sera délaissée. La transmission DPI doit être **friction-zero** (Étape 4 prévue).
- **Maintenance par une seule personne** : projet porté par Ismail. Bus factor = 1. Documentation à renforcer pour le transfert de connaissance.
- **Pas de retour utilisateur formalisé** : pas de système de feedback intégré (ex. modal "Cas mal trié, pourquoi ?" pour collecter du training data continu).

---

## 8. Potentiel par horizon temporel

### Horizon court terme (3-6 mois)

**Wins rapides à valeur immédiate** :

1. **Bouton SBAR → DPI 1 tap** : copier-coller structuré + audit log automatique. Élimine la dernière friction de double saisie.
2. **FAB Réévaluation modale** : ouvre un dialog 3 champs (FC/PAS/SpO2) avec calcul delta NEWS2. Réduit la friction de la réévaluation à 30 min.
3. **Versioning modèles** : `{"model": ..., "version": "2.1", "trained_at": ..., "dataset_hash": ...}` dans tous les bundles joblib.
4. **CI GitHub Actions** : lint (ruff) + pytest + bandit (sécurité) + couverture coverage.
5. **Découpage `streamlit_app.py`** : extraire les onglets Patient/Outils/Suivi dans `ui/*_tab.py`. Passer de 1500 à ~300 lignes orchestrateur.
6. **Export FHIR R4 Observation** : pour les vitaux + Condition pour le triage. Facile à implémenter (lib `fhir.resources`), gros impact intégration DPI.

### Horizon moyen terme (6-18 mois)

**Évolutions structurantes** :

1. **Validation prospective sur le service cible** : 200 cas IAO sur 1 mois. Comparer triage app vs triage humain. Publier les résultats. C'est la condition pour passer du prototype à l'outil légitime.

2. **Re-training du modèle mortalité sur dataset local** : si le service produit 1 000-5 000 séjours/an, on peut atteindre un dataset stable en 12 mois. Réduit le drift MIMIC-III → population belge.

3. **Mode offline complet** : Whisper local pour la dictée (au lieu de Claude API), service worker PWA. Garantit l'utilisation en zone réseau dégradée (UMH SMUR).

4. **Marquage CE classe IIa (DM logiciel)** : ouvre l'utilisation officielle hors recherche/expérimental. Demande un dossier technique, validation analytique, validation clinique. Investissement 50-150 k€ mais accès à un marché.

5. **Dashboard multi-IAO** : vue agrégée temps réel des patients triés, délais cibles, alertes critiques. Bascule du tool individuel au tool d'équipe.

6. **Audit log signé numériquement** : chaque décision IAO signée avec une clé du service. Force juridique sans alourdir le workflow.

7. **Exploitation de `diagnoses.csv`** : modèle de prédiction de séjour (LOS) à partir du motif + ATCD. Très utile pour le bed management.

### Horizon long terme (18+ mois)

**Visions stratégiques** :

1. **Réseau d'hôpitaux belges utilisateurs** : 5-10 services urgences déployés, partage anonymisé du training data, modèle ML continuellement amélioré. Effet d'échelle local.

2. **Certification HAS / KCE / Centre Fédéral d'Expertise** : passer du logiciel "communauté" au standard de référence régional pour le triage IAO.

3. **Plateforme de recherche** : la richesse de l'audit log (vitaux + décisions + résultats patient) devient une mine de données pour des publications scientifiques (BMC Emergency Medicine, Resuscitation, etc.).

4. **Modules complémentaires** :
   - **SMUR / pré-hospitalier** : variantes pour ambulanciers
   - **Régulation 112** : aide au dispatch
   - **Plateforme téléconsultation post-urgence**
   - **Module formation IAO** : cas cliniques générés depuis MIMIC

5. **Open-source vs commercial** : décision à prendre. Open-source avec support payant ? SaaS pour les hôpitaux ? Modèle freemium ? Chaque option a des implications.

6. **Intégration EMR commerciaux** : connecteurs vers les DPI Belges/Français (CGM, Maincare, EPIC, Mediboard…). Vendre du middleware d'aide à la décision.

---

## 9. Positionnement stratégique

### Marché et concurrence

**Concurrents directs** (apps de triage francophones) :
- ***Triage IAO*** (Le Bon Coin Médical, gratuit) : grille FRENCH simple sans IA, sans pharmacie.
- ***Cerner CareAware*** : module triage des EMR Cerner. Cher, intégré, mais pas mobile-first.
- ***SmartScripts ATS*** : Australian Triage Scale. Pas adapté FR/BE.
- ***ALARM-IAO*** (CHU Toulouse, recherche) : projet académique, non publiquement déployé.

**Concurrents indirects** :
- Calculateurs cliniques web (MD Calc, QxMD) — pas d'orchestration ni d'IA.
- DPI hospitalier embarqué — pas mobile, pas IA explicable.

**Niche distinctive d'AKIR-IAO** :
- **Mobile-first authentique BYOD** + **FRENCH V1.1 complet** + **IA explicable** + **Datasets réels (KTAS + MIMIC)** + **Open architecture extensible**.

C'est une niche **réelle et défendable**, surtout si la validation prospective réussit.

### Modèles économiques envisageables

| Modèle | Pour qui | Avantages | Inconvénients |
|---|---|---|---|
| **Open-source pur (MIT/AGPL)** | Communauté académique + petits services | Adoption rapide, contributions, visibilité | Pas de revenus, soutien gratuit fatigant |
| **Open-core + support payant** | Hôpitaux moyens | Compromis sain | Difficulté à délimiter open/payant |
| **SaaS hosted multi-tenants** | Réseau d'hôpitaux | Revenus récurrents, contrôle qualité | Charge opérationnelle hosting, RGPD |
| **Licence on-premise** | Grands hôpitaux + DM CE | Revenus uniques + maintenance | Cycle vente long, certification CE coûteuse |
| **Recherche / partenariats publics** | Fondation/INAMI/KCE | Subventions, légitimité | Pas d'autonomie économique |

Recommandation : **open-core + partenariats recherche d'abord** pour valider. Décider du modèle commercial une fois la validation prospective publiée.

---

## 10. Recommandations stratégiques prioritaires

### Maintenant (semaines)

1. **Finir l'étape 4** : bouton SBAR → DPI 1 tap. C'est la dernière friction perçue.
2. **Finir l'étape 5** : FAB réévaluation modale. Boucle le workflow IAO.
3. **Découper streamlit_app.py** en modules. Avant que la dette ne devienne ingérable.
4. **Versionner les modèles** dans le bundle joblib. Évite l'incertitude de reproductibilité.
5. **Ajouter CI/CD GitHub Actions**. 30 minutes de setup pour des années de confiance.

### Soon (mois)

6. **Démarrer la validation prospective** sur 1-2 IAO du service cible. 50-100 cas. Ne pas attendre la perfection.
7. **Export FHIR R4** des vitaux et de la décision triage. Pose la fondation interop.
8. **Mode offline PWA** (service worker + Whisper local). Garantit la robustesse terrain.
9. **Documentation utilisateur** : guide IAO en PDF de 5 pages avec captures + workflow. Transfert de connaissance.
10. **Politique RGPD explicite** : durée de conservation audit log, droit d'effacement, base légale.

### Plus tard (trimestres)

11. **Re-training modèle mortalité** sur dataset local après 1000+ séjours collectés.
12. **Dashboard multi-IAO temps réel**. Bascule outil → plateforme.
13. **Préparation dossier CE marking** : commencer par l'analyse des écarts (gap analysis) MDR.
14. **Publication scientifique** : article méthodologique + validation prospective.
15. **Choisir le modèle économique** définitif à la lumière des retours.

---

## 11. Verdict final

AKIR-IAO est un projet **techniquement remarquable** et **cliniquement pertinent**. Sa **maturité produit est forte pour un projet single-developer** :

- Architecture propre, testée, sourcée.
- Mobile-first authentique pour BYOD IAO.
- Intelligence inter-modules effective (next-action + prefill).
- Bases de données solides (KTAS + MIMIC-III + 30k réadmissions).
- Modèles ML explicables avec probabilités et features influentes.

Ses **limites principales sont des limites attendues** à ce stade :

- Dataset mortalité trop petit (action : refaire training local).
- Pas d'export DPI structuré (action : FHIR R4).
- Pas de marquage CE (action : gap analysis MDR à 6 mois).
- Pas de validation prospective (action : 50-100 cas dans le service cible).

Le **potentiel est significatif** dans trois directions complémentaires :
1. **Outil opérationnel du service cible** (à 6 mois si étapes 1-5 finies + validation prospective).
2. **Plateforme de recherche** (à 12 mois si publication scientifique).
3. **Standard régional / open-source ou commercial** (à 18-36 mois si certification + multi-sites).

Sur l'échelle classique TRL (Technology Readiness Level), AKIR-IAO se situe actuellement entre **TRL 5 (validation technologique en environnement représentatif)** et **TRL 6 (démonstration en environnement opérationnel)**. Le passage à TRL 7 (démonstration prototype en environnement opérationnel) nécessite la validation prospective. Le passage à TRL 9 (système qualifié) demande la certification CE.

**Score global, par dimension** :

| Dimension | Note | Commentaire |
|---|---|---|
| Architecture & technique | **A−** | Modulaire, testé, mais monolithe à découper |
| Précision clinique | **A** | Sources, fail-loud, défense profondeur |
| UX flux tendu mobile | **A** | Bottom nav + next-action + presets |
| Intelligence inter-modules | **A−** | Next-action + prefill effectifs |
| Données & ML | **B+** | KTAS+MIMIC OK, mortalité fragile |
| Sécurité / RGPD | **B** | Anonymisation OK, politique manquante |
| Réglementaire (CE) | **C+** | Tout à faire mais clairement faisable |
| Maturité production | **B+** | Manque CI/CD, monitoring, doc |

**Note globale : A−**

Une suite de décisions stratégiques nettes au cours des 6 prochains mois peut faire passer ce projet de "prototype avancé" à "outil légitime de référence dans son service cible". Au-delà, son potentiel d'extension vers un standard régional ou un produit commercial est crédible — sous réserve d'investir dans la validation prospective et le marquage CE.

---

*Document à mettre à jour à chaque révision majeure de l'application. Version 1.0 — 13 mai 2026.*
