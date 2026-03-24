# Plan d'implémentation — Version minimale entièrement instanciée

## Référence

Spécification : [docs/specifications/specification.md](../specifications/specification.md), Section 10.

## Rappel de l'instance cible

| Paramètre | Valeur |
|---|---|
| Horizon | $T$ (configurable, ex. 1000) |
| Bras | $\mathcal{A} = \{C, U\}$ (crème solaire, parapluie) |
| État latent | $Z_t \in \{S, R\}$ (soleil, pluie) |
| Régimes | Alternance stricte $S, R, S, R, \dots$ de longueur $L_j \equiv 100$ |
| Visiteurs | $N_t \equiv N$ constant (ex. 100) |
| Prix unitaires | $m_C = m_U = 1$ |
| Probabilités d'achat | $p_{C,S}=0.6$, $p_{C,R}=0.1$, $p_{U,S}=0.3$, $p_{U,R}=0.55$ |
| Observation | $R_t = X_t(A_t)$ uniquement (pas de contexte, pas de météo) |
| Oracle | $a_t^\star = C$ si $Z_t = S$, $a_t^\star = U$ si $Z_t = R$ |
| Métrique | Regret dynamique $\sum_{t=1}^{T}(\mu_t(a_t^\star) - \mu_t(A_t))$ |

---

## Contrainte

**Aucun fichier existant ne doit être modifié.** Tous les ajouts sont de nouveaux fichiers qui s'intègrent à l'arborescence existante.

---

## Architecture des nouveaux fichiers

```
main_weather.py                              # Point d'entrée dédié
Src/
  algorithms/
    WeatherBandit.py                         # Tous les algorithmes (Random, ε-Greedy, UCB1, Thompson)
  process/
    weather_simulator.py                     # Environnement + simulateur + métriques
  Reporting/
    weather_report_generator.py              # Sauvegarde CSV et courbes
tests/
  test_weather.py                            # Tous les tests (unitaires + intégration)
requirements_weather.txt                     # Dépendances supplémentaires
```

**Total : 6 nouveaux fichiers — 0 fichier existant modifié.**

---

## Phases d'implémentation

### Phase 1 — Algorithmes (`Src/algorithms/WeatherBandit.py`)

**Objectif :** Un seul fichier contenant l'interface commune et les 4 algorithmes pour le problème 2-bras à récompense numérique, sans dépendance aux DataFrames.

#### 1a. Interface commune

Classe abstraite `BaseWeatherAlgorithm(ABC)` :

| Méthode | Signature | Description |
|---|---|---|
| `__init__` | `(arms: list[str])` | Stocke les bras disponibles |
| `select_arm` | `() -> str` | Choisit un bras (abstrait) |
| `update` | `(arm: str, reward: float) -> None` | Met à jour l'état interne (abstrait) |
| `reset` | `() -> None` | Réinitialise l'algorithme (abstrait) |
| `name` | `-> str` | Propriété : nom de l'algorithme |

**Différences clés avec l'interface existante :**
- Pas de `observed_value` (DataFrame) → paramètres scalaires `arm` et `reward`
- Pas de `user_context` → pas de contexte (H5 de la spécification)
- Pas de `threshold` → la récompense est numérique, pas binaire
- `select_arm()` au lieu de `run()` + `choose_action()` → interface simplifiée

#### 1b. `WBRandom`

- `select_arm()` : choix uniforme parmi les bras
- `update()` : no-op

#### 1c. `WBEGreedy`

**Paramètres :** `epsilon: float = 0.1`

**État interne :**
- `cumulated_rewards: dict[str, float]` — somme des récompenses par bras
- `tries: dict[str, int]` — nombre de tirages par bras

**Logique :**
- `select_arm()` : avec probabilité $\varepsilon$, choix uniforme ; sinon, bras de meilleure moyenne $\bar{x}_a = \text{cum}_a / n_a$
- `update(arm, reward)` : incrémente `cumulated_rewards[arm]` et `tries[arm]`

#### 1d. `WBUCB1`

**État interne :**
- `cumulated_rewards: dict[str, float]`
- `tries: dict[str, int]`
- `total_plays: int`

