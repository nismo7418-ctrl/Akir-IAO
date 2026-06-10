"""
ml/ecg_predictor.py — Inférence du classifieur ECG image AKIR-IAO

Fonction publique : predict_ecg(image) → dict

Architecture :
    - Modèle : EfficientNet-B2 fine-tuné (timm) sur images ECG 12 dérivations
    - Input  : PIL.Image, np.ndarray (HWC) ou bytes (jpg/png)
    - Output : dict avec diagnostic, probabilités, priorité KTAS suggérée,
               alerte clinique, override (règles absolues)

Le module utilise des lazy imports pour torch/timm — l'app reste fonctionnelle
même si ces librairies ne sont pas installées. Dans ce cas, predict_ecg
retourne une erreur explicite invitant à installer les dépendances.

Format attendu pour les poids : ml/ecg_model.pth
    - state_dict d'un timm.create_model(MODEL_NAME, num_classes=15)
    - ou dict avec clé "state_dict"

Voir ml/train_ecg_model.py pour générer ces poids depuis un dataset
d'images ECG labellisées.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import numpy as np

_LOG = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent / "ecg_model.pth"

# ── Configuration modèle ──────────────────────────────────────────────────────
# MobileNetV3-Small à 160 px : optimisé pour CPU (≈ 2,5 M params, ~1 min/époque
# sur 2 cœurs avec 2 200 images), tient dans une fenêtre Bash de 10 min même
# pour 5-7 époques. Reste un bon classifieur ECG image sur 8 classes.
# Le checkpoint mémorise son propre model_name : on peut donc l'entraîner en
# EfficientNet-B2 sur GPU et l'inférer ici sans changer le code, grâce à
# _load_model().
MODEL_NAME       = "mobilenetv3_small_100"
INPUT_RESOLUTION = 160
IMAGENET_MEAN    = (0.485, 0.456, 0.406)
IMAGENET_STD     = (0.229, 0.224, 0.225)

# ── 15 labels diagnostiques ───────────────────────────────────────────────────
ECG_LABELS: list[str] = [
    "NORM",
    "STEMI_ANT",
    "STEMI_INF",
    "STEMI_LAT",
    "NSTEMI",
    "AF",
    "AFL",
    "VT",
    "VF",
    "AVB1",
    "AVB2",
    "AVB3",
    "LBBB",
    "RBBB",
    "HYPERK",
]

ECG_LABEL_FR: dict[str, str] = {
    "NORM":      "Rythme sinusal normal",
    "STEMI_ANT": "STEMI antérieur",
    "STEMI_INF": "STEMI inférieur",
    "STEMI_LAT": "STEMI latéral",
    "NSTEMI":    "NSTEMI / ischémie sous-épicardique",
    "AF":        "Fibrillation atriale",
    "AFL":       "Flutter atrial",
    "VT":        "Tachycardie ventriculaire",
    "VF":        "Fibrillation ventriculaire",
    "AVB1":      "BAV 1ᵉʳ degré",
    "AVB2":      "BAV 2ᵉ degré",
    "AVB3":      "BAV complet (3ᵉ degré)",
    "LBBB":      "Bloc de branche gauche",
    "RBBB":      "Bloc de branche droit",
    "HYPERK":    "Hyperkaliémie (signes ECG)",
}

# ── Priorité KTAS suggérée par diagnostic ────────────────────────────────────
ECG_DEFAULT_PRIORITY: dict[str, int] = {
    "NORM":      5,
    "STEMI_ANT": 1,
    "STEMI_INF": 1,
    "STEMI_LAT": 1,
    "NSTEMI":    2,
    "AF":        3,
    "AFL":       3,
    "VT":        1,
    "VF":        1,
    "AVB1":      4,
    "AVB2":      2,
    "AVB3":      1,
    "LBBB":      2,
    "RBBB":      4,
    "HYPERK":    1,
}

# ── Couleur par priorité (cohérent avec triage_predictor) ────────────────────
_PRIO_COLOR: dict[int, str] = {
    1: "#EF4444",
    2: "#F97316",
    3: "#EAB308",
    4: "#22C55E",
    5: "#64748B",
}

# ── Alertes cliniques associées ──────────────────────────────────────────────
ECG_CLINICAL_ALERT: dict[str, str | None] = {
    "NORM":      None,
    "STEMI_ANT": "STEMI antérieur — appel cardio + USIC immédiat — angioplastie < 90 min",
    "STEMI_INF": "STEMI inférieur — explorer V4R (VD) — risque BAV / hypotension à la nitro",
    "STEMI_LAT": "STEMI latéral — appel cardio + USIC immédiat",
    "NSTEMI":    "Ischémie suspectée — Troponines T0/H3 + appel cardio < 1 h",
    "AF":        "Fibrillation atriale — fréquence à contrôler + CHA₂DS₂-VASc pour anticoagulation",
    "AFL":       "Flutter atrial — contrôle de fréquence + évaluer anticoagulation",
    "VT":        "TV soutenue — instable : CEE 100-200 J — stable : amiodarone 300 mg IVL",
    "VF":        "FV — Choc 200 J biphasique immédiat — RCP 30:2 — appel REA",
    "AVB1":      "BAV 1ᵉʳ — surveillance, contexte clinique (digitaliques, BB, IDM)",
    "AVB2":      "BAV 2ᵉ — scope continu + appel cardio — préparer pacing externe",
    "AVB3":      "BAV complet — atropine 0,5 mg IV + pacing externe — USIC immédiat",
    "LBBB":      "BBG — exclure SCA (nouveau BBG = STEMI équivalent jusqu'à preuve du contraire)",
    "RBBB":      "BBD — généralement bénin — si récent, exclure embolie pulmonaire",
    "HYPERK":    "Hyperkaliémie ECG — Gluconate Ca 10 % 10 mL IV + insuline-glucose — K+ urgent",
}

# ── Cache du modèle ──────────────────────────────────────────────────────────
_model: Any = None
_device: Any = None
_torch_mod: Any = None


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


_active_labels: list[str] | None = None


def _load_model():
    """Charge le modèle EfficientNet-B2 fine-tuné. Lève si poids absents.

    Format de checkpoint attendu :
        {
            "state_dict": {...},      # poids du modèle
            "labels":     [...],      # sous-ensemble de ECG_LABELS effectivement appris
            "model_name": "efficientnet_b2",
            "input_resolution": 260,
        }
    Si l'ancien format (state_dict pur) est trouvé, on retombe sur les 15 labels.
    """
    global _model, _device, _active_labels
    if _model is not None:
        return _model, _device

    torch = _lazy_torch()
    import timm

    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle ECG introuvable : {_MODEL_PATH}\n"
            "Entraîne le modèle d'abord : python ml/train_ecg_model.py"
        )

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(_MODEL_PATH, map_location="cpu")

    if isinstance(ckpt, dict) and "labels" in ckpt:
        _active_labels = list(ckpt["labels"])
        state = ckpt["state_dict"]
        model_name = ckpt.get("model_name", MODEL_NAME)
    elif isinstance(ckpt, dict) and "state_dict" in ckpt:
        _active_labels = list(ECG_LABELS)
        state = ckpt["state_dict"]
        model_name = ckpt.get("model_name", MODEL_NAME)
    else:
        _active_labels = list(ECG_LABELS)
        state = ckpt
        model_name = MODEL_NAME

    state = {k.replace("module.", ""): v for k, v in state.items()}
    net = timm.create_model(model_name, pretrained=False, num_classes=len(_active_labels))
    net.load_state_dict(state, strict=True)
    _model = net.to(_device).eval()
    _LOG.info("Modèle ECG chargé depuis %s (device=%s, %d classes : %s)",
              _MODEL_PATH, _device, len(_active_labels), _active_labels)
    return _model, _device


def get_active_labels() -> list[str]:
    """Retourne la liste des labels que le modèle a effectivement appris.
    Lève si le modèle n'est pas chargé. Sinon retourne le subset de ECG_LABELS.
    """
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
    """Image PIL → tensor torch [1,3,H,W] normalisé ImageNet."""
    torch = _lazy_torch()
    img = pil_img.resize((INPUT_RESOLUTION, INPUT_RESOLUTION))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - np.array(IMAGENET_MEAN, dtype=np.float32)) / np.array(IMAGENET_STD, dtype=np.float32)
    arr = arr.transpose(2, 0, 1)
    return torch.from_numpy(arr).unsqueeze(0).contiguous()


def predict_ecg(image: Any, *, top_k: int = 5) -> dict:
    """
    Classifie une image ECG 12 dérivations.

    Args:
        image: PIL.Image, bytes (jpg/png), chemin, ou np.ndarray
        top_k: nombre de labels à retourner triés par probabilité

    Returns:
        dict avec clés :
            top_label, top_label_fr, top_proba
            probabilites : dict[label_code, float]
            top_k        : list[(label_code, label_fr, proba)]
            priorite     : int 1-5 (KTAS suggérée)
            couleur      : code hex
            alerte_clinique : str | None
            override     : str | None — règle de sécurité appliquée
            features_input : dict (resolution, model)
            erreur       : str | None
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

    active = _active_labels or ECG_LABELS
    # Labels couverts par le modèle → probabilité réelle ; les autres → 0
    prob_map = {lbl: 0.0 for lbl in ECG_LABELS}
    for i, lbl in enumerate(active):
        prob_map[lbl] = float(probs[i])
    ranked = sorted(prob_map.items(), key=lambda kv: -kv[1])
    top_label, top_proba = ranked[0]

    priorite_ml = ECG_DEFAULT_PRIORITY.get(top_label, 3)
    priorite, override = _apply_clinical_overrides(top_label, top_proba, prob_map, priorite_ml)
    alerte = ECG_CLINICAL_ALERT.get(top_label)

    return {
        "top_label":       top_label,
        "top_label_fr":    ECG_LABEL_FR[top_label],
        "top_proba":       top_proba,
        "probabilites":    prob_map,
        "top_k": [
            (lbl, ECG_LABEL_FR[lbl], float(p))
            for lbl, p in ranked[: max(1, top_k)]
        ],
        "priorite":        priorite,
        "priorite_ml":     priorite_ml,
        "couleur":         _PRIO_COLOR.get(priorite, "#64748B"),
        "alerte_clinique": alerte,
        "override":        override,
        "features_input": {
            "model":      MODEL_NAME,
            "resolution": INPUT_RESOLUTION,
            "n_classes":  len(ECG_LABELS),
        },
        "erreur": None,
    }


