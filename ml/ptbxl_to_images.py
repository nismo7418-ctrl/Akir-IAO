"""
ml/ptbxl_to_images.py — Conversion PTB-XL waveforms → images ECG pour AKIR-IAO

PTB-XL est un dataset de waveforms 12-dérivations au format WFDB. Notre
classifieur (ml/ecg_predictor.py) prend des images. Ce script :

  1. Lit ptbxl_database.csv (métadonnées + codes SCP-ECG par enregistrement)
  2. Mappe les codes SCP-ECG vers nos 15 labels diagnostiques
  3. Pour chaque enregistrement sélectionné : charge le signal WFDB, trace
     un ECG standard 12-dérivations (3 lignes × 4 colonnes + bande II) et
     l'exporte en PNG sous data/ecg/images/<ecg_id>.png
  4. Génère data/ecg/labels.csv au format attendu par ml/train_ecg_model.py

╔══ Format de sortie ════════════════════════════════════════════════════════╗
║   data/ecg/                                                                ║
║     images/                                                                ║
║       00001.png  (ECG 1200×800 px, mise en page standard)                  ║
║       00002.png                                                            ║
║       ...                                                                  ║
║     labels.csv                                                             ║
║       image_id,label                                                       ║
║       00001,NORM                                                           ║
║       00002,STEMI_INF                                                      ║
║       ...                                                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

Mapping SCP-ECG → 15 labels AKIR-IAO :
    NORM      ← NORM
    STEMI_ANT ← AMI, ASMI, ALMI
    STEMI_INF ← IMI, ILMI
    STEMI_LAT ← LMI, IPLMI
    NSTEMI    ← ISCAL, ISCAS, ISCIL, ISCIN, ISCLA, ISC_, NDT, NST_
    AF        ← AFIB
    AFL       ← AFLT
    VT        ← (peu/aucun cas dans PTB-XL, classe sous-représentée)
    VF        ← (idem)
    AVB1      ← 1AVB
    AVB2      ← 2AVB
    AVB3      ← 3AVB
    LBBB      ← CLBBB, ILBBB
    RBBB      ← CRBBB, IRBBB
    HYPERK    ← (pas de code spécifique dans PTB-XL — classe vide ou
                 à compléter manuellement)

Les enregistrements multi-labellisés sont assignés à leur label le plus
critique (priorité KTAS la plus basse — cf. ECG_DEFAULT_PRIORITY).

Usage :
    python ml/ptbxl_to_images.py                    # tout convertir (long !)
    python ml/ptbxl_to_images.py --max-per-class 500
    python ml/ptbxl_to_images.py --dry-run          # juste les stats
    python ml/ptbxl_to_images.py --rate 500         # signal 500 Hz (défaut 100)
"""

from __future__ import annotations

import argparse
import ast
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
_LOG = logging.getLogger(__name__)

from ml.ecg_predictor import ECG_DEFAULT_PRIORITY, ECG_LABELS

# ── Chemins ──────────────────────────────────────────────────────────────────
PTBXL_ROOT  = Path("data/physionet.org/files/ptb-xl/1.0.3")
PTBXL_CSV   = PTBXL_ROOT / "ptbxl_database.csv"
OUT_ROOT    = Path("data/ecg")
OUT_IMAGES  = OUT_ROOT / "images"
OUT_LABELS  = OUT_ROOT / "labels.csv"

# ── Mapping SCP-ECG → nos 15 labels ──────────────────────────────────────────
SCP_TO_LABEL: dict[str, str] = {
    # Normal
    "NORM": "NORM",
    # Infarctus antérieurs (STEMI_ANT)
    "AMI":   "STEMI_ANT",   # anterior MI
    "ASMI":  "STEMI_ANT",   # antero-septal MI
    "ALMI":  "STEMI_ANT",   # antero-lateral MI
    # Infarctus inférieurs (STEMI_INF)
    "IMI":   "STEMI_INF",
    "ILMI":  "STEMI_INF",
    # Infarctus latéraux (STEMI_LAT)
    "LMI":   "STEMI_LAT",
    "IPLMI": "STEMI_LAT",
    "PMI":   "STEMI_LAT",
    # Ischémie / NSTEMI (anomalies ST/T sans STEMI)
    "ISC_":  "NSTEMI",
    "ISCAL": "NSTEMI",
    "ISCAS": "NSTEMI",
    "ISCIL": "NSTEMI",
    "ISCIN": "NSTEMI",
    "ISCLA": "NSTEMI",
    "NDT":   "NSTEMI",
    "NST_":  "NSTEMI",
    # Arythmies atriales
    "AFIB":  "AF",
    "AFLT":  "AFL",
    # BAV
    "1AVB":  "AVB1",
    "2AVB":  "AVB2",
    "3AVB":  "AVB3",
    # Blocs de branche
    "CLBBB": "LBBB",
    "ILBBB": "LBBB",
    "CRBBB": "RBBB",
    "IRBBB": "RBBB",
}

