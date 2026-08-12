"""
Gemini Summary Tool
===================
Envoie les données structurées (indicateurs + news) à Gemini Flash et
récupère un résumé de marché clair, en français, à visée éducative.

Fonction publique :
    - generate_market_summary(payload) -> str

Points clés :
    - La clé API est lue via GEMINI_API_KEY (jamais en dur).
    - Si la clé est absente, si le SDK n'est pas installé, ou si l'appel
      échoue : on génère un résumé "fallback" local, sans planter.
    - Le prompt impose des consignes strictes : PAS de conseil financier.
"""

from typing import List

from src import config
from src.utils.formatting import fmt_pct, fmt_price, trend_label
from src.utils.logging import info, warn

# --------------------------------------------------------------------------
# Consigne stricte envoyée à Gemini (garde-fou "éducatif, pas de conseil").
# --------------------------------------------------------------------------
SYSTEM_INSTRUCTION = (
    "Tu es un assistant IA éducatif de veille de marché.\n"
    "Tu ne donnes jamais de conseil financier personnalisé.\n"
    'Tu ne dois pas dire "acheter", "vendre", "investir" ou "shorter".\n'
    'Tu dois utiliser les termes "à surveiller", "signal positif", '
    '"signal négatif", "risque à suivre".\n'
    "Tu dois préciser que l'analyse est éducative et ne constitue pas un "
    "conseil financier."
)


def _format_asset_line(asset: dict) -> str:
    """Une ligne lisible par actif pour le prompt."""
    return (
        f"- {asset.get('name')} ({asset.get('ticker')}) : "
        f"prix {fmt_price(asset.get('last_price'))}, "
        f"1j {fmt_pct(asset.get('change_1d'))}, "
        f"5j {fmt_pct(asset.get('change_5d'))}, "
        f"1 mois {fmt_pct(asset.get('change_1mo'))}, "
        f"tendance {trend_label(asset.get('trend'))}"
    )


def _format_group(title: str, assets: List[dict]) -> str:
    lines = [f"### {title}"]
    if not assets:
        lines.append("- (données indisponibles)")
    else:
        lines.extend(_format_asset_line(a) for a in assets)
    return "\n".join(lines)


def _build_prompt(payload: dict) -> str:
    """Construit le prompt texte envoyé à Gemini à partir du payload."""
    parts: List[str] = []

    parts.append(
        "Voici des données de marché réelles, déjà calculées par des outils "
        "(yfinance + indicateurs maison). Rédige une analyse éducative en "
        f"{'français' if config.REPORT_LANGUAGE == 'fr' else config.REPORT_LANGUAGE}."
    )
    parts.append(f"Date de génération : {payload.get('generated_at_human', '')}")

    # --- Marché US ---
    parts.append("\n## Marché US")
    parts.append(_format_group("Indices US", payload["us"]["indices"]))
    parts.append(_format_group("Watchlist US", payload["us"]["watchlist"]))

    # --- Marché France / Europe ---
    parts.append("\n## Marché France / Europe")
    parts.append(_format_group("Indices Europe", payload["eu"]["indices"]))
    parts.append(_format_group("Watchlist France", payload["eu"]["watchlist"]))

    # --- Signaux ---
    pos = payload.get("positive_signals", [])
    neg = payload.get("negative_signals", [])
    risks = payload.get("risks", [])

    parts.append("\n## Signaux positifs (variation 5j > +3%)")
    parts.append(
        "\n".join(f"- {s['name']} ({s['ticker']}) : {fmt_pct(s['change_5d'])}" for s in pos)
        or "- Aucun"
    )

    parts.append("\n## Signaux négatifs (variation 5j < -3%)")
    parts.append(
        "\n".join(f"- {s['name']} ({s['ticker']}) : {fmt_pct(s['change_5d'])}" for s in neg)
        or "- Aucun"
    )

    parts.append("\n## Risques à suivre")
    parts.append(
        "\n".join(f"- {r['name']} ({r['ticker']}) : {r['reason']}" for r in risks)
        or "- Aucun risque particulier détecté"
    )

    # --- News ---
    news = payload.get("news", [])
    parts.append("\n## Actualités récentes")
    if news:
        parts.append("\n".join(f"- [{n['source']}] {n['title']}" for n in news))
    else:
        parts.append("- (aucune actualité disponible)")

    # --- Consignes de rédaction ---
    parts.append(
        "\n## Consignes de rédaction\n"
        "- Ton clair et professionnel.\n"
        "- Sépare clairement le marché US et le marché France / Europe.\n"
        "- Mets en avant les signaux positifs, les signaux négatifs et les "
        "risques à suivre.\n"
        "- Termine par une courte conclusion éducative.\n"
        "- Rappelle que l'analyse est éducative et ne constitue pas un conseil "
        "financier.\n"
        "- N'utilise jamais les mots acheter, vendre, investir ou shorter."
    )

    return "\n".join(parts)


