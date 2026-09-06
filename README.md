# AKIR-IAO v20

Système expert Streamlit d'aide au triage infirmier d'accueil et d'orientation (IAO), conçu pour un usage clinique aux urgences.  
L'application regroupe le triage FRENCH, les constantes vitales, les scores d'urgence, la pharmacologie de première ligne, les outils de réanimation, la réévaluation et une transmission SBAR exploitable.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://akir-iao.streamlit.app/)

## Objectif

AKIR-IAO aide l'IAO à structurer rapidement une situation d'urgence :

- recueillir le profil patient, les antécédents, traitements, allergies et facteurs de risque ;
- calculer NEWS2, PEWS pédiatrique, Shock Index et indicateurs de gravité ;
- proposer un niveau de triage FRENCH avec justification clinique ;
- générer des alertes de cohérence, de pharmacovigilance et de délai ;
- préparer la réévaluation, l'historique anonymisé et la transmission SBAR.

L'interface v20 est pensée comme un workflow compact, utilisable au poste de tri comme sur tablette ou smartphone.

## Fonctionnalités

### Triage IAO

- Classification FRENCH V1.1 : Tri M, 1, 2, 3A, 3B, 4 et 5.
- Hiérarchie de décision : critères vitaux, NEWS2, priorités cliniques, motif et discriminants.
- Motifs spécialisés : cardiovasculaire, respiratoire, neurologique, traumatique, digestif, infectieux, métabolique, psychiatrie, intoxication et pédiatrie.
- Critères discriminants enrichis par motif.
- Pré-remplissage par dictée clinique avec anonymisation du texte avant traitement.
- Détection d'incohérences entre constantes, motif et niveau de triage.

### Patient et sécurité

- Profil patient : âge, sexe, poids, taille, IMC, poids idéal, fragilité CFS.
- Antécédents structurés, facteurs de risque et traitements courants.
- Alertes immédiates : anticoagulants, grossesse, insuffisance rénale, IMAO, immunodépression, asthme, drépanocytose, allergies.
- Mode pédiatrique avec seuils adaptés.

### Scores et outils cliniques

- Scores d'urgence : NEWS2, PEWS, GCS, qSOFA, HEART, TIMI, NIHSS, ABCD2, Wells, PERC, GRACE, CURB-65, CIWA, PRAM, croup, SOFA partiel.
- Toxicologie : PSS, toxidromes, paracétamol, tricycliques ECG, score TOXIC2.
- Outils urgences : RSI, recharge volémique, Broselow, conversion opioïdes, DFGe CKD-EPI, correction de natrémie, code stroke, énergie de défibrillation, Glasgow-Blatchford.

### Pharmacie et réanimation

- Calculs de doses selon poids, âge, contexte clinique et contre-indications.
- Protocoles IAO : antalgiques, adrénaline, glucose, ceftriaxone, antiémétiques, salbutamol, sepsis, épilepsie pédiatrique, crise hypertensive.
- Perfusions IV : morphine, piritramide, kétamine, midazolam, adrénaline, noradrénaline, insuline, amiodarone, labétalol, magnésium, nicardipine, dobutamine.
- Base de dilutions de réanimation adaptée au contexte belge.
- Vérification de compatibilité IV en Y.
- Étiquettes de préparation et rappel de la règle des 5B.

### Suivi et traçabilité

- Réévaluation des constantes avec delta NEWS2.
- Courbe temporelle des vitaux.
- Registre anonymisé limité en taille.
- Export CSV de session.
- Journal d'audit anonymisé avec chaîne SHA-256 vérifiable.
- Transmission SBAR générée et téléchargeable.

### Module ML expérimental

Le dépôt contient un classifieur Random Forest de priorité de triage (`ml/triage_predictor.py`) entraînable localement. Il fournit une aide secondaire à partir de constantes vitales, NEWS2 et AVPU. Ce module ne remplace pas le moteur clinique FRENCH et doit être considéré comme expérimental.

## Architecture

```text
.
├── streamlit_app.py          # Point d'entrée v20
├── clinical/                 # Moteurs cliniques, scores, triage, pharmacologie
├── ui/                       # Onglets Streamlit et composants d'interface
├── persistence/              # Registre anonymisé et audit
├── ml/                       # Modèle ML de triage expérimental
├── data/                     # Données pharmacie/réanimation
└── tests/                    # Tests unitaires et intégration clinique
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

L'application est ensuite disponible par défaut sur :

```text
http://localhost:8501
```

Pour un usage sur smartphone connecté au même réseau :

```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Puis ouvrir `http://IP_DU_POSTE:8501` depuis le navigateur mobile.

