# ml/train_ecg_model.py — Entraînement du classifieur ECG — AKIR-IAO v21
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# À LANCER SUR TA MACHINE (GPU + accès PhysioNet) :
#     pip install torch timm --index-url https://download.pytorch.org/whl/cpu  # ou cu121
#     pip install wfdb pandas numpy matplotlib pillow scikit-learn
#     python ml/train_ecg_model.py --ptbxl /chemin/ptbxl --epochs 15
#     python ml/train_ecg_model.py --smoke      # vérifie le pipeline sans PTB-XL
#
# Principes (issus de l'audit) :
#   - Libellés HONNÊTES : on n'invente pas STEMI/NSTEMI/TV/FV/HYPERK que PTB-XL
#     ne couvre pas. Les classes sans données (UNSUPPORTED_CODES) sont EXCLUES
#     de l'entraînement. Voir clinical/ecg_labels.py.
#   - Split PATIENT (strat_fold PTB-XL) — aucune fuite entre train/val/test.
#   - Déséquilibre traité par pondération de classes (CrossEntropy weights).
#   - Le « meilleur » modèle est choisi sur le RAPPEL STEMI, pas l'accuracy.
#   - Après entraînement : métriques par classe + calibration (T*) + gate de
#     déployabilité via ml/ecg_eval.py, écrits dans un JSON pour le model card.
#
# torch / timm / wfdb / matplotlib sont importés PARESSEUSEMENT : ce fichier
# s'importe (et son mapping se teste) sans aucune de ces dépendances.

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Permet `python ml/train_ecg_model.py` depuis la racine du dépôt.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clinical.ecg_labels import (
    LABELS, UNSUPPORTED_CODES, classify, resolve_code,
)

IMG_SIZE = 260
SEED = 42
MODEL_NAME = "efficientnet_b2"

# Le predictor (ml/ecg_predictor.py) charge ce fichier ; on garde le même nom
# pour que train et inférence restent cohérents.
DEFAULT_CHECKPOINT = "ecg_model.pth"

# Classes réellement entraînables = taxonomie honnête MOINS les classes sans données.
TRAINABLE_LABELS: List[str] = [c for c in LABELS if c not in UNSUPPORTED_CODES
                               and c != "UNKNOWN"]


# ─────────────────────────────────────────────────────────────────────────────
# Mapping SCP-ECG (PTB-XL) — libellés canoniques honnêtes  [PUR — testé ici]
# ─────────────────────────────────────────────────────────────────────────────
#
# ⚠️ PTB-XL annote surtout des MI SÉQUELLAIRES, pas la lésion aiguë : le mapping
# vers ST_ELEVATION est donc APPROXIMATIF (data_support = PARTIAL). À vérifier
# contre scp_statements.csv. Codes non pertinents — None (ignorés).

_SCP_TO_CANONICAL: Dict[str, str] = {
    # Normal
    "NORM": "NORM",
    # Infarctus (territoires) — sus-décalage / ischémie aiguë (approximatif)
    "AMI": "ST_ELEVATION", "ASMI": "ST_ELEVATION", "ALMI": "ST_ELEVATION",
    "IMI": "ST_ELEVATION", "ILMI": "ST_ELEVATION", "IPMI": "ST_ELEVATION",
    "IPLMI": "ST_ELEVATION", "INJAS": "ST_ELEVATION", "INJAL": "ST_ELEVATION",
    "INJIN": "ST_ELEVATION", "INJIL": "ST_ELEVATION", "INJLA": "ST_ELEVATION",
    "LMI": "ST_ELEVATION", "PMI": "ST_ELEVATION",
    # Anomalies ST/T sans sus-décalage — ischémie non-ST (— contexte NSTEMI)
    "ISCAL": "ISCHEMIA_NONST", "ISCAS": "ISCHEMIA_NONST", "ISCLA": "ISCHEMIA_NONST",
    "ISCAN": "ISCHEMIA_NONST", "ISCIN": "ISCHEMIA_NONST", "ISCIL": "ISCHEMIA_NONST",
    "ISC_": "ISCHEMIA_NONST", "NDT": "ISCHEMIA_NONST", "NST_": "ISCHEMIA_NONST",
    "STD_": "ISCHEMIA_NONST", "DIG": "ISCHEMIA_NONST",
    # Rythme
    "AFIB": "AFIB", "AFLT": "AFLUTTER",
    # Conduction
    "1AVB": "AVB1", "2AVB": "AVB2", "3AVB": "AVB3",
    "CLBBB": "LBBB", "ILBBB": "LBBB",
    "CRBBB": "RBBB", "IRBBB": "RBBB",
}