LEAD_ORDER = ["I", "II", "III", "aVR", "aVL", "aVF",
              "V1", "V2", "V3", "V4", "V5", "V6"]


def _lazy_imports():
    try:
        import wfdb  # noqa: F401
        import matplotlib  # noqa: F401
        matplotlib.use("Agg")  # backend non-interactif
        import matplotlib.pyplot as plt  # noqa: F401
        import pandas as pd  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "❌ Dépendances manquantes pour la conversion PTB-XL.\n"
            "    pip install wfdb matplotlib pandas\n"
            f"    (vu : {exc})"
        )


# ── Sélection du label le plus critique ──────────────────────────────────────

def _pick_best_label(scp_codes: dict[str, float]) -> str | None:
    """
    Un enregistrement peut avoir plusieurs codes SCP. On garde le label avec
    la priorité KTAS la plus basse (= la plus critique).
    Retourne None si aucun code ne map vers nos 15 labels.
    """
    candidates = []
    for code, _confidence in scp_codes.items():
        lbl = SCP_TO_LABEL.get(code)
        if lbl is not None:
            candidates.append((ECG_DEFAULT_PRIORITY[lbl], lbl))
    if not candidates:
        return None
    candidates.sort()  # tri croissant sur priorité (1 = plus urgent)
    return candidates[0][1]


# ── Chargement du dataset ────────────────────────────────────────────────────

def _load_metadata(rate: int):
    """Lit ptbxl_database.csv, parse scp_codes, mappe vers nos labels."""
    import pandas as pd

    if not PTBXL_CSV.exists():
        raise SystemExit(
            f"❌ {PTBXL_CSV} introuvable.\n"
            "    Télécharge d'abord PTB-XL :\n"
            "    cd data && wget -r -N -c -np https://physionet.org/files/ptb-xl/1.0.3/"
        )

    df = pd.read_csv(PTBXL_CSV, index_col="ecg_id")
    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)
    df["label"]     = df["scp_codes"].apply(_pick_best_label)
    df = df.dropna(subset=["label"])

    fname_col = "filename_hr" if rate == 500 else "filename_lr"
    df = df[df[fname_col].notna()].copy()
    df["wfdb_path"] = df[fname_col].apply(lambda f: PTBXL_ROOT / f)

    _LOG.info("Métadonnées chargées : %d enregistrements labellisés (sur %d)",
              len(df), len(pd.read_csv(PTBXL_CSV)))
    dist = Counter(df["label"])
    _LOG.info("Distribution avant équilibrage : %s",
              {l: dist.get(l, 0) for l in ECG_LABELS})
    return df


# ── Tracé ECG 12 dérivations style standard ──────────────────────────────────

