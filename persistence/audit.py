import datetime, json, os

LOG_FILE = "audit_log.txt"

def audit_log(uid, action, operateur, details):
    timestamp = datetime.datetime.now().isoformat()
    entry = f"{timestamp} | {uid} | {action} | {operateur} | {json.dumps(details)}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except:
        pass
