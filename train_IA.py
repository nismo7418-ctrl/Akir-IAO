import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


DATA_DIR = "data"
INPUT_FILE = "triage_clean.csv"
OUTPUT_MODEL = "triage_model.joblib"
FEATURE_COLUMNS = ["Sex", "Age", "SBP", "DBP", "HR", "RR", "BT", "Saturation"]
TARGET_COLUMN = "KTAS_expert"


def main() -> None:
    data_path = os.path.join(DATA_DIR, INPUT_FILE)

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Fichier introuvable : {data_path}. "
            "Exécutez d'abord nettoyage_IA.py pour créer data/triage_clean.csv."
        )

    print("🚀 Début de l'entraînement du modèle AKIR-IAO...")

    df = pd.read_csv(data_path, encoding="latin-1")

    missing_cols = [col for col in FEATURE_COLUMNS + [TARGET_COLUMN] if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Colonnes manquantes dans {data_path} : {missing_cols}")

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN]

    X['Sex'] = X['Sex'].astype(str).str.strip().map({
        'Male': 0,
        'Female': 1,
        'M': 0,
        'F': 1,
        'male': 0,
        'female': 1,
        'm': 0,
        'f': 1,
    })

    numeric_columns = ['Age', 'SBP', 'DBP', 'HR', 'RR', 'BT', 'Saturation']
    for col in numeric_columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')

    if X.isna().any().any():
        print("⚠️ Données invalides détectées dans les features, remplissage par la moyenne.")
        X = X.fillna(X.mean())

    print(f"   Données chargées : {len(df)} lignes")
    print(f"   Features utilisées : {FEATURE_COLUMNS}")
    print(f"   Cible : {TARGET_COLUMN}")

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Split : {len(X_train)} train, {len(X_test)} test")

    model = RandomForestClassifier(
        n_estimators=100,
        n_jobs=-1,
        random_state=42,
    )

    model.fit(X_train, y_train)
    print("✅ Entraînement terminé.")

    # Évaluation simple
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"📊 Accuracy sur test : {accuracy:.3f}")
    print("\n=== Rapport de classification ===")
    print(classification_report(y_test, y_pred))

    joblib.dump(model, OUTPUT_MODEL)
    print(f"✅ Modèle sauvegardé dans : {OUTPUT_MODEL}")


if __name__ == "__main__":
    main()