# ── Garde-fous cliniques absolus ─────────────────────────────────────────────

def _apply_clinical_overrides(
    top_label: str, top_proba: float, prob_map: dict[str, float], prio_ml: int,
) -> tuple[int, str | None]:
    """
    Applique les règles cliniques absolues sur la sortie du modèle.
    Le but : ne jamais sous-évaluer une urgence vitale même si la probabilité
    n'est pas écrasante, dès qu'un signe critique est détecté avec une
    confiance raisonnable.
    """
    # Règle 1 — Tout STEMI ou TV/FV détecté avec proba ≥ 0,30 → P1 immédiat
    critiques = {"STEMI_ANT", "STEMI_INF", "STEMI_LAT", "VT", "VF", "AVB3", "HYPERK"}
    for lbl in critiques:
        if prob_map.get(lbl, 0.0) >= 0.30 and ECG_DEFAULT_PRIORITY[lbl] == 1:
            if prio_ml > 1:
                return 1, f"Signe critique détecté : {ECG_LABEL_FR[lbl]} (p={prob_map[lbl]:.0%})"
            return 1, None

    # Règle 2 — Confiance faible (< 0,40) sur un diagnostic non-NORM → minimum P3
    if top_label != "NORM" and top_proba < 0.40 and prio_ml >= 4:
        return 3, f"Confiance ML insuffisante ({top_proba:.0%}) — surveillance médicale"

    return prio_ml, None


def _error_result(msg: str) -> dict:
    return {
        "top_label":       None,
        "top_label_fr":    "—",
        "top_proba":       0.0,
        "probabilites":    {},
        "top_k":           [],
        "priorite":        None,
        "priorite_ml":     None,
        "couleur":         "#64748B",
        "alerte_clinique": None,
        "override":        None,
        "features_input":  {},
        "erreur":          msg,
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
        res = predict_ecg(fake)
        print(json.dumps({k: v for k, v in res.items() if k != "probabilites"}, indent=2, default=str))
