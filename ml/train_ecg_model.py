"""
ml/train_ecg_model.py — Entraînement du classifieur ECG image AKIR-IAO

Architecture : EfficientNet-B2 fine-tuné (timm) — 15 classes diagnostiques
Loss         : CrossEntropyLoss (single-label) avec class weights pour
               compenser le déséquilibre habituel des datasets ECG.

╔══ Format dataset attendu ══════════════════════════════════════════════════╗
║                                                                            ║
║   data/ecg/                                                                ║
║     images/                                                                ║
║       <image_id>.png  (ou .jpg)                                            ║
║       ...                                                                  ║
║     labels.csv                                                             ║
║       image_id,label                                                       ║
║       0001,STEMI_ANT                                                       ║
║       0002,NORM                                                            ║
║       ...                                                                  ║
║                                                                            ║
║   Les codes de label doivent appartenir à ml.ecg_predictor.ECG_LABELS      ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

Datasets compatibles :
    - PTB-XL (waveforms convertibles en images via matplotlib + script de plot)
    - CPSC2018 / CinC Challenge 2020
    - Datasets internes (ECG photographiés en triage)

Sortie : ml/ecg_model.pth

Usage :
    python ml/train_ecg_model.py
    python ml/train_ecg_model.py --epochs 30 --batch-size 16 --lr 1e-4
"""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
_LOG = logging.getLogger(__name__)

from ml.ecg_predictor import (
    ECG_LABELS,
    INPUT_RESOLUTION,
    IMAGENET_MEAN,
    IMAGENET_STD,
    MODEL_NAME,
)

DATA_DIR     = Path("data/ecg")
IMAGES_DIR   = DATA_DIR / "images"
LABELS_CSV   = DATA_DIR / "labels.csv"
OUTPUT_PATH  = Path("ml/ecg_model.pth")

DEFAULT_EPOCHS     = 20
DEFAULT_BATCH_SIZE = 16
DEFAULT_LR         = 1e-4
DEFAULT_WORKERS    = 2
DEFAULT_VAL_RATIO  = 0.15
SEED               = 42


def _lazy_imports():
    try:
        import torch  # noqa: F401
        import timm   # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "❌ Dépendances manquantes pour l'entraînement ECG.\n"
            "    pip install torch torchvision timm pillow pandas\n"
            f"    (vu : {exc})"
        )


# ── Dataset ─────────────────────────────────────────────────────────────────

def _build_dataset():
    """Crée le Dataset PyTorch ; vérifie présence des images + cohérence labels."""
    import pandas as pd
    from PIL import Image
    import torch
    from torch.utils.data import Dataset

    if not LABELS_CSV.exists():
        raise SystemExit(
            f"❌ {LABELS_CSV} introuvable.\n"
            "    Place ton fichier labels.csv (image_id,label) sous data/ecg/."
        )
    if not IMAGES_DIR.exists():
        raise SystemExit(
            f"❌ {IMAGES_DIR} introuvable.\n"
            "    Place les images ECG (.png/.jpg) sous data/ecg/images/."
        )

    df = pd.read_csv(LABELS_CSV, dtype={"image_id": str})
    if not {"image_id", "label"}.issubset(df.columns):
        raise SystemExit("❌ labels.csv doit contenir les colonnes image_id,label")

    unknown = set(df["label"]) - set(ECG_LABELS)
    if unknown:
        raise SystemExit(
            f"❌ Labels inconnus dans labels.csv : {sorted(unknown)}\n"
            f"    Codes autorisés : {ECG_LABELS}"
        )

    # Résolution des chemins (.png ou .jpg)
    def _resolve_path(image_id: str) -> Path | None:
        for ext in (".png", ".jpg", ".jpeg"):
            p = IMAGES_DIR / f"{image_id}{ext}"
            if p.exists():
                return p
        return None

    paths = []
    raw_labels = []
    missing = 0
    for _, row in df.iterrows():
        p = _resolve_path(str(row["image_id"]))
        if p is None:
            missing += 1
            continue
        paths.append(p)
        raw_labels.append(row["label"])

    if missing:
        _LOG.warning("%d images référencées dans labels.csv mais absentes du disque", missing)
    if not paths:
        raise SystemExit("❌ Aucune image valide trouvée — vérifier IMAGES_DIR et labels.csv")

    # Labels actifs = ceux réellement présents (préserve l'ordre canonique de ECG_LABELS)
    present = set(raw_labels)
    active_labels = [l for l in ECG_LABELS if l in present]
    label_to_idx = {l: i for i, l in enumerate(active_labels)}
    labels = [label_to_idx[l] for l in raw_labels]

    _LOG.info("Dataset : %d images sur %d classes actives", len(paths), len(active_labels))
    _LOG.info("Distribution : %s",
              {l: c for l, c in zip(active_labels, [Counter(raw_labels)[l] for l in active_labels])})
    skipped = [l for l in ECG_LABELS if l not in present]
    if skipped:
        _LOG.warning("Classes absentes du dataset (modèle aveugle dessus) : %s", skipped)

    class ECGImageDataset(Dataset):
        def __init__(self, paths, labels, transform):
            self.paths = paths
            self.labels = labels
            self.transform = transform

        def __len__(self):
            return len(self.paths)

        def __getitem__(self, idx):
            img = Image.open(self.paths[idx]).convert("RGB")
            return self.transform(img), self.labels[idx]

    return paths, labels, active_labels, ECGImageDataset


