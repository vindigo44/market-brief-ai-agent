"""
Email Tool
==========
Envoie le rapport de marché par email à chaque exécution de l'agent.

Fonction publique :
    - send_report_email(subject, summary, report_path, data) -> bool

Fonctionne avec n'importe quel serveur SMTP (Gmail par défaut). Aucune
dépendance externe : on utilise smtplib / email de la bibliothèque standard.

Robustesse : si l'email n'est pas configuré (pas d'identifiants SMTP) ou si
l'envoi échoue, l'étape est simplement ignorée. L'agent ne plante jamais.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from src import config
from src.utils.logging import info, warn


def _build_message(subject: str, summary: str, report_path: Optional[str]) -> EmailMessage:
    """Construit l'email : corps texte (résumé) + rapport Markdown en pièce jointe."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = ", ".join(config.EMAIL_TO_LIST)

    body = (
        f"{summary}\n\n"
        "-----\n"
        "Le rapport complet (tableaux, signaux, news) est en pièce jointe.\n"
        "Analyse éducative — ne constitue pas un conseil financier.\n"
        "Généré automatiquement par Market Brief AI Agent."
    )
    msg.set_content(body)

    # Pièce jointe : le rapport Markdown complet.
    if report_path and os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            msg.add_attachment(
                content.encode("utf-8"),
                maintype="text",
                subtype="markdown",
                filename=os.path.basename(report_path),
            )
        except OSError as exc:
            warn(f"Impossible de joindre le rapport ({exc}) — email envoyé sans pièce jointe.")

    return msg


def send_report_email(
    subject: str,
    summary: str,
    report_path: Optional[str] = None,
    data: Optional[dict] = None,
) -> bool:
    """
    Envoie le rapport par email.

    Retourne True si l'email est parti, False sinon (non configuré ou erreur).
    Ne lève jamais d'exception vers l'appelant.
    """
    if not config.EMAIL_ENABLED:
        info("Email non configuré (SMTP_USER / SMTP_PASSWORD / destinataire) — envoi ignoré.")
        return False

    try:
        message = _build_message(subject, summary, report_path)
        context = ssl.create_default_context()

        info(f"Envoi de l'email via {config.SMTP_HOST}:{config.SMTP_PORT}...")
        if config.SMTP_PORT == 465:
            # SSL direct
            with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=context, timeout=30) as server:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.send_message(message)
        else:
            # STARTTLS (cas Gmail sur le port 587)
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.send_message(message)

        info(f"Email envoyé à : {', '.join(config.EMAIL_TO_LIST)}")
        return True

    except Exception as exc:  # noqa: BLE001 - un échec d'email ne doit rien casser
        warn(f"Envoi de l'email échoué ({exc}) — étape ignorée, le rapport reste disponible.")
        return False
