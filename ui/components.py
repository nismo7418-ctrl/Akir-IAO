import streamlit as st
from datetime import datetime
from config import LABELS, SECTEURS, DELAIS, TCSS, HBCSS, GLYC
from clinical.vitaux import mgdl_mmol

def H(s): st.markdown(s, unsafe_allow_html=True)
def SEC(t): H(f'<div class="sec">{t}</div>')
def AL(msg, typ="danger"):
    ico = {"danger":"⚠️","warning":"⚠️","success":"✅","info":"ℹ️"}.get(typ,"")
    H(f'<div class="al {typ}"><span class="al-ico">{ico}</span><span>{msg}</span></div>')
def CARD(title="", icon=""):
    if title:
        H(f'<div class="card"><div class="card-title">{icon} {title}</div>')
    else:
        H('<div class="card">')
def CARD_END(): H('</div>')
def PURPURA(det):
    if det and det.get("purpura"):
        H('<div class="purp"><div class="purp-title">PURPURA FULMINANS — TRI 1 IMMÉDIAT</div>'
          '<div class="purp-body">Ceftriaxone 2g IV — NE PAS ATTENDRE LE BILAN.</div></div>')
def N2_BANNER(n2):
    if n2>=9:
        H(f'<div class="purp" style="background:linear-gradient(135deg,#1A0A2E,#2D1B69);border-color:#7C3AED;">'
          f'<div class="purp-title" style="color:#E879F9;">NEWS2 {n2} — ENGAGEMENT VITAL</div></div>')
    elif n2>=7: AL(f"NEWS2 {n2}>=7 — Appel médical immédiat","danger")
    elif n2>=5: AL(f"NEWS2 {n2}>=5 — Réévaluation toutes les 30 min","warning")
def GAUGE(n2, bpco=False):
    from clinical.news2 import n2_meta
    lbl,css,pct = n2_meta(n2)
    note = '<div style="font-size:.62rem;opacity:.75;margin-top:4px;">Échelle 2 BPCO — Cible SpO2 88-92%</div>' if bpco else ""
    H(f'<div class="n2-dash {css}">'
      f'<div style="font-size:.62rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;opacity:.7;">SCORE NEWS2</div>'
      f'<div class="n2-big">{n2}</div><div class="n2-lbl">{lbl}</div>{note}'
      f'<div class="n2-bar-wrap"><div class="n2-bar" style="width:{max(pct,4)}%;"></div></div>'
      f'</div>')
def VITAUX(fc,pas,spo2,fr,temp,gcs,bpco=False):
    fc_n = "crit" if fc>=150 or fc<=40 else ("warn" if fc>=120 or fc<=50 else "")
    pas_n = "crit" if pas<=90 else ("warn" if pas<=100 else "")
    sp_warn=88 if bpco else 94; sp_crit=85 if bpco else 90
    sp_n = "crit" if spo2<=sp_crit else ("warn" if spo2<=sp_warn else "")
    fr_n = "crit" if fr>=30 else ("warn" if fr>=22 else "")
    t_n = "crit" if temp>=40 or temp<=35 else ("warn" if temp>=38.5 or temp<=36 else "")
    g_n = "crit" if gcs<=8 else ("warn" if gcs<=13 else "")
    H(f'<div class="vit-wrap">'
      f'<div class="vit {fc_n}"><div class="vit-k">FC</div><div class="vit-v">{fc}</div><div class="vit-u">bpm</div></div>'
      f'<div class="vit {pas_n}"><div class="vit-k">PAS</div><div class="vit-v">{pas}</div><div class="vit-u">mmHg</div></div>'
      f'<div class="vit {sp_n}"><div class="vit-k">SpO2{"*" if bpco else ""}</div><div class="vit-v">{spo2}</div><div class="vit-u">%</div></div>'
      f'<div class="vit {fr_n}"><div class="vit-k">FR</div><div class="vit-v">{fr}</div><div class="vit-u">/min</div></div>'
      f'<div class="vit {t_n}"><div class="vit-k">Temp</div><div class="vit-v">{temp}</div><div class="vit-u">°C</div></div>'
      f'<div class="vit {g_n}"><div class="vit-k">GCS</div><div class="vit-v">{gcs}</div><div class="vit-u">/15</div></div>'
      f'</div>')
def TRI_CARD_INLINE(niv,just,n2):
    css = TCSS.get(niv,"tri-5"); lbl = LABELS.get(niv,niv); sec = SECTEURS.get(niv,""); d = DELAIS.get(niv,"?")
    H(f'<div class="{css}"><div class="tri-card"><div class="tri-lbl">{lbl}</div>'
      f'<div class="tri-detail">{just}</div><div class="tri-sector">{sec}</div>'
      f'<div class="tri-chips"><span class="tri-chip">Délai max : {d} min</span>'
      f'<span class="tri-chip">NEWS2 : {n2}</span></div></div></div>')
def TRI_BANNER_FIXED(niv,just,n2):
    css = TCSS.get(niv,"tri-5"); lbl = LABELS.get(niv,niv); sec = SECTEURS.get(niv,""); d = DELAIS.get(niv,"?")
    H(f'<div class="tri-banner-wrap"><div class="tri-banner {css}">'
      f'<div><div class="tri-niv">{lbl}</div><div class="tri-sec">{sec}</div>'
      f'<div class="tri-just">{just}</div></div>'
      f'<span class="tri-delai">Max {d} min | N2={n2}</span></div></div>')
