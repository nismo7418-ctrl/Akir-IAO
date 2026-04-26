# ui/styles.py — CSS Design Médical Professionnel — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Design : Interface médicale claire, contrastes WCAG AAA, mobile-first

def load_css() -> str:
    return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --P: #004A99; --PL: #1A69B8; --PD: #002F66; --PP: #EBF3FD;
  --BG: #F0F4F8; --CARD: #FFFFFF; --B: #E2E8F0;
  --T: #1A202C; --TM: #4A5568; --TW: #FFFFFF;
  /* Triage colors */
  --TM-bg: #7F1D1D; --TM-ac: #FECACA; --TM-t: #FEF2F2;
  --T1-bg: #B91C1C; --T1-ac: #FECACA; --T1-t: #FEF2F2;
  --T2-bg: #C2410C; --T2-ac: #FED7AA; --T2-t: #FFF7ED;
  --T3A-bg:#075985; --T3A-ac:#BAE6FD; --T3A-t:#F0F9FF;
  --T3B-bg:#1D4ED8; --T3B-ac:#DBEAFE; --T3B-t:#EFF6FF;
  --T4-bg: #1E40AF; --T4-ac: #DBEAFE; --T4-t:#EFF6FF;
  --T5-bg: #334155; --T5-ac: #E2E8F0; --T5-t:#F8FAFC;
  --ERR-bg:#FEF2F2; --ERR:#EF4444; --ERR-t:#B91C1C;
  --WRN-bg:#FFFBEB; --WRN:#F59E0B; --WRN-t:#92400E;
  --SUC-bg:#F0FDF4; --SUC:#22C55E; --SUC-t:#166534;
  --INF-bg:#EFF6FF; --INF:#3B82F6; --INF-t:#1D4ED8;
  --r:12px; --r2:8px;
  --s1:0 1px 3px rgba(0,0,0,.08);
  --s2:0 4px 12px rgba(0,74,153,.12);
  --s3:0 8px 24px rgba(0,74,153,.18);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; }
#MainMenu, footer, header, [data-testid="stToolbar"] { display:none!important; }
.block-container { padding:.75rem 1rem 4rem!important; max-width:900px; margin:0 auto; }

html, body, [class*="st-"] {
  font-family:'Inter',-apple-system,sans-serif;
  color:var(--T); background:var(--BG);
}

/* ── EN-TÊTE ─────────────────────────────────────────────────────────── */
.app-hdr {
  background:linear-gradient(130deg,var(--PD) 0%,var(--P) 55%,var(--PL) 100%);
  border-radius:14px; padding:18px 20px; margin-bottom:16px;
  box-shadow:var(--s3);
}
.app-hdr-title {
  font-size:1.2rem; font-weight:800; color:#fff; letter-spacing:-.02em;
  font-family:'IBM Plex Mono',monospace;
}
.app-hdr-sub { font-size:.72rem; color:rgba(255,255,255,.75); margin-top:2px; }
.app-hdr-tags { display:flex; gap:6px; flex-wrap:wrap; margin-top:10px; }
.tag {
  background:rgba(255,255,255,.15); color:#fff; font-size:.58rem;
  padding:2px 8px; border-radius:20px; font-family:'IBM Plex Mono',monospace;
  letter-spacing:.06em; border:1px solid rgba(255,255,255,.25);
}

/* ── CARTES ──────────────────────────────────────────────────────────── */
.card {
  background:var(--CARD); border-radius:var(--r); padding:16px 18px;
  box-shadow:var(--s1); border:1px solid var(--B); margin-bottom:12px;
}
.card-title {
  font-size:.7rem; font-weight:600; text-transform:uppercase;
  letter-spacing:.1em; color:var(--TM); margin-bottom:12px;
  font-family:'IBM Plex Mono',monospace;
}

/* ── ALERTES ─────────────────────────────────────────────────────────── */
.al { border-radius:0 6px 6px 0; padding:9px 14px; margin:6px 0; font-size:.78rem; font-weight:500; line-height:1.6; }
.al.danger  { background:var(--ERR-bg); border-left:4px solid var(--ERR); color:var(--ERR-t); }
.al.warning { background:var(--WRN-bg); border-left:4px solid var(--WRN); color:var(--WRN-t); }
.al.success { background:var(--SUC-bg); border-left:4px solid var(--SUC); color:var(--SUC-t); }
.al.info    { background:var(--INF-bg); border-left:4px solid var(--INF); color:var(--INF-t); }

