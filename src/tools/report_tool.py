"""
Report Tool
===========
Assemble et sauvegarde le rapport final en Markdown.

Fonction publique :
    - save_markdown_report(summary, data) -> str  (chemin du rapport "latest")

Deux fichiers sont écrits :
    - reports/latest-market-brief.md          (toujours à jour)
    - reports/market-brief-YYYY-MM-DD-HH-MM.md (archive horodatée)
"""

import os
from datetime import datetime
from typing import List

from src import config
from src.utils.formatting import (
    fmt_pct,
    fmt_price,
    fmt_volume,
    trend_icon,
    trend_label,
)
from src.utils.logging import info


def _asset_table(assets: List[dict]) -> str:
    """Construit un tableau Markdown pour une liste d'actifs."""
    header = (
        "| Actif | Dernier | 1j | 5j | 1 mois | Tendance | Volume |\n"
        "| --- | ---: | ---: | ---: | ---: | :---: | ---: |\n"
    )
    if not assets:
        return header + "| _Données indisponibles_ | | | | | | |\n"

    rows = []
    for a in assets:
        rows.append(
            "| {name} ({ticker}) | {price} | {d1} | {d5} | {d30} | {trend} | {vol} |".format(
                name=a.get("name", ""),
                ticker=a.get("ticker", ""),
                price=fmt_price(a.get("last_price")),
                d1=fmt_pct(a.get("change_1d")),
                d5=fmt_pct(a.get("change_5d")),
                d30=fmt_pct(a.get("change_1mo")),
                trend=f"{trend_icon(a.get('trend'))} {trend_label(a.get('trend'))}",
                vol=fmt_volume(a.get("volume")),
            )
        )
    return header + "\n".join(rows) + "\n"


def _watchlist_section(us_watch: List[dict], eu_watch: List[dict]) -> str:
    """Liste consolidée des actions à surveiller (US + Europe)."""
    lines = []
    for a in us_watch + eu_watch:
        if not a.get("ok"):
            continue
        lines.append(
            f"- **{a['name']}** ({a['ticker']}) — {fmt_price(a.get('last_price'))} "
            f"| 5j {fmt_pct(a.get('change_5d'))} | tendance "
            f"{trend_icon(a.get('trend'))} {trend_label(a.get('trend'))}"
        )
    return "\n".join(lines) if lines else "_Aucune donnée disponible._"


def _signals_block(signals: List[dict], positive: bool) -> str:
    if not signals:
        return "_Aucun signal marqué sur 5 jours._"
    return "\n".join(
        f"- **{s['name']}** ({s['ticker']}) : {fmt_pct(s['change_5d'])} sur 5 jours"
        for s in signals
    )


def _risks_block(risks: List[dict]) -> str:
    if not risks:
        return "_Aucun risque particulier détecté par les indicateurs._"
    lines = []
    for r in risks:
        vol = r.get("volatility")
        vol_txt = f" (volatilité {vol:.2f}%)" if vol is not None else ""
        lines.append(f"- **{r['name']}** ({r['ticker']}) : {r['reason']}{vol_txt}")
    return "\n".join(lines)


def _news_block(news: List[dict]) -> str:
    if not news:
        return "_Aucune actualité disponible (flux RSS indisponibles)._"
    lines = []
    for n in news:
        title = n.get("title", "")
        link = n.get("link", "")
        source = n.get("source", "")
        if link:
            lines.append(f"- [{title}]({link}) — *{source}*")
        else:
            lines.append(f"- {title} — *{source}*")
    return "\n".join(lines)


def _build_markdown(summary: str, data: dict) -> str:
    generated = data.get("generated_at_human", datetime.now().strftime("%Y-%m-%d %H:%M"))

    md = f"""# Market Brief AI Agent

**Date et heure de génération :** {generated}

> ⚠️ Analyse **éducative** générée automatiquement. Elle ne constitue **pas** un conseil financier.

## Résumé IA

{summary}

## Marché US

### Indices
{_asset_table(data["us"]["indices"])}
### Watchlist actions US
{_asset_table(data["us"]["watchlist"])}
## Marché France / Europe

### Indices
{_asset_table(data["eu"]["indices"])}
### Watchlist actions France
{_asset_table(data["eu"]["watchlist"])}
## Actions à surveiller

{_watchlist_section(data["us"]["watchlist"], data["eu"]["watchlist"])}

## Signaux positifs

{_signals_block(data.get("positive_signals", []), positive=True)}

## Signaux négatifs

{_signals_block(data.get("negative_signals", []), positive=False)}

## Risques à suivre

{_risks_block(data.get("risks", []))}

## News principales

{_news_block(data.get("news", []))}

## Disclaimer

Cette analyse est éducative et ne constitue pas un conseil financier.
Les données proviennent de sources publiques (yfinance, flux RSS) et peuvent
contenir des erreurs ou des retards. Aucune décision d'investissement ne
devrait être prise sur la seule base de ce document.

---
*Rapport généré automatiquement par Market Brief AI Agent — modèle IA : `{config.GEMINI_MODEL}`.*
"""
    return md


def save_markdown_report(summary: str, data: dict) -> str:
    """
    Écrit le rapport Markdown sur le disque.

    Retourne le chemin du rapport "latest" (reports/latest-market-brief.md).
    """
    os.makedirs(config.REPORTS_DIR, exist_ok=True)

    markdown = _build_markdown(summary, data)

    # 1) Version "toujours à jour"
    latest_path = os.path.join(config.REPORTS_DIR, config.LATEST_REPORT_NAME)
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    # 2) Version horodatée (archive)
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    dated_path = os.path.join(config.REPORTS_DIR, f"market-brief-{stamp}.md")
    with open(dated_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    info(f"Rapport horodaté : {dated_path}")
    return latest_path
