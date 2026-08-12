"""
Market Brief Agent
==================
Orchestre l'ensemble : c'est le "cerveau" qui enchaîne les outils (tools)
dans un ordre précis pour transformer des données brutes en rapport final.

Fonction publique :
    - run_market_brief_agent() -> dict

C'est cette séquence "données + tools + LLM + automatisation" qui fait de ce
programme un véritable agent IA, et pas un simple appel à un modèle.
"""

from datetime import datetime
from typing import Dict, List

from src import config
from src.tools.email_tool import send_report_email
from src.tools.gemini_tool import generate_market_summary
from src.tools.indicators_tool import calculate_market_indicators
from src.tools.market_data_tool import get_market_history
from src.tools.news_tool import get_financial_news
from src.tools.report_tool import save_markdown_report
from src.utils.logging import info, log, step


def _group(per_ticker: Dict[str, dict], mapping: Dict[str, str]) -> List[dict]:
    """Extrait, dans l'ordre du mapping, les actifs exploitables d'un groupe."""
    items: List[dict] = []
    for ticker in mapping:
        entry = per_ticker.get(ticker)
        if entry and entry.get("ok"):
            items.append(entry)
    return items


def run_market_brief_agent() -> dict:
    """
    Exécute le pipeline complet de l'agent et retourne un dict :
        {
          "report_path": chemin du rapport latest,
          "summary": texte du résumé,
          "payload": données structurées utilisées,
        }
    """
    log("=" * 64)
    log("  Market Brief AI Agent — analyse éducative de marché")
    log("=" * 64)

    all_tickers = list(config.ALL_TICKERS.keys())

    # [1/7] Données de marché
    step(1, 7, "Récupération des données marché...")
    market_data = get_market_history(all_tickers, period=config.HISTORY_PERIOD)
    ok_count = sum(1 for d in market_data.values() if d.get("ok"))
    info(f"{ok_count}/{len(all_tickers)} tickers récupérés avec succès.")

    # [2/7] Indicateurs
    step(2, 7, "Calcul des indicateurs...")
    indicators = calculate_market_indicators(market_data)
    per_ticker = indicators["per_ticker"]
    info(
        f"{len(indicators['positive_signals'])} signaux positifs, "
        f"{len(indicators['negative_signals'])} signaux négatifs, "
        f"{len(indicators['risks'])} risques."
    )

    # [3/7] News
    step(3, 7, "Récupération des news...")
    news = get_financial_news()
    info(f"{len(news)} actualités récupérées.")

    # Construction du payload structuré (partagé par Gemini et le rapport).
    generated_at = datetime.now().astimezone()
    payload = {
        "generated_at": generated_at.isoformat(),
        "generated_at_human": generated_at.strftime("%Y-%m-%d %H:%M (%Z)"),
        "language": config.REPORT_LANGUAGE,
        "us": {
            "indices": _group(per_ticker, config.US_INDICES),
            "watchlist": _group(per_ticker, config.US_WATCHLIST),
        },
        "eu": {
            "indices": _group(per_ticker, config.EU_INDICES),
            "watchlist": _group(per_ticker, config.EU_WATCHLIST),
        },
        "positive_signals": indicators["positive_signals"],
        "negative_signals": indicators["negative_signals"],
        "risks": indicators["risks"],
        "news": news,
    }

    # [4/7] Résumé IA (Gemini ou fallback)
    step(4, 7, "Génération du résumé avec Gemini...")
    summary = generate_market_summary(payload)

    # [5/7] Sauvegarde du rapport
    step(5, 7, "Sauvegarde du rapport...")
    report_path = save_markdown_report(summary, payload)
    info(f"Rapport principal : {report_path}")

    # [6/7] Envoi de l'email (si configuré ; sinon étape ignorée sans erreur)
    step(6, 7, "Envoi du rapport par email...")
    subject = f"📊 Market Brief — {payload['generated_at_human']}"
    email_sent = send_report_email(subject, summary, report_path, payload)

    # [7/7] Terminé
    step(7, 7, "Terminé.")
    log("=" * 64)

    return {
        "report_path": report_path,
        "summary": summary,
        "payload": payload,
        "email_sent": email_sent,
    }
