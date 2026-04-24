def load_css():
    return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap');
    :root {
      --P: #004A99; --PL: #1A69B8; --PD: #002F66; --PP: #EBF3FD;
      --BG: #F8F9FA; --CARD: #FFFFFF; --B: #E2E8F0;
      --T: #1A202C; --TM: #64748B; --TW: #FFFFFF;
      --TM-bg: #1A0A2E; --TM-ac: #E879F9;
      --T1-bg: #7F1D1D; --T1-ac: #FCA5A5;
      --T2-bg: #78350F; --T2-ac: #FDE68A;
      --T3A-bg:#1E3A5F; --T3A-ac:#93C5FD;
      --T3B-bg:#1E3A5F; --T3B-ac:#BAE6FD;
      --T4-bg: #14532D; --T4-ac: #86EFAC;
      --T5-bg: #334155; --T5-ac: #CBD5E1;
      --ERR: #FEF2F2; --ERR-b: #EF4444; --ERR-t: #B91C1C;
      --WRN: #FFFBEB; --WRN-b: #F59E0B; --WRN-t: #92400E;
      --SUC: #F0FDF4; --SUC-b: #22C55E; --SUC-t: #166534;
      --INF: #EFF6FF; --INF-b: #3B82F6; --INF-t: #1D4ED8;
      --s1: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
      --s2: 0 4px 12px rgba(0,74,153,.12);
      --s3: 0 8px 24px rgba(0,74,153,.18);
      --r: 12px; --r2: 8px;
    }
    *, *::before, *::after { box-sizing: border-box; }
    #MainMenu, footer, header, [data-testid="stToolbar"] { display:none!important; }
    .block-container { padding: .75rem 1rem 4rem!important; max-width: 860px; margin: 0 auto; }
    html, body, [class*="st-"] {
      font-family: 'Inter', -apple-system, sans-serif;
      color: var(--T); background: var(--BG);
    }
    .app-hdr {
      background: linear-gradient(130deg, var(--PD) 0%, var(--P) 55%, var(--PL) 100%);
      border-radius: var(--r); padding: 18px 22px 16px; margin-bottom: 18px;
      box-shadow: var(--s3); position: relative; overflow: hidden;
    }
    .app-hdr-title { font-size:1.2rem; font-weight:800; color:#fff; }
    .app-hdr-sub   { font-size:.72rem; color:rgba(255,255,255,.75); margin-top:3px; }
    .app-hdr-tags  { margin-top:10px; display:flex; gap:6px; flex-wrap:wrap; }
    .tag { background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.28);
           color:#fff; font-size:.62rem; font-weight:600; padding:2px 9px;
           border-radius:20px; letter-spacing:.04em; }
    .card { background:var(--CARD); border:1px solid var(--B);
            border-radius:var(--r); padding:16px 18px; margin-bottom:14px; box-shadow:var(--s1); }
    .card-title { font-size:.63rem; font-weight:700; letter-spacing:.1em;
                  text-transform:uppercase; color:var(--P);
                  border-bottom:2px solid var(--PP); padding-bottom:8px; margin-bottom:12px; }
    .card-icon { width:32px; height:32px; border-radius:8px;
                 background:var(--PP); display:flex; align-items:center;
                 justify-content:center; font-size:1rem; }
    .sec { font-size:.6rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
           color:var(--P); border-bottom:2px solid var(--PP); padding-bottom:5px; margin:16px 0 10px; }
    .al { border-radius:var(--r2); padding:11px 14px; margin:7px 0;
          font-size:.82rem; font-weight:500; line-height:1.5; display:flex; align-items:flex-start; gap:9px;
          border-left:4px solid; }
    .al.danger  { background:var(--ERR); border-color:var(--ERR-b); color:var(--ERR-t); }
    .al.warning { background:var(--WRN); border-color:var(--WRN-b); color:var(--WRN-t); }
    .al.success { background:var(--SUC); border-color:var(--SUC-b); color:var(--SUC-t); }
    .al.info    { background:var(--INF); border-color:var(--INF-b); color:var(--INF-t); }
    .n2-dash { border-radius:var(--r); padding:18px 20px; text-align:center; border:2px solid; margin-bottom:14px; }
    .n2-0 { background:#F0FDF4; border-color:#22C55E; }
    .n2-1 { background:#F0FDF4; border-color:#22C55E; }
    .n2-2 { background:#FEFCE8; border-color:#EAB308; }
    .n2-3 { background:#FFF7ED; border-color:#F97316; }
    .n2-4 { background:#FFF1F2; border-color:#F43F5E; }
    .n2-5 { background:#FAF5FF; border-color:#7C3AED; }
    .n2-big { font-family:'JetBrains Mono',monospace; font-size:3.5rem; font-weight:700; line-height:1; margin:6px 0 2px; }
    .n2-0 .n2-big, .n2-1 .n2-big { color:#16A34A; }
    .n2-2 .n2-big { color:#CA8A04; } .n2-3 .n2-big { color:#EA580C; }
    .n2-4 .n2-big { color:#E11D48; } .n2-5 .n2-big { color:#7C3AED; }
    .vit-wrap { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:10px 0; }
    .vit { background:var(--CARD); border:1.5px solid var(--B); border-radius:var(--r2);
           padding:10px 12px; text-align:center; box-shadow:var(--s1); }
    .vit.warn { border-color:#F59E0B; background:#FFFBEB; }
    .vit.crit { border-color:#EF4444; background:#FEF2F2; }
    .vit-k { font-size:.58rem; font-weight:600; text-transform:uppercase; color:var(--TM); }
    .vit-v { font-family:'JetBrains Mono',monospace; font-size:1.25rem; font-weight:700; }
    .tri-banner-wrap { position:fixed; bottom:0; left:0; right:0; z-index:999; }
    .tri-banner { padding:14px 20px; display:flex; align-items:center;
                  justify-content:space-between; flex-wrap:wrap; gap:8px; }
    .tri-M { background:var(--TM-bg); } .tri-1 { background:var(--T1-bg); }
    .tri-2 { background:var(--T2-bg); } .tri-3A { background:var(--T3A-bg); }
    .tri-3B { background:var(--T3B-bg); } .tri-4 { background:var(--T4-bg); }
    .tri-5 { background:var(--T5-bg); }
    .tri-niv { font-family:'JetBrains Mono',monospace; font-size:1.1rem; font-weight:800; }
    .tri-M .tri-niv { color:var(--TM-ac); } .tri-1 .tri-niv { color:var(--T1-ac); }
    .tri-2 .tri-niv { color:var(--T2-ac); } .tri-3A .tri-niv { color:var(--T3A-ac); }
    .tri-3B .tri-niv { color:var(--T3B-ac); } .tri-4 .tri-niv { color:var(--T4-ac); }
    .tri-5 .tri-niv { color:var(--T5-ac); }
    .si-box { background:var(--CARD); border:1.5px solid var(--B); border-radius:var(--r2);
              padding:12px 16px; text-align:center; }
    .si-v { font-family:'JetBrains Mono',monospace; font-size:1.8rem; font-weight:700; }
    .si-ok { color:#22C55E; } .si-w { color:#F59E0B; } .si-c { color:#EF4444; }
    .disc { background:#F8FAFC; border:1px solid var(--B); border-top:3px solid var(--P);
            border-radius:var(--r2); padding:12px 16px; margin-top:24px;
            font-size:.64rem; color:var(--TM); line-height:1.8; }
    """
