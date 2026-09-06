@echo off
setlocal EnableExtensions
REM ══════════════════════════════════════════════════════════════════════════
REM  AKIR-IAO — Lanceur local sécurisé (poste de triage)
REM  100 % local : télémétrie off, localhost uniquement, NLP cloud off.
REM  Double-cliquer sur ce fichier suffit.
REM ══════════════════════════════════════════════════════════════════════════
cd /d "%~dp0"

REM ── Durcissement : aucune donnée ne quitte ce poste ─────────────────────────
set AKIR_ALLOW_CLOUD_NLP=0
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_ADDRESS=localhost

REM ── Vérification rapide de l'environnement ──────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [AKIR-IAO] Python introuvable. Installez Python 3.10+ et relancez.
    pause
    exit /b 1
)

REM ── Ouverture du navigateur (serveur sur localhost:8501) ───────────────────
start "" "http://localhost:8501"

REM ── Démarrage de l'application ──────────────────────────────────────────────
python -m streamlit run streamlit_app.py
if errorlevel 1 (
    echo.
    echo [AKIR-IAO] Le démarrage de l'application a echoue.
    echo Verifiez :
    echo   1. python -m pip install -r requirements.txt
    echo   2. git lfs pull          (restaurer les poids ML/ECG)
    echo   3. python -m pytest tests -q  (diagnostic)
    echo.
    pause
)
endlocal
exit /b 0
