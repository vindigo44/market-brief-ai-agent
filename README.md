# Market Brief AI Agent 📊🤖

> Agent IA **éducatif** de veille de marché. Il récupère de **vraies données**
> de marché, calcule des indicateurs simples, lit des actualités financières,
> puis demande à **Gemini Flash** de rédiger un résumé clair en français.
> Le tout automatisé **toutes les 12 heures** avec GitHub Actions.

⚠️ **Projet 100 % éducatif.** Il ne donne **aucun conseil financier**.
Il ne dit jamais « acheter », « vendre », « investir » ou « shorter ». Il parle
de **signaux positifs**, **signaux négatifs**, **risques à suivre** et **actions
à surveiller**.

---

## 1. Ce que fait le projet

À chaque exécution, l'agent :

1. récupère de vraies données de marché (indices + actions) via **yfinance** ;
2. suit deux zones : **marché US** et **marché France / Europe** ;
3. suit une **watchlist** d'actions ;
4. récupère des **news financières** via des flux **RSS gratuits** ;
5. calcule des **indicateurs simples** (variations, moyenne mobile, volatilité) ;
6. détecte des **signaux positifs et négatifs** ;
7. envoie ces données **structurées** à **Gemini Flash** ;
8. génère un **résumé clair en français** ;
9. sauvegarde un **rapport Markdown** ;
10. peut tourner **automatiquement toutes les 12 h** via GitHub Actions.

Résultat : le fichier [`reports/latest-market-brief.md`](reports/) est mis à jour
avec un panorama de marché lisible.

---

## 2. Pourquoi c'est un agent IA ?

Ce n'est pas « juste un appel à un LLM ». C'est un **agent** parce que :

- **il a un objectif** : produire un briefing de marché éducatif ;
- **il utilise plusieurs tools** : données, indicateurs, news, IA, rapport ;
- **il exécute une séquence** d'étapes ordonnées ;
- **il transforme des données** brutes en analyse structurée ;
- **il génère un résultat final** (le rapport) de façon autonome.

> **Le point clé à retenir pour la présentation :**
>
> ```
> Le LLM ne récupère pas les chiffres tout seul.
> Les chiffres viennent des tools.
> Gemini sert à transformer les données structurées en résumé clair.
> C'est la combinaison "données + tools + LLM + automatisation" qui crée l'agent.
> ```

---

## 3. Skills / tools utilisés

| Tool (skill)          | Fichier                              | Rôle |
| --------------------- | ------------------------------------ | ---- |
| **Market Data Tool**  | `src/tools/market_data_tool.py`      | Récupère prix & historiques via yfinance |
| **Indicators Tool**   | `src/tools/indicators_tool.py`       | Calcule variations, MM20, volatilité, signaux |
| **News Tool**         | `src/tools/news_tool.py`             | Lit les flux RSS financiers |
| **Gemini Summary Tool** | `src/tools/gemini_tool.py`         | Demande à Gemini un résumé (fallback local si pas de clé) |
| **Report Tool**       | `src/tools/report_tool.py`           | Assemble et sauvegarde le rapport Markdown |
| **Telegram Tool**     | `src/tools/telegram_tool.py`         | Envoie le rapport sur Telegram à chaque exécution (optionnel) |

L'**agent** (`src/agent/market_brief_agent.py`) est le chef d'orchestre qui
appelle ces tools dans le bon ordre.

### Schéma du pipeline

```
[yfinance] ──┐
             ├─► Indicators Tool ─► signaux + tendances ─┐
[RSS feeds] ─┘                                            ├─► payload ─► Gemini ─► Résumé
                                                          │                        │
                                                          └──────────► Report Tool ┘
                                                                            │
                                                                            ▼
                                                          reports/latest-market-brief.md
                                                                            │
                                                                            ▼
                                                          Telegram Tool ─► 📲 Telegram
```

---

## 4. Installation

Pré-requis : **Python 3.11+**.

