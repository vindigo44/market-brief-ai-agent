"""
Configuration centrale du Market Brief AI Agent.

Tout ce qui est "réglable" est ici : watchlists, indices, flux RSS,
modèle Gemini, langue et chemins de sortie.

Les variables sensibles / configurables sont lues depuis l'environnement
(fichier .env en local, secrets/variables GitHub Actions en CI) :
    - GEMINI_API_KEY  : clé API Gemini (JAMAIS en dur dans le code)
    - GEMINI_MODEL    : modèle Gemini à utiliser
    - REPORT_LANGUAGE : langue du rapport
"""

import os

from dotenv import load_dotenv

# Charge le fichier .env s'il existe (aucune erreur s'il est absent).
load_dotenv()

# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# --------------------------------------------------------------------------
# Langue & sorties
# --------------------------------------------------------------------------
REPORT_LANGUAGE = os.getenv("REPORT_LANGUAGE", "fr").strip()

# Dossier où sont écrits les rapports Markdown.
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports").strip()
# Nom du rapport "toujours à jour".
LATEST_REPORT_NAME = "latest-market-brief.md"

# --------------------------------------------------------------------------
# Marché US
# --------------------------------------------------------------------------
US_INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^DJI": "Dow Jones",
}

US_WATCHLIST = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "Nvidia",
    "TSLA": "Tesla",
    "AMZN": "Amazon",
    "META": "Meta",
    "GOOGL": "Alphabet (Google)",
}

# --------------------------------------------------------------------------
# Marché France / Europe
# --------------------------------------------------------------------------
EU_INDICES = {
    "^FCHI": "CAC 40",
    "^STOXX50E": "Euro Stoxx 50",
    "^GDAXI": "DAX",
}

EU_WATCHLIST = {
    "MC.PA": "LVMH",
    "OR.PA": "L'Oréal",
    "AIR.PA": "Airbus",
    "TTE.PA": "TotalEnergies",
    "BNP.PA": "BNP Paribas",
    "SU.PA": "Schneider Electric",
    "RMS.PA": "Hermès",
}

# Agrégat pratique {ticker: nom lisible} pour tout le portefeuille suivi.
ALL_TICKERS = {
    **US_INDICES,
    **US_WATCHLIST,
    **EU_INDICES,
    **EU_WATCHLIST,
}

# --------------------------------------------------------------------------
# Flux RSS financiers (gratuits, sans clé API)
#
# La liste est volontairement configurable. Si un flux est indisponible,
# l'agent l'ignore et continue (voir news_tool.py) : il ne plante jamais.
# --------------------------------------------------------------------------
RSS_FEEDS = [
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
    {"name": "MarketWatch", "url": "http://feeds.marketwatch.com/marketwatch/topstories/"},
    {
        "name": "CNBC Markets",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    },
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news_25.rss"},
]

# --------------------------------------------------------------------------
# Divers
# --------------------------------------------------------------------------
# Nombre maximum de news envoyées à Gemini (prompt court = rapide & économique).
MAX_NEWS_ITEMS = 12
# Nombre max de news récupérées par flux avant dédoublonnage.
MAX_NEWS_PER_FEED = 5
# Fenêtre d'historique récupérée pour les calculs.
HISTORY_PERIOD = "1mo"

# --------------------------------------------------------------------------
# Seuils des indicateurs (logique pédagogique simple, facile à expliquer)
# --------------------------------------------------------------------------
# Variation 5 jours au-dessus de ce seuil (%) => signal positif.
SIGNAL_POSITIVE_THRESHOLD = 3.0
# Variation 5 jours en dessous de ce seuil (%) => signal négatif.
SIGNAL_NEGATIVE_THRESHOLD = -3.0
# Volatilité (écart-type des variations quotidiennes en %) au-dessus
# de ce seuil => risque à surveiller.
VOLATILITY_RISK_THRESHOLD = 2.5
# Volume du dernier jour > ce multiple de la moyenne => volume inhabituel.
UNUSUAL_VOLUME_MULTIPLIER = 1.5
# Fenêtre de la moyenne mobile.
MOVING_AVERAGE_WINDOW = 20