### Lancement rapide (Windows)

Double-cliquer sur `LANCER_AKIR-IAO.bat` : le lanceur force le mode local sécurisé (télémétrie off, serveur sur `localhost`), vérifie Python, ouvre `http://localhost:8501` et démarre l'application.

## Mode local sécurisé (zéro fuite de données)

AKIR-IAO est conçu pour tourner **100 % en local**, sans aucune transmission de données médicales hors du poste :

- **Aucune télémétrie Streamlit** : `gatherUsageStats = false` dans `.streamlit/config.toml` (et `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` dans le lanceur).
- **Aucune ressource distante** : les polices sont celles du système (aucun `@import` Google Fonts), aucune requête réseau n'est émise au démarrage.
- **Serveur borné à `localhost`** par défaut : l'application n'est accessible que depuis le poste (à ouvrir explicitement avec `--server.address 0.0.0.0` pour un usage tablette sur le même réseau, à votre propre responsabilité réseau).
- **NLP local par défaut** : l'extraction de dictée et l'analyse sémantique tournent en local. Les chemins NLP cloud (Claude / GPT) sont **inactifs par défaut**, même si des clés API sont présentes dans l'environnement.

### Activer le NLP cloud (opt-in, à votre propre responsabilité)

Le NLP cloud n'est activé que si **les trois** conditions sont réunies :

1. la variable d'environnement `AKIR_ALLOW_CLOUD_NLP=1` est posée ;
2. les dépendances optionnelles sont installées : `pip install anthropic pydantic openai` (section commentée de `requirements.txt`) ;
3. une clé API valide est fournie dans l'environnement.

Sans le flag, toute clé API présente est **ignorée** et un avertissement est affiché dans l'interface. Aucune donnée n'est alors envoyée à un service tiers.

### Modèles ML et données (Git LFS)

Les fichiers binaires volumineux (`ml/triage_rf_model.joblib`, `ml/triage_model.joblib`, `ml/ecg_model.pth`, `data/*.csv`) sont stockés via **Git LFS**. Après un clone, ils peuvent apparaître comme de petits fichiers texte « pointeur » (~130 octets) : les modules ML/ECG détectent ce cas et affichent un message d'aide au lieu de planter.

```bash
git lfs pull
```

Cette commande restaure les vrais binaires. Sans elle, le moteur clinique FRENCH reste pleinement opérationnel ; seules les aides ML/ECG expérimentales sont indisponibles.

## Tests

```bash
pytest
```

Les tests couvrent notamment le moteur de triage FRENCH, NEWS2, les scores, la pharmacologie, les perfusions, la compatibilité IV et le pré-remplissage par dictée.

## Confidentialité

Voir la section [Mode local sécurisé](#mode-local-sécurisé-zéro-fuite-de-données) : par défaut, aucune donnée ne quitte le poste.

- Aucune identité patient n'est nécessaire au fonctionnement.
- Le registre utilise des UID de session anonymes.
- Les exports ne contiennent pas de nom ni de prénom.
- La dictée clinique est anonymisée avant traitement NLP.
- Le journal d'audit détecte les altérations rétroactives par chaînage SHA-256.

## Références intégrées

Le code s'appuie notamment sur :

- FRENCH Triage V1.1, SFMU 2018 ;
- NEWS2, Royal College of Physicians ;
- protocoles et références BCFI/AFMPS pour le contexte belge ;
- scores cliniques validés cités dans les modules concernés ;
- compatibilités IV issues de tableaux HUG pour l'aide à la préparation.

## Avertissement médical

AKIR-IAO est un outil d'aide à la décision destiné exclusivement à des professionnels de santé qualifiés.  
Il ne remplace pas le jugement clinique, les protocoles institutionnels, les prescriptions médicales, ni les procédures locales de l'établissement.

Toute décision diagnostique, thérapeutique ou d'orientation reste sous la responsabilité de l'équipe soignante.

## Développement

Développeur : Ismail Ibn-Daifa  
Contexte : urgences, Hainaut, Wallonie, Belgique  
Version applicative : v20  
Licence : Apache License 2.0