def _build_transforms():
    """Augmentations : modérées car ECG est sensible à la déformation."""
    import torchvision.transforms as T

    train_tf = T.Compose([
        T.Resize((INPUT_RESOLUTION, INPUT_RESOLUTION)),
        T.ColorJitter(brightness=0.15, contrast=0.15),  # variations photo
        T.RandomAffine(degrees=2, translate=(0.02, 0.02)),  # mini-rotation
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    val_tf = T.Compose([
        T.Resize((INPUT_RESOLUTION, INPUT_RESOLUTION)),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    return train_tf, val_tf


def _split_indices(labels: list[int], val_ratio: float, seed: int) -> tuple[list[int], list[int]]:
    """Split stratifié sur les labels."""
    import numpy as np
    rng = np.random.default_rng(seed)
    by_class: dict[int, list[int]] = {}
    for i, lbl in enumerate(labels):
        by_class.setdefault(lbl, []).append(i)
    train_idx, val_idx = [], []
    for lbl, idxs in by_class.items():
        rng.shuffle(idxs)
        n_val = max(1, int(len(idxs) * val_ratio))
        val_idx.extend(idxs[:n_val])
        train_idx.extend(idxs[n_val:])
    rng.shuffle(train_idx); rng.shuffle(val_idx)
    return train_idx, val_idx


# ── Entraînement ────────────────────────────────────────────────────────────

def train(
    epochs: int = DEFAULT_EPOCHS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    lr: float = DEFAULT_LR,
    workers: int = DEFAULT_WORKERS,
    val_ratio: float = DEFAULT_VAL_RATIO,
    output_path: Path = OUTPUT_PATH,
):
    _lazy_imports()
    import torch
    import torch.nn as nn
    import timm
    from torch.utils.data import DataLoader, Subset

    paths, labels, active_labels, DatasetCls = _build_dataset()
    n_classes = len(active_labels)
    train_tf, val_tf = _build_transforms()

    train_idx, val_idx = _split_indices(labels, val_ratio, SEED)
    _LOG.info("Split : %d train / %d val", len(train_idx), len(val_idx))

    train_ds = DatasetCls(paths, labels, train_tf)
    val_ds   = DatasetCls(paths, labels, val_tf)

    train_loader = DataLoader(
        Subset(train_ds, train_idx),
        batch_size=batch_size, shuffle=True,
        num_workers=workers, pin_memory=True,
    )
    val_loader = DataLoader(
        Subset(val_ds, val_idx),
        batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=True,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _LOG.info("Device : %s", device)

    net = timm.create_model(
        MODEL_NAME, pretrained=True, num_classes=n_classes,
    ).to(device)

    # Class weights inversement proportionnels à la fréquence (gère déséquilibre)
    counts = Counter(labels)
    weights = torch.tensor(
        [1.0 / counts.get(i, 1) for i in range(n_classes)],
        dtype=torch.float32, device=device,
    )
    weights = weights * (n_classes / weights.sum())
    _LOG.info("Class weights : %s", {active_labels[i]: f"{w:.2f}" for i, w in enumerate(weights.tolist())})

    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    for epoch in range(1, epochs + 1):
        # ── Train ──
        net.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        for imgs, lbls in train_loader:
            imgs = imgs.to(device, non_blocking=True)
            lbls = torch.tensor(lbls, device=device) if not isinstance(lbls, torch.Tensor) else lbls.to(device)

            optimizer.zero_grad()
            logits = net(imgs)
            loss = criterion(logits, lbls)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * imgs.size(0)
            train_correct += (logits.argmax(1) == lbls).sum().item()
            train_total += imgs.size(0)

        scheduler.step()

        # ── Validation ──
        net.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                imgs = imgs.to(device, non_blocking=True)
                lbls = torch.tensor(lbls, device=device) if not isinstance(lbls, torch.Tensor) else lbls.to(device)
                logits = net(imgs)
                val_correct += (logits.argmax(1) == lbls).sum().item()
                val_total += imgs.size(0)

        train_acc = train_correct / max(1, train_total)
        val_acc   = val_correct / max(1, val_total)
        _LOG.info(
            "Epoch %02d/%d — loss %.4f — train acc %.3f — val acc %.3f",
            epoch, epochs, train_loss / max(1, train_total), train_acc, val_acc,
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "state_dict":       net.state_dict(),
                "labels":           active_labels,
                "model_name":       MODEL_NAME,
                "input_resolution": INPUT_RESOLUTION,
                "val_acc":          val_acc,
            }, output_path)
            _LOG.info("  ✓ Meilleur modèle sauvegardé → %s (val acc %.3f)", output_path, val_acc)

    _LOG.info("Entraînement terminé. Meilleure val acc : %.3f", best_val_acc)
    return best_val_acc


def _cli():
    p = argparse.ArgumentParser(description="Entraînement classifieur ECG image AKIR-IAO")
    p.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    p.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p.add_argument("--lr", type=float, default=DEFAULT_LR)
    p.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    p.add_argument("--val-ratio", type=float, default=DEFAULT_VAL_RATIO)
    p.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        workers=args.workers,
        val_ratio=args.val_ratio,
        output_path=args.output,
    )