def _call_gemini(prompt: str) -> str:
    """Appelle réellement l'API Gemini via le SDK officiel google-genai."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
        ),
    )
    return (response.text or "").strip()


def _fallback_summary(payload: dict) -> str:
    """
    Résumé local généré sans IA (aucune clé requise).
    Assemble un texte propre à partir des mêmes données structurées.
    Utilisé si Gemini n'est pas disponible.
    """
    pos = payload.get("positive_signals", [])
    neg = payload.get("negative_signals", [])
    risks = payload.get("risks", [])

    def describe(assets: List[dict]) -> str:
        ok = [a for a in assets if a.get("last_price") is not None]
        if not ok:
            return "Données indisponibles pour le moment."
        pieces = [
            f"{a['name']} ({fmt_pct(a.get('change_1d'))} sur 1j, "
            f"tendance {trend_label(a.get('trend'))})"
            for a in ok
        ]
        return "; ".join(pieces) + "."

    lines: List[str] = []
    lines.append(
        "_Résumé généré localement (mode fallback, sans IA). Analyse éducative, "
        "ne constitue pas un conseil financier._\n"
    )

    lines.append("**Marché US.** " + describe(
        payload["us"]["indices"] + payload["us"]["watchlist"]
    ))
    lines.append("")
    lines.append("**Marché France / Europe.** " + describe(
        payload["eu"]["indices"] + payload["eu"]["watchlist"]
    ))
    lines.append("")

    if pos:
        lines.append(
            "**Signaux positifs à surveiller :** "
            + ", ".join(f"{s['name']} ({fmt_pct(s['change_5d'])} sur 5j)" for s in pos)
            + "."
        )
    else:
        lines.append("**Signaux positifs à surveiller :** aucun signal marqué sur 5 jours.")

    if neg:
        lines.append(
            "**Signaux négatifs à surveiller :** "
            + ", ".join(f"{s['name']} ({fmt_pct(s['change_5d'])} sur 5j)" for s in neg)
            + "."
        )
    else:
        lines.append("**Signaux négatifs à surveiller :** aucun signal marqué sur 5 jours.")

    if risks:
        lines.append(
            "**Risques à suivre :** "
            + ", ".join(f"{r['name']} ({r['reason']})" for r in risks)
            + "."
        )
    else:
        lines.append("**Risques à suivre :** pas de risque particulier détecté par les indicateurs.")

    lines.append("")
    lines.append(
        "**Conclusion éducative.** Ce panorama présente des signaux positifs, "
        "des signaux négatifs et des risques à suivre, uniquement à titre "
        "pédagogique. Il ne constitue pas un conseil financier."
    )

    return "\n".join(lines)


def generate_market_summary(payload: dict) -> str:
    """
    Génère le résumé de marché.

    - Si GEMINI_API_KEY est présente : appelle Gemini.
    - Sinon (ou en cas d'erreur / SDK manquant) : résumé fallback local.
    Dans tous les cas, ne lève jamais d'exception vers l'appelant.
    """
    prompt = _build_prompt(payload)

    if not config.GEMINI_API_KEY:
        warn("GEMINI_API_KEY absente — génération d'un résumé fallback local.")
        return _fallback_summary(payload)

    try:
        info(f"Appel de Gemini (modèle : {config.GEMINI_MODEL})...")
        text = _call_gemini(prompt)
        if text:
            return text
        warn("Réponse Gemini vide — utilisation du résumé fallback local.")
        return _fallback_summary(payload)
    except Exception as exc:  # noqa: BLE001 - fallback garanti
        warn(f"Appel Gemini échoué ({exc}) — utilisation du résumé fallback local.")
        return _fallback_summary(payload)
