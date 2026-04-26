# ui/styles.py — Design Médical Professionnel WCAG AA — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Standard : DPI moderne, palette hospitalière, densité maximale

import streamlit as st


def load_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ══════════════════════════════════════════════════════════════════
   TOKENS — Palette Hospitalière Bleu Médical + Gris Acier
══════════════════════════════════════════════════════════════════ */
:root {
  /* Primaire */
  --P:   #004A99;
  --PL:  #1A69B8;
  --PD:  #002F66;
  --PP:  #EBF3FD;
  --P05: rgba(0,74,153,.05);
  --P12: rgba(0,74,153,.12);
  --P20: rgba(0,74,153,.20);

  /* Surfaces — Gris Acier hospitalier */
  --BG:   #F8FAFC;
  --BG2:  #F1F5F9;
  --CARD: #FFFFFF;
  --B:    #E2E8F0;
  --B2:   #CBD5E1;

  /* Texte */
  --T:  #0F172A;
  --TM: #475569;
  --TS: #64748B;
  --TW: #FFFFFF;

  /* Triage — codes couleur FRENCH */
  --TM-bg:#4C1D95; --TM-ac:#E879F9; --TM-t:#F5F3FF;
  --T1-bg:#7F1D1D; --T1-ac:#FCA5A5; --T1-t:#FEF2F2;
  --T2-bg:#78350F; --T2-ac:#FDE68A; --T2-t:#FFFBEB;
  --T3A-bg:#1E3A5F;--T3A-ac:#93C5FD;--T3A-t:#EFF6FF;
  --T3B-bg:#164E63;--T3B-ac:#A5F3FC;--T3B-t:#ECFEFF;
  --T4-bg:#14532D; --T4-ac:#86EFAC; --T4-t:#F0FDF4;
  --T5-bg:#1E293B; --T5-ac:#CBD5E1; --T5-t:#F8FAFC;

  /* Sémantique — contraste WCAG AA */
  --ERR:#EF4444; --ERR-bg:#FEF2F2; --ERR-t:#991B1B; --ERR-b:#FCA5A5;
  --WRN:#D97706; --WRN-bg:#FFFBEB; --WRN-t:#78350F; --WRN-b:#FDE68A;
  --SUC:#16A34A; --SUC-bg:#F0FDF4; --SUC-t:#14532D; --SUC-b:#86EFAC;
  --INF:#2563EB; --INF-bg:#EFF6FF; --INF-t:#1E3A8A; --INF-b:#93C5FD;

  /* Géométrie */
  --r:  10px;
  --r2:  7px;
  --r3:  5px;

  /* Ombres */
  --s0: 0 1px 2px rgba(0,0,0,.06);
  --s1: 0 1px 4px rgba(0,0,0,.08), 0 0 0 1px rgba(0,74,153,.04);
  --s2: 0 4px 12px rgba(0,74,153,.10);
  --s3: 0 8px 24px rgba(0,74,153,.16);
}

/* ══════════════════════════════════════════════════════════════════
   RESET & BASE
══════════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

html, body, [class*="st-"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--T);
  background: var(--BG);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ══════════════════════════════════════════════════════════════════
   LAYOUT — Conteneur dense
══════════════════════════════════════════════════════════════════ */
.block-container {
  padding: .5rem .875rem 3rem !important;
  max-width: 960px;
  margin: 0 auto;
}
@media (min-width: 1200px) {
  .block-container { max-width: 1040px; padding: .75rem 1.5rem 3rem !important; }
}
@media (min-width: 769px) and (max-width: 1199px) {
  .block-container { max-width: 820px; }
}
@media (max-width: 768px) {
  .block-container { padding: .4rem .6rem 2.5rem !important; max-width: 100%; }
}

