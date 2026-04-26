# ui/components.py — Composants UI — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Design : Médical — Contrastes WCAG AAA — Mobile-friendly (44px min boutons)

import streamlit as st
from typing import Optional
from datetime import datetime
from config import LABELS, SECTEURS, DELAIS, TCSS, HBCSS


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
    """Alerte avec icône et couleur sémantique. levels: danger|warning|success|info"""
    icons  = {"danger": "🔴", "warning": "🟠", "success": "🟢", "info": "🔵"}
    H(f'<div class="al {level}">{icons.get(level, "ℹ️")} {msg}</div>')


def DISC() -> None:
    """Disclaimer juridique et mention auteur — obligatoire sur chaque onglet."""
    H("""<div class="disclaimer">
      <div class="disclaimer-title">⚖️ Avertissement Légal — AKIR-IAO v19.0</div>
      Cette application est un <strong style="color:#94A3B8;">outil d'aide à la décision clinique</strong>
      destiné aux professionnels de santé qualifiés. Elle ne se substitue en aucun cas
      au jugement clinique du praticien ni aux protocoles institutionnels en vigueur.<br>
      Classification fondée sur la grille <strong style="color:#94A3B8;">FRENCH Triage V1.1 (SFMU 2018)</strong>
      et les protocoles <strong style="color:#94A3B8;">BCFI Belgique</strong>.
      Localisation : Urgences — Province de Hainaut, Wallonie, Belgique.<br>
      <strong style="color:#64748B;">Aucune donnée nominative n'est stockée (RGPD).</strong><br>
      <span style="color:#475569;">Développeur exclusif : Ismail Ibn-Daifa — v19.0 — 2025</span>
    </div>""")


# ═══════════════════════════════════════════════════════════════════════════════
# BARRE EVA VISUELLE
# ═══════════════════════════════════════════════════════════════════════════════

_EVA_COLORS = [
    "#22C55E", "#4ADE80", "#86EFAC",  # 0-2 vert
    "#FCD34D", "#FBBF24", "#F59E0B",  # 3-5 jaune
    "#FB923C", "#F97316",              # 6-7 orange
    "#EF4444", "#DC2626", "#991B1B",  # 8-10 rouge
]

def EVA_BAR(eva: int) -> None:
    """Barre visuelle EVA 0-10 avec dégradé vert → rouge et valeur active surlignée."""
    cells = ""
    for i, color in enumerate(_EVA_COLORS):
        text_color = "#fff" if i >= 5 else "#1A202C"
        active = " active" if i == eva else ""
        cells += (
            f'<div class="eva-cell{active}" '
            f'style="background:{color};color:{text_color};">'
            f'{i}</div>'
        )
    H(f'<div class="eva-bar">{cells}</div>')


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTES NEWS2
# ═══════════════════════════════════════════════════════════════════════════════

def N2_BANNER(n2: int) -> None:
    """Bannière NEWS2 selon le niveau de risque."""
    if n2 >= 9:
        H(f'<div class="n2-alert n2-m">'
          f'🟣 NEWS2 {n2} ≥ 9 — APPEL MÉDICAL IMMÉDIAT — DÉCHOCAGE</div>')
    elif n2 >= 7:
        H(f'<div class="n2-alert n2-crit">'
          f'🔴 NEWS2 {n2} ≥ 7 — APPEL MÉDICAL IMMÉDIAT</div>')


def PURPURA(det: dict) -> None:
    """Alerte purpura fulminans si cochée."""
    if det.get("purpura") or det.get("neff") or det.get("non_effacable"):
        H("""<div style="
            background:#7F1D1D;color:#FEE2E2;border-radius:12px;
            padding:16px 20px;font-weight:700;font-size:.85rem;
            margin:8px 0;animation:pulse 2s infinite;border:2px solid #EF4444;">
          🔴 PURPURA FULMINANS SUSPECTÉ<br>
          <span style="font-size:.78rem;font-weight:400;">
          → Ceftriaxone 2 g IV IMMÉDIAT — Ne pas attendre le médecin<br>
          → TRI 1 — Déchocage
          </span></div>""")


