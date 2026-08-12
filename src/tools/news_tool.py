"""
News Tool
=========
Récupère des titres d'actualité financière via des flux RSS gratuits
(feedparser, sans clé API).

Fonction publique :
    - get_financial_news() -> list[dict]

Robustesse : si un flux RSS est indisponible ou vide, il est simplement
ignoré. L'agent ne plante jamais à cause d'une source d'actualité.
"""

import socket
from typing import List, Optional

import feedparser

from src import config
from src.utils.logging import warn


def _entry_date(entry) -> Optional[str]:
    """Retourne la date de publication de l'entrée si disponible."""
    for key in ("published", "updated", "created"):
        value = getattr(entry, key, None)
        if value:
            return value
    return None


def get_financial_news(max_items: int = config.MAX_NEWS_ITEMS) -> List[dict]:
    """
    Récupère les titres récents depuis tous les flux RSS configurés.

    Chaque news retournée contient :
        - title  : titre
        - source : nom du flux
        - link   : lien
        - date   : date de publication (si disponible)

    Le résultat est dédoublonné (par titre) et limité à `max_items`.
    """
    # Évite qu'un flux lent bloque tout le programme.
    socket.setdefaulttimeout(10)

    collected: List[dict] = []

    for feed in config.RSS_FEEDS:
        name = feed.get("name", "RSS")
        url = feed.get("url", "")
        try:
            parsed = feedparser.parse(url)
            entries = getattr(parsed, "entries", []) or []

            if not entries:
                warn(f"Flux RSS vide ou inaccessible : {name} — ignoré.")
                continue

            for entry in entries[: config.MAX_NEWS_PER_FEED]:
                title = (getattr(entry, "title", "") or "").strip()
                if not title:
                    continue
                collected.append(
                    {
                        "title": title,
                        "source": name,
                        "link": getattr(entry, "link", "") or "",
                        "date": _entry_date(entry),
                    }
                )

        except Exception as exc:  # noqa: BLE001 - un flux HS ne doit rien casser
            warn(f"Erreur sur le flux RSS {name} : {exc} — ignoré.")
            continue

    # Dédoublonnage par titre (insensible à la casse).
    seen = set()
    unique: List[dict] = []
    for item in collected:
        key = item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    if not unique:
        warn("Aucune actualité récupérée (tous les flux indisponibles).")

    return unique[:max_items]