/* ══════════════════════════════════════════════════════════════════
   EN-TÊTE APPLICATION
══════════════════════════════════════════════════════════════════ */
.app-hdr {
  background: linear-gradient(130deg, var(--PD) 0%, var(--P) 55%, var(--PL) 100%);
  border-radius: var(--r);
  padding: 14px 18px;
  margin-bottom: 12px;
  box-shadow: var(--s3);
}
.app-hdr-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -.02em;
  font-family: 'IBM Plex Mono', monospace;
  line-height: 1.2;
}
.app-hdr-sub {
  font-size: .68rem;
  color: rgba(255,255,255,.72);
  margin-top: 2px;
}
.app-hdr-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.tag {
  background: rgba(255,255,255,.14);
  color: rgba(255,255,255,.92);
  font-size: .56rem;
  padding: 2px 7px;
  border-radius: 20px;
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: .06em;
  border: 1px solid rgba(255,255,255,.22);
}

/* ══════════════════════════════════════════════════════════════════
   CARTES — Dense
══════════════════════════════════════════════════════════════════ */
.card {
  background: var(--CARD);
  border-radius: var(--r);
  padding: 13px 16px;
  box-shadow: var(--s1);
  border: 1px solid var(--B);
  margin-bottom: 10px;
}
.card-title {
  font-size: .65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--TM);
  margin-bottom: 10px;
  font-family: 'IBM Plex Mono', monospace;
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-title::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 12px;
  background: var(--P);
  border-radius: 2px;
}

