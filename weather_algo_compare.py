"""Comparaison de tous les algorithmes Weather sur le WeatherSimulator.

Lance une simulation identique (même seed) pour chaque algorithme,
puis affiche un tableau récapitulatif et des graphiques de comparaison.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Src.process.weather_simulator import WeatherSimulator
from Src.algorithms.EMAStopLoss import EMAStopLoss
from Src.algorithms.WeatherRandom import WeatherRandom
from Src.algorithms.WeatherEGreedy import WeatherEGreedy
from Src.algorithms.WeatherUCB1 import WeatherUCB1
from Src.algorithms.WeatherThompsonSampling import WeatherThompsonSampling


# ── Paramètres de simulation ──────────────────────────────────────────
T = 1000                # nombre total de jours
REGIME_LENGTH = 100     # durée d'un régime météo
SEED = 42               # graine pour reproductibilité
ARMS = ["C", "U"]


def compute_metrics(results):
    """Calcule les métriques de performance à partir des résultats bruts."""
    actions = results["actions"]
    oracle = results["oracle"]
    c = np.array(results["c"])
    Q = np.array(results["Q"])

    # Taux de conversion moyen
    avg_conversion = c.mean()

    # Regret : différence entre l'oracle et l'algo à chaque tour
    oracle_proba = {
        ("C", "S"): 0.6, ("C", "R"): 0.1,
        ("U", "S"): 0.3, ("U", "R"): 0.55,
    }
    weather = results["weather"]
    oracle_rewards = np.array([oracle_proba[(oracle[t], weather[t])] for t in range(len(actions))])
    algo_expected = np.array([oracle_proba[(actions[t], weather[t])] for t in range(len(actions))])
    per_step_regret = oracle_rewards - algo_expected
    cumulated_regret = per_step_regret.cumsum()
    total_regret = cumulated_regret[-1]

    # Taux de bon choix (action == oracle)
    correct = sum(1 for a, o in zip(actions, oracle) if a == o)
    accuracy = correct / len(actions)

    # Nombre de switches
    switches = sum(1 for i in range(1, len(actions)) if actions[i] != actions[i - 1])

    return {
        "avg_conversion": avg_conversion,
        "total_regret": total_regret,
        "accuracy": accuracy,
        "switches": switches,
        "cumulated_regret": cumulated_regret,
        "per_step_conversion": c,
    }


def run_all():
    """Lance la simulation pour chaque algo et retourne les résultats."""
    algorithms = [
        EMAStopLoss(ARMS, alpha=0.05, x=2.0),
        WeatherEGreedy(ARMS, epsilon=0.05),
        WeatherUCB1(ARMS),
        WeatherThompsonSampling(ARMS),
        WeatherRandom(ARMS),
    ]

    all_results = {}
    for algo in algorithms:
        # Même environnement (même seed) pour chaque algo → comparaison équitable
        env = WeatherSimulator(T, REGIME_LENGTH, SEED)
        results = env.run_simulation(algo)
        metrics = compute_metrics(results)
        all_results[algo.name] = {"results": results, "metrics": metrics}

    return all_results


def print_summary(all_results):
    """Affiche un tableau récapitulatif dans le terminal."""
    header = f"{'Algorithme':<20} {'Conv. moy.':>10} {'Regret total':>13} {'Précision':>10} {'Switches':>9}"
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    for name, data in all_results.items():
        m = data["metrics"]
        print(f"{name:<20} {m['avg_conversion']:>10.4f} {m['total_regret']:>13.1f} {m['accuracy']:>10.2%} {m['switches']:>9d}")

    print("=" * len(header))


def plot_comparison(all_results):
    """Génère les graphiques de comparaison."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[matplotlib non installé — graphiques ignorés]")
        return

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # ── Graphique 1 : Regret cumulé ──
    ax1 = axes[0]
    for name, data in all_results.items():
        ax1.plot(data["metrics"]["cumulated_regret"], label=name, linewidth=1.2)
    ax1.set_ylabel("Regret cumulé")
    ax1.set_title("Comparaison des algorithmes — WeatherSimulator")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # Fond coloré pour les régimes météo (sur le premier algo disponible)
    first = next(iter(all_results.values()))
    weather = first["results"]["weather"]
    _shade_weather(ax1, weather)

    # ── Graphique 2 : Taux de conversion glissant (fenêtre 20 jours) ──
    ax2 = axes[1]
    window = 20
    for name, data in all_results.items():
        c = data["metrics"]["per_step_conversion"]
        rolling = np.convolve(c, np.ones(window) / window, mode="valid")
        ax2.plot(range(window - 1, len(c)), rolling, label=name, linewidth=1.2)
    ax2.set_ylabel(f"Conversion (moy. glissante {window}j)")
    ax2.set_xlabel("Jour")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)
    _shade_weather(ax2, weather)

    plt.tight_layout()
    plt.savefig("weather_algo_comparison.png", dpi=150)
    print("\n[Graphique sauvegardé : weather_algo_comparison.png]")
    plt.close()


def _shade_weather(ax, weather):
    """Ajoute un fond coloré jaune (soleil) / bleu (pluie) sur l'axe."""
    i = 0
    while i < len(weather):
        regime = weather[i]
        start = i
        while i < len(weather) and weather[i] == regime:
            i += 1
        color = "#FFF9C4" if regime == "S" else "#BBDEFB"
        ax.axvspan(start, i, alpha=0.3, color=color, zorder=0)


# ── Point d'entrée ────────────────────────────────────────────────────
if __name__ == "__main__":
    all_results = run_all()
    print_summary(all_results)
    plot_comparison(all_results)
