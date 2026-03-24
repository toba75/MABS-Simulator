# Spécification de l’algorithme EMA–volatilité–stop-loss

Cette note spécifie l’algorithme de décision associé au problème précédent. L’idée est de conserver l’intuition initiale — suivre un produit tant que ses performances restent compatibles avec sa tendance récente, puis **basculer** vers l’autre produit lorsqu’une **rupture** est détectée — mais sous une forme rigoureuse et exploitable pour l’implémentation, le backtesting et l’analyse.

L’algorithme n’utilise **aucune information de météo** ni aucun contexte externe. Il observe uniquement la **récompense du produit effectivement affiché**. C’est donc une politique **model-free** de détection de changement, adaptée au cas particulier d’un bandit non stationnaire à **deux bras**.

## 1. Positionnement de l’algorithme

L’algorithme n’est pas un algorithme canonique de type UCB ou Thompson Sampling. C’est une **heuristique de changement de régime** fondée sur :

1. une estimation locale de la performance moyenne d’un bras par **moyenne exponentiellement pondérée** ;
2. une estimation locale de la dispersion des erreurs de prédiction par **variance EWMA** ;
3. une règle de **stop-loss unilatérale** qui déclenche un changement de bras si la récompense observée devient anormalement faible relativement au régime en cours ;
4. un **cooldown** pour limiter le phénomène de ping-pong.

La quantité

$$
e_t = r_t - \hat\mu_{a,t-1}
$$

est appelée ici **résidu de prédiction**. Ce n’est pas une TD-error au sens strict des MDP, car il n’y a pas de terme de valeur future de type
$r_t + \gamma V(s_{t+1}) - V(s_t)$.

## 2. Entrées, sorties et convention temporelle

On travaille sur un horizon discret en jours. L’ensemble des actions est

$$
\mathcal A = \{C,U\},
$$

avec :

- $C$ : afficher la crème solaire ;
- $U$ : afficher le parapluie.

La convention temporelle est la suivante :

- pendant le jour $t$, le site affiche le produit $A_t$ ;
- à la fin du jour $t$, on observe une récompense scalaire $r_t$ ;
- à partir de cette observation, l’algorithme décide le produit $A_{t+1}$ à afficher le jour suivant.

L’algorithme implémente donc une politique

$$
A_{t+1} = \pi_\theta(H_t),
\qquad
H_t = (A_1,r_1,\dots,A_t,r_t),
$$

paramétrée par un vecteur d’hyperparamètres $\theta$.

## 3. Récompense fournie à l’algorithme

L’algorithme prend en entrée une récompense scalaire $r_t$. Trois choix sont possibles.

### 3.1 Cas recommandé si le trafic journalier varie

Si le nombre de visiteurs $N_t$ varie fortement d’un jour à l’autre et qu’il est observé, on recommande de normaliser la récompense :

$$
r_t = \frac{CA_t}{N_t}
$$

ou, plus généralement, d’utiliser une métrique du type **profit par visite** ou **revenu par session**.

### 3.2 Cas simple si le trafic est constant

Si $N_t$ est constant, on peut utiliser directement :

$$
r_t = CA_t.
$$

### 3.3 Cas jouet / simulateur minimal

Si l’on fixe des marges unitaires identiques, on peut prendre :

$$
r_t = Q_t,
$$

c’est-à-dire simplement le nombre de ventes du jour.

Dans toute la suite, $r_t$ désigne la récompense scalaire effectivement injectée dans l’algorithme.

## 4. Hyperparamètres

L’algorithme est gouverné par les hyperparamètres suivants.

### 4.1 Coefficient de mémoire

$$
\alpha \in (0,1]
$$

contrôle la vitesse d’oubli de l’EMA et de la variance EWMA.

- $\alpha$ grand : adaptation rapide, mais plus grande nervosité ;
- $\alpha$ petit : adaptation lente, mais meilleure robustesse au bruit.

### 4.2 Multiplicateur de stop-loss

$$
x > 0
$$

contrôle la sensibilité du seuil de rupture.

