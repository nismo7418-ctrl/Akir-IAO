from typing import List, Tuple

def calculer_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco=False):
    s = 0; w = []
    # FR
    if fr <= 8: s += 3; w.append(f"FR {fr}/min critique")
    elif fr <= 11: s += 1
    elif fr <= 20: pass
    elif fr <= 24: s += 2
    else: s += 3; w.append(f"FR {fr}/min — tachypnée sévère")
    # SpO2
    if bpco:
        if spo2 <= 83: s += 3; w.append(f"SpO2 {spo2}% critique (BPCO)")
        elif spo2 <= 85: s += 2
        elif spo2 <= 87: s += 1
        elif spo2 <= 92: pass
        elif spo2 <= 94: pass
        elif spo2 <= 96: s += 1; w.append(f"SpO2 {spo2}% élevée — risque hyperoxie BPCO")
        else: s += 3; w.append(f"SpO2 {spo2}% > 96% — RISQUE NARCOSE CO₂ (BPCO)")
    else:
        if spo2 <= 91: s += 3; w.append(f"SpO2 {spo2}% — hypoxémie sévère")
        elif spo2 <= 93: s += 2
        elif spo2 <= 95: s += 1
    # O2 supp
    if o2: s += 2; w.append("O₂ supplémentaire +2 pts")
    # Temp
    if temp <= 35.0: s += 3; w.append(f"T {temp}°C — hypothermie")
    elif temp <= 36.0: s += 1
    elif temp <= 38.0: pass
    elif temp <= 39.0: s += 1
    else: s += 2; w.append(f"T {temp}°C — hyperthermie")
    # PAS
    if pas <= 90: s += 3; w.append(f"PAS {pas}mmHg — état de choc")
    elif pas <= 100: s += 2
    elif pas <= 110: s += 1
    elif pas <= 219: pass
    else: s += 3; w.append(f"PAS {pas}mmHg — HTA extrême")
    # FC
    if fc <= 40: s += 3; w.append(f"FC {fc}bpm — bradycardie critique")
    elif fc <= 50: s += 1
    elif fc <= 90: pass
    elif fc <= 110: s += 1
    elif fc <= 130: s += 2
    else: s += 3; w.append(f"FC {fc}bpm — tachycardie critique")
    # GCS
    if gcs == 15: pass
    elif gcs >= 13: s += 3; w.append(f"GCS {gcs}/15")
    else: s += 3; w.append(f"GCS {gcs}/15 — altération majeure")
    return s, w

def n2_meta(s):
    if s == 0: return "Risque nul", "n2-0", 0
    elif s <= 4: return "Risque faible", "n2-1", int(s/12*100)
    elif s <= 6: return "Risque modéré", "n2-2", int(s/12*100)
    elif s <= 8: return "Risque élevé", "n2-3", int(s/12*100)
    else: return "CRITIQUE", "n2-5", min(int(s/12*100), 100)
