"""
Indicators Tool
===============
Transforme les données brutes de marché en indicateurs simples et lisibles.

Fonction publique :
    - calculate_market_indicators(market_data) -> dict

Logique pédagogique (facile à expliquer en présentation) :
    - variation 5 jours  > +3 %   => signal positif
    - variation 5 jours  < -3 %   => signal négatif
    - volatilité élevée           => risque à surveiller
    - prix au-dessus de la MM20   => tendance haussière (bullish)
    - prix en dessous de la MM20  => tendance baissière (bearish)
    - volume anormalement élevé   => volume inhabituel
"""

import statistics
from typing import Dict, List, Optional

from src import config
from src.utils.logging import warn


def _moving_average(closes: List[float], window: int) -> Optional[float]:
    """Moyenne mobile simple sur les `window` dernières clôtures."""
    if not closes or len(closes) < window:
        return None
    return sum(closes[-window:]) / window


def _volatility(closes: List[float]) -> Optional[float]:
    """
    Volatilité "simple" = écart-type des variations quotidiennes (en %).
    Plus la valeur est grande, plus l'actif bouge fort d'un jour à l'autre.
    """
    if not closes or len(closes) < 3:
        return None
    daily_returns: List[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev:
            daily_returns.append((closes[i] - prev) / prev * 100.0)
    if len(daily_returns) < 2:
        return None
    return statistics.pstdev(daily_returns)


def _is_unusual_volume(volumes: List[float]) -> bool:
    """Vrai si le dernier volume dépasse nettement la moyenne des précédents."""
    if not volumes or len(volumes) < 5:
        return False
    previous = volumes[:-1]
    avg = sum(previous) / len(previous) if previous else 0
    if avg <= 0:
        return False
    return volumes[-1] > config.UNUSUAL_VOLUME_MULTIPLIER * avg


def calculate_market_indicators(market_data: Dict[str, dict]) -> dict:
    """
    Calcule les indicateurs pour chaque actif et agrège les signaux.

    Retourne un dict :
        {
          "per_ticker": {ticker: {indicateurs...}},
          "positive_signals": [...],
          "negative_signals": [...],
          "risks": [...],
        }
    """
    per_ticker: Dict[str, dict] = {}
    positive_signals: List[dict] = []
    negative_signals: List[dict] = []
    risks: List[dict] = []

    for ticker, data in market_data.items():
        name = config.ALL_TICKERS.get(ticker, ticker)

        if not data.get("ok"):
            per_ticker[ticker] = {"ticker": ticker, "name": name, "ok": False}
            continue

        closes = data.get("closes", []) or []
        volumes = data.get("volumes", []) or []
        last_price = data.get("last_price")
        change_5d = data.get("change_5d")

        ma20 = _moving_average(closes, config.MOVING_AVERAGE_WINDOW)
        volatility = _volatility(closes)

        # --- Tendance simple : prix vs moyenne mobile 20 jours ---
        trend = "neutral"
        if ma20 is not None and last_price is not None:
            if last_price > ma20:
                trend = "bullish"
            elif last_price < ma20:
                trend = "bearish"

        # --- Volume inhabituel ---
        unusual_volume = _is_unusual_volume(volumes)

        # --- Volatilité élevée => risque ---
        high_volatility = (
            volatility is not None and volatility > config.VOLATILITY_RISK_THRESHOLD
        )

        # --- Signal positif / négatif basé sur la variation 5 jours ---
        signal = "neutral"
        if change_5d is not None:
            if change_5d > config.SIGNAL_POSITIVE_THRESHOLD:
                signal = "positive"
            elif change_5d < config.SIGNAL_NEGATIVE_THRESHOLD:
                signal = "negative"

        info = {
            "ticker": ticker,
            "name": name,
            "ok": True,
            "last_price": last_price,
            "change_1d": data.get("change_1d"),
            "change_5d": change_5d,
            "change_1mo": data.get("change_1mo"),
            "ma20": ma20,
            "volatility": volatility,
            "trend": trend,
            "unusual_volume": unusual_volume,
            "high_volatility": high_volatility,
            "signal": signal,
            "volume": data.get("volume"),
        }
        per_ticker[ticker] = info

        # --- Agrégation des signaux ---
        if signal == "positive":
            positive_signals.append(
                {"ticker": ticker, "name": name, "change_5d": change_5d}
            )
        elif signal == "negative":
            negative_signals.append(
                {"ticker": ticker, "name": name, "change_5d": change_5d}
            )

        if high_volatility:
            risks.append(
                {
                    "ticker": ticker,
                    "name": name,
                    "volatility": volatility,
                    "reason": "volatilité élevée",
                }
            )
        if unusual_volume:
            risks.append(
                {
                    "ticker": ticker,
                    "name": name,
                    "volatility": volatility,
                    "reason": "volume inhabituel",
                }
            )

    # Tri du plus significatif au moins significatif.
    positive_signals.sort(key=lambda x: (x["change_5d"] is not None, x["change_5d"]), reverse=True)
    negative_signals.sort(key=lambda x: (x["change_5d"] is None, x["change_5d"]))
    risks.sort(key=lambda x: (x["volatility"] is not None, x["volatility"] or 0), reverse=True)

    if not any(d.get("ok") for d in per_ticker.values()):
        warn("Aucune donnée exploitable : indicateurs calculés sur un ensemble vide.")

    return {
        "per_ticker": per_ticker,
        "positive_signals": positive_signals,
        "negative_signals": negative_signals,
        "risks": risks,
    }
