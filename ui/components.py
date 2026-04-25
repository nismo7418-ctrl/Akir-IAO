# ui/components.py — Composants UI — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# DESIGN MÉDICAL
#   Contrastes WCAG AAA pour alertes critiques
#   Typographie lisible sous forte luminosité (tuiles blanches)
#   Boutons "one-hand friendly" (min 44px height)
#   Animations limitées (éviter les distractions en urgence)
#
# @st.fragment : Jauge NEWS2 se met à jour sans recharger la page entière

import streamlit as st
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS DE BASE
# ═══════════════════════════════════════════════════════════════════════════════

def H(html: str) -> None:
    """Injecte du HTML brut — unsafe_allow_html=True."""
    st.markdown(html, unsafe_allow_html=True)


def SEC(label: str) -> None:
    """Séparateur de section dans la sidebar."""
    H(f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;'
      f'font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.12em;'
      f'margin:16px 0 4px;">{label}</div>')


def CARD(title: str, _: str = "") -> None:
    """Ouvre une carte."""
    H(f'<div class="card"><div class="card-title">{title}</div>')


def CARD_END() -> None:
    """Ferme une carte."""
    H('</div>')


def AL(msg: str, level: str = "info") -> None:
    """Alerte avec icône et couleur sémantique.
    levels : danger | warning | success | info
    """
    icons = {"danger":"🔴","warning":"🟠","success":"🟢","info":"🔵"}
    colors = {
        "danger":  "#EF4444",
        "warning": "#F59E0B",
        "success": "#22C55E",
        "info":    "#3B82F6",
    }
    bg = {
        "danger":  "#FEF2F2",
        "warning": "#FFFBEB",
        "success": "#F0FDF4",
        "info":    "#EFF6FF",
    }
    H(f'<div class="al {level}" style="'
      f'background:{bg.get(level,"#EFF6FF")};'
      f'border-left:4px solid {colors.get(level,"#3B82F6")};'
      f'padding:9px 14px;border-radius:0 6px 6px 0;margin:6px 0;'
      f'font-size:.78rem;line-height:1.6;font-weight:500;">'
      f'{icons.get(level,"ℹ️")} {msg}</div>')


def DISC() -> None:
    """Disclaimer juridique et mention auteur — obligatoire chaque onglet."""
    H("""<div style="
        background:#0F172A;border:1px solid #1E293B;border-radius:10px;
        padding:14px 18px;margin-top:28px;font-size:.68rem;
        color:#64748B;line-height:1.9;font-style:italic;">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:.6rem;
            font-weight:600;color:#475569;text-transform:uppercase;
            letter-spacing:.1em;margin-bottom:8px;">
        ⚖️ Avertissement Légal — AKIR-IAO v19.0
      </div>
      Cette application est un <strong style="color:#94A3B8;">outil d'aide à la décision clinique</strong>
      destiné aux professionnels de santé qualifiés. Elle ne se substitue en aucun cas
      au jugement clinique du praticien ni aux protocoles institutionnels en vigueur.
      Les doses calculées sont indicatives et doivent être validées par un médecin avant toute administration.
      Protocoles BCFI Belgique — FRENCH SFMU V1.1 — Hainaut, Wallonie.<br>
      <strong style="color:#94A3B8;">Développeur exclusif : Ismail Ibn-Daifa</strong> —
      Application non commerciale — Données anonymisées (RGPD UE 2016/679 — Loi belge 2018) —
      AR 18/06/1990 relatif à l'exercice de la profession infirmière.<br>
      <span style="color:#475569;">
        Références : Taboulet P. FRENCH SFMU V1.1, 2018 · RCP London NEWS2, 2017 ·
        BCFI Répertoire Commenté des Médicaments, Belgique · SSC Guidelines 2021.
      </span>
    </div>""")


# ═══════════════════════════════════════════════════════════════════════════════
# JAUGE NEWS2 — @st.fragment — Mise à jour instantanée
# ═══════════════════════════════════════════════════════════════════════════════