# ═══════════════════════════════════════════════════════════════════════════════
# CARTE DE TRIAGE
# ═══════════════════════════════════════════════════════════════════════════════

def TRI_CARD_INLINE(niv: str, justif: str, n2: int) -> None:
    """Carte de triage principale avec code couleur standard."""
    css    = TCSS.get(niv, "tri-3B")
    label  = LABELS.get(niv, f"TRI {niv}")
    secteur= SECTEURS.get(niv, "À définir")
    delai  = DELAIS.get(niv, 60)
    H(f'<div class="tri-card {css}">'
      f'<div class="tri-label">{label}</div>'
      f'<div class="tri-just">{justif}</div>'
      f'<div class="tri-delay">📍 {secteur} — Délai médecin ≤ {delai} min — NEWS2 {n2}</div>'
      f'</div>')


def TRI_BANNER_FIXED(niv: str) -> None:
    """Bannière de triage fixe en bas de page."""
    css   = TCSS.get(niv, "tri-3B")
    label = LABELS.get(niv, f"TRI {niv}")
    H(f'<div style="position:fixed;bottom:0;left:0;right:0;z-index:999;">'
      f'<div class="tri-card {css}" style="border-radius:0;margin:0;padding:10px;">'
      f'<div style="font-size:.9rem;font-weight:800;">{label}</div>'
      f'</div></div>')


# ═══════════════════════════════════════════════════════════════════════════════
# VITAUX DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def _vital_css(val: float, normal_min: float, normal_max: float) -> str:
    if val < normal_min or val > normal_max:
        return "vital-crit"
    if val < normal_min * 1.1 or val > normal_max * 0.9:
        return "vital-warn"
    return "vital-ok"


def VITAUX(fc: float, pas: float, spo2: float, fr: float, temp: float, gcs: int, bpco: bool = False) -> None:
    """Tableau de bord des vitaux avec code couleur."""
    si_val = fc / pas if pas > 0 else 0
    si_css = "vital-crit" if si_val >= 1.0 else ("vital-warn" if si_val >= 0.8 else "vital-ok")

    H(f"""<div class="vitaux-grid">
      <div class="vital-box">
        <div class="vital-label">FC (bpm)</div>
        <div class="vital-val {_vital_css(fc,60,100)}">{fc:.0f}</div>
      </div>
      <div class="vital-box">
        <div class="vital-label">PAS (mmHg)</div>
        <div class="vital-val {_vital_css(pas,90,140)}">{pas:.0f}</div>
      </div>
      <div class="vital-box">
        <div class="vital-label">SpO2 (%)</div>
        <div class="vital-val {_vital_css(spo2,94,100)}">{spo2:.0f}</div>
      </div>
      <div class="vital-box">
        <div class="vital-label">FR (/min)</div>
        <div class="vital-val {_vital_css(fr,12,20)}">{fr:.0f}</div>
      </div>
      <div class="vital-box">
        <div class="vital-label">T° (°C)</div>
        <div class="vital-val {_vital_css(temp,36.0,38.0)}">{temp:.1f}</div>
      </div>
      <div class="vital-box">
        <div class="vital-label">GCS</div>
        <div class="vital-val {_vital_css(gcs,14,15)}">{gcs}/15</div>
      </div>
    </div>
    <div style="text-align:center;font-size:.75rem;margin-top:4px;">
      Shock Index : <span class="{si_css}" style="font-weight:700;font-family:'IBM Plex Mono',monospace;">{si_val:.2f}</span>
    </div>""")