def scp_to_canonical(code: str) -> Optional[str]:
    """Mappe un code SCP-ECG vers un libellé canonique honnête, ou None si ignoré."""
    if not code:
        return None
    c = _SCP_TO_CANONICAL.get(code.strip().upper())
    if c is None:
        return None
    # Filtre de sûreté : on n'entraîne jamais une classe sans données.
    return c if c in TRAINABLE_LABELS else None


def select_primary_label(codes: Iterable[str]) -> Optional[str]:
    """Parmi les codes SCP d'un enregistrement, retient le libellé le PLUS urgent.

    Logique « pire cas » : un tracé avec MI + trouble de conduction est étiqueté
    sur l'anomalie la plus critique. NORM n'est retenu que s'il est seul.
    """
    cands = [c for c in (scp_to_canonical(x) for x in codes) if c]
    if not cands:
        return None
    non_norm = [c for c in cands if c != "NORM"]
    if not non_norm:
        return "NORM"
    # priorité de base : 1 = plus urgent — on prend le min
    return min(non_norm, key=lambda c: classify(c)[1])


# ─────────────────────────────────────────────────────────────────────────────
# Rendu waveform — image (PTB-XL)            [paresseux : wfdb/matplotlib/PIL]
# ─────────────────────────────────────────────────────────────────────────────

def waveform_to_image(signal, fs: int = 100):
    """Trace 12 dérivations empilées en une image RGB IMG_SIZE×IMG_SIZE.

    ⚠️ COHÉRENCE TRAIN/PROD : ce rendu doit ressembler à ce que verra le modèle
    en production. Si tu déploies sur des PHOTOS de tracés papier, entraîne sur
    des photos (ou ajoute un prétraitement de redressement) — sinon décalage.
    """
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    n_leads = signal.shape[1]
    fig, axes = plt.subplots(n_leads, 1, figsize=(4, 4), dpi=IMG_SIZE / 4)
    if n_leads == 1:
        axes = [axes]
    for i, ax in enumerate(axes):
        ax.plot(signal[:, i], linewidth=0.5, color="black")
        ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB").resize((IMG_SIZE, IMG_SIZE))


# ─────────────────────────────────────────────────────────────────────────────
# Dataset PTB-XL                                                  [paresseux]
# ─────────────────────────────────────────────────────────────────────────────

def build_dataframe(ptbxl_dir: Path):
    """Charge ptbxl_database.csv + scp_statements.csv et calcule le label primaire."""
    import ast
    import pandas as pd

    df = pd.read_csv(ptbxl_dir / "ptbxl_database.csv", index_col="ecg_id")
    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)
    df["label"] = df["scp_codes"].apply(lambda d: select_primary_label(d.keys()))
    df = df[df["label"].notna()].copy()
    return df


class PTBXLDataset:
    """Dataset torch (importé paresseusement pour rester testable sans torch)."""

    def __init__(self, df, ptbxl_dir: Path, label_to_idx: Dict[str, int], fs: int = 100):
        self.df = df.reset_index()
        self.dir = Path(ptbxl_dir)
        self.label_to_idx = label_to_idx
        self.fs = fs
        self.fcol = "filename_lr" if fs == 100 else "filename_hr"

    def __len__(self):
        return len(self.df)

    def __getitem__(self, i):
        import numpy as np
        import torch
        import wfdb
        from torchvision import transforms

        row = self.df.iloc[i]
        sig, _ = wfdb.rdsamp(str(self.dir / row[self.fcol]))
        img = waveform_to_image(np.asarray(sig), self.fs)
        x = transforms.ToTensor()(img)
        x = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])(x)
        y = self.label_to_idx[row["label"]]
        return x, y


# ─────────────────────────────────────────────────────────────────────────────
# Entraînement
# ─────────────────────────────────────────────────────────────────────────────