@st.fragment
def GAUGE(n2: int, bpco: bool = False) -> None:
    """
    Jauge NEWS2 animée avec st.fragment.
    Se met à jour sans recharger l'intégralité de la page.
    Design gradients : vert → orange → rouge → violet (Tri M).
    """
    max_n2 = 20
    pct    = min(n2 / max_n2, 1.0)

    if   n2 >= 9:  color, label, css = "#7C3AED", "TRI M — ENGAGEMENT VITAL",  "n2-m"
    elif n2 >= 7:  color, label, css = "#DC2626", "APPEL MÉDICAL IMMÉDIAT",     "n2-crit"
    elif n2 >= 5:  color, label, css = "#EA580C", "SURVEILLANCE RAPPROCHÉE",    "n2-warn"
    elif n2 >= 3:  color, label, css = "#D97706", "RISQUE MODÉRÉ",              "n2-mod"
    else:          color, label, css = "#16A34A", "RISQUE FAIBLE",              "n2-ok"

    bpco_tag = ' <span style="font-size:.65rem;background:#1E40AF;color:#fff;padding:2px 6px;border-radius:999px;">BPCO Éch.2</span>' if bpco else ""

    H(f"""
    <div class="n2-widget" style="margin:12px 0;">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
        <span style="font-family:'IBM Plex Mono',monospace;font-size:.65rem;
              color:#94A3B8;text-transform:uppercase;letter-spacing:.1em;">
          NEWS2{bpco_tag}
        </span>
        <span style="font-size:1.4rem;font-weight:800;color:{color};
              font-family:'IBM Plex Mono',monospace;">{n2}</span>
      </div>
      <div style="background:#1E293B;border-radius:999px;height:10px;overflow:hidden;">
        <div style="height:100%;width:{pct*100:.1f}%;
              background:linear-gradient(90deg,#16A34A,{color});
              border-radius:999px;
              transition:width .4s ease;"></div>
      </div>
      <div style="font-size:.68rem;font-weight:600;color:{color};
            margin-top:5px;text-align:center;letter-spacing:.04em;">{label}</div>
    </div>""")


# ═══════════════════════════════════════════════════════════════════════════════
# BANDEAUX TRIAGE
# ═══════════════════════════════════════════════════════════════════════════════

_TRI_COLORS = {
    "M":  ("#4C1D95", "#DDD6FE"),
    "1":  ("#7F1D1D", "#FEE2E2"),
    "2":  ("#7C2D12", "#FED7AA"),
    "3A": ("#713F12", "#FEF08A"),
    "3B": ("#78350F", "#FDE68A"),
    "4":  ("#14532D", "#BBF7D0"),
    "5":  ("#1E3A5F", "#BFDBFE"),
}

_TRI_LABELS = {
    "M":  "TRI M — IMMÉDIAT",
    "1":  "TRI 1 — URGENCE EXTRÊME",
    "2":  "TRI 2 — TRÈS URGENT",
    "3A": "TRI 3A — URGENT",
    "3B": "TRI 3B — URGENT DIFFÉRÉ",
    "4":  "TRI 4 — MOINS URGENT",
    "5":  "TRI 5 — NON URGENT",
}

_TRI_DELAIS = {"M":5,"1":5,"2":15,"3A":30,"3B":60,"4":120,"5":999}

_SECTEURS = {
    "M":  "Déchocage — Immédiat",
    "1":  "Déchocage — Immédiat",
    "2":  "Soins aigus — Méd. < 20 min",
    "3A": "Soins aigus — Méd. < 30 min",
    "3B": "Polyclinique — Méd. < 1 h",
    "4":  "Consultation — Méd. < 2 h",
    "5":  "Salle d'attente — MG",
}


def TRI_CARD_INLINE(niv: str, just: str, n2: int) -> None:
    """Card de triage inline avec couleur sémantique et délai cible."""
    if not niv:
        return
    bg, fg   = _TRI_COLORS.get(niv, ("#1E293B", "#E2E8F0"))
    label    = _TRI_LABELS.get(niv, niv)
    delai    = _TRI_DELAIS.get(niv, "?")
    secteur  = _SECTEURS.get(niv, "—")
    flash    = 'animation:pulse 1s infinite;' if niv in ("M","1") else ""
    H(f"""
    <div style="background:{bg};border-radius:14px;padding:20px 24px;margin:12px 0;
          box-shadow:0 4px 24px {bg}88;{flash}">
      <div style="font-size:1.8rem;font-weight:900;color:{fg};
            letter-spacing:-.02em;margin-bottom:4px;">{label}</div>
      <div style="font-size:.82rem;color:{fg}CC;margin-bottom:8px;">{just}</div>
      <div style="display:flex;gap:16px;font-size:.72rem;color:{fg}99;">
        <span>🏥 {secteur}</span>
        <span>⏱ Délai cible : {delai} min</span>
        <span>📊 NEWS2 : {n2}</span>
      </div>
    </div>""")