def GAUGE(n2: int, bpco: bool = False) -> None:
    """Jauge NEWS2 visuelle."""
    if n2 >= 9:     color = "#7C3AED"
    elif n2 >= 7:   color = "#EF4444"
    elif n2 >= 5:   color = "#F59E0B"
    elif n2 >= 1:   color = "#22C55E"
    else:           color = "#3B82F6"

    bpco_note = " (Échelle BPCO)" if bpco else ""
    H(f'<div class="gauge-container">'
      f'<div class="gauge-label">NEWS2{bpco_note}</div>'
      f'<div class="gauge-val" style="color:{color};">{n2}</div>'
      f'<div class="gauge-label">/ 20</div>'
      f'</div>')


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGETS CLINIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def GLYC_WIDGET(key: str, label: str = "Glycémie capillaire (mg/dl)", req: bool = False) -> Optional[float]:
    """Widget glycémie avec conversion mg/dl ↔ mmol/l et alertes."""
    v = st.number_input(label, 0, 1500, 0, 5, key=key, help="0 = non mesuré")
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


def BPCO_WIDGET(active: bool) -> None:
    """Info BPCO et cible SpO2."""
    if active:
        AL("BPCO — Cible SpO2 88-92 % — Risque narcose CO₂ si > 96 %", "warning")


def SI_WIDGET(fc: float, pas: float, age: float = 45.0) -> None:
    """Shock Index avec interprétation."""
    si_val = fc / pas if pas > 0 else 0
    if si_val >= 1.5:
        AL(f"Shock Index {si_val:.2f} ≥ 1.5 — CHOC DÉCOMPENSÉ", "danger")
    elif si_val >= 1.0:
        AL(f"Shock Index {si_val:.2f} ≥ 1.0 — Instabilité hémodynamique", "warning")
    else:
        st.caption(f"Shock Index : {si_val:.2f} — Stable")


# ═══════════════════════════════════════════════════════════════════════════════
# CARDS PHARMACOLOGIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def RX(nom: str, dose: str, details: list, ref: str, palier: str = "2", alertes: Optional[list] = None) -> None:
    """Card médicament avec code couleur palier OMS + alertes ATCD."""
    palier_colors = {"U": "#7F1D1D", "1": "#DC2626", "2": "#2563EB", "3": "#7C3AED"}
    pc = palier_colors.get(palier, "#2563EB")
    det_html = "".join(f"<div>• {d}</div>" for d in details if d)
    als_html = ""
    if alertes:
        for al_msg, al_css in alertes:
            icons_ = {"danger": "🔴", "warning": "🟠", "info": "🔵"}
            bg = "#FEF2F2" if al_css == "danger" else "#FFFBEB"
            bc = "#EF4444" if al_css == "danger" else "#F59E0B"
            als_html += (f'<div style="background:{bg};border-left:3px solid {bc};'
                         f'padding:5px 10px;margin:4px 0;font-size:.72rem;border-radius:0 4px 4px 0;">'
                         f'{icons_.get(al_css,"ℹ️")} {al_msg}</div>')
    H(f'<div style="border-left:4px solid {pc};padding:12px 16px;'
      f'background:#F8FAFC;border-radius:0 10px 10px 0;margin:8px 0;">'
      f'<div style="font-weight:700;font-size:.88rem;color:#1E293B;">{nom}</div>'
      f'<div style="font-size:1.1rem;font-weight:800;color:{pc};margin:4px 0;">{dose}</div>'
      f'<div style="font-size:.75rem;color:#4A5568;line-height:1.8;">{det_html}</div>'
      f'{als_html}'
      f'<div style="font-size:.62rem;color:#94A3B8;margin-top:6px;font-style:italic;">Réf: {ref}</div></div>')


def RX_LOCK(msg: str) -> None:
    """Protocole verrouillé — affiche le motif."""
    H(f'<div style="background:#F1F5F9;border:2px dashed #CBD5E1;'
      f'border-radius:10px;padding:14px;text-align:center;'
      f'color:#64748B;font-size:.78rem;margin:8px 0;">🔒 {msg}</div>')


