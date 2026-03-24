import random


class WeatherThompsonSampling:
    """Thompson Sampling (Bernoulli) pour le WeatherSimulator.

    Pour chaque bras, maintient un posterior Beta(succès+1, échecs+1).
    À chaque tour, échantillonne un theta par bras et joue le meilleur.

    Le taux de conversion c_t = Q_t/100 est converti en succès/échec
    via un tirage de Bernoulli(c_t) (version généralisée, Agrawal & Goyal 2012).

    Interface identique à EMAStopLoss : choose_action(), update(Q_t), arm_chosen, name.
    """

    def __init__(self, arms):
        self.arms = list(arms)
        self.name = "ThompsonSampling"
        self.arm_chosen = self.arms[0]
        self._rng = random.Random()

        self.p_estimation = {a: 0.5 for a in self.arms}
        self.v_estimation = {a: 0.0 for a in self.arms}
        self.x = 0.0
        self._successes = {a: 0.0 for a in self.arms}
        self._failures = {a: 0.0 for a in self.arms}

    def choose_action(self):
        best_arm = None
        best_sample = -1.0
        for a in self.arms:
            alpha = self._successes[a] + 1
            beta = self._failures[a] + 1
            sample = self._rng.betavariate(alpha, beta)
            if sample > best_sample:
                best_sample = sample
                best_arm = a
        self.arm_chosen = best_arm
        return self.arm_chosen

    def update(self, Q_t):
        a = self.arm_chosen
        c_t = Q_t / 100
        # Version généralisée : Bernoulli(c_t) pour convertir [0,1] en {0,1}
        if self._rng.random() < c_t:
            self._successes[a] += 1
        else:
            self._failures[a] += 1
        total = self._successes[a] + self._failures[a]
        self.p_estimation[a] = self._successes[a] / total if total > 0 else 0.5