- petit $x$ : détection rapide mais nombreuses fausses alertes ;
- grand $x$ : peu de fausses alertes mais retard à la détection.

### 4.3 Cooldown

$$
K \in \mathbb N
$$

est le nombre minimal de jours pendant lesquels l’algorithme s’interdit de re-switcher après un changement de produit.

### 4.4 Taille de warm-up par bras

$$
m_0 \ge 2
$$

est le nombre minimal d’observations initiales par bras utilisé pour initialiser les statistiques.

### 4.5 Plancher de variance

$$
v_{\min} > 0
$$

empêche une variance estimée trop faible au démarrage, ce qui rendrait le seuil de stop-loss artificiellement trop serré.

Le vecteur des hyperparamètres est donc :

$$
\theta = (\alpha, x, K, m_0, v_{\min}).
$$

## 5. État interne de l’algorithme

L’algorithme maintient des statistiques **séparées pour chaque bras**. Cela est essentiel : mélanger dans une seule EMA les observations de la crème et du parapluie conduirait à estimer une moyenne d’un processus composite, sans signification opérationnelle.

Pour chaque bras $a \in \{C,U\}$, on maintient à la fin du jour $t$ :

- $n_{a,t}$ : nombre total d’observations du bras $a$ jusqu’au jour $t$ ;
- $\hat\mu_{a,t}$ : estimation EWMA du reward moyen du bras $a$ ;
- $\hat v_{a,t}$ : estimation EWMA de la variance des résidus du bras $a$ ;
- $\hat\sigma_{a,t} = \sqrt{\hat v_{a,t}}$ : volatilité estimée du bras $a$.

L’algorithme maintient également :

- $A_t$ : bras affiché pendant le jour $t$ ;
- $c_t$ : compteur de cooldown au **début** du jour $t$.

On adopte la convention suivante pour le bras opposé :

$$
\bar C = U,
\qquad
\bar U = C.
$$

## 6. Phase d’initialisation (warm-up)

Une spécification complète doit traiter le problème du **cold start**. Si l’on démarre avec une seule observation sur un seul bras, la variance est mal définie et la bascule initiale devient arbitraire.

On introduit donc une phase de warm-up sur les $2m_0$ premiers jours.

### 6.1 Politique de warm-up

Pendant les $2m_0$ premiers jours, on alterne déterministiquement les bras :

$$
A_1=C,\; A_2=U,\; A_3=C,\; A_4=U,\; \dots
$$

jusqu’à obtenir exactement $m_0$ observations sur chaque bras.

### 6.2 Initialisation des statistiques

Soit $\mathcal R_a^{(0)} = \{r_{a,1},\dots,r_{a,m_0}\}$ l’ensemble des $m_0$ récompenses observées pour le bras $a$ pendant le warm-up.

On initialise alors :

$$
n_{a,2m_0}=m_0,
$$

$$
\hat\mu_{a,2m_0} = \frac{1}{m_0}\sum_{i=1}^{m_0} r_{a,i},
$$

$$
\hat v_{a,2m_0} = \max\left\{ \frac{1}{m_0-1}\sum_{i=1}^{m_0}(r_{a,i}-\hat\mu_{a,2m_0})^2,\; v_{\min} \right\},
$$

$$
\hat\sigma_{a,2m_0} = \sqrt{\hat v_{a,2m_0}}.
$$

Enfin, on pose :

$$
c_{2m_0+1}=0,
\qquad
A_{2m_0+1} = \arg\max_{a \in \{C,U\}} \hat\mu_{a,2m_0}.
$$

En cas d’égalité, on choisit par convention le bras joué au jour $2m_0$, ou à défaut la crème solaire.

## 7. Boucle principale de l’algorithme

Pour tout jour $t \ge 2m_0+1$, l’algorithme exécute les opérations suivantes.

### 7.1 Exposition du bras actif

Le site affiche le produit

$$
A_t = a.
$$

### 7.2 Observation de la récompense du jour

À la fin du jour, l’algorithme observe

$$
r_t.
$$

Aucune récompense n’est observée pour le bras $\bar a$.

