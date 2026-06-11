"""
ml/ecg_predictor.py — Inférence du classifieur ECG image — AKIR-IAO v21
Développeur : Ismail Ibn-Daifa — Hainaut, Belgique

Fonction publique : predict_ecg(image, *, age_years=None) → dict

Architecture (taxonomie honnête, cf. clinical/ecg_labels.py) :
    - Modèle : CNN timm fine-tuné sur images ECG 12 dérivations (PTB-XL),
      classes canoniques honnêtes (NORM, ST_ELEVATION, ISCHEMIA_NONST, …).
    - Input  : PIL.Image, np.ndarray (HWC) ou bytes (jpg/png).
    - Output : dict { probabilities, verdict, top_label, top_proba, … }.

AUCUNE logique de priorité/criticité ici : elle est déléguée à
clinical/ecg_garde_fous.apply_ecg_garde_fous (fonction pure, testable sans
torch). Le predictor se contente de produire les probabilités et de demander
le verdict aux garde-fous.

Le module utilise des lazy imports pour torch/timm — l'app reste fonctionnelle
même si ces librairies ne sont pas installées. Dans ce cas, predict_ecg
retourne une erreur explicite invitant à installer les dépendances.

Format attendu pour le checkpoint : ml/ecg_model.pth
    {
        "state_dict":       {...},               # poids du modèle timm
        "labels":           [...],               # codes canoniques appris
        "model_name":       "efficientnet_b2",   # architecture timm
        "input_resolution": 260,                 # côté de l'image d'entrée
    }
Voir ml/train_ecg_model.py pour générer ce checkpoint depuis PTB-XL.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np

from clinical.ecg_labels import LABELS, UNSUPPORTED_CODES, display_name
from clinical.ecg_garde_fous import apply_ecg_garde_fous

_LOG = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent / "ecg_model.pth"

# ── Valeurs par défaut (si le checkpoint ne les précise pas) ──────────────────
DEFAULT_MODEL_NAME       = "efficientnet_b2"
DEFAULT_INPUT_RESOLUTION = 260
IMAGENET_MEAN            = (0.485, 0.456, 0.406)
IMAGENET_STD             = (0.229, 0.224, 0.225)

# Labels honnêtes par défaut = taxonomie MOINS les classes sans données et UNKNOWN.
DEFAULT_LABELS: list[str] = [c for c in LABELS if c not in UNSUPPORTED_CODES
                             and c != "UNKNOWN"]

# ── Cache du modèle ───────────────────────────────────────────────────────────
_model: Any = None
_device: Any = None
_torch_mod: Any = None
_active_labels: Optional[list[str]] = None
_model_name: str = DEFAULT_MODEL_NAME
_input_resolution: int = DEFAULT_INPUT_RESOLUTION


def _lazy_torch():
    """Import paresseux de torch/timm. Lève RuntimeError si absents."""
    global _torch_mod
    if _torch_mod is not None:
        return _torch_mod
    try:
        import torch
        import timm  # noqa: F401  (importé pour valider la dispo)
    except ImportError as exc:
        raise RuntimeError(
            "Dépendances ECG manquantes : installe `torch` et `timm` "
            "(pip install torch timm pillow). Vu : " + str(exc)
        ) from exc
    _torch_mod = torch
    return torch


def _load_model():
    """Charge le modèle ECG fine-tuné. Lève si les poids sont absents."""
    global _model, _device, _active_labels, _model_name, _input_resolution
    if _model is not None:
        return _model, _device

    torch = _lazy_torch()
    import timm

    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle ECG introuvable : {_MODEL_PATH}\n"
            "Entraîne le modèle d'abord : python ml/train_ecg_model.py --ptbxl ..."
        )

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(_MODEL_PATH, map_location="cpu")

    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        state = ckpt["state_dict"]
        _active_labels = list(ckpt.get("labels", DEFAULT_LABELS))
        _model_name = ckpt.get("model_name", DEFAULT_MODEL_NAME)
        _input_resolution = int(ckpt.get("input_resolution", DEFAULT_INPUT_RESOLUTION))
    else:
        # Ancien format : state_dict pur, pas de métadonnées.
        state = ckpt
        _active_labels = list(DEFAULT_LABELS)
        _model_name = DEFAULT_MODEL_NAME
        _input_resolution = DEFAULT_INPUT_RESOLUTION

    state = {k.replace("module.", ""): v for k, v in state.items()}
    net = timm.create_model(_model_name, pretrained=False, num_classes=len(_active_labels))
    net.load_state_dict(state, strict=True)
    _model = net.to(_device).eval()
    _LOG.info("Modèle ECG chargé depuis %s (device=%s, %d classes : %s)",
              _MODEL_PATH, _device, len(_active_labels), _active_labels)
    return _model, _device


def get_active_labels() -> list[str]:
    """Liste des codes canoniques que le modèle a effectivement appris."""
    if _active_labels is None:
        _load_model()
    return list(_active_labels) if _active_labels else []


def _to_pil(image: Any):
    """Normalise l'entrée en PIL.Image RGB."""
    from PIL import Image
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(image)).convert("RGB")
    if isinstance(image, (str, Path)):
        return Image.open(str(image)).convert("RGB")
    if isinstance(image, np.ndarray):
        arr = image
        if arr.dtype != np.uint8:
            arr = np.clip(arr * 255 if arr.max() <= 1.0 else arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr).convert("RGB")
    raise TypeError(f"Type d'image non supporté : {type(image).__name__}")