/* ── NIVEAUX DE TRIAGE ───────────────────────────────────────────────── */
.tri-M,  .hb-M  { background:var(--TM-bg)!important;  color:var(--TM-ac)!important; }
.tri-1,  .hb-1  { background:var(--T1-bg)!important;  color:var(--T1-ac)!important; }
.tri-2,  .hb-2  { background:var(--T2-bg)!important;  color:var(--T2-ac)!important; }
.tri-3A, .hb-3A { background:var(--T3A-bg)!important; color:var(--T3A-ac)!important; }
.tri-3B, .hb-3B { background:var(--T3B-bg)!important; color:var(--T3B-ac)!important; }
.tri-4,  .hb-4  { background:var(--T4-bg)!important;  color:var(--T4-ac)!important; }
.tri-5,  .hb-5  { background:var(--T5-bg)!important;  color:var(--T5-ac)!important; }

/* Carte de triage principale */
.tri-card {
  border-radius:var(--r); padding:20px; margin:12px 0;
  text-align:left; box-shadow:var(--s2);
}
.tri-label { font-size:1.6rem; font-weight:900; letter-spacing:-.02em; }
.tri-just  { font-size:.8rem; margin-top:8px; opacity:.9; line-height:1.5; }
.tri-delay { font-size:.68rem; margin-top:10px; opacity:.82; font-family:'IBM Plex Mono',monospace; }

/* ── NEWS2 BANNERS ───────────────────────────────────────────────────── */
.n2-alert {
  border-radius:10px; padding:12px 16px; margin:8px 0;
  font-weight:700; font-size:.82rem; text-align:center;
}
.n2-m    { background:#4C1D95; color:#E879F9; border:2px solid #7C3AED; }
.n2-crit { background:#7F1D1D; color:#FCA5A5; border:2px solid #EF4444; }

@keyframes pulse {
  0%,100%{opacity:1;transform:scale(1)}
  50%{opacity:.85;transform:scale(1.01)}
}
.n2-m { animation:pulse 1.5s infinite; }

/* ── VITAUX DASHBOARD ────────────────────────────────────────────────── */
.vitaux-grid {
  display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:10px 0;
}
.vital-box {
  background:var(--CARD); border:1px solid var(--B); border-radius:var(--r2);
  padding:10px; text-align:center;
}
.vital-label { font-size:.58rem; color:var(--TM); text-transform:uppercase; letter-spacing:.08em; }
.vital-val   { font-size:1.3rem; font-weight:700; font-family:'IBM Plex Mono',monospace; }
.vital-ok    { color:#22C55E; }
.vital-warn  { color:#F59E0B; }
.vital-crit  { color:#EF4444; }

/* ── PHARMACOLOGIE ───────────────────────────────────────────────────── */
.rx {
  border-radius:0 10px 10px 0; padding:12px 16px;
  background:#F8FAFC; margin:8px 0; border-left:4px solid var(--P);
}

/* ── SBAR ────────────────────────────────────────────────────────────── */
.sbar-block {
  background:#0F172A; color:#94A3B8; border-radius:var(--r);
  padding:16px 20px; font-family:'IBM Plex Mono',monospace;
  font-size:.7rem; line-height:1.9; white-space:pre-wrap;
  border:1px solid #1E293B; margin-top:12px;
}

/* ── DISCLAIMER ──────────────────────────────────────────────────────── */
.disclaimer {
  background:#0F172A; border:1px solid #1E293B; border-radius:10px;
  padding:14px 18px; margin-top:28px; font-size:.68rem;
  color:#64748B; line-height:1.9; font-style:italic;
}
.disclaimer-title {
  font-family:'IBM Plex Mono',monospace; font-size:.6rem; font-weight:600;
  color:#475569; text-transform:uppercase; letter-spacing:.1em; margin-bottom:8px;
}

/* ── MOBILE OPTIMISATION ─────────────────────────────────────────────── */
@media (max-width:768px) {
  .vitaux-grid { grid-template-columns:repeat(2,1fr); }
  .tri-label   { font-size:1.3rem; }
  .block-container { padding:.5rem .75rem 3rem!important; }
  button { min-height:44px!important; font-size:.9rem!important; }
  .stButton>button { min-height:48px!important; border-radius:10px!important; font-weight:600!important; }
}

/* ── FORMULAIRES ─────────────────────────────────────────────────────── */
.stNumberInput input, .stTextInput input, .stSelectbox select {
  border-radius:8px!important; font-size:.9rem!important;
}
.stCheckbox { padding:4px 0!important; }
.stTabs [data-baseweb="tab"] { font-size:.78rem!important; padding:6px 12px!important; }

/* ── JAUGE NEWS2 ─────────────────────────────────────────────────────── */
.gauge-container { 
  background:var(--CARD); border-radius:var(--r); padding:14px;
  border:1px solid var(--B); margin:10px 0; text-align:center;
}
.gauge-val {
  font-size:2.5rem; font-weight:900; font-family:'IBM Plex Mono',monospace;
}
.gauge-label { font-size:.72rem; color:var(--TM); margin-top:4px; }
"""
