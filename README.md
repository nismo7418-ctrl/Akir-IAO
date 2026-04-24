# 🚑 AKIR-IAO — Système Expert de Triage Urgences

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://akir-iao.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Version](https://img.shields.io/badge/Version-18.0_Pro-purple.svg)

**AKIR-IAO** est une application web de grade médical conçue pour assister les Infirmiers Organisateurs de l'Accueil (IAO) dans le processus de triage aux urgences.

---

## 🌟 Fonctionnalités Clés
* **Triage Normé** : Implémentation stricte de l'algorithme **FRENCH (SFMU)**.
* **Calculateur de Gravité** : Score **NEWS2** dynamique.
* **Communication SBAR** : Rapports de transmission structurés.
* **Sécurité & Audit** : Registre local persistant pour la traçabilité.

---

## 🏗️ Architecture du Projet
```text
├── streamlit_app.py      # Point d'entrée principal
├── config.py             # Constantes et styles
├── clinical/             # Logique métier
├── persistence/          # Gestion des données
└── ui/                   # Interface et composants
```

---

## 🚀 Installation Locale
1. **Cloner le dépôt** : `git clone https://github.com/nismo7418-ctrl/Akir-IAO.git`
2. **Installer** : `pip install -r requirements.txt`
3. **Lancer** : `streamlit run streamlit_app.py`

---

## 👨‍💻 Développeur
**Ismail Ibn-Daifa**

## ⚖️ Licence
Apache-2.0
