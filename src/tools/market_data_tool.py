"""
Market Data Tool
================
Récupère de vraies données de marché via yfinance (gratuit, sans clé API).

Fonctions publiques :
    - get_market_history(tickers, period="1mo") -> dict
    - get_latest_prices(tickers) -> dict

Robustesse : chaque ticker est traité indépendamment. Si un ticker échoue,
il est marqué {"ok": False} et l'agent continue avec les autres.
"""

from typing import Dict, List, Optional

import yfinance as yf

from src.utils.logging import warn


def _safe_change(closes: List[float], periods: int) -> Optional[float]:
    """
    Variation en % sur `periods` séances de bourse.

    Exemple : periods=1 => variation vs la veille ; periods=5 => vs 5 séances.
    Retourne None si les données sont insuffisantes.
    """
    try:
        if closes is None or len(closes) <= periods:
            return None
        last = float(closes[-1])
        past = float(closes[-1 - periods])
        if past == 0:
            return None
        return (last - past) / past * 100.0
    except (IndexError, TypeError, ValueError):
        return None


def get_market_history(tickers: List[str], period: str = "1mo") -> Dict[str, dict]:
    """
    Récupère l'historique de prix pour une liste de tickers.

    Retourne un dict {ticker: {...}} où chaque entrée contient :
        - ok         : bool (True si les données sont exploitables)
        - last_price : dernier prix disponible
        - change_1d  : variation 1 jour (%)
        - change_5d  : variation 5 jours (%)
        - change_1mo : variation sur la période (~1 mois) (%)
        - volume     : dernier volume disponible
        - closes     : liste des prix de clôture (pour les indicateurs)
        - volumes    : liste des volumes (pour détecter un volume inhabituel)
    """
    result: Dict[str, dict] = {}

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period, auto_adjust=False)

            if hist is None or hist.empty or "Close" not in hist:
                warn(f"Aucune donnée pour {ticker} — ignoré.")
                result[ticker] = {"ticker": ticker, "ok": False, "error": "no_data"}
                continue

            close_series = hist["Close"].dropna()
            closes = [float(x) for x in close_series.tolist()]

            volumes: List[float] = []
            if "Volume" in hist:
                volume_series = hist["Volume"].dropna()
                volumes = [float(x) for x in volume_series.tolist()]

            if not closes:
                warn(f"Historique de clôtures vide pour {ticker} — ignoré.")
                result[ticker] = {"ticker": ticker, "ok": False, "error": "empty_close"}
                continue

            last_price = closes[-1]
            last_volume = volumes[-1] if volumes else None

            result[ticker] = {
                "ticker": ticker,
                "ok": True,
                "last_price": last_price,
                "change_1d": _safe_change(closes, 1),
                "change_5d": _safe_change(closes, 5),
                # Variation "1 mois" = du 1er point de la fenêtre au dernier.
                "change_1mo": _safe_change(closes, len(closes) - 1),
                "volume": last_volume,
                "closes": closes,
                "volumes": volumes,
            }

        except Exception as exc:  # noqa: BLE001 - on veut vraiment tout attraper
            warn(f"Erreur lors de la récupération de {ticker} : {exc}")
            result[ticker] = {"ticker": ticker, "ok": False, "error": str(exc)}

    return result


def get_latest_prices(tickers: List[str]) -> Dict[str, Optional[float]]:
    """
    Récupère uniquement le dernier prix disponible pour chaque ticker.

    Retourne {ticker: last_price ou None}.
    S'appuie sur get_market_history avec une courte période (5 jours).
    """
    history = get_market_history(tickers, period="5d")
    prices: Dict[str, Optional[float]] = {}
    for ticker, data in history.items():
        prices[ticker] = data.get("last_price") if data.get("ok") else None
    return prices