def TRI_BANNER_FIXED(niv: str, just: str, n2: int) -> None:
    """Bandeau fixe en bas de l'écran si Tri ≤ 2."""
    if niv not in ("M","1","2"):
        return
    bg, fg = _TRI_COLORS.get(niv, ("#7F1D1D","#FEE2E2"))
    label  = _TRI_LABELS.get(niv, niv)
    H(f"""<div style="
        position:fixed;bottom:0;left:0;right:0;z-index:9999;
        background:{bg};color:{fg};
        padding:10px 20px;display:flex;justify-content:space-between;
        align-items:center;font-size:.82rem;font-weight:700;
        box-shadow:0 -4px 20px #00000080;">
      <span>{label}</span>
      <span style="font-size:.72rem;opacity:.9;">{just} · NEWS2 {n2}</span>
    </div>""")


def N2_BANNER(n2: int) -> None:
    """Alerte rouge clignotante si NEWS2 ≥ 7."""
    if n2 >= 9:
        H(f'<div class="n2-alert n2-m" style="animation:pulse 1s infinite;">'
          f'🟣 NEWS2 {n2} ≥ 9 — APPEL MÉDICAL IMMÉDIAT — DÉCHOCAGE</div>')
    elif n2 >= 7:
        H(f'<div class="n2-alert n2-crit">'
          f'🔴 NEWS2 {n2} ≥ 7 — APPEL MÉDICAL IMMÉDIAT</div>')


def PURPURA(det: dict) -> None:
    """Alerte purpura fulminans si cochée."""
    if det.get("purpura") or det.get("neff") or det.get("non_effacable"):
        H("""<div style="
            background:#7F1D1D;color:#FEE2E2;
            border-radius:12px;padding:16px 20px;
            font-weight:700;font-size:.85rem;
            margin:8px 0;animation:pulse 2s infinite;
            border:2px solid #EF4444;">
          🔴 PURPURA FULMINANS SUSPECTÉ<br>
          <span style="font-size:.78rem;font-weight:400;">
          → Ceftriaxone 2 g IV IMMÉDIAT — Ne pas attendre le médecin<br>
          → TRI 1 — Déchocage
          </span>
        </div>""")


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGETS CLINIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def GLYC_WIDGET(key: str, label: str = "Glycémie capillaire (mg/dl)",
                req: bool = False) -> Optional[float]:
    """Widget glycémie avec conversion mg/dl ↔ mmol/l et alertes."""
    v = st.number_input(label, 0, 1500, 0, 5, key=key,
                        help="0 = non mesuré")
    if v == 0:
        if req:
            st.warning("⚠️ Glycémie capillaire requise pour ce motif")
        return None
    mm = round(v / 18.016, 1)
    st.caption(f"→ {mm} mmol/l")
    if v < 54:
        st.error(f"🔴 HYPOGLYCÉMIE SÉVÈRE {v} mg/dl ({mm} mmol/l) — Glucose 30 % IV IMMÉDIAT")
    elif v < 70:
        st.warning(f"🟠 Hypoglycémie modérée {v} mg/dl ({mm} mmol/l)")
    elif v > 360:
        st.error(f"🔴 Hyperglycémie sévère {v} mg/dl ({mm} mmol/l) — Bilan acidocétose")
    elif v > 180:
        st.warning(f"🟠 Hyperglycémie {v} mg/dl ({mm} mmol/l)")
    return float(v)


def VITAUX(fc: float, pas: float, spo2: float,
           fr: float, temp: float, gcs: int, bpco: bool = False) -> None:
    """Tableau de bord des vitaux avec code couleur."""
    from clinical.vitaux import si as shock_index  # type: ignore
    sh  = shock_index(fc, pas)
    spo2_alerte = 92 if bpco else 95

    def _col(val, unit, label, low=None, high=None, inv=False):
        ok  = True
        col = "#22C55E"
        if low  is not None and val < low:  ok = False; col = "#EF4444"
        if high is not None and val > high: ok = False; col = "#EF4444"
        if inv: col = "#EF4444" if ok else "#22C55E"  # inversé (ex: GCS)
        return (f'<div style="text-align:center;padding:8px 4px;">'
                f'<div style="font-size:1.1rem;font-weight:700;color:{col};">'
                f'{val:.0f if isinstance(val,float) else val}{unit}</div>'
                f'<div style="font-size:.6rem;color:#94A3B8;">{label}</div></div>')

    cols_html = (
        _col(fc,   " bpm","FC",   40, 150)
        + _col(pas, " mmHg","PAS",  90, 180)
        + _col(spo2," %",  "SpO2", spo2_alerte, 100)
        + _col(fr,  "/min","FR",   10,  30)
        + _col(temp," °C", "Temp", 35.5, 38.5)
        + _col(gcs, "/15","GCS", high=None, low=14, inv=True)
        + f'<div style="text-align:center;padding:8px 4px;">'
          f'<div style="font-size:1.1rem;font-weight:700;'
          f'color:{"#EF4444" if sh>=1.0 else ("#F59E0B" if sh>=0.8 else "#22C55E")};">'
          f'{sh}</div>'
          f'<div style="font-size:.6rem;color:#94A3B8;">Shock Index</div></div>'
    )
    H(f'<div style="display:grid;grid-template-columns:repeat(7,1fr);'
      f'background:#1E293B;border-radius:10px;margin:10px 0;">'
      f'{cols_html}</div>')


