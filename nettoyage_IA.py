import os
import numpy as np
import pandas as pd

# Configuration des dossiers
DOSSIER_DATA = "data"

# Valeur KTAS non évaluable pour NRS_pain (encodage corrompu du fichier coréen)
_NRS_NA_VALUES = {"#BOÞ!", "#BOEÞ!", "#BOE!", "?", "??", ""}


def executer_nettoyage():
    print("🧹 Début du nettoyage des données (Optimisation AKIR-IAO)...")

    if not os.path.isdir(DOSSIER_DATA):
        print(f"❌ Dossier de données introuvable : {DOSSIER_DATA}")
        return

    # --- 1. TRAITEMENT DU FICHIER TRIAGE (data.csv) ---
    path_triage = os.path.join(DOSSIER_DATA, "data.csv")
    if os.path.exists(path_triage):
        try:
            df_triage = pd.read_csv(path_triage, sep=';', encoding='latin-1')

            cols_vitals = [
                'Sex', 'Age', 'SBP', 'DBP', 'HR', 'RR', 'BT', 'Saturation', 'KTAS_expert'
            ]
            df_triage = df_triage.loc[:, cols_vitals]

            # Remplissage des valeurs manquantes numériques par la moyenne
            numeric_cols = df_triage.select_dtypes(include=['number']).columns
            df_triage[numeric_cols] = df_triage[numeric_cols].fillna(df_triage[numeric_cols].mean())

            path_out_triage = os.path.join(DOSSIER_DATA, "triage_clean.csv")
            df_triage.to_csv(path_out_triage, index=False, encoding='latin-1')
            print(f"✅ Fichier créé : {path_out_triage}")
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage de data.csv : {e}")

    # --- 1b. TRIAGE ENRICHI avec features cliniques complètes (triage_enriched.csv) ---
    if os.path.exists(path_triage):
        try:
            df = pd.read_csv(path_triage, sep=';', encoding='latin-1')

            # Normaliser les noms de colonnes (espaces → _)
            df.columns = df.columns.str.strip().str.replace(' ', '_')

            # Colonnes requises
            cols_req = ['Sex', 'Age', 'SBP', 'DBP', 'HR', 'RR', 'BT', 'Saturation',
                        'Mental', 'NRS_pain', 'Arrival_mode', 'Injury', 'KTAS_expert']
            missing = [c for c in cols_req if c not in df.columns]
            if missing:
                print(f"⚠️  Colonnes absentes dans data.csv : {missing} — triage_enriched ignoré")
            else:
                df = df[cols_req].copy()

                # Renommage vers les noms du modèle
                df.rename(columns={
                    'SBP': 'pas', 'DBP': 'pad', 'HR': 'fc', 'RR': 'fr',
                    'BT': 'temp', 'Saturation': 'spo2',
                    'Mental': 'mental', 'NRS_pain': 'nrs_pain_raw',
                    'Arrival_mode': 'arrival_mode',
                    'Injury': 'injury',
                    'Sex': 'sex', 'Age': 'age',
                    'KTAS_expert': 'priorite',
                }, inplace=True)

                # Vitales : '??' et valeurs non numériques → NaN → médiane
                for col in ['pas', 'pad', 'fc', 'fr', 'temp', 'spo2', 'age']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].fillna(df[col].median())

                # Mental → avpu_enc  (1=Alert→0, 2=Voice→1, 3=Pain→2, 4=Unresponsive→3)
                df['avpu_enc'] = (
                    pd.to_numeric(df['mental'], errors='coerce')
                    .sub(1).clip(0, 3).fillna(0).astype(int)
                )

                # NRS_pain : valeurs non évaluables → 0, sinon numérique 0-10
                nrs = df['nrs_pain_raw'].astype(str).str.strip()
                nrs = nrs.replace(list(_NRS_NA_VALUES), "0")
                df['nrs_pain'] = pd.to_numeric(nrs, errors='coerce').fillna(0).clip(0, 10)

                # Arrival mode → binaire ambulance
                # Documentation KTAS : 1=Walking, 2=Ambulance publique, 3=Véhicule privé,
                # 4=Ambulance privée, 5-7=Autre → ambulance = codes 2 ou 4
                _am = pd.to_numeric(df['arrival_mode'], errors='coerce')
                df['arrival_ambulance'] = _am.isin([2, 4]).astype(int)

                # Injury → binaire (documentation : 1=Non, 2=Oui)
                df['injury'] = (
                    pd.to_numeric(df['injury'], errors='coerce') == 2
                ).astype(int)

                # Sex → numérique (1=homme, 2=femme dans KTAS → map 0/1)
                df['sex'] = (pd.to_numeric(df['sex'], errors='coerce').fillna(1) - 1).clip(0, 1).astype(int)

                # Features dérivées
                df['shock_index'] = (df['fc'] / df['pas'].replace(0, np.nan)).fillna(1.0).clip(0, 5)
                df['map_val']     = (df['pas'] + 2 * df['pad']) / 3
                df['pp']          = df['pas'] - df['pad']

                # Priorité (cible)
                df['priorite'] = pd.to_numeric(df['priorite'], errors='coerce')

                # Sélection et export — supprimer les lignes avec cible manquante
                out_cols = ['fc', 'fr', 'pas', 'pad', 'spo2', 'temp',
                            'avpu_enc', 'nrs_pain', 'arrival_ambulance', 'injury',
                            'shock_index', 'map_val', 'pp', 'priorite']
                df_out = df[out_cols].dropna(subset=['priorite'])
                df_out['priorite'] = df_out['priorite'].astype(int)

                path_out_enriched = os.path.join(DOSSIER_DATA, "triage_enriched.csv")
                df_out.to_csv(path_out_enriched, index=False)
                dist = df_out['priorite'].value_counts().sort_index().to_dict()
                print(f"✅ Fichier créé : {path_out_enriched} ({len(df_out)} lignes | {dist})")

        except Exception as e:
            print(f"❌ Erreur lors de la création de triage_enriched.csv : {e}")
    else:
        print(f"⚠️ Fichier introuvable : {path_triage}")

    # --- 2. TRAITEMENT DES RÉADMISSIONS (hospital_readmissions_30k.csv) ---
    path_30k = os.path.join(DOSSIER_DATA, "hospital_readmissions_30k.csv")
    if os.path.exists(path_30k):
        try:
            df_30k = pd.read_csv(path_30k, encoding='latin-1')

            if 'blood_pressure' in df_30k.columns:
                blood_pressure = df_30k['blood_pressure'].astype(str).str.strip()
                split_bp = blood_pressure.str.split('/', expand=True)
                df_30k['systolic'] = pd.to_numeric(split_bp[0], errors='coerce')
                df_30k['diastolic'] = pd.to_numeric(split_bp[1], errors='coerce')
            else:
                raise KeyError('Colonne blood_pressure introuvable')

            if 'gender' in df_30k.columns:
                df_30k['gender'] = df_30k['gender'].astype(str).str.strip().map({
                    'Male': 0,
                    'Female': 1,
                    'Other': 2,
                    'M': 0,
                    'F': 1
                })
            else:
                raise KeyError('Colonne gender introuvable')

            for col in ['diabetes', 'hypertension', 'readmitted_30_days']:
                if col in df_30k.columns:
                    df_30k[col] = df_30k[col].astype(str).str.strip().map({'Yes': 1, 'No': 0})
                else:
                    print(f"⚠️ Colonne manquante dans readmissions: {col}")

            path_out_30k = os.path.join(DOSSIER_DATA, "readmissions_clean.csv")
            df_30k.to_csv(path_out_30k, index=False, encoding='latin-1')
            print(f"✅ Fichier créé : {path_out_30k}")
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage de hospital_readmissions_30k.csv : {e}")
    else:
        print(f"⚠️ Fichier introuvable : {path_30k}")


if __name__ == '__main__':
    executer_nettoyage()
