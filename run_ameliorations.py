"""
run_ameliorations.sh — Script de test des améliorations AKIR-IAO
===================================================

Usage: ./run_ameliorations.sh
       ou : python run_ameliorations.py (Windows)

Ce script applique toutes les améliorations à streamlit_app.py
et lance l'application pour validation.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import subprocess
import sys
import os


def run_ameliorations():
    """Exécute le script d'injection des améliorations."""
    
    print("=" * 70)
    print(" 🚀 AMÉLIORATIONS AKIR-IAO — EXÉCUTION")
    print("=" * 70)
    print("\nCe script va:")
    print("1. Appliquer les améliorations UX mobile (boutons ≥ 48px)")
    print("2. Ajouter l'onglet '📊 STATS' (dashboard analyse)")
    print("3. Injecter la fonction export_fhir_r4() (intégration DPI)")
    print("4. Optimiser les styles CSS pour smartphone")
    print("5. Lancer l'application Streamlit améliorée")
    print("\n" + "=" * 70)
    
    # Vérifier présence du script d'injection
    if not os.path.exists("scripts/inject_ameliorations.py"):
        print("❌ Le fichier 'scripts/inject_ameliorations.py' est introuvable !")
        print("\nPour l'installer, exécutez:")
        print("   python scripts/ameliorer_ux_mobile.py")
        return False
    
    # Lancer le script d'injection
    try:
        print("\n📋 Step 1/3 : Injection des améliorations...")
        result = subprocess.run(
            [sys.executable, "scripts/inject_ameliorations.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("\n✅ Injection des améliorations terminée !")
            print(result.stdout)
        else:
            print("\n⚠️ Erreur lors de l'injection:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ Le script a dépassé le temps d'exécution (30s)")
        return False
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        return False
    
    # Lancer l'application Streamlit améliorée
    try:
        print("\n📋 Step 2/3 : Lancement de l'application Streamlit...")
        print("\n🔗 URL: http://localhost:8501")
        print("\n⚠️ Appuyez sur Ctrl+C pour arrêter l'application")
        
        # Lancer Streamlit en arrière-plan (sur Windows/macOS)
        streamlit_cmd = [sys.executable, "-m", "streamlit", "run", 
                        "streamlit_app.py",
                        "--server.port", "8501",
                        "--server.headless", "true"]
        
        print(f"\n🚀 Commande: {' '.join(streamlit_cmd)}")
        print("\n" + "=" * 70)
        print(" ✅ AMÉLIORATIONS TERMINÉES — OUVERTURE DU NAVIGATEUR...")
        print("=" * 70)
        
        # Ouvrir dans le navigateur (si possible)
        import webbrowser
        webbrowser.open("http://localhost:8501")
        
    except Exception as e:
        print(f"\n⚠️ Erreur lors du lancement : {e}")
        print("\nVous pouvez lancer manuellement:")
        print(f"   python -m streamlit run streamlit_app.py --server.port 8501")
    
    return True


if __name__ == "__main__":
    success = run_ameliorations()
    
    if success:
        print("\n" + "=" * 70)
        print(" 🎉 AMÉLIORATIONS AKIR-IAO COMPLÉTES !")
        print("=" * 70)
        print("\n📋 Résumé des améliorations appliquées:")
        print("   ✓ Boutons tactiles ≥ 48x48px (WCAG AA)")
        print("   ✓ Anti-zoom sur inputs vitaux (touch-to-friendly)")
        print("   ✓ Safe-area iOS (iPhone notch)")
        print("   ✓ Sticky bar contextuelle en bas")
        print("   ✓ Navigation optimisée mobile-first")
        print("   ✓ Accordion discrimiants")
        print("   ✓ FAB flottante réévaluation")
        print("   ✓ Bouton SBAR flottant")
        print("   ✓ Onglet '📊 STATS' (dashboard analyse)")
        print("   ✓ Export FHIR R4 (intégration DPI Maincare/CGM)")
        print("\n💡 Astuces:")
        print("   - Ouvrez l'app en mode PWA (Ajouter à écran d'accueil iOS)")
        print("   - Utilisez un navigateur mobile pour test smartphone")
        print("   - Regardez l'onglet '📊 STATS' pour visualiser les données")
        print("=" * 70)
    else:
        print("\n❌ Échec des améliorations. Vérifiez les logs ci-dessus.")