def VITAUX(fc: float, pas: float, spo2: float,
           fr: float, temp: float, gcs: int, bpco: bool = False) -> None:
    """Tableau de bord des vitaux avec code couleur."""
    from clinical.vitaux import si as shock_index  # type: ignore

    sh = shock_index(fc, pas)
    spo2_alerte = 92 if bpco else 95

    def _fmt_val(val) -> str:
        if isinstance(val, float):
            return f"{val:.0f}" if val.is_integer() else f"{val:.1f}"
        return str(val)

    def _col(val, unit, label, low=None, high=None, inv=False):
        ok = True
        col = "#22C55E"
        if low is not None and val < low:
            ok = False
            col = "#EF4444"
        if high is not None and val > high:
            ok = False
            col = "#EF4444"
        if inv:
            col = "#EF4444" if ok else "#22C55E"  # inverse (ex: GCS)
        return (f'<div style="text-align:center;padding:8px 4px;">'
                f'<div style="font-size:1.1rem;font-weight:700;color:{col};">'
                f'{_fmt_val(val)}{unit}</div>'
                f'<div style="font-size:.6rem;color:#94A3B8;">{label}</div></div>')

    cols_html = (
        _col(fc, " bpm", "FC", 40, 150)
        + _col(pas, " mmHg", "PAS", 90, 180)
        + _col(spo2, " %", "SpO2", spo2_alerte, 100)
        + _col(fr, "/min", "FR", 10, 30)
        + _col(temp, " Â°C", "Temp", 35.5, 38.5)
        + _col(gcs, "/15", "GCS", low=14, inv=True)
        + f'<div style="text-align:center;padding:8px 4px;">'
          f'<div style="font-size:1.1rem;font-weight:700;'
          f'color:{"#EF4444" if sh >= 1.0 else ("#F59E0B" if sh >= 0.8 else "#22C55E")};">'
          f'{sh}</div>'
          f'<div style="font-size:.6rem;color:#94A3B8;">Shock Index</div></div>'
    )
    H(f'<div style="display:grid;grid-template-columns:repeat(7,1fr);'
      f'background:#1E293B;border-radius:10px;margin:10px 0;">'
      f'{cols_html}</div>')


def SI_WIDGET(fc: float, pas: float) -> None:
    """Indicateur Shock Index."""
    sh  = round(fc / max(pas, 1), 2)
    if   sh >= 1.0: css, lbl = "si-c", "CHOC PROBABLE"
    elif sh >= 0.8: css, lbl = "si-w", "Instabilité débutante"
    else:           css, lbl = "si-ok","Normal"
    H(f'<div class="si-box"><div class="si-l">Shock Index</div>'
      f'<div class="si-v {css}">{sh}</div>'
      f'<div class="si-l">{lbl}</div></div>')


def BPCO_WIDGET(bpco: bool) -> None:
    """Affiche la cible SpO2 adaptée BPCO."""
    if bpco:
        AL("BPCO — Cible SpO2 88-92 % — Risque narcose CO₂ si > 96 %", "warning")


# ═══════════════════════════════════════════════════════════════════════════════
# CARDS PHARMACOLOGIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def RX(nom: str, dose: str, details: list, ref: str,
       palier: str = "2", alertes: Optional[list] = None) -> None:
    """Card médicament avec code couleur palier OMS + alertes ATCD."""
    palier_colors = {"U":"#7F1D1D","1":"#DC2626","2":"#2563EB","3":"#7C3AED"}
    pc = palier_colors.get(palier, "#2563EB")
    det_html = "".join(f"<div>• {d}</div>" for d in details if d)
    als_html = ""
    if alertes:
        for al_msg, al_css in alertes:
            icons_ = {"danger":"🔴","warning":"🟠","info":"🔵","success":"🟢"}
            als_html += (f'<div style="background:{"#FEF2F2" if al_css=="danger" else "#FFFBEB"};'
                         f'border-left:3px solid {"#EF4444" if al_css=="danger" else "#F59E0B"};'
                         f'padding:5px 10px;margin:4px 0;font-size:.72rem;border-radius:0 4px 4px 0;">'
                         f'{icons_.get(al_css,"ℹ️")} {al_msg}</div>')
    H(f'<div class="rx" style="border-left:4px solid {pc};padding:12px 16px;'
      f'background:#0F172A;border-radius:0 10px 10px 0;margin:8px 0;">'
      f'<div style="font-weight:700;font-size:.9rem;color:#E2E8F0;">{nom}</div>'
      f'<div style="font-size:1.2rem;font-weight:800;color:{pc};margin:4px 0;">{dose}</div>'
      f'<div style="font-size:.75rem;color:#94A3B8;line-height:1.8;">{det_html}</div>'
      f'{als_html}'
      f'<div style="font-size:.62rem;color:#475569;margin-top:6px;font-style:italic;">'
      f'Réf: {ref}</div></div>')


