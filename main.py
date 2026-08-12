"""
Point d'entrée du Market Brief AI Agent.

Usage :
    python main.py
"""

import sys

# Force l'UTF-8 en sortie console (utile sous Windows pour les accents/emojis).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from src.agent.market_brief_agent import run_market_brief_agent

if __name__ == "__main__":
    run_market_brief_agent()
