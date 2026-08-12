"""
Telegram Tool
=============
Envoie le rapport de marché sur Telegram à chaque exécution de l'agent.

Fonction publique :
    - send_report_telegram(summary, report_path, data) -> bool

Utilise l'API Bot de Telegram (gratuite) :
    - sendMessage  : le résumé (découpé en morceaux < 4096 caractères) ;
    - sendDocument : le rapport Markdown complet en pièce jointe.

Robustesse : si Telegram n'est pas configuré (token / chat_id absents) ou si
l'envoi échoue, l'étape est simplement ignorée. L'agent ne plante jamais.

Configuration requise (voir README) :
    - TELEGRAM_BOT_TOKEN : jeton fourni par @BotFather
    - TELEGRAM_CHAT_ID   : identifiant de la conversation cible
"""

import os
from typing import List, Optional

import requests

from src import config
from src.utils.logging import info, warn

_API = "https://api.telegram.org/bot{token}/{method}"
# Marge de sécurité sous la limite Telegram (4096 caractères par message).
_MAX_LEN = 4000


def _chunks(text: str, size: int = _MAX_LEN) -> List[str]:
    """Découpe un texte long en morceaux <= size, en respectant les paragraphes."""
    parts: List[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            parts.append(current)
            current = ""
        # Un paragraphe seul plus long que la limite : découpe "dure".
        while len(paragraph) > size:
            parts.append(paragraph[:size])
            paragraph = paragraph[size:]
        current = paragraph
    if current:
        parts.append(current)
    return parts


def _send_message(text: str) -> None:
    url = _API.format(token=config.TELEGRAM_BOT_TOKEN, method="sendMessage")
    resp = requests.post(
        url,
        data={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code} sur sendMessage : {resp.text}")


def _send_document(report_path: Optional[str]) -> None:
    if not report_path or not os.path.exists(report_path):
        return
    url = _API.format(token=config.TELEGRAM_BOT_TOKEN, method="sendDocument")
    with open(report_path, "rb") as f:
        resp = requests.post(
            url,
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "caption": "Rapport complet (Markdown) — analyse éducative.",
            },
            files={"document": (os.path.basename(report_path), f, "text/markdown")},
            timeout=60,
        )
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code} sur sendDocument : {resp.text}")


def send_report_telegram(
    summary: str,
    report_path: Optional[str] = None,
    data: Optional[dict] = None,
) -> bool:
    """
    Envoie le rapport sur Telegram.

    Retourne True si l'envoi a réussi, False sinon (non configuré ou erreur).
    Ne lève jamais d'exception vers l'appelant.
    """
    if not config.TELEGRAM_ENABLED:
        info("Telegram non configuré (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) — envoi ignoré.")
        return False

    try:
        when = (data or {}).get("generated_at_human", "")
        header = f"📊 Market Brief — {when}".strip()
        body = (
            f"{header}\n\n"
            f"{summary}\n\n"
            "⚠️ Analyse éducative — ne constitue pas un conseil financier."
        )

        info("Envoi de la notification Telegram...")
        for chunk in _chunks(body):
            _send_message(chunk)
        _send_document(report_path)

        info(f"Notification Telegram envoyée (chat {config.TELEGRAM_CHAT_ID}).")
        return True

    except Exception as exc:  # noqa: BLE001 - un échec Telegram ne doit rien casser
        warn(f"Envoi Telegram échoué ({exc}) — étape ignorée, le rapport reste disponible.")
        return False