def _plot_ecg(signal, sample_rate: int, out_path: Path, title: str = ""):
    """
    Trace un ECG 12 dérivations en mise en page standard (3 lignes × 4 colonnes
    + bande II en rythme).

    Implémentation **rapide** : un seul Axes, dérivations posées par offset
    (x = colonne·2,5 s ; y = 14 mV·(3-row)). Grille mm-paper dessinée
    manuellement par lignes (10× plus rapide que matplotlib gridspec).
    Sortie : ~5× plus rapide que la version multi-subplot, suffisant pour
    le modèle qui ré-échantillonne à 260×260 px de toute façon.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    n_samples = signal.shape[0]
    duration  = n_samples / sample_rate          # ≈ 10 s
    t_full    = np.linspace(0, duration, n_samples)
    seg_len   = int(2.5 * sample_rate)

    grid_layout = [
        ["I",   "aVR", "V1", "V4"],
        ["II",  "aVL", "V2", "V5"],
        ["III", "aVF", "V3", "V6"],
    ]
    lead_idx = {l: i for i, l in enumerate(LEAD_ORDER)}

    # Coordonnées : x ∈ [0, 10 s] · y ∈ [0, 16 mV] (4 bandes de 4 mV chacune)
    X_MAX = 10.0
    Y_MAX = 16.0
    BAND_H = 4.0
    LEAD_AMP = 1.5  # gain visuel des dérivations dans leur bande

    fig = plt.figure(figsize=(9.5, 6), dpi=80, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, X_MAX); ax.set_ylim(0, Y_MAX)
    ax.set_axis_off()

    # ── Grille mm-paper (lignes uniquement, pas de minor grid) ────────────
    # Lignes verticales tous les 0,2 s (gros carreau)
    xs_major = np.arange(0, X_MAX + 0.01, 0.2)
    ys_major = np.arange(0, Y_MAX + 0.01, 0.5)
    ax.vlines(xs_major, 0, Y_MAX, colors="#FCA5A5", linewidths=0.4, zorder=1)
    ax.hlines(ys_major, 0, X_MAX, colors="#FCA5A5", linewidths=0.4, zorder=1)

    # ── 12 dérivations en 3 × 4 ──
    for r in range(3):
        y_center = Y_MAX - BAND_H * (r + 0.5)
        for c in range(4):
            lead = grid_layout[r][c]
            i = lead_idx[lead]
            seg_start = c * seg_len
            seg_end   = min(seg_start + seg_len, n_samples)
            xs = (t_full[seg_start:seg_end] - t_full[seg_start]) + c * 2.5
            ys = signal[seg_start:seg_end, i] * LEAD_AMP + y_center
            ax.plot(xs, ys, color="black", linewidth=0.6, zorder=2)
            ax.text(c * 2.5 + 0.05, y_center + BAND_H * 0.35, lead,
                    fontsize=9, fontweight="bold", color="black", zorder=3)

    # ── Bande rythme II (10 s complètes) ──
    y_rhythm = BAND_H * 0.5
    ax.plot(t_full, signal[:, lead_idx["II"]] * LEAD_AMP + y_rhythm,
            color="black", linewidth=0.6, zorder=2)
    ax.text(0.05, y_rhythm + BAND_H * 0.35, "II",
            fontsize=9, fontweight="bold", color="black", zorder=3)

    if title:
        ax.text(X_MAX / 2, Y_MAX - 0.15, title, fontsize=7, color="#475569",
                ha="center", va="top", zorder=3)

    fig.savefig(out_path, dpi=80, facecolor="white")
    plt.close(fig)


# ── Échantillonnage équilibré ────────────────────────────────────────────────

def _balance_by_class(df, max_per_class: int, min_per_class: int = 0):
    """
    Filtre + sous-échantillonne :
      - Exclut les classes < min_per_class (pas assez d'exemples pour entraîner)
      - Plafonne chaque classe restante à max_per_class
    """
    import pandas as pd
    parts = []
    dropped = []
    for lbl in ECG_LABELS:
        sub = df[df["label"] == lbl]
        if len(sub) < min_per_class:
            if len(sub) > 0:
                dropped.append((lbl, len(sub)))
            continue
        if len(sub) > max_per_class:
            sub = sub.sample(n=max_per_class, random_state=42)
        parts.append(sub)
    if dropped:
        _LOG.info("Classes exclues (< %d exemples) : %s",
                  min_per_class, {l: n for l, n in dropped})
    return pd.concat(parts) if parts else df.iloc[0:0]


# ── Pipeline principal ───────────────────────────────────────────────────────

def convert(
    max_per_class: int = 500,
    min_per_class: int = 50,
    rate: int = 100,
    dry_run: bool = False,
    out_root: Path = OUT_ROOT,
):
    _lazy_imports()
    import wfdb
    import pandas as pd

    df = _load_metadata(rate)
    # Filtrer aux enregistrements WFDB réellement présents en local (PTB-XL partiel ok)
    n_before = len(df)
    df = df[df["wfdb_path"].apply(lambda p: (p.parent / (p.name + ".dat")).exists())]
    _LOG.info("Records labellisés présents en local : %d / %d", len(df), n_before)

    df = _balance_by_class(df, max_per_class, min_per_class=min_per_class)
    dist = Counter(df["label"])
    _LOG.info("Distribution après équilibrage (max %d/classe) : %s",
              max_per_class, {l: dist.get(l, 0) for l in ECG_LABELS})

    if dry_run:
        _LOG.info("[DRY-RUN] %d images seraient générées dans %s", len(df), out_root)
        for lbl in ECG_LABELS:
            n = dist.get(lbl, 0)
            warn = "  ⚠️ classe vide" if n == 0 else ""
            print(f"  {lbl:10s} : {n:>5d}{warn}")
        return

    out_images = out_root / "images"
    out_images.mkdir(parents=True, exist_ok=True)
    out_labels = out_root / "labels.csv"

    tasks = [(int(ecg_id), str(row["wfdb_path"]), row["label"], out_images)
             for ecg_id, row in df.iterrows()]
    n_total = len(tasks)

    try:
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, (os.cpu_count() or 2))
        _LOG.info("Conversion parallèle sur %d cœurs (%d images)", n_jobs, n_total)
        results = Parallel(n_jobs=n_jobs, backend="loky", verbose=5)(
            delayed(_render_one)(t) for t in tasks
        )
    except ImportError:
        _LOG.info("joblib indisponible — conversion séquentielle")
        results = [_render_one(t) for t in tasks]

    rows = [r for r in results if r is not None]
    n_done = len(rows)
    n_fail = n_total - n_done

    pd.DataFrame(rows).to_csv(out_labels, index=False)
    _LOG.info("✅ Terminé : %d images générées → %s", n_done, out_images)
    _LOG.info("    labels.csv → %s (%d échecs)", out_labels, n_fail)


def _render_one(task):
    """Worker : charge un record WFDB, trace l'ECG, sauvegarde le PNG.
    Retourne {image_id, label} ou None en cas d'échec.
    Doit rester picklable (pas de fermeture sur des objets matplotlib).
    """
    ecg_id, wfdb_path, label, out_images = task
    try:
        import wfdb
        sig, fields = wfdb.rdsamp(wfdb_path)
        sig_names = [n.replace("AVR", "aVR").replace("AVL", "aVL").replace("AVF", "aVF")
                     for n in fields["sig_name"]]
        if sig_names != LEAD_ORDER:
            idx_map = [sig_names.index(l) for l in LEAD_ORDER if l in sig_names]
            if len(idx_map) != 12:
                return None
            sig = sig[:, idx_map]

        image_id = f"{ecg_id:05d}"
        out_path = out_images / f"{image_id}.png"
        _plot_ecg(sig, sample_rate=int(fields["fs"]), out_path=out_path,
                  title=f"PTB-XL {image_id} · {label}")
        return {"image_id": image_id, "label": label}
    except Exception:  # noqa: BLE001
        return None


def _cli():
    p = argparse.ArgumentParser(description="PTB-XL → images ECG pour AKIR-IAO")
    p.add_argument("--max-per-class", type=int, default=500,
                   help="Plafond d'enregistrements par label (défaut : 500)")
    p.add_argument("--min-per-class", type=int, default=50,
                   help="Seuil minimum sous lequel la classe est exclue (défaut : 50)")
    p.add_argument("--rate", type=int, choices=[100, 500], default=100,
                   help="Fréquence d'échantillonnage (100 ou 500 Hz, défaut : 100)")
    p.add_argument("--dry-run", action="store_true",
                   help="Affiche les statistiques sans générer d'images")
    p.add_argument("--out-root", type=Path, default=OUT_ROOT,
                   help="Dossier de sortie (défaut : data/ecg/)")
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    convert(
        max_per_class=args.max_per_class,
        min_per_class=args.min_per_class,
        rate=args.rate,
        dry_run=args.dry_run,
        out_root=args.out_root,
    )