### 7.3 Calcul du résidu de prédiction

Le résidu est calculé à partir des statistiques **pré-update** du bras actif :

$$
e_t = r_t - \hat\mu_{a,t-1}.
$$

C’est ce résidu qui mesure l’écart entre la performance observée et la performance attendue sous le régime récemment estimé.

### 7.4 Calcul du seuil de rupture

Le seuil de stop-loss du bras actif au jour $t$ est :

$$
\tau_t = \hat\mu_{a,t-1} - x\,\hat\sigma_{a,t-1}.
$$

Le test de rupture est **unilatéral à la baisse** :

$$
\text{alarm}_t = \mathbf 1\{r_t < \tau_t\}.
$$

Cette étape doit être effectuée **avant** la mise à jour de l’EMA et de la variance. Sinon, le choc observé serait immédiatement absorbé par les estimateurs, ce qui réduirait artificiellement la probabilité de détecter une rupture.

### 7.5 Mise à jour du bras actif

Les statistiques du bras joué sont ensuite mises à jour avec le résidu $e_t$.

#### Mise à jour de l’EMA

$$
\hat\mu_{a,t} = \hat\mu_{a,t-1} + \alpha e_t.
$$

#### Mise à jour de la variance EWMA

$$
\hat v_{a,t} = (1-\alpha)\hat v_{a,t-1} + \alpha e_t^2.
$$

#### Mise à jour de la volatilité

$$
\hat\sigma_{a,t} = \sqrt{\max\{\hat v_{a,t}, v_{\min}\}}.
$$

#### Comptage des observations

$$
n_{a,t} = n_{a,t-1}+1.
$$

### 7.6 État du bras non joué

Pour le bras $\bar a$, aucune observation nouvelle n’est disponible. Les statistiques restent donc inchangées :

$$
\hat\mu_{\bar a,t} = \hat\mu_{\bar a,t-1},
\qquad
\hat v_{\bar a,t} = \hat v_{\bar a,t-1},
\qquad
\hat\sigma_{\bar a,t} = \hat\sigma_{\bar a,t-1},
\qquad
n_{\bar a,t} = n_{\bar a,t-1}.
$$

Cette propriété est importante : l’algorithme **n’invente pas** de récompense pour le bras non joué. Il conserve simplement sa dernière estimation disponible jusqu’à la prochaine observation réelle.

### 7.7 Décision pour le jour suivant

La décision de switch dépend du cooldown.

#### Si le cooldown est actif

Si

$$
c_t > 0,
$$

alors le switch est interdit, même si une alarme a été déclenchée. On impose :

$$
A_{t+1}=a,
\qquad
c_{t+1}=\max(c_t-1,0).
$$

#### Si le cooldown est inactif

Si

$$
c_t = 0,
$$

alors :

- si $\text{alarm}_t=1$, on switch vers l’autre bras ;
- sinon, on conserve le bras courant.

Formellement,

$$
A_{t+1}=
\begin{cases}
\bar a, & \text{si } c_t=0 \text{ et } r_t < \hat\mu_{a,t-1} - x\hat\sigma_{a,t-1},\\
a, & \text{sinon.}
\end{cases}
$$

et le cooldown évolue selon

$$
c_{t+1}=
\begin{cases}
K, & \text{si } A_{t+1}=\bar a,\\
0, & \text{si } A_{t+1}=a \text{ et } c_t=0,\\
\max(c_t-1,0), & \text{si } c_t>0.
\end{cases}
$$

### 7.8 Interprétation du cooldown

Si un switch est décidé à la fin du jour $t$, alors le nouveau bras est forcé pendant les $K$ jours suivants. Autrement dit, avec $K=2$, l’algorithme ne peut pas re-switcher aux fins de journée $t+1$ et $t+2$. Le premier instant où un nouveau switch redevient possible est la fin du jour $t+3$.

## 8. Pseudo-code

