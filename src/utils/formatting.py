"""
Fonctions de formatage pour l'affichage (prix, pourcentages, volumes).
Centralisées ici pour garder un rendu homogène dans tout le rapport.
"""

from typing import Optional


def fmt_pct(value: Optional[float]) -> str:
    """Formate un pourcentage avec signe, ex: +1.23% / -0.50% / N/A."""
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def fmt_price(value: Optional[float]) -> str:
    """Formate un prix, ex: 1 234.56 / N/A."""
    if value is None:
        return "N/A"
    return f"{value:,.2f}".replace(",", " ")


def fmt_volume(value: Optional[float]) -> str:
    """Formate un volume en entier lisible, ex: 12 345 678 / N/A."""
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return "N/A"


def trend_label(trend: Optional[str]) -> str:
    """Traduit la tendance interne en libellé français lisible."""
    return {
        "bullish": "haussière",
        "bearish": "baissière",
        "neutral": "neutre",
    }.get(trend, "neutre")


def trend_icon(trend: Optional[str]) -> str:
    """Petite pastille visuelle pour la tendance."""
    return {
        "bullish": "🟢",
        "bearish": "🔴",
        "neutral": "⚪",
    }.get(trend, "⚪")
