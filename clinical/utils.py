# clinical/utils.py — Fonctions utilitaires partagées
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
import unicodedata

def norm(value) -> str:
    """Normalise une chaîne pour comparaison insensible à la casse, accents, espaces."""
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())
