"""
Petit utilitaire de logs pour afficher clairement les étapes de l'agent
dans le terminal. Volontairement minimaliste (pas de dépendance externe).
"""


def log(message: str) -> None:
    """Affiche une ligne de log simple."""
    print(message, flush=True)


def step(current: int, total: int, message: str) -> None:
    """Affiche une étape numérotée, ex: [1/6] Récupération des données..."""
    print(f"[{current}/{total}] {message}", flush=True)


def warn(message: str) -> None:
    """Affiche un avertissement non bloquant (l'agent continue)."""
    print(f"  [!] {message}", flush=True)


def info(message: str) -> None:
    """Affiche une information secondaire, légèrement indentée."""
    print(f"      {message}", flush=True)
