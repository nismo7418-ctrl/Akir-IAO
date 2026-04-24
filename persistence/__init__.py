import os
import datetime
import json

def save_triage_record(record_data: dict, folder: str = "data/records"):
    """
    Sauvegarde les données de triage dans un fichier JSON local.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/triage_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=4)
        return filename
    except Exception as e:
        print(f"Erreur de sauvegarde : {e}")
        return None
