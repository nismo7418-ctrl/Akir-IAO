import hashlib, json, os
from datetime import datetime
from typing import Optional, Tuple

ALF = "akir_audit.log"
EF  = "akir_errors.log"
_HASH_GENESIS = "0" * 64

def _hash_entree(contenu: str, hash_precedent: str) -> str:
    """Génère un hash SHA-256 combinant le contenu actuel et le hash précédent."""
    return hashlib.sha256(f"{contenu}|{hash_precedent}".encode()).hexdigest()

def audit_log(uid: str, action: str, operateur: str, details: Optional[dict] = None) -> None:
    """Enregistre une action dans le journal d'audit avec chaînage de hash."""
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        det_str = json.dumps(details or {}, ensure_ascii=False, separators=(",",":"))
        contenu = f"{ts}|{uid}|{action}|{operateur}|{det_str}"
        
        hash_prev = _HASH_GENESIS
        if os.path.exists(ALF):
            with open(ALF, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            if lines:
                # On récupère le hash à la fin de la dernière ligne
                hash_prev = lines[-1].rsplit("|", 1)[-1]
        
        hash_actuel = _hash_entree(contenu, hash_prev)
        
        with open(ALF, "a", encoding="utf-8") as f:
            f.write(f"{contenu}|{hash_actuel}\n")
            
    except Exception as e:
        try:
            with open(EF, "a", encoding="utf-8") as fe:
                fe.write(f"[{datetime.now().isoformat()}] AUDIT_ERROR: {e}\n")
        except:
            pass

def audit_verifier_integrite() -> Tuple[bool, str]:
    """Vérifie que la chaîne de hash du journal n'a pas été altérée."""
    if not os.path.exists(ALF):
        return True, "Journal d'audit absent (aucun enregistrement)"
    
    try:
        with open(ALF, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        if not lines:
            return True, "Journal d'audit vide"
            
        hash_prev = _HASH_GENESIS
        for i, ligne in enumerate(lines, 1):
            parts = ligne.rsplit("|", 1)
            if len(parts) != 2:
                return False, f"Ligne {i} mal formée (structure corrompue)"
            
            contenu, hash_stocke = parts[0], parts[1]
            hash_calcule = _hash_entree(contenu, hash_prev)
            
            if hash_calcule != hash_stocke:
                return False, f"Intégrité violée à la ligne {i} (altération détectée)"
            
            hash_prev = hash_stocke
            
        return True, f"Journal intègre ({len(lines)} entrées vérifiées)"
    except Exception as e:
        return False, f"Erreur lors de la vérification : {str(e)}"
