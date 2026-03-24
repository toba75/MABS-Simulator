import random


class WeatherEGreedy:
    """Epsilon-Greedy pour le WeatherSimulator.

    Explore avec probabilité epsilon (choix aléatoire), exploite sinon
    (bras avec la meilleure moyenne de conversion observée).

    Interface identique à EMAStopLoss : choose_action(), update(Q_t), arm_chosen, name.
    """

    def __init__(self, arms, epsilon=0.05):
        self.arms = list(arms)
        self.name = "EGreedy"
        self.epsilon = epsilon
        self.arm_chosen = self.arms[0]
        self._rng = random.Random()

        # Moyenne du taux de conversion par bras
        self.p_estimation = {a: 0.5 for a in self.arms}
        self.v_estimation = {a: 0.0 for a in self.arms}
        self.x = 0.0
        self._tries = {a: 0 for a in self.arms}
        self._cumulated = {a: 0.0 for a in self.arms}

    def choose_action(self):
        # Phase d'initialisation : jouer chaque bras au moins une fois
        for a in self.arms:
            if self._tries[a] == 0:
                self.arm_chosen = a
                return self.arm_chosen

        if self._rng.random() < self.epsilon:
            self.arm_chosen = self._rng.choice(self.arms)
        else:
            self.arm_chosen = max(self.arms, key=lambda a: self.p_estimation[a])
        return self.arm_chosen

    def update(self, Q_t):
        a = self.arm_chosen
        c_t = Q_t / 100
        self._tries[a] += 1
        self._cumulated[a] += c_t
        self.p_estimation[a] = self._cumulated[a] / self._tries[a]