/* ══════════════════════════════════════════════════════════════════
   ALERTES WCAG AA — Contraste renforcé
══════════════════════════════════════════════════════════════════ */
.al {
  border-radius: 0 var(--r3) var(--r5) 0;
  padding: 7px 12px;
  margin: 4px 0;
  font-size: .76rem;
  font-weight: 500;
  line-height: 1.55;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.al.danger  { background:var(--ERR-bg); border-left:3px solid var(--ERR); color:var(--ERR-t); }
.al.warning { background:var(--WRN-bg); border-left:3px solid var(--WRN); color:var(--WRN-t); }
.al.success { background:var(--SUC-bg); border-left:3px solid var(--SUC); color:var(--SUC-t); }
.al.info    { background:var(--INF-bg); border-left:3px solid var(--INF); color:var(--INF-t); }

/* Bannière priorité critique — pleine largeur */
.al-banner {
  border-radius: var(--r2);
  padding: 10px 14px;
  margin: 6px 0;
  font-size: .78rem;
  font-weight: 700;
  text-align: center;
  letter-spacing: .01em;
}
.al-banner.danger  { background: var(--ERR); color: #fff; }
.al-banner.warning { background: var(--WRN); color: #fff; }

/* ══════════════════════════════════════════════════════════════════
   NIVEAUX DE TRIAGE — Couleurs FRENCH
══════════════════════════════════════════════════════════════════ */
.tri-M,  .hb-M  { background:var(--TM-bg) !important; color:var(--TM-ac) !important; }
.tri-1,  .hb-1  { background:var(--T1-bg) !important; color:var(--T1-ac) !important; }
.tri-2,  .hb-2  { background:var(--T2-bg) !important; color:var(--T2-ac) !important; }
.tri-3A, .hb-3A { background:var(--T3A-bg)!important; color:var(--T3A-ac)!important; }
.tri-3B, .hb-3B { background:var(--T3B-bg)!important; color:var(--T3B-ac)!important; }
.tri-4,  .hb-4  { background:var(--T4-bg) !important; color:var(--T4-ac) !important; }
.tri-5,  .hb-5  { background:var(--T5-bg) !important; color:var(--T5-ac) !important; }

.tri-card {
  border-radius: var(--r);
  padding: 16px 18px;
  margin: 8px 0;
  text-align: center;
  box-shadow: var(--s2);
}
.tri-label { font-size: 1.45rem; font-weight: 900; letter-spacing: -.02em; }
.tri-just  { font-size: .76rem; margin-top: 6px; opacity: .9; line-height: 1.5; }
.tri-delay { font-size: .64rem; margin-top: 4px; opacity: .72; font-family:'IBM Plex Mono',monospace; }

/* ══════════════════════════════════════════════════════════════════
   NEWS2 BANNERS
══════════════════════════════════════════════════════════════════ */
.n2-alert {
  border-radius: var(--r2);
  padding: 10px 14px;
  margin: 6px 0;
  font-weight: 700;
  font-size: .8rem;
  text-align: center;
}
.n2-m    { background:#4C1D95; color:#E879F9; border:2px solid #7C3AED; }
.n2-crit { background:#7F1D1D; color:#FCA5A5; border:2px solid #EF4444; }

@keyframes pulse {
  0%,100% { opacity:1; transform:scale(1); }
  50%      { opacity:.85; transform:scale(1.008); }
}
.n2-m { animation: pulse 1.5s infinite; }

/* ══════════════════════════════════════════════════════════════════
   VITAUX DASHBOARD — Compact
══════════════════════════════════════════════════════════════════ */
.vitaux-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin: 8px 0;
}
@media (max-width: 768px) { .vitaux-grid { grid-template-columns: repeat(2,1fr); } }

.vital-box {
  background: var(--BG2);
  border: 1px solid var(--B);
  border-radius: var(--r2);
  padding: 8px 6px;
  text-align: center;
}
.vital-label { font-size: .55rem; color: var(--TS); text-transform: uppercase; letter-spacing: .08em; }
.vital-val   { font-size: 1.2rem; font-weight: 700; font-family:'IBM Plex Mono',monospace; line-height: 1.1; }
.vital-ok    { color: #16A34A; }
.vital-warn  { color: #D97706; }
.vital-crit  { color: #DC2626; }

/* ══════════════════════════════════════════════════════════════════
   PHARMACOLOGIE — Cards RX
══════════════════════════════════════════════════════════════════ */
.rx-card {
  border-radius: 0 var(--r2) var(--r2) 0;
  padding: 10px 14px;
  background: var(--BG2);
  margin: 6px 0;
  border-left: 4px solid var(--P);
}

/* Bandeau urgence pharma (Tri 1/2 + EVA ≥ 7) */
.pharma-urgent {
  background: linear-gradient(135deg, #7F1D1D 0%, #B91C1C 100%);
  color: #FEE2E2;
  border-radius: var(--r);
  padding: 12px 16px;
  margin-bottom: 12px;
  font-weight: 700;
  font-size: .82rem;
  border: 2px solid #EF4444;
  animation: pulse 2s infinite;
}

/* ══════════════════════════════════════════════════════════════════
   JAUGE NEWS2
══════════════════════════════════════════════════════════════════ */
.gauge-container {
  background: var(--CARD);
  border-radius: var(--r);
  padding: 10px 14px;
  border: 1px solid var(--B);
  margin: 8px 0;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.gauge-val   { font-size: 2.2rem; font-weight: 900; font-family:'IBM Plex Mono',monospace; line-height:1; }
.gauge-label { font-size: .66rem; color: var(--TM); }

/* ══════════════════════════════════════════════════════════════════
   BARRE EVA
══════════════════════════════════════════════════════════════════ */
.eva-bar {
  display: flex;
  gap: 2px;
  margin: 4px 0 8px;
  border-radius: var(--r3);
  overflow: hidden;
}
.eva-cell {
  flex: 1;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'IBM Plex Mono', monospace;
  font-size: .7rem;
  font-weight: 600;
  border-radius: 3px;
  transition: transform .1s;
}
.eva-cell.active {
  transform: scaleY(1.15);
  box-shadow: 0 0 0 2px #0F172A;
  font-size: .75rem;
  z-index: 1;
  position: relative;
}

/* ══════════════════════════════════════════════════════════════════
   SBAR — Monospace DPI
══════════════════════════════════════════════════════════════════ */
.sbar-block {
  background: #0F172A;
  color: #94A3B8;
  border-radius: var(--r);
  padding: 14px 18px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: .68rem;
  line-height: 1.85;
  white-space: pre-wrap;
  border: 1px solid #1E293B;
  margin-top: 10px;
}

/* ══════════════════════════════════════════════════════════════════
   DISCLAIMER
══════════════════════════════════════════════════════════════════ */
.disclaimer {
  background: #0F172A;
  border: 1px solid #1E293B;
  border-radius: var(--r2);
  padding: 12px 16px;
  margin-top: 20px;
  font-size: .65rem;
  color: #64748B;
  line-height: 1.8;
  font-style: italic;
}
.disclaimer-title {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .58rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: .1em;
  margin-bottom: 6px;
}

/* ══════════════════════════════════════════════════════════════════
   ONGLETS Streamlit
══════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  gap: 2px !important;
  background: var(--BG2) !important;
  border-radius: var(--r2) !important;
  padding: 3px !important;
  margin-bottom: 8px !important;
}
.stTabs [data-baseweb="tab"] {
  font-size: .74rem !important;
  font-weight: 500 !important;
  padding: 6px 12px !important;
  border-radius: var(--r3) !important;
  color: var(--TM) !important;
  transition: all .15s ease !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: var(--CARD) !important;
  color: var(--PD) !important;
  font-weight: 700 !important;
  box-shadow: var(--s0) !important;
}

/* ══════════════════════════════════════════════════════════════════
   BOUTONS
══════════════════════════════════════════════════════════════════ */
.stButton > button {
  border-radius: var(--r2) !important;
  min-height: 42px !important;
  padding: 8px 16px !important;
  background: linear-gradient(135deg, var(--PD), var(--P)) !important;
  color: #fff !important;
  border: none !important;
  font-weight: 600 !important;
  font-size: .82rem !important;
  box-shadow: 0 4px 14px var(--P20) !important;
  transition: all .15s ease !important;
  letter-spacing: .01em !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, var(--P), var(--PL)) !important;
  box-shadow: 0 6px 18px var(--P20) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active {
  transform: translateY(0) !important;
  box-shadow: 0 2px 6px var(--P12) !important;
}
@media (max-width: 768px) {
  .stButton > button { min-height: 48px !important; font-size: .88rem !important; }
}

/* ══════════════════════════════════════════════════════════════════
   INPUTS — Champs numériques, textes
══════════════════════════════════════════════════════════════════ */
.stNumberInput input,
.stTextInput input {
  border-radius: var(--r3) !important;
  border: 1.5px solid var(--B2) !important;
  font-size: .88rem !important;
  padding: 6px 10px !important;
  background: var(--CARD) !important;
  color: var(--T) !important;
  transition: border-color .15s, box-shadow .15s !important;
}
.stNumberInput input:focus,
.stTextInput input:focus {
  border-color: var(--P) !important;
  box-shadow: 0 0 0 3px var(--P12) !important;
  outline: none !important;
}
@media (max-width: 768px) {
  .stNumberInput input, .stTextInput input { font-size: 16px !important; }
}

/* Selectbox */
[data-baseweb="select"] > div {
  border-radius: var(--r3) !important;
  border-color: var(--B2) !important;
  font-size: .86rem !important;
  min-height: 36px !important;
}
[data-baseweb="select"] > div:focus-within {
  border-color: var(--P) !important;
  box-shadow: 0 0 0 3px var(--P12) !important;
}

/* ══════════════════════════════════════════════════════════════════
   CHECKBOXES — Visibilité tablette renforcée (WCAG AA)
══════════════════════════════════════════════════════════════════ */
[data-testid="stCheckbox"] {
  padding: 5px 4px !important;
  border-radius: var(--r3) !important;
  transition: background .12s !important;
}
[data-testid="stCheckbox"]:hover {
  background: var(--P05) !important;
}
[data-testid="stCheckbox"] p {
  font-size: .84rem !important;
  font-weight: 500 !important;
  color: var(--T) !important;
  margin: 0 !important;
  line-height: 1.4 !important;
}
[data-testid="stCheckbox"] label {
  cursor: pointer !important;
  align-items: center !important;
  gap: 10px !important;
  display: flex !important;
}

/* Boîte visuelle — non cochée */
[data-baseweb="checkbox"] > label > div:first-child {
  border: 2px solid var(--B2) !important;
  border-radius: 4px !important;
  background: var(--CARD) !important;
  width: 18px !important;
  height: 18px !important;
  min-width: 18px !important;
  transition: all .12s ease !important;
}

/* Hover */
[data-testid="stCheckbox"]:hover [data-baseweb="checkbox"] > label > div:first-child {
  border-color: var(--P) !important;
  box-shadow: 0 0 0 3px var(--P12) !important;
}

/* Coché */
[data-baseweb="checkbox"][aria-checked="true"] > label > div:first-child {
  background: var(--P) !important;
  border-color: var(--P) !important;
  box-shadow: 0 0 0 2px var(--P12) !important;
}

/* Fallback navigateurs modernes */
input[type="checkbox"] {
  accent-color: var(--P) !important;
  width: 17px !important;
  height: 17px !important;
}

/* ══════════════════════════════════════════════════════════════════
   SLIDERS — Track, Thumb, Labels (tablette 44px min)
══════════════════════════════════════════════════════════════════ */
[data-testid="stSlider"] {
  padding: 4px 2px 10px !important;
}
[data-testid="stSlider"] > div > label,
[data-testid="stSlider"] > label {
  font-size: .72rem !important;
  font-weight: 600 !important;
  color: var(--TM) !important;
  text-transform: uppercase !important;
  letter-spacing: .06em !important;
  margin-bottom: 4px !important;
}

/* Track arrière-plan */
[data-baseweb="slider"] > div {
  height: 6px !important;
  border-radius: 3px !important;
  background: var(--B) !important;
}

/* Portion active */
[data-baseweb="slider"] [role="progressbar"] {
  height: 6px !important;
  border-radius: 3px !important;
  background: linear-gradient(90deg, var(--PD) 0%, var(--P) 60%, var(--PL) 100%) !important;
}

/* Thumb — 22px + halo focus WCAG */
[data-baseweb="slider"] [role="slider"] {
  width: 22px !important;
  height: 22px !important;
  background: var(--P) !important;
  border: 3px solid #fff !important;
  border-radius: 50% !important;
  box-shadow: 0 2px 8px var(--P20) !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  cursor: grab !important;
  transition: box-shadow .12s, transform .12s, background .12s !important;
}
[data-baseweb="slider"] [role="slider"]:hover,
[data-baseweb="slider"] [role="slider"]:focus {
  background: var(--PL) !important;
  box-shadow: 0 0 0 5px var(--P20), 0 2px 8px var(--P20) !important;
  transform: translateY(-50%) scale(1.12) !important;
}

/* Valeur courante */
[data-testid="stSlider"] p {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: .74rem !important;
  font-weight: 600 !important;
  color: var(--P) !important;
}

/* Tick min/max */
[data-testid="stTickBarMin"],
[data-testid="stTickBarMax"] {
  font-size: .6rem !important;
  color: var(--TS) !important;
  font-family: 'IBM Plex Mono', monospace !important;
}

/* ══════════════════════════════════════════════════════════════════
   MÉTRIQUES Streamlit
══════════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--BG2) !important;
  border: 1px solid var(--B) !important;
  border-radius: var(--r2) !important;
  padding: 10px 12px !important;
}
[data-testid="stMetricLabel"] p {
  font-size: .66rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: .08em !important;
  color: var(--TM) !important;
}
[data-testid="stMetricValue"] {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.4rem !important;
  font-weight: 800 !important;
  color: var(--T) !important;
}

/* ══════════════════════════════════════════════════════════════════
   EXPANDERS SIDEBAR — Compact
══════════════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  border: 1px solid var(--B) !important;
  border-radius: var(--r2) !important;
  margin-bottom: 6px !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  padding: 8px 12px !important;
  font-size: .78rem !important;
  font-weight: 600 !important;
  background: var(--BG2) !important;
}
[data-testid="stExpander"] summary:hover {
  background: var(--PP) !important;
}

/* ══════════════════════════════════════════════════════════════════
   FORM — Pas de bordure Streamlit
══════════════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
  border: 1px solid var(--B) !important;
  border-radius: var(--r2) !important;
  padding: 10px 12px !important;
  background: var(--BG2) !important;
}

/* ══════════════════════════════════════════════════════════════════
   SIDEBAR — Fond acier
══════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--BG2) !important;
  border-right: 1px solid var(--B) !important;
}
[data-testid="stSidebar"] .block-container {
  padding: .5rem .75rem 2rem !important;
}
"""
