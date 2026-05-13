"""
ml/prepare_mimic_data.py — Pipeline MIMIC-III → datasets ML

Produit deux fichiers :
  data/mimic_mortality_features.csv  — prédiction mortalité hospitalière (70 séjours ICU)
  data/mimic_triage_enrichment.csv   — enrichissement triage P1/P2 (vitaux réels ICU)

Sources :
  data/PATIENTS.csv       — démographie + mortalité
  data/ADMISSIONS.csv     — type/lieu admission, diagnostic, expire_flag
  data/CHARTEVENTS.csv    — séries temporelles vitaux ICU (758 k mesures)

Usage : python ml/prepare_mimic_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("data")

# ── Items vitaux MIMIC-III ────────────────────────────────────────────────────
VITAL_ITEMS = {
    220045: "hr",    # Fréquence cardiaque (bpm)
    220277: "spo2",  # SpO2 (%)
    220210: "rr",    # Fréquence respiratoire
    220179: "sbp",   # Pression systolique non-invasive
    220180: "dbp",   # Pression diastolique non-invasive
    220181: "map",   # PAM non-invasive
    220050: "sbp",   # Pression systolique invasive (fusionnée)
    220051: "dbp",   # Pression diastolique invasive (fusionnée)
    220052: "map",   # PAM invasive (fusionnée)
    223761: "temp_f",# Température °F
    220074: "cvp",   # Pression veineuse centrale
}

# Plages valides pour filtrer les outliers
VALID_RANGES = {
    "hr":     (20,  300),
    "spo2":   (50,  100),
    "rr":     (4,   60),
    "sbp":    (40,  300),
    "dbp":    (10,  200),
    "map":    (20,  200),
    "temp_f": (85,  115),
    "cvp":    (-5,  30),
}


def _load_patients() -> pd.DataFrame:
    df = pd.read_csv(DATA / "PATIENTS.csv", encoding="latin-1",
                     parse_dates=["dob", "dod"])
    df["gender_enc"] = (df["gender"] == "F").astype(int)
    # MIMIC anonymise les naissances > 89 ans → âge fictif ~300
    # On plafonne à 90 pour garder un signal cohérent
    df["age_approx"] = ((df["dod"] - df["dob"]).dt.days / 365.25).clip(upper=90)
    return df[["subject_id", "gender_enc", "age_approx"]]


def _load_admissions() -> pd.DataFrame:
    df = pd.read_csv(DATA / "ADMISSIONS.csv", encoding="latin-1",
                     parse_dates=["admittime", "dischtime", "edregtime", "edouttime"])
    df["admission_type_enc"] = df["admission_type"].map(
        {"ELECTIVE": 0, "URGENT": 1, "EMERGENCY": 2}
    ).fillna(1).astype(int)
    df["ed_hours"] = (
        (df["edouttime"] - df["edregtime"]).dt.total_seconds() / 3600
    ).clip(lower=0)
    df["los_hours"] = (
        (df["dischtime"] - df["admittime"]).dt.total_seconds() / 3600
    ).clip(lower=0)
    return df[[
        "subject_id", "hadm_id",
        "admission_type_enc", "hospital_expire_flag",
        "ed_hours", "los_hours",
    ]]


def _load_chartevents() -> pd.DataFrame:
    print("Chargement CHARTEVENTS.csv (758 k lignes)…")
    df = pd.read_csv(DATA / "CHARTEVENTS.csv", encoding="latin-1",
                     low_memory=False,
                     usecols=["hadm_id", "itemid", "valuenum", "error"])
    # Exclure mesures en erreur
    df = df[(df["error"] != 1) & df["valuenum"].notna()].copy()
    df = df[df["itemid"].isin(VITAL_ITEMS)]
    df["vital"] = df["itemid"].map(VITAL_ITEMS)
    return df[["hadm_id", "vital", "valuenum"]]


def _aggregate_vitals(chart: pd.DataFrame) -> pd.DataFrame:
    """Agrège les vitaux par séjour (hadm_id)."""
    rows = []
    for hadm_id, grp in chart.groupby("hadm_id"):
        row: dict = {"hadm_id": hadm_id}
        for vital, limits in VALID_RANGES.items():
            vals = grp.loc[grp["vital"] == vital, "valuenum"]
            vals = vals[(vals >= limits[0]) & (vals <= limits[1])]
            if len(vals) == 0:
                row[f"{vital}_mean"] = np.nan
                row[f"{vital}_min"]  = np.nan
                row[f"{vital}_max"]  = np.nan
            else:
                row[f"{vital}_mean"] = vals.mean()
                row[f"{vital}_min"]  = vals.min()
                row[f"{vital}_max"]  = vals.max()
        row["n_vital_measures"] = len(grp)
        rows.append(row)
    return pd.DataFrame(rows)


def _celsius(f: float) -> float:
    return (f - 32) * 5 / 9


def build_mortality_dataset(
    patients: pd.DataFrame,
    admissions: pd.DataFrame,
    vitals_agg: pd.DataFrame,
) -> pd.DataFrame:
    """Construit le dataset mortalité : 1 ligne = 1 séjour ICU avec vitaux."""
    df = admissions.merge(patients, on="subject_id", how="left")
    df = df.merge(vitals_agg, on="hadm_id", how="left")

    # Température en °C
    for stat in ("mean", "min", "max"):
        col = f"temp_f_{stat}"
        if col in df.columns:
            df[f"temp_c_{stat}"] = df[col].apply(
                lambda x: _celsius(x) if pd.notna(x) else np.nan
            )
            df.drop(columns=[col], inplace=True)

    # Features dérivées
    df["shock_index"] = (df["hr_mean"] / df["sbp_mean"].replace(0, np.nan)).clip(0, 5)

    # Garder uniquement les séjours avec au moins quelques vitaux
    df = df[df["n_vital_measures"].fillna(0) >= 10].copy()

    print(f"Dataset mortalité : {len(df)} séjours | "
          f"décès={df['hospital_expire_flag'].sum()} "
          f"({df['hospital_expire_flag'].mean()*100:.1f}%)")
    return df


def build_triage_enrichment(vitals_agg: pd.DataFrame) -> pd.DataFrame:
    """
    Crée des exemples triage réels KTAS depuis les vitaux ICU.
    Les patients ICU sont tous au moins P2 ; on classe P1 si critères de choc/détresse.
    """
    df = vitals_agg.copy()

    # Température en °C si dispo
    for stat in ("mean", "min", "max"):
        col = f"temp_f_{stat}"
        if col in df.columns:
            df[f"temp_c_{stat}"] = df[col].apply(
                lambda x: _celsius(x) if pd.notna(x) else np.nan
            )

    # Critères P1 (choc / défaillance vitale franche)
    p1_mask = (
        (df["hr_mean"].fillna(0) / df["sbp_mean"].replace(0, np.nan).fillna(100) > 1.0)  # shock index
        | (df["spo2_min"].fillna(100) < 88)
        | (df["sbp_min"].fillna(100) < 70)
        | (df["rr_max"].fillna(0) > 30)
    )
    df["priorite"] = np.where(p1_mask, 1, 2)

    # Renommer pour correspondre au format triage_enriched
    rename = {
        "hr_mean":        "fc",
        "rr_mean":        "fr",
        "sbp_mean":       "pas",
        "dbp_mean":       "pad",
        "spo2_mean":      "spo2",
        "temp_c_mean":    "temp",
    }
    df.rename(columns=rename, inplace=True)

    # Features dérivées
    df["shock_index"]     = (df["fc"] / df["pas"].replace(0, np.nan)).clip(0, 5)
    df["map_val"]         = ((df["pas"] + 2 * df["pad"]) / 3)
    df["pp"]              = df["pas"] - df["pad"]
    df["avpu_enc"]        = 1       # ICU — au minimum réactif à la voix
    df["nrs_pain"]        = 5.0     # douleur supposée modérée en ICU
    df["arrival_ambulance"] = 1
    df["injury"]          = 0

    cols = ["fc", "fr", "pas", "pad", "spo2", "temp",
            "avpu_enc", "nrs_pain", "arrival_ambulance", "injury",
            "shock_index", "map_val", "pp", "priorite"]
    available = [c for c in cols if c in df.columns]
    df_out = df[available].dropna(subset=["fc", "fr", "pas", "spo2"])

    print(f"Enrichissement triage : {len(df_out)} séjours | "
          f"P1={( df_out['priorite']==1).sum()} P2={(df_out['priorite']==2).sum()}")
    return df_out


def main() -> None:
    print("=== Pipeline MIMIC-III → datasets ML ===\n")

    patients   = _load_patients()
    admissions = _load_admissions()
    chart      = _load_chartevents()

    print(f"PATIENTS  : {len(patients)} patients")
    print(f"ADMISSIONS: {len(admissions)} séjours")
    print(f"CHARTEVENTS filtrés : {len(chart):,} mesures vitaux\n")

    print("Agrégation des vitaux par séjour…")
    vitals_agg = _aggregate_vitals(chart)
    print(f"  {len(vitals_agg)} séjours avec données vitaux\n")

    # ── Dataset mortalité ─────────────────────────────────────────────────────
    mortality_df = build_mortality_dataset(patients, admissions, vitals_agg)
    out1 = DATA / "mimic_mortality_features.csv"
    mortality_df.to_csv(out1, index=False)
    print(f"→ Sauvegardé : {out1}  ({len(mortality_df)} lignes)\n")

    # ── Enrichissement triage ─────────────────────────────────────────────────
    triage_df = build_triage_enrichment(vitals_agg)
    out2 = DATA / "mimic_triage_enrichment.csv"
    triage_df.to_csv(out2, index=False)
    print(f"→ Sauvegardé : {out2}  ({len(triage_df)} lignes)\n")

    print("Pipeline terminé.")


if __name__ == "__main__":
    main()
