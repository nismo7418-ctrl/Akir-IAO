# persistence/audit.py — Journal d'audit anonymisé RGPD — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# RGPD : Aucun nom/prénom — Identifiant de session uniquement

import json, os
from datetime import datetime

AUDIT_FILE = "akir_audit.log"


def audit_log(uid: str, action: str, operateur: str, details: dict = None) -> None:
    """Enregistre un événement dans le journal d'audit (anonymisé)."""
    try:
        entry = {
            "ts": datetime.now().isoformat(),
            "uid": uid,
            "action": action,
            "op": operateur,
            "details": details or {},
        }
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Ne jamais faire planter l'app pour un log


def audit_verifier_integrite() -> dict:
    """Vérifie l'intégrité du journal d'audit. Retourne les statistiques."""
    try:
        if not os.path.exists(AUDIT_FILE):
            return {"ok": True, "entrees": 0, "message": "Journal vide — prêt"}
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            lignes = [l.strip() for l in f if l.strip()]
        valides = 0
        for l in lignes:
            try:
                json.loads(l)
                valides += 1
            except Exception:
                pass
        return {
            "ok": valides == len(lignes),
            "entrees": len(lignes),
            "valides": valides,
            "message": f"{valides}/{len(lignes)} entrées valides",
        }
    except Exception as e:
        return {"ok": False, "entrees": 0, "message": str(e)}
