# Model card — Classifieur ECG AKIR-IAO

> Gabarit à compléter avec les chiffres RÉELS produits par l'entraînement.
> Tant que les champs `<À COMPLÉTER>` ne sont pas remplis et le gate franchi,
> le module reste **expérimental, non substitutif** (cf. `ECG_REGLEMENTAIRE.md`).

## Identité

| Champ | Valeur |
|-------|--------|
| Version du modèle | `<À COMPLÉTER — ex. v21.0>` |
| Date d'entraînement | `<À COMPLÉTER>` |
| Architecture | EfficientNet-B2 (timm), `input_resolution=260` |
| Fichier de poids | `ml/ecg_model.pth` |
| SHA-256 des poids | `<À COMPLÉTER — voir ml/ecg_metrics.json>` |
| Jeu de données | PTB-XL 1.0.3 (waveforms → images), split patient `strat_fold` |

## Taxonomie & support données

Source unique : [clinical/ecg_labels.py](clinical/ecg_labels.py). Chaque classe
porte un niveau de **support données** :

- `FULL` — couvert correctement par PTB-XL.
- `PARTIAL` — présent mais non distinctif / surtout séquellaire (ex. `ST_ELEVATION`,
  `ISCHEMIA_NONST`, `AVB2`, `AVB3`).
- `NONE` — quasi absent : **classes exclues de l'entraînement** (`VT`, `VF`, `HYPERK`).
  Le modèle ne prédit jamais ces classes ; l'UI signale leur non-fiabilité.

Classes entraînées : `NORM, ST_ELEVATION, ISCHEMIA_NONST, AFIB, AFLUTTER, AVB1,
AVB2, AVB3, LBBB, RBBB`.

## Métriques (jeu de test indépendant — fold 10)

> Générer via `ml/train_ecg_model.py` (écrit `ml/ecg_metrics.json`) ou
> `ml/evaluate_ecg.markdown_report(y_true, y_pred, calibration)`.

| Classe | Sensibilité | Spécificité | Support |
|--------|-------------|-------------|---------|
| `<À COMPLÉTER>` | | | |

**Rappel STEMI groupé (ST_ELEVATION) : `<À COMPLÉTER>` — cible ≥ 95 %** (métrique bloquante).

## Calibration

| Champ | Avant | Après (T\*) |
|-------|-------|-------------|
| Température T\* | 1.0 | `<À COMPLÉTER>` |
| NLL | `<À COMPLÉTER>` | `<À COMPLÉTER>` |
| ECE | `<À COMPLÉTER>` | `<À COMPLÉTER>` |

> ⚠️ Les seuils des garde-fous (R1 = 0.30, R2 = 0.40 dans
> [clinical/ecg_garde_fous.py](clinical/ecg_garde_fous.py)) doivent être
> **re-fixés APRÈS** application de T\*.

## Gate de déployabilité

Produit par `ml/ecg_eval.safety_gate`. Le rappel STEMI < 95 % bloque le déploiement.

```
deployable        : <À COMPLÉTER>
stemi_sensitivity : <À COMPLÉTER>
reasons           : <À COMPLÉTER>
```

## Limites connues

- PTB-XL annote surtout des MI **séquellaires** : `ST_ELEVATION` est approximatif
  (mapping `PARTIAL`), à valider contre `scp_statements.csv`.
- L'ECG seul ne distingue pas un NSTEMI (diagnostic troponine) — libellés à lire
  comme « pattern ischémique », pas comme diagnostic.
- **Cohérence prétraitement train/prod** : entraîné sur rendus matplotlib ; un
  déploiement sur **photos de tracés papier** nécessite d'entraîner sur photos
  (ou un prétraitement de redressement) — sinon décalage de distribution.
- Non validé en **pédiatrie** (< 16 ans) : abstention automatique (R0).

## Supervision

Décision finale **humaine** : confirmation IAO avant injection dans le triage
(majoration upgrade-only), confirmation **cardiologue obligatoire**.