def RX(nom,dose,details,ref,palier="2",alertes=None):
    if alertes:
        for a in alertes: AL(a,"danger")
    dt = "<br>".join([x for x in details if x])
    H(f'<div class="rx"><div class="rx-name">{nom}</div><div class="rx-dose">{dose}</div>'
      f'<div class="rx-detail">{dt}</div><div class="rx-ref">{ref}</div></div>')
def RX_LOCK(msg="Donnée manquante — Protocole désactivé"):
    H(f'<div class="rx-lock"><strong>Protocole désactivé</strong><br>{msg}</div>')
def GLYC_WIDGET(key, label="Glycémie capillaire (mg/dl)", req=False):
    v = st.number_input(label, 0, 1500, 0, 5, key=key)
    if v == 0:
        if req: AL("Glycémie non saisie — saisir la valeur pour activer les protocoles","warning")
        return None
    mm = mgdl_mmol(v)
    st.caption(f"→ {mm} mmol/l")
    if v < GLYC["hs"]: AL(f"HYPOGLYCÉMIE SÉVÈRE {v}mg/dl ({mm}mmol/l) — Glucose 30% IV immédiat","danger")
    elif v < GLYC["hm"]: AL(f"Hypoglycémie modérée {v}mg/dl","warning")
    return float(v)
def BPCO_WIDGET(pfx):
    bp = st.checkbox("Patient BPCO connu ?", key=f"{pfx}_bp")
    if bp: AL("BPCO — Cible SpO2 88-92% — Échelle 2 activée","warning")
    pa = st.radio("S'exprime en phrases complètes ?", [True, False],
                  format_func=lambda x: "Oui — phrases complètes" if x else "Non — mots isolés",
                  horizontal=True, key=f"{pfx}_pa")
    return bp, pa
def SI_WIDGET(fc, pas):
    from clinical.vitaux import si
    sh = si(fc, pas)
    css = "si-c" if sh>=1.0 else ("si-w" if sh>=0.8 else "si-ok")
    lbl = "CHOC PROBABLE" if sh>=1.0 else ("Surveillance rapprochée" if sh>=0.8 else "Normal")
    H(f'<div class="si-box"><div class="si-l">Shock Index</div><div class="si-v {css}">{sh}</div><div class="si-l">{lbl}</div></div>')
def SBAR_RENDER(s):
    H(f'<div class="sbar"><div class="sbar-hdr"><div class="sbar-hdr-title">RAPPORT SBAR</div></div>'
      f'<div class="sbar-sec"><div class="sbar-sec-head"><div class="sbar-letter">S</div>'
      f'<div class="sbar-sec-title">Situation</div></div>'
      f'<div class="sbar-body">Patient de {s["age"]} ans | Motif : <strong>{s["motif"]}</strong><br>'
      f'Niveau : <strong>{s["niv"]}</strong> | Secteur : {s["sec"]} | Délai max : {s["delai"]} min</div></div>'
      f'<div class="sbar-sec"><div class="sbar-sec-head"><div class="sbar-letter">B</div>'
      f'<div class="sbar-sec-title">Background</div></div>'
      f'<div class="sbar-body">ATCD : {s["atcd"]}<br>Allergies : {s["alg"]}<br>O2 : {s["o2"]} | Glycémie : {s["gl"]}</div></div>'
      f'<div class="sbar-sec"><div class="sbar-sec-head"><div class="sbar-letter">A</div>'
      f'<div class="sbar-sec-title">Assessment</div></div><div class="sbar-body">{s["just"]}</div></div>'
      f'<div class="sbar-sec"><div class="sbar-sec-head"><div class="sbar-letter">R</div>'
      f'<div class="sbar-sec-title">Recommendation</div></div>'
      f'<div class="sbar-body">Orientation : <strong>{s["sec"]}</strong><br>Délai maximum : {s["delai"]} min</div></div>'
      f'<div class="sbar-ftr">Document d\'aide à la décision — AKIR-IAO v18.0</div></div>')
def DISC():
    H('<div class="disc">AKIR-IAO est un outil d\'aide à la décision clinique. '
      'Doses conformes au BCFI Belgique — validation médicale obligatoire. '
      'RGPD : UUID anonyme — aucun identifiant nominal collecté.</div>')
def build_sbar(age, motif, cat, atcd, alg, o2, temp, fc, pas, spo2, fr, gcs, eva, n2, niv, just, crit, op="IAO", gl=None):
    return {"heure": datetime.now().strftime("%d/%m/%Y %H:%M"), "op": op, "age": int(age),
            "motif": motif, "cat": cat, "atcd": ", ".join(atcd) if atcd else "Aucun",
            "alg": alg or "Aucune", "o2": "O2 supp" if o2 else "Air ambiant",
            "gl": f"{gl}mg/dl ({mgdl_mmol(gl)}mmol/l)" if gl else "Non mesurée",
            "niv": LABELS.get(niv,niv), "sec": SECTEURS.get(niv,""), "delai": DELAIS.get(niv,"?"),
            "crit": crit, "just": just, "fc": fc, "pas": pas, "spo2": spo2, "fr": fr,
            "temp": temp, "gcs": gcs, "eva": eva, "n2": n2}
