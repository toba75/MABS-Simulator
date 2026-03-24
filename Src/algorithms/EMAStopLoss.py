import math


class EMAStopLoss:
    """Politique de sélection de produit basée sur EMA et stop-loss.

    L'idée : on suit le taux de conversion du produit affiché avec une
    moyenne mobile exponentielle (EMA). Si le taux observé chute trop
    en dessous de l'EMA (= alarme stop-loss), on bascule vers l'autre produit.

    Deux hyperparamètres seulement :
        alpha -- vitesse d'adaptation de l'EMA (petit = lent et stable)
        x     -- sensibilité de l'alarme (grand = moins de fausses alertes)
    """

    def __init__(self, alpha=0.2, x=2.0):
        """Crée la politique.

        alpha -- coefficient EWMA, entre 0 et 1 (défaut 0.05)
        x     -- multiplicateur du seuil de stop-loss (défaut 2.0)
        """
        self.alpha = alpha  # vitesse d'oubli de l'EMA
        self.x = x          # largeur du seuil en nombre d'écarts-types
        self.reset()

    def reset(self):
        """Réinitialise l'état interne (prior neutre)."""
        # EMA du taux de conversion par bras (initialisé à 0.5 = aucune préférence)
        self.p_estimation = {"C": 0.5, "U": 0.5}
        # Variance EWMA des résidus par bras (initialisée à 0.01)
        self.v_estimation = {"C": 0.01, "U": 0.01}
        # Bras actuellement affiché
        self.current_arm = "C"

    def get_action(self):
        """Retourne le produit à afficher aujourd'hui ("C" ou "U")."""
        return self.current_arm

    def update(self, Q_t):
        """Met à jour les statistiques après avoir observé Q_t achats.

        Q_t -- nombre d'achats du jour (sur 100 visiteurs)

        Étapes :
        1. Calculer le taux de conversion observé c_t = Q_t / 100
        2. Calculer le résidu e_t = c_t - EMA courante (AVANT mise à jour)
        3. Vérifier si c_t est sous le seuil d'alarme (stop-loss)
        4. Mettre à jour l'EMA du taux et de la variance
        5. Si alarme : basculer vers l'autre produit
        """
        a = self.current_arm
        c_t = Q_t / 100  # taux de conversion observé (entre 0 et 1)

        # Résidu : écart entre l'observation et la prédiction AVANT mise à jour
        e_t = c_t - self.p_estimation[a]

        # Seuil de rupture : p̂ - x × σ (clippé à 0 car c_t ne peut pas être négatif)
        sigma = math.sqrt(self.v_estimation[a])  # écart-type local estimé
        threshold = max(0, self.p_estimation[a] - self.x * sigma)
        alarm = c_t < threshold  # True si le taux est anormalement bas

        # Mise à jour de l'EMA du taux de conversion
        self.p_estimation[a] = (1 - self.alpha) * self.p_estimation[a] + self.alpha * c_t
        # Mise à jour de l'EMA de la variance des résidus
        self.v_estimation[a] = (1 - self.alpha) * self.v_estimation[a] + self.alpha * e_t ** 2

        # Si alarme déclenchée : basculer vers l'autre produit
        if alarm:
            if a == "C":
                self.current_arm = "U"
            else:
                self.current_arm = "C"
