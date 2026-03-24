import numpy as np
import math


class WeatherSimulator():
    """Simule un site e-commerce avec deux produits (crème solaire C, parapluie U)
    et une météo cachée qui alterne entre soleil (S) et pluie (R).

    Chaque jour, 100 visiteurs arrivent. La probabilité qu'un visiteur achète
    dépend du produit affiché et de la météo :
        C + soleil = 0.60    C + pluie = 0.10
        U + soleil = 0.30    U + pluie = 0.55

    L'algorithme ne voit JAMAIS la météo. Il observe uniquement le nombre
    d'achats Q_t après avoir choisi quel produit afficher.
    """

    def __init__(self, T, regime_length, seed):
        """Crée l'environnement.

        T             -- nombre total de jours de simulation
        regime_length -- durée d'un régime météo (ex: 100 jours de soleil puis 100 de pluie)
        seed          -- graine aléatoire pour la reproductibilité
        """
        self.T = T                          # horizon total
        self.regime_length = regime_length  # jours par régime météo
        self.rng = np.random.default_rng(seed)  # générateur aléatoire

        # Matrice des probabilités de conversion : (produit, météo) -> proba d'achat
        self.proba = {
            ("C", "S"): 0.6,   # crème + soleil
            ("C", "R"): 0.1,   # crème + pluie
            ("U", "S"): 0.3,   # parapluie + soleil
            ("U", "R"): 0.55,  # parapluie + pluie
        }

        # Séquence météo pré-générée : ["S", "S", ..., "R", "R", ..., "S", ...]
        self.weather = []
        current = "S"  # on commence par le soleil
        while len(self.weather) < T:
            self.weather += [current] * regime_length
            current = "R" if current == "S" else "S"
        self.weather = self.weather[:T]

    def step(self, t, action):
        """Simule un jour : 100 visiteurs voient le produit 'action'.

        t      -- numéro du jour (0 à T-1)
        action -- "C" (crème) ou "U" (parapluie)

        Retourne Q_t = nombre d'achats (entre 0 et 100).
        Le taux de conversion est simplement Q_t / 100.
        """
        p = self.proba[(action, self.weather[t])]
        return self.rng.binomial(100, p)

    def get_oracle_action(self, t):
        """Retourne le meilleur produit pour le jour t (connaît la météo).
        Sert uniquement à mesurer la performance, jamais utilisé par l'algo."""
        if self.weather[t] == "S":
            return "C"  # soleil -> crème convertit mieux (0.6 > 0.3)
        else:
            return "U"  # pluie -> parapluie convertit mieux (0.55 > 0.1)

    def get_weather(self, t):
        """Retourne la météo du jour t. Pour l'analyse uniquement."""
        return self.weather[t]
    
    def run_simulation(self, ema_stop_loss):
        """Lance la simulation jour par jour sur l'horizon complet.

        ema_stop_loss -- instance d'EMAStopLoss

        Retourne un dictionnaire contenant les historiques :
            actions   -- liste des produits affichés chaque jour ("C" ou "U")
            Q         -- liste des nombres d'achats (0 à 100)
            c         -- liste des taux de conversion (Q/100)
            oracle    -- liste des bras optimaux (pour mesurer le regret)
            weather   -- liste des météos ("S" ou "R", pour l'analyse)
            p_estimation  -- liste des EMA du taux de conversion (après update)
            threshold -- liste des seuils de stop-loss (avant update)
        """
        actions = []       # produit affiché chaque jour
        Q_list = []        # nombre d'achats chaque jour
        c_list = []        # taux de conversion = Q/100
        oracle_list = []   # meilleur bras (connaît la météo)
        weather_list = []  # météo du jour (pour les graphiques)
        p_estimation_list = []    # EMA après mise à jour
        threshold_list = []  # seuil avant mise à jour

        for t in range(self.T):
            action = ema_stop_loss.get_action()
            Q_t = self.step(t, action)
            c_t = Q_t / 100

            # Sauvegarder le seuil AVANT update (c'est celui utilisé pour la décision)
            a = ema_stop_loss.current_arm
            sigma = math.sqrt(ema_stop_loss.v_estimation[a])
            threshold = max(0, ema_stop_loss.p_estimation[a] - ema_stop_loss.x * sigma)

            ema_stop_loss.update(Q_t)

            actions.append(action)
            Q_list.append(Q_t)
            c_list.append(c_t)
            oracle_list.append(self.get_oracle_action(t))
            weather_list.append(self.get_weather(t))
            p_estimation_list.append(ema_stop_loss.p_estimation[a])  # p_estimation APRÈS update
            threshold_list.append(threshold)

        return {
            "actions": actions,
            "Q": Q_list,
            "c": c_list,
            "oracle": oracle_list,
            "weather": weather_list,
            "p_estimation": p_estimation_list,
            "threshold": threshold_list,
        }    