```text
Entrées : alpha, x, K, m0, v_min
Actions : C, U

Warm-up :
    Jouer alternativement C, U, C, U, ... jusqu'à obtenir m0 observations par bras
    Pour chaque bras a in {C, U} :
        mu_hat[a] <- moyenne empirique des m0 rewards initiaux
        v_hat[a]  <- max(variance empirique, v_min)
        sigma_hat[a] <- sqrt(v_hat[a])
        n[a] <- m0
    A <- argmax_a mu_hat[a]
    c <- 0

Pour chaque jour t >= 2m0+1 :
    Afficher le bras A pendant le jour t
    Observer le reward r

    a <- A
    e <- r - mu_hat[a]
    threshold <- mu_hat[a] - x * sigma_hat[a]
    alarm <- (r < threshold)

    mu_hat[a] <- mu_hat[a] + alpha * e
    v_hat[a] <- (1 - alpha) * v_hat[a] + alpha * e^2
    v_hat[a] <- max(v_hat[a], v_min)
    sigma_hat[a] <- sqrt(v_hat[a])
    n[a] <- n[a] + 1

    Si c > 0 :
        A <- a
        c <- c - 1
    Sinon :
        Si alarm est vrai :
            A <- bras opposé de a
            c <- K
        Sinon :
            A <- a
            c <- 0

    Passer au jour suivant
```

## 9. Nature de la règle de décision

La règle de décision peut se lire comme suit.

Tant que la récompense observée reste compatible avec la performance moyenne récemment anticipée du bras courant, l’algorithme **exploite** et conserve ce bras. Dès qu’une journée apparaît comme une **rupture significative vers le bas**, il interprète cela comme un possible changement de régime de l’environnement et **explore** l’autre bras.

Dans le cas à deux bras, cette stratégie est suffisante pour produire une politique opérationnelle complète : une rupture sur le bras actif entraîne automatiquement un test réel de l’autre bras dès le lendemain.

## 10. Pourquoi les statistiques sont par bras et non globales

C’est un point décisif de la spécification.

Si l’on utilisait une EMA globale du “produit actuellement affiché”, alors une séquence de jours sur la crème suivie d’une séquence sur le parapluie ferait converger l’estimateur vers une moyenne hybride, mélangeant deux objets statistiques différents. Le seuil de rupture perdrait alors sa signification.

Avec des statistiques séparées par bras, on estime au contraire :

- la tendance propre de la crème lorsqu’elle est jouée ;
- la tendance propre du parapluie lorsqu’il est joué.

L’algorithme compare donc chaque récompense au **régime historique du même bras**, ce qui est bien la structure logique du stop-loss.

## 11. Choix recommandés des hyperparamètres

Les valeurs exactes doivent être sélectionnées par backtesting, mais la logique qualitative est la suivante.

### 11.1 Coefficient de mémoire $\alpha$

Un intervalle plausible pour commencer est :

$$
\alpha \in [0.05, 0.3].
$$

- vers $0.05$–$0.1$ : mémoire longue, peu de nervosité ;
- vers $0.2$–$0.3$ : détection plus rapide, mais plus grand risque de faux switch.

La demi-vie mémoire approximative est

$$
h_{1/2} \approx \frac{\ln(0.5)}{\ln(1-\alpha)}.
$$

Par exemple, pour $\alpha=0.2$, on obtient une demi-vie d’environ $3.1$ jours.

### 11.2 Multiplicateur $x$

Un point de départ raisonnable est :

$$
x \in [1.5, 3].
$$

Sous une hypothèse gaussienne simplifiée et pour un test **unilatéral**, les taux de déclenchement dus au seul bruit sont environ :

- $x=1$ : 15.9 % ;
- $x=2$ : 2.3 % ;
- $x=3$ : 0.13 %.

Ces valeurs ne doivent pas être prises comme vérités structurelles du problème, mais comme ordres de grandeur pour comprendre la sensibilité du seuil.

### 11.3 Cooldown $K$

Un intervalle pratique est :

$$
K \in \{0,1,2,3\}.
$$

- $K=0$ : maximum de réactivité, risque élevé de ping-pong ;
- $K=2$ ou $3$ : compromis souvent raisonnable dans un environnement de régimes longs.

