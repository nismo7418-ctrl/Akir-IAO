import json, os, uuid
from datetime import datetime
from config import REGISTRE_CAP
from persistence.audit import audit_log

RF = "akir_reg.json"

def _load():
    if os.path.exists(RF):
        try:
            with open(RF, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def _save(data):
    try:
        with open(RF, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

def enregistrer_patient(d: dict) -> str:
    uid = str(uuid.uuid4())[:8].upper()
    reg = _load()
    reg.insert(0, {
        "uid": uid,
        "heure": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "motif": d.get("motif",""),
        "cat": d.get("cat",""),
        "niv": d.get("niv",""),
        "n2": d.get("n2",0),
        "fc": d.get("fc"),
        "pas": d.get("pas"),
        "spo2": d.get("spo2"),
        "fr": d.get("fr"),
        "temp": d.get("temp"),
        "gcs": d.get("gcs"),
        "op": d.get("op","IAO"),
    })
    _save(reg[:REGISTRE_CAP])
    audit_log(uid, "TRIAGE", d.get("op","IAO"), {"motif":d.get("motif",""),"niv":d.get("niv",""),"n2":d.get("n2",0)})
    return uid

def charger_registre():
    return _load()