def RX_LOCK(msg: str) -> None:
    """Protocole verrouillé — affiche le motif."""
    H(f'<div style="background:#1E293B;border:2px dashed #475569;'
      f'border-radius:10px;padding:14px;text-align:center;'
      f'color:#64748B;font-size:.78rem;margin:8px 0;">'
      f'🔒 {msg}</div>')


# ═══════════════════════════════════════════════════════════════════════════════
# RAPPORT SBAR
# ═══════════════════════════════════════════════════════════════════════════════

def build_sbar(age, motif, cat, atcd, alg, o2,
               temp, fc, pas, spo2, fr, gcs,
               eva, n2, niv, just, crit,
               operateur="IAO", gl=None) -> dict:
    """Construit le dict SBAR pour l'onglet Transmission."""
    from datetime import datetime
    from config import SECTEURS, DELAIS
    return {
        "S": {
            "operateur": operateur,
            "heure":     datetime.now().strftime("%d/%m/%Y %H:%M"),
            "motif":     motif,
            "niveau":    niv,
            "label":     f"TRI {niv} — {just}",
        },
        "B": {
            "age":    age,
            "atcd":   atcd or [],
            "alg":    alg or "Aucune connue",
            "o2":     o2,
            "gl":     gl,
        },
        "A": {
            "fc": fc, "pas": pas, "spo2": spo2, "fr": fr,
            "temp": temp, "gcs": gcs, "eva": eva, "n2": n2,
            "crit": crit,
        },
        "R": {
            "secteur": SECTEURS.get(niv,"—"),
            "delai":   DELAIS.get(niv,"—"),
            "remarques": "",
        },
    }


def SBAR_RENDER(sbar: dict) -> None:
    """Affiche le rapport SBAR formaté."""
    S, B, A, R = sbar["S"], sbar["B"], sbar["A"], sbar["R"]
    sections = [
        ("S — SITUATION", [
            f"Opérateur : {S['operateur']}",
            f"Heure : {S['heure']}",
            f"Motif : {S['motif']}",
            f"Résultat triage : {S['label']}",
        ]),
        ("B — BACKGROUND", [
            f"Âge : {B['age']} ans",
            f"Antécédents : {', '.join(B['atcd']) if B['atcd'] else 'Aucun'}",
            f"Allergies : {B['alg']}",
            f"O₂ supplémentaire : {'Oui' if B['o2'] else 'Non'}",
            *([ f"Glycémie : {B['gl']:.0f} mg/dl" ] if B.get("gl") else []),
        ]),
        ("A — ASSESSMENT", [
            f"FC {A['fc']:.0f} bpm — PAS {A['pas']:.0f} mmHg — SpO2 {A['spo2']:.0f} %",
            f"FR {A['fr']:.0f}/min — T° {A['temp']:.1f} °C — GCS {A['gcs']}/15",
            f"EVA {A['eva']}/10 — NEWS2 {A['n2']}",
            f"Critère : {A['crit']}",
        ]),
        ("R — RECOMMANDATION", [
            f"Orientation : {R['secteur']}",
            f"Délai cible : {R['delai']} min",
            f"Remarques : {R['remarques'] or 'A completer par l operateur'}",
        ]),
    ]
    sbar_css = ("background:#0F172A;border-radius:12px;padding:20px 24px;"
                "margin:8px 0;font-size:.78rem;font-family:'IBM Plex Mono',monospace;")
    full = f'<div style="{sbar_css}">'
    for sec_title, items in sections:
        full += (f'<div style="color:#3B82F6;font-weight:700;font-size:.72rem;'
                 f'text-transform:uppercase;letter-spacing:.1em;margin:14px 0 4px 0;">'
                 f'{sec_title}</div>')
        for item in items:
            full += f'<div style="color:#94A3B8;line-height:1.8;">· {item}</div>'
    full += '</div>'
    H(full)