# ═══════════════════════════════════════════════════════════════════════════════
# RAPPORT SBAR
# ═══════════════════════════════════════════════════════════════════════════════

def build_sbar(
    age, motif, cat, atcd, alg, o2,
    temp, fc, pas, spo2, fr, gcs,
    eva, n2, niv, just, crit,
    operateur="IAO", gl=None,
) -> dict:
    """Construit le dict SBAR pour l'onglet Transmission."""
    now = datetime.now()
    si_val = round(fc / pas, 2) if pas > 0 else 0
    label  = LABELS.get(niv, f"TRI {niv}")
    secteur= SECTEURS.get(niv, "Évaluation")
    delai  = DELAIS.get(niv, 60)
    atcd_str = ", ".join(atcd) if atcd else "Aucun connu"
    alg_str  = alg or "Aucune connue"
    gl_str   = f"{gl:.0f} mg/dl ({gl/18.016:.1f} mmol/l)" if gl else "Non mesurée"

    return {
        "date": now.strftime("%d/%m/%Y"),
        "heure": now.strftime("%H:%M"),
        "age": age,
        "motif": motif,
        "cat": cat,
        "niv": niv,
        "label": label,
        "secteur": secteur,
        "delai": delai,
        "atcd": atcd_str,
        "alg": alg_str,
        "o2": o2,
        "temp": temp, "fc": fc, "pas": pas, "spo2": spo2, "fr": fr, "gcs": gcs,
        "si": si_val,
        "eva": eva,
        "n2": n2,
        "just": just,
        "crit": crit,
        "gl": gl_str,
        "operateur": operateur,
    }


def SBAR_RENDER(s: dict) -> None:
    """Affiche la transmission SBAR formatée."""
    txt = f"""╔══════════════════════════════════════════════════════════╗
║  TRANSMISSION SBAR — AKIR-IAO v19.0                     ║
║  Service des Urgences — Hainaut, Wallonie, Belgique      ║
║  {s['date']} — {s['heure']}                                        ║
╚══════════════════════════════════════════════════════════╝

━━━ [S] SITUATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Patient     : Anonyme (Session RGPD), {s['age']} ans
  Admission   : {s['date']} à {s['heure']}
  Motif       : {s['motif']} ({s['cat']})
  Douleur     : EVA {s['eva']}/10
  Conscience  : GCS {s['gcs']}/15
  ► NIVEAU    : {s['label']}

━━━ [B] BACKGROUND ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ATCD        : {s['atcd']}
  Allergies   : {s['alg']}
  O2 admission: {'OUI' if s['o2'] else 'NON'}

━━━ [A] ASSESSMENT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Constantes :
    T° {s['temp']}°C | FC {s['fc']} bpm | PAS {s['pas']} mmHg
    SpO2 {s['spo2']}% | FR {s['fr']}/min | GCS {s['gcs']}/15
  Shock Index : {s['si']}
  Glycémie    : {s['gl']}
  NEWS2       : {s['n2']}

  Justification triage : {s['just']}
  Référence FRENCH     : {s['crit']}

━━━ [R] RECOMMENDATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Orientation : {s['secteur']}
  Délai médecin cible : ≤ {s['delai']} min

──────────────────────────────────────────────────────────
  IAO : Ismail Ibn-Daifa — {s['heure']}
  Réf. FRENCH Triage SFMU V1.1 — BCFI Belgique
  Province de Hainaut, Wallonie, Belgique
──────────────────────────────────────────────────────────"""

    H(f'<div class="sbar-block">{txt}</div>')
    st.download_button(
        "📋 Télécharger la transmission SBAR (.txt)",
        data=txt,
        file_name=f"SBAR_{s['date'].replace('/','')}_{s['heure'].replace(':','')}_Tri{s['niv']}.txt",
        mime="text/plain",
        use_container_width=True,
    )