### 11.4 Warm-up $m_0$

On recommande :

$$
m_0 \in \{2,3,5\}.
$$

Un $m_0$ trop petit donne des estimateurs très instables. Un $m_0$ trop grand retarde l’entrée en phase adaptative.

## 12. Complexité algorithmique

L’algorithme a un coût extrêmement faible.

- **Mémoire** : $O(1)$, car seuls quelques scalaires sont stockés pour chaque bras ;
- **Temps par jour** : $O(1)$, car la mise à jour et la décision nécessitent un nombre constant d’opérations.

Cela en fait une politique facile à déployer dans un environnement de production léger.

## 13. Limites structurelles

Cette spécification doit aussi expliciter ce que l’algorithme **ne fait pas**.

### 13.1 Il ne modélise pas explicitement la météo cachée

L’algorithme ne cherche pas à inférer un état latent $Z_t$. Il détecte seulement des ruptures dans la série de rewards du bras actif.

### 13.2 Il ne met pas à jour le bras non joué

Quand un bras n’est pas affiché, aucune information nouvelle n’est obtenue sur lui. Ses statistiques peuvent donc devenir **obsolètes** après une longue période d’inactivité.

### 13.3 Il ne compare pas les deux bras à chaque date

La décision de switch dépend uniquement d’une rupture détectée sur le bras courant. L’algorithme n’est donc pas un estimateur simultané de

$$
\arg\max_{a \in \{C,U\}} \hat\mu_{a,t}
$$

mis à jour chaque jour à partir d’observations complètes, car de telles observations n’existent pas dans le bandit.

## 14. Variantes facultatives

Les éléments suivants peuvent être ajoutés, mais **ne font pas partie du cœur de la spécification**.

### 14.1 Confirmation par deux alertes consécutives

On peut remplacer la règle de switch immédiat par une règle exigeant deux jours consécutifs sous le seuil. Cela réduit les faux positifs mais augmente le retard de détection.

### 14.2 Vieillissement passif d’un bras inactif

On peut introduire une pénalisation de l’ancienneté d’un estimateur non rafraîchi, par exemple en augmentant légèrement sa variance estimée avec le temps d’inactivité. Cela rend la politique plus prudente lors d’un retour sur un bras anciennement abandonné.

### 14.3 Seuils asymétriques

Si le coût économique d’un mauvais choix est plus élevé dans un sens que dans l’autre, on peut utiliser :

$$
x_{C \to U} \neq x_{U \to C}.
$$

Par exemple, si rester trop longtemps sur la crème sous la pluie coûte davantage que rester trop longtemps sur le parapluie au soleil, on peut prendre un seuil plus agressif pour détecter la transition vers le parapluie.

## 15. Spécification condensée en une phrase

L’algorithme est une politique déterministe à deux bras qui maintient, pour chaque produit, une estimation EWMA de son reward moyen et de sa volatilité, détecte une rupture baissière du bras actuellement affiché via un seuil de type

$$
\hat\mu - x\hat\sigma,
$$

puis bascule vers l’autre produit sous réserve qu’aucun cooldown ne soit actif.

## 16. Formulation prête à intégrer dans le rapport

> Nous proposons un algorithme de détection de changement à deux bras fondé sur une moyenne exponentiellement pondérée et une estimation locale de volatilité. À la fin de chaque journée, l’algorithme observe la récompense du produit affiché, calcule un résidu de prédiction par rapport à l’estimation courante de ce même produit, puis teste un seuil de rupture unilatéral de type $\hat\mu - x\hat\sigma$. Si la récompense observée passe sous ce seuil et qu’aucun cooldown n’est actif, l’algorithme bascule vers l’autre produit pour la journée suivante ; sinon il conserve le produit courant. Les statistiques sont maintenues séparément pour chaque bras, mises à jour uniquement lorsqu’un reward réel de ce bras est observé, et initialisées par une courte phase de warm-up. L’algorithme constitue ainsi une heuristique model-free de suivi de régime adaptée à un bandit non stationnaire à deux bras.
