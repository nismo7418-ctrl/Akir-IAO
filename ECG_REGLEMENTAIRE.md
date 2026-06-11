# Mémo réglementaire — AKIR-IAO (module ECG & CDSS de triage)

> Document de travail à destination de la cellule qualité / DPO de l'établissement.
> Rédigé par un développeur, **pas par un juriste** : à faire valider par un
> spécialiste affaires réglementaires et le délégué à la protection des données.
> Objectif : cadrer ce qui doit être réglé **avant** tout usage en conditions réelles.

---

## 1. De quoi parle-t-on

AKIR-IAO propose à l'infirmier d'accueil (IAO) un **niveau de priorité de tri** à partir
de constantes, d'un motif, et — pour le module ECG — d'une **photo d'ECG 12 dérivations**
classée par un modèle. C'est un **système d'aide à la décision clinique (CDSS)**.

Point central : un logiciel qui **oriente la priorisation d'un patient** n'est pas un
simple outil bureautique. Dès lors qu'il influence une décision de soin, il entre dans
le champ du **dispositif médical** et de l'**IA à haut risque**.

---

## 2. Statut dispositif médical (MDR 2017/745)

**Règle 11** (logiciels) : un logiciel destiné à fournir des informations utilisées
pour prendre des décisions à finalité diagnostique ou thérapeutique est en principe
**classe IIa**, et monte en **IIb** si ces décisions peuvent causer une détérioration
grave de l'état de santé ou une intervention chirurgicale.

Application à AKIR-IAO :
- Le triage oriente la rapidité de prise en charge ; un **sous-tri** peut entraîner une
  détérioration grave (infarctus, sepsis non priorisés). — plaide pour **IIb**, ou a
  minima **IIa**, à confirmer.
- Conséquence : **marquage CE**, système de gestion de la qualité (ISO 13485),
  documentation technique, **évaluation clinique**, surveillance après commercialisation.

> Tant que ces éléments n'existent pas, l'usage doit rester **interne, expérimental,
> non substitutif** au jugement IAO, et clairement étiqueté comme tel (déjà le cas dans l'UI).

---

## 3. Statut AI Act (Règlement UE 2024/1689)

Un dispositif médical intégrant de l'IA et soumis à évaluation de conformité au titre du
MDR est classé **IA à haut risque**. Obligations principales qui en découlent :

- **Gestion des risques** documentée sur tout le cycle de vie.
- **Gouvernance des données** : qualité, représentativité, biais des données d'entraînement.
  — directement lié à la limite PTB-XL relevée à l'audit (STEMI/NSTEMI/TV/FV/HYPERK).
- **Transparence** vis-à-vis de l'utilisateur : l'IAO doit savoir qu'il interagit avec une
  IA, ses limites, ses cas d'abstention. — l'onglet ECG l'affiche déjà (disclaimer,
  abstention pédiatrique, alerte fiabilité).
- **Supervision humaine** : décision finale humaine, jamais automatique. — respecté
  (confirmation avant injection, confirmation cardiologue obligatoire).
- **Exactitude, robustesse** : métriques documentées (cf. `ml/ecg_eval.py` + model card).
- **Journalisation** des événements. — le journal d'audit chaîné existe côté app.

---

## 4. RGPD — ce qui doit être en place

Le système traite des **données de santé** (art. 9), même pseudonymisées.

- [ ] **Base légale** du traitement identifiée (mission d'intérêt public / soins).
- [ ] **Registre des traitements** mis à jour (finalité, catégories, durées).
- [ ] **AIPD / DPIA** réalisée — obligatoire pour un traitement de données de santé à
      grande échelle et/ou un profilage influençant une prise en charge.
- [ ] **Minimisation** : aucun nom/prénom (déjà le cas dans la v21 ; registre **pseudonymisé**,
      pas anonyme — vocabulaire à corriger partout).
- [ ] **Durée de conservation** du registre définie et justifiée.
- [ ] **Sécurité** : hébergement conforme données de santé (pas de FS éphémère type
      Streamlit Cloud pour la persistance — SQLite WAL local ou base hospitalière).
- [ ] **Sous-traitants IA externes** (Anthropic / OpenAI du moteur de dictée) :
      - opt-in désactivé par défaut (déjà en place v21) ;
      - **DPA / contrat de sous-traitance** signé avant toute activation ;
      - vérifier la localisation d'hébergement et les **transferts hors UE** ;
      - tracer ce qui est envoyé ; l'anonymisation regex est une réduction de risque,
        **pas une garantie** — ne pas activer sans accord formel.

---

## 5. Spécifique au module ECG — prérequis de sûreté avant usage réel

- [ ] **Rappel STEMI ≥ 95 %** mesuré sur set de test indépendant (`ml/ecg_eval.py`).
- [ ] **Matrice de confusion** + sensibilité/spécificité par classe documentées (model card).
- [ ] **Calibration** appliquée (température T\*) et **seuils garde-fous re-fixés** après.
- [ ] **Cohérence prétraitement** entraînement — production (décalage photo) vérifiée.
- [ ] Classes **non couvertes** (TV/FV/HYPERK) retirées ou sourcées sur dataset dédié.
- [ ] **Model card** complété (chiffres réels, SHA-256 des poids, version).
- [ ] Validation par un **cardiologue / médecin urgentiste** référent.

---

## 6. Position de repli recommandée (en attendant la conformité)

Usage **interne, expérimental, en double lecture** : l'outil propose, l'humain décide et
trace. Pas de substitution au tri IAO, pas de décision automatique, étiquetage
« expérimental » visible. C'est l'état actuel de l'app — à **maintenir explicitement**
jusqu'à l'obtention du marquage CE et la réalisation de l'AIPD.
