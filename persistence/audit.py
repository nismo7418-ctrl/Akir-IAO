import hashlib
# persistence/audit.py — Journal d'audit anonymisé RGPD — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# RGPD : Aucun nom/prénom — Identifiant de session uniquement

import json, os
from datetime import datetime

AUDIT_FILE = "akir_audit.log"


_LAST_HASH_FILE = "akir_audit_last_hash"

def _read_last_hash() -> str:
    try:
        if os.path.exists(_LAST_HASH_FILE):
            return open(_LAST_HASH_FILE).read().strip()
    except Exception:
        pass
    return "0" * 64

def _write_last_hash(h: str) -> None:
    try:
        open(_LAST_HASH_FILE, 'w').write(h)
    except Exception:
        pass

def audit_log(uid: str, action: str, operateur: str, details: dict = None) -> None:
    """Enregistre un événement dans le journal d'audit avec chaîne de hachage SHA-256.
    Chaque entrée est liée à la précédente — toute altération est détectable.
    """
    try:
        entry = {
            "ts": datetime.now().isoformat(),
            "uid": uid,
            "action": action,
            "op": operateur,
            "details": details or {},
        }
        contenu = json.dumps(entry, ensure_ascii=False)
        prev_hash = _read_last_hash()
        new_hash  = hashlib.sha256((contenu + prev_hash).encode()).hexdigest()
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(contenu + "|" + new_hash + "\n")
        _write_last_hash(new_hash)
    except Exception:
        pass


def audit_verifier_integrite() -> dict:
    """Vérifie la chaîne de hachage SHA-256 du journal d'audit.
    Détecte toute altération rétroactive des entrées.
    """
    try:
        if not os.path.exists(AUDIT_FILE):
            return {"ok": True, "entrees": 0, "message": "Journal vide — prêt"}
        prev_hash = "0" * 64
        valides   = 0
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            for i, ligne in enumerate(f, 1):
                ligne = ligne.strip()
                if not ligne:
                    continue
                if "|" not in ligne:
                    return {"ok": False, "entrees": i, "message": f"Ligne {i} sans hash"}
                contenu, hash_stocke = ligne.rsplit("|", 1)
                hash_calc = hashlib.sha256((contenu + prev_hash).encode()).hexdigest()
                if hash_calc != hash_stocke:
                    return {"ok": False, "entrees": i,
                            "message": f"Intégrité violée à la ligne {i} — journal altéré"}
                prev_hash = hash_stocke
                valides  += 1
        return {"ok": True, "entrees": valides, "valides": valides,
                "message": f"{valides} entrées — chaîne SHA-256 intacte"}
    except Exception as e:
        return {"ok": False, "entrees": 0, "message": str(e)}