```bash
git clone <votre-repo>
cd market-brief-ai-agent
pip install -r requirements.txt
```

(Optionnel mais recommandé : créer un environnement virtuel avant `pip install`.)

```bash
python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS / Linux :
source .venv/bin/activate
```

---

## 5. Créer une clé Gemini (gratuite)

1. Aller sur **Google AI Studio** : <https://aistudio.google.com/app/apikey>
2. Se connecter avec un compte Google.
3. Cliquer sur **« Create API key »**.
4. Copier la clé (elle ressemble à `AIza...`).

Le **free tier** de Gemini suffit largement pour ce projet.
Modèles recommandés : `gemini-2.5-flash` ou `gemini-2.5-flash-lite`.

---

## 6. Créer le fichier `.env` (en local)

Copier le modèle fourni :

```bash
cp .env.example .env
```

Puis éditer `.env` :

```env
GEMINI_API_KEY=AIza...votre_cle...
GEMINI_MODEL=gemini-2.5-flash
REPORT_LANGUAGE=fr
```

> 🔒 Le fichier `.env` est déjà dans `.gitignore` : il **ne sera jamais**
> envoyé sur GitHub. Ne mettez **jamais** votre clé en dur dans le code.

**Bon à savoir :** sans clé Gemini, le projet fonctionne quand même. Il génère
un résumé « fallback » local (sans IA), assemblé à partir des mêmes données.

---

## 7. Lancer en local

```bash
python main.py
```

Vous verrez les étapes s'afficher :

```
[1/7] Récupération des données marché...
[2/7] Calcul des indicateurs...
[3/7] Récupération des news...
[4/7] Génération du résumé avec Gemini...
[5/7] Sauvegarde du rapport...
[6/7] Envoi de la notification Telegram...
[7/7] Terminé.
```

Le rapport est écrit dans :

- `reports/latest-market-brief.md` (toujours à jour) ;
- `reports/market-brief-AAAA-MM-JJ-HH-MM.md` (archive horodatée).

---

## 8. Automatiser avec GitHub Actions

Le workflow [`.github/workflows/market-brief.yml`](.github/workflows/market-brief.yml) :

- se lance **manuellement** (bouton *Run workflow* dans l'onglet **Actions**) ;
- se lance **automatiquement toutes les 12 h** (`cron: "0 */12 * * *"`, en UTC) ;
- installe Python + les dépendances ;
- exécute `python main.py` ;
- sauvegarde les rapports en **artifact** téléchargeable ;
- committe `reports/latest-market-brief.md` dans le dépôt (optionnel).

> ℹ️ Sur GitHub, le `cron` peut être décalé de quelques minutes selon la charge.

---

## 9. Ajouter le secret `GEMINI_API_KEY` sur GitHub

1. Sur GitHub, ouvrir votre dépôt.
2. **Settings** → **Secrets and variables** → **Actions**.
3. Onglet **Secrets** → **New repository secret**.
4. **Name** : `GEMINI_API_KEY`
5. **Secret** : collez votre clé Gemini (`AIza...`).
6. **Add secret**.

Le workflow lit ce secret via `${{ secrets.GEMINI_API_KEY }}`.

(Optionnel) Dans l'onglet **Variables**, vous pouvez aussi définir
`GEMINI_MODEL` et `REPORT_LANGUAGE` ; sinon les valeurs par défaut
(`gemini-2.5-flash`, `fr`) s'appliquent.

> Pour que le commit automatique du rapport fonctionne, le workflow demande
> déjà `permissions: contents: write`. Si votre organisation restreint les
> Actions, vérifiez **Settings → Actions → General → Workflow permissions** et
> autorisez **Read and write permissions**.

---

## 📲 Recevoir le rapport sur Telegram (optionnel)

L'agent peut **t'envoyer le rapport sur Telegram à chaque exécution** : le
résumé dans un message + le rapport Markdown complet en pièce jointe. C'est
optionnel : sans token ni chat_id, l'étape est simplement ignorée (aucun
plantage).

