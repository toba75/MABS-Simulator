import math


class WeatherUCB1:
    """UCB1 pour le WeatherSimulator.

    À chaque tour, joue le bras maximisant :
        x_bar_a + sqrt(2 * ln(n) / n_a)
    où x_bar_a est la moyenne du taux de conversion du bras a,
    n le nombre total de tours, et n_a le nombre de fois que a a été joué.

    Interface identique à EMAStopLoss : choose_action(), update(Q_t), arm_chosen, name.
    """

    def __init__(self, arms):
        self.arms = list(arms)
        self.name = "UCB1"
        self.arm_chosen = self.arms[0]

        self.p_estimation = {a: 0.5 for a in self.arms}
        self.v_estimation = {a: 0.0 for a in self.arms}
        self.x = 0.0
        self._tries = {a: 0 for a in self.arms}
        self._cumulated = {a: 0.0 for a in self.arms}
        self._total_plays = 0

    def choose_action(self):
        # Phase d'initialisation : jouer chaque bras au moins une fois
        for a in self.arms:
            if self._tries[a] == 0:
                self.arm_chosen = a
                return self.arm_chosen

        def ucb_value(a):
            mean = self._cumulated[a] / self._tries[a]
            bonus = math.sqrt(2 * math.log(self._total_plays) / self._tries[a])
            return mean + bonus

        self.arm_chosen = max(self.arms, key=ucb_value)
        return self.arm_chosen

    def update(self, Q_t):
        a = self.arm_chosen
        c_t = Q_t / 100
        self._tries[a] += 1
        self._cumulated[a] += c_t
        self._total_plays += 1
        self.p_estimation[a] = self._cumulated[a] / self._tries[a]