def train(ptbxl_dir: Path, epochs: int = 15, batch_size: int = 32,
          lr: float = 3e-4, out_dir: Path = Path("ml")) -> None:
    import numpy as np
    import torch
    import timm
    from torch.utils.data import DataLoader
    from sklearn.utils.class_weight import compute_class_weight

    from ml.ecg_eval import per_class_metrics, grouped_sensitivity, safety_gate, STEMI_GROUP

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    ckpt_path = out_dir / DEFAULT_CHECKPOINT

    df = build_dataframe(ptbxl_dir)
    labels = sorted(df["label"].unique())
    label_to_idx = {l: i for i, l in enumerate(labels)}
    idx_to_label = {i: l for l, i in label_to_idx.items()}
    print(f"Classes entraînées : {labels}")
    print(f"Exclues (sans données) : {sorted(UNSUPPORTED_CODES)}")

    # Split patient via strat_fold PTB-XL (8 train / 9 val / 10 test).
    tr = df[df.strat_fold <= 8]
    va = df[df.strat_fold == 9]
    te = df[df.strat_fold == 10]

    def loader(frame, shuffle):
        ds = PTBXLDataset(frame, ptbxl_dir, label_to_idx)
        return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, num_workers=4)

    dl_tr, dl_va, dl_te = loader(tr, True), loader(va, False), loader(te, False)

    # Pondération de classes (déséquilibre — protège le rappel des classes rares).
    cw = compute_class_weight("balanced", classes=np.arange(len(labels)),
                              y=tr["label"].map(label_to_idx).values)
    weights = torch.tensor(cw, dtype=torch.float32, device=device)

    model = timm.create_model(MODEL_NAME, pretrained=True,
                              num_classes=len(labels)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    crit = torch.nn.CrossEntropyLoss(weight=weights)

    def _save_checkpoint():
        # Checkpoint riche : le predictor lit labels / model_name / input_resolution.
        torch.save({
            "state_dict": model.state_dict(),
            "labels": labels,
            "model_name": MODEL_NAME,
            "input_resolution": IMG_SIZE,
        }, ckpt_path)

    best_stemi = -1.0
    for ep in range(1, epochs + 1):
        model.train()
        for x, y in dl_tr:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            crit(model(x), y).backward()
            opt.step()

        # Validation — rappel STEMI comme critère de sélection.
        model.eval()
        yt, yp = [], []
        with torch.no_grad():
            for x, y in dl_va:
                pred = model(x.to(device)).argmax(1).cpu().numpy()
                yt += [idx_to_label[int(i)] for i in y.numpy()]
                yp += [idx_to_label[int(i)] for i in pred]
        stemi = grouped_sensitivity(yt, yp, STEMI_GROUP) or 0.0
        print(f"Epoch {ep}: rappel STEMI (val) = {stemi:.1%}")
        if stemi > best_stemi:
            best_stemi = stemi
            _save_checkpoint()

    # Évaluation finale sur le fold test + écriture des métriques pour le model card.
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    yt, yp = [], []
    with torch.no_grad():
        for x, y in dl_te:
            pred = model(x.to(device)).argmax(1).cpu().numpy()
            yt += [idx_to_label[int(i)] for i in y.numpy()]
            yp += [idx_to_label[int(i)] for i in pred]

    metrics = {
        "labels": labels,
        "per_class": per_class_metrics(yt, yp, labels),
        "stemi_recall": grouped_sensitivity(yt, yp, STEMI_GROUP),
        "gate": safety_gate(yt, yp, labels),
        "weights_sha256": _sha256(ckpt_path),
    }
    (out_dir / "ecg_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    print("\n=== GATE DE DÉPLOYABILITÉ ===")
    print(json.dumps(metrics["gate"], indent=2, ensure_ascii=False, default=str))
    print("Métriques écrites dans ml/ecg_metrics.json (à reporter dans le model card).")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test (sans PTB-XL) : vérifie le câblage du pipeline
# ─────────────────────────────────────────────────────────────────────────────

def smoke() -> None:
    """Vérifie le pipeline pur (mapping + sélection) sans torch ni dataset."""
    samples = [
        (["NORM"], "NORM"),
        (["IMI", "1AVB"], "ST_ELEVATION"),       # le plus urgent l'emporte
        (["1AVB"], "AVB1"),
        (["AFIB", "CRBBB"], "AFIB"),             # AFIB (P3) vs RBBB (P3) — 1er trouvé urgent
        (["ZZZ"], None),                         # code inconnu ignoré
    ]
    ok = True
    for codes, expected in samples:
        got = select_primary_label(codes)
        flag = "OK" if got == expected else "ÉCHEC"
        if got != expected:
            ok = False
        print(f"[{flag}] {codes} — {got} (attendu {expected})")
    print(f"\nClasses entraînables : {TRAINABLE_LABELS}")
    print(f"Exclues faute de données : {sorted(UNSUPPORTED_CODES)}")
    print("Smoke OK" if ok else "Smoke ÉCHEC")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Entraînement ECG AKIR-IAO")
    ap.add_argument("--ptbxl", type=Path, help="Dossier PTB-XL décompressé")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--smoke", action="store_true", help="Vérifier le pipeline sans données")
    args = ap.parse_args()

    if args.smoke:
        smoke()
    elif args.ptbxl:
        train(args.ptbxl, epochs=args.epochs, batch_size=args.batch_size)
    else:
        ap.error("Fournir --ptbxl /chemin/ptbxl ou --smoke")