**Logique :**
- Initialisation : jouer chaque bras une fois
- `select_arm()` : $\arg\max_a \left[\bar{x}_a + \sqrt{\frac{2 \ln n}{n_a}}\right]$
- `update(arm, reward)` : mise à jour compteurs

#### 1e. `WBThompson`

**Paramètres :** `prior_mean: float = 0.0`, `prior_var: float = 1000.0`

**Approche :** Modèle Normal-Normal (conjugué gaussien) car les récompenses sont $\text{Bin}(N, p)$ avec $N$ grand, bien approximées par une gaussienne.

**État interne par bras :**
- `mean: float` — moyenne postérieure
- `precision: float` — précision postérieure ($1/\text{variance}$)

**Logique :**
- `select_arm()` : pour chaque bras, tirer $\theta_a \sim \mathcal{N}(\mu_a, 1/\tau_a)$, jouer $\arg\max_a \theta_a$
- `update(arm, reward)` : mise à jour bayésienne Normal-Normal :
  - $\tau_a' = \tau_a + \tau_{\text{obs}}$
  - $\mu_a' = (\tau_a \mu_a + \tau_{\text{obs}} \cdot r) / \tau_a'$

> **Simplification :** $\tau_{\text{obs}} = 1$ (chaque observation apporte une unité de précision).

---

### Phase 2 — Simulateur (`Src/process/weather_simulator.py`)

**Objectif :** Un seul fichier regroupant la configuration, l'environnement piecewise-stationary, le stockage des métriques et la boucle de simulation.

#### 2a. Configuration (dictionnaire ou dataclass interne)

Les paramètres de l'instance sont passés directement au constructeur de `WeatherSimulator`. Pas de classe séparée : les valeurs par défaut de la section 10 sont en dur dans le constructeur.

| Paramètre | Défaut | Description |
|---|---|---|
| `horizon` | `1000` | $T$ |
| `n_visitors` | `100` | $N$ |
| `regime_length` | `100` | $L_j$ |
| `initial_state` | `"S"` | Premier état météo |
| `purchase_probs` | `{"C": {"S": 0.6, "R": 0.1}, "U": {"S": 0.3, "R": 0.55}}` | Matrice $P$ |
| `seed` | `None` | Graine PRNG |

#### 2b. Environnement (méthodes internes de `WeatherSimulator`)

La logique environnement est intégrée directement dans le simulateur :

| Méthode | Description |
|---|---|
| `_build_weather_sequence() -> list[str]` | Pré-calcule $Z_1, \dots, Z_T$ (alternance $S/R$ tous les `regime_length` jours) |
| `_draw_reward(arm: str, state: str) -> int` | Tire $X_t(a) \sim \text{Bin}(N, p_{a,z})$ |
| `_expected_reward(arm: str, state: str) -> float` | Retourne $\mu_t(a) = N \cdot p_{a,z}$ |
| `_optimal_arm(state: str) -> str` | Retourne $a_t^\star$ |

#### 2c. Stockage des résultats (attributs du simulateur)

Tableaux numpy alloués dans `__init__` :

| Attribut | Type | Description |
|---|---|---|
| `chosen_arms` | `np.ndarray` (object) | $A_t$ pour chaque jour |
| `observed_rewards` | `np.ndarray` (float) | $R_t$ |
| `oracle_expected` | `np.ndarray` (float) | $\mu_t(a_t^\star)$ |
| `chosen_expected` | `np.ndarray` (float) | $\mu_t(A_t)$ |
| `cumulated_regret` | `np.ndarray` (float) | Regret cumulé |

Méthode `summary() -> dict` : regret total, % bras optimal, durée.

#### 2d. Boucle principale `run(algorithm) -> dict`

```
weather_seq = _build_weather_sequence()

pour t = 0, ..., T-1 :
    state = weather_seq[t]
    oracle_exp       = _expected_reward(_optimal_arm(state), state)
    arm              = algorithm.select_arm()
    chosen_exp       = _expected_reward(arm, state)
    reward           = _draw_reward(arm, state)
    algorithm.update(arm, reward)
    # stocker dans les tableaux
    cumulated_regret[t] = cumulated_regret[t-1] + (oracle_exp - chosen_exp)

retourner summary()
```

