import random


class WeatherRandom:
    """Sélection aléatoire uniforme parmi les bras disponibles.

    Baseline sans apprentissage pour le WeatherSimulator.
    Interface identique à EMAStopLoss : choose_action(), update(Q_t), arm_chosen, name.
    """

    def __init__(self, arms):
        self.arms = list(arms)
        self.name = "Random"
        self.arm_chosen = self.arms[0]
        # Statistiques exposées pour compatibilité avec run_simulation
        self.p_estimation = {a: 0.5 for a in self.arms}
        self.v_estimation = {a: 0.0 for a in self.arms}
        self.x = 0.0
        self._rng = random.Random()

    def choose_action(self):
        self.arm_chosen = self._rng.choice(self.arms)
        return self.arm_chosen

    def update(self, Q_t):
        a = self.arm_chosen
        c_t = Q_t / 100
        # Mise à jour des moyennes glissantes (pour les diagnostics uniquement)
        alpha = 0.05
        self.p_estimation[a] = (1 - alpha) * self.p_estimation[a] + alpha * c_t