def _preprocess(pil_img) -> Any:
    """Image PIL — tensor torch [1,3,H,W] normalisé ImageNet."""
    torch = _lazy_torch()
    res = _input_resolution
    img = pil_img.resize((res, res))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - np.array(IMAGENET_MEAN, dtype=np.float32)) / np.array(IMAGENET_STD, dtype=np.float32)
    arr = arr.transpose(2, 0, 1)
    return torch.from_numpy(arr).unsqueeze(0).contiguous()


def predict_ecg(image: Any, *, age_years: Optional[float] = None) -> dict:
    """
    Classifie une image ECG 12 dérivations puis applique les garde-fous cliniques.

    Args:
        image:     PIL.Image, bytes (jpg/png), chemin, ou np.ndarray
        age_years: âge du patient (déclenche l'abstention pédiatrique R0)

    Returns:
        dict avec clés :
            probabilities : dict[code_canonique, float]
            verdict       : dict des garde-fous (priorite, override,
                            critical_flags, abstain, data_support, …) | None
            top_label     : str  | code canonique le plus probable
            top_proba     : float
            features_input: dict (model, resolution, n_classes)
            erreur        : str | None
    """
    try:
        torch = _lazy_torch()
        net, device = _load_model()
        pil = _to_pil(image)
    except (RuntimeError, FileNotFoundError, TypeError) as exc:
        return _error_result(str(exc))

    try:
        tensor = _preprocess(pil).to(device)
        with torch.no_grad():
            logits = net(tensor)
            probs  = torch.softmax(logits, dim=1)[0].cpu().numpy()
    except Exception as exc:  # noqa: BLE001  — l'inférence peut planter sur image corrompue
        return _error_result(f"Inférence ECG impossible : {exc}")

    active = _active_labels or DEFAULT_LABELS
    prob_map = {lbl: float(probs[i]) for i, lbl in enumerate(active)}

    verdict = apply_ecg_garde_fous(prob_map, age_years=age_years)

    top_label = max(prob_map, key=prob_map.get)
    top_proba = prob_map[top_label]

    return {
        "probabilities": prob_map,
        "verdict":       verdict,
        "top_label":     top_label,
        "top_label_fr":  display_name(top_label),
        "top_proba":     top_proba,
        "features_input": {
            "model":      _model_name,
            "resolution": _input_resolution,
            "n_classes":  len(active),
        },
        "erreur": None,
    }


def _error_result(msg: str) -> dict:
    return {
        "probabilities": {},
        "verdict":       None,
        "top_label":     None,
        "top_label_fr":  "—",
        "top_proba":     0.0,
        "features_input": {},
        "erreur":        msg,
    }


def model_available() -> bool:
    """True si torch/timm sont installés ET le fichier de poids existe."""
    try:
        _lazy_torch()
    except RuntimeError:
        return False
    return _MODEL_PATH.exists()


if __name__ == "__main__":
    import json
    if not model_available():
        print("Modèle ECG non disponible — entraînement requis (ml/train_ecg_model.py)")
    else:
        # Smoke test : image aléatoire
        from PIL import Image
        rng = np.random.default_rng(0)
        fake = Image.fromarray(rng.integers(0, 255, (260, 260, 3), dtype=np.uint8))
        res = predict_ecg(fake, age_years=50)
        print(json.dumps({k: v for k, v in res.items() if k != "probabilities"},
                         indent=2, ensure_ascii=False, default=str))