**Intégration avec l'existant :**
- Utilise `RepositoryManager` (non modifié) pour créer les répertoires de sortie
- Peut utiliser `ReportGenerator` (non modifié) pour les logs de progression

---

### Phase 3 — Reporting (`Src/Reporting/weather_report_generator.py`)

**Objectif :** Sauvegarder les résultats en fichiers et produire des visualisations.

**Classe `WeatherReportGenerator` :**

| Méthode | Signature | Description |
|---|---|---|
| `__init__` | `(output_path: str)` | Crée la structure de sortie via `RepositoryManager` |
| `save_results_csv` | `(simulator)` | Exporte les tableaux numpy en CSV |
| `save_config` | `(simulator)` | Sauvegarde les paramètres en JSON |
| `plot_cumulated_regret` | `(simulator)` | Courbe du regret cumulé vs. $t$ |
| `plot_reward_history` | `(simulator)` | Récompenses observées avec indication des régimes |
| `plot_arm_selection` | `(simulator)` | Proportion de sélection de chaque bras au fil du temps |
| `save_summary` | `(simulator)` | Résumé textuel des performances |

**Structure de sortie :**
```
Output/<timestamp>/
  config.json
  results.csv
  cumulated_regret.png
  reward_history.png
  arm_selection.png
  summary.txt
```

---

### Phase 4 — Point d'entrée (`main_weather.py`)

**Fichier créé :** `main_weather.py`

```python
from Src.algorithms.WeatherBandit import WBEGreedy
from Src.process.weather_simulator import WeatherSimulator

def main():
    simulator = WeatherSimulator(horizon=1000, n_visitors=100, seed=42)
    algorithm = WBEGreedy(arms=["C", "U"], epsilon=0.1)
    results = simulator.run(algorithm)

if __name__ == "__main__":
    main()
```

---

### Phase 5 — Tests (`tests/test_weather.py`)

**Fichier unique** regroupant tous les tests unitaires et d'intégration.

#### Tests algorithmes

| Test | Vérification |
|---|---|
| `test_random_returns_valid_arm` | `WBRandom.select_arm()` retourne `"C"` ou `"U"` |
| `test_egreedy_exploits_best` | Après 500 updates avec un bras dominant, ε-Greedy le sélectionne > 80% du temps |
| `test_ucb1_init_plays_all` | Les 2 premiers appels de `WBUCB1` jouent chaque bras une fois |
| `test_thompson_returns_valid_arm` | `WBThompson.select_arm()` retourne `"C"` ou `"U"` |
| `test_reset_clears_state` | Après `reset()`, l'état interne est vierge |

#### Tests simulateur (environnement + boucle)

| Test | Vérification |
|---|---|
| `test_weather_sequence_alternates` | 100 × S, 100 × R, 100 × S, … |
| `test_draw_reward_in_range` | $R_t \in [0, N]$ |
| `test_expected_reward_values` | $\mu(C, S) = 60$, $\mu(U, R) = 55$ |
| `test_oracle_zero_regret` | Un algorithme omniscient → regret cumulé = 0 |
| `test_random_positive_regret` | Random → regret > 0 |
| `test_results_length` | `len(chosen_arms) == horizon` |
| `test_reproducibility` | Deux runs avec même seed → mêmes résultats |

---

## Fichier `requirements_weather.txt`

```
numpy>=2.4
matplotlib>=3.8
```

> Séparé de `requirements.txt` pour respecter la contrainte de non-modification.

---

## Ordre d'implémentation

```
Phase 1  ─────>  Phase 2  ─────>  Phase 3  ─────>  Phase 4  ─────>  Phase 5
(Algo)          (Simulateur)     (Reporting)       (main)           (Tests)
```

---

## Récapitulatif des fichiers créés

| # | Fichier | Phase |
|---|---|---|
| 1 | `Src/algorithms/WeatherBandit.py` | 1 |
| 2 | `Src/process/weather_simulator.py` | 2 |
| 3 | `Src/Reporting/weather_report_generator.py` | 3 |
| 4 | `main_weather.py` | 4 |
| 5 | `tests/test_weather.py` | 5 |
| 6 | `requirements_weather.txt` | 3 |

**Total : 6 nouveaux fichiers — 0 fichier existant modifié.**