### a) Créer un bot Telegram (30 secondes)

1. Sur Telegram, ouvre une conversation avec **@BotFather**.
2. Envoie `/newbot`, choisis un nom et un identifiant se terminant par `bot`.
3. BotFather te donne un **token** du type `123456789:ABCdef...` → c'est
   `TELEGRAM_BOT_TOKEN`.

### b) Récupérer ton `TELEGRAM_CHAT_ID`

1. **Important :** ouvre ton bot et envoie-lui d'abord un message (ex. `/start`).
   Un bot ne peut pas écrire à quelqu'un qui ne l'a jamais contacté.
2. Ouvre dans un navigateur (remplace `<TOKEN>`) :
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Cherche `"chat":{"id":123456789,...}` → ce nombre est ton `TELEGRAM_CHAT_ID`.

> Astuce : tu peux aussi écrire à **@userinfobot** qui te renvoie directement
> ton identifiant. Pour envoyer dans un **groupe**, ajoute le bot au groupe ;
> les ids de groupe commencent souvent par `-`.

### c) En local — compléter le fichier `.env`

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=123456789
```

Puis `python main.py` : tu reçois le brief directement sur Telegram.

### d) Sur GitHub Actions — ajouter les secrets

Dans **Settings → Secrets and variables → Actions → Secrets** :

| Type | Name | Valeur |
| ---- | ---- | ------ |
| Secret | `TELEGRAM_BOT_TOKEN` | le token de @BotFather |
| Secret | `TELEGRAM_CHAT_ID` | ton identifiant de chat |

Une fois ces secrets ajoutés, **chaque exécution** (manuelle ou toutes les 12 h)
t'enverra le rapport sur Telegram automatiquement.

---

## 10. Expliquer le projet en présentation

Trois phrases suffisent :

1. **Les tools récupèrent les vraies données** (prix, indicateurs, news).
2. **L'agent orchestre** ces tools dans une séquence claire.
3. **Gemini transforme** les données structurées en résumé lisible, et
   **GitHub Actions automatise** le tout toutes les 12 h.

C'est l'illustration parfaite de : **données + tools + LLM + automatisation = agent**.

---

## Structure du projet

```
market-brief-ai-agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py
├── src/
│   ├── config.py
│   ├── tools/
│   │   ├── market_data_tool.py
│   │   ├── news_tool.py
│   │   ├── indicators_tool.py
│   │   ├── gemini_tool.py
│   │   ├── report_tool.py
│   │   └── telegram_tool.py
│   ├── agent/
│   │   └── market_brief_agent.py
│   └── utils/
│       ├── formatting.py
│       └── logging.py
├── reports/
│   └── .gitkeep
└── .github/
    └── workflows/
        └── market-brief.yml
```

---

## Limites

- **Données dépendantes de yfinance** : gratuit mais non garanti, parfois en
  retard ou incomplet.
- **Free tier Gemini limité** : quotas de requêtes par minute / par jour.
- **Pas de conseil financier** : usage strictement pédagogique.
- **Pas de trading automatique** : l'agent n'exécute aucun ordre.
- **Pas de garantie d'exactitude** : ne prenez aucune décision sur cette base.

---

## Sécurité

- La clé Gemini **n'est jamais** écrite en dur dans le code.
- En local, elle vit dans `.env` (ignoré par Git).
- En CI, elle vit dans un **secret GitHub** (`GEMINI_API_KEY`).
- Ne partagez jamais votre clé ; en cas de fuite, révoquez-la dans AI Studio.

---

## Disclaimer

Cette application et les rapports qu'elle génère sont **éducatifs** et ne
constituent **pas** un conseil financier, ni une recommandation d'achat ou de
vente. Faites vos propres recherches et, si besoin, consultez un professionnel
agréé.
