"""
Package UI pour AKIR-IAO.
Regroupe les composants Streamlit pour la saisie, l'affichage et l'administration.
"""

import streamlit as st

def set_page_config():
    """Configure le style global de l'application."""
    st.set_page_config(
        page_title="AKIR-IAO | Triage Urgences",
        page_icon="🚑",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def inject_custom_css():
    """Injecte du CSS pour améliorer le rendu des niveaux de triage."""
    st.markdown("""
        <style>
        .triage-1 { background-color: #ff4b4b; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
        .triage-2 { background-color: #ffa500; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
        .triage-3 { background-color: #ffff00; color: black; padding: 10px; border-radius: 5px; font-weight: bold; }
        .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
        </style>
    """, unsafe_allow_html=True)
