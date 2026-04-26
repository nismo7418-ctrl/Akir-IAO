# 🏥 AKIR-IAO v19.0 — Système expert de triage médical

Application Streamlit professionnelle pour l'aide à la décision clinique en urgences.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://akir-iao.streamlit.app/)

## 🚀 Installation & Utilisation

### Installation rapide
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Mode mobile (application dans la poche)
1. Lancez l'app localement : `streamlit run streamlit_app.py --server.port 8501`
2. Sur votre smartphone : ouvrez le navigateur et allez à `http://[IP_DE_VOTRE_PC]:8501`
3. Ajoutez à l'écran d'accueil pour un accès rapide

## 📋 Fonctionnalités principales

- ⚡ **Tri Rapide** : Constantes vitales + motif = triage instantané
- 📊 **Vitaux & GCS** : Évaluation neurologique détaillée
- 🔍 **Anamnèse** : Questionnaire PQRST + antécédents
- ⚖️ **Triage FRENCH v1.1** : Classification officielle SFMU
- 🧮 **Scores Cliniques** : NEWS2, qSOFA, HEART, TIMI, etc.
- 💊 **Pharmacie** : Doses calculées automatiquement + alertes
- 🔄 **Réévaluation** : Suivi temporel des constantes
- 📋 **Historique** : Registre anonymisé RGPD

## ⚖️ Avertissement médical

**Cette application est un outil d'aide à la décision clinique destiné exclusivement aux professionnels de santé qualifiés.**

Elle ne se substitue en aucun cas au jugement clinique du praticien ni aux protocoles institutionnels en vigueur.

- Classification fondée sur **FRENCH Triage V1.1 (SFMU 2018)**
- Protocoles **BCFI Belgique**
- Localisation : Urgences — Province de Hainaut, Wallonie

**Aucune donnée nominative n'est stockée (RGPD compliant).**

## 🛠️ Développement

Développeur : Ismail Ibn-Daifa  
Contact : ismail.ibn-daifa@outlook.com  
Version : 19.0 (2025)

## 📄 Licence

Apache License 2.0
