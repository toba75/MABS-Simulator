# Spécification de l’algorithme EMA–volatilité–stop-loss pour maximiser le taux de conversion

Cette note spécifie une version rigoureuse de l’algorithme dans laquelle l’objectif n’est plus de maximiser le chiffre d’affaires, mais le **taux de conversion** du produit affiché. L’algorithme choisit chaque jour entre deux actions — afficher la crème solaire ou le parapluie — en se fondant uniquement sur l’historique observé du produit effectivement affiché.

Le changement conceptuel est simple mais important : la grandeur injectée dans l’algorithme n’est plus un montant monétaire, mais une **proportion** comprise entre 0 et 1. L’algorithme cherche donc à suivre le produit dont la **probabilité de conversion** est actuellement la plus élevée, indépendamment du prix de vente, de la marge unitaire ou du chiffre d’affaires associé.

## 1. Positionnement de l’algorithme

L’algorithme est une politique **model-free** de détection de changement pour un bandit non stationnaire à deux bras. Il n’est ni un UCB, ni un Thompson Sampling, ni un filtre bayésien explicite sur la météo cachée. Il repose sur quatre mécanismes simples :

1. une estimation locale du taux de conversion d’un bras par **moyenne exponentiellement pondérée** ;
2. une estimation locale de la dispersion des résidus par **variance EWMA** ;
3. une règle de **stop-loss unilatérale** sur le taux de conversion observé ;
4. un **cooldown** empêchant les allers-retours trop rapides entre les deux produits.

L’idée est la suivante : tant que le taux de conversion observé du produit affiché reste compatible avec son régime récent, on continue à l’exploiter ; si ce taux de conversion devient anormalement faible, on interprète cela comme un possible changement de régime et on bascule sur l’autre produit.

## 2. Grandeurs observées et objectif d’optimisation

### 2.1 Actions

L’ensemble des actions est

$$
\mathcal A = \{C,U\},
$$

avec :

- $C$ : afficher la crème solaire ;
- $U$ : afficher le parapluie.

### 2.2 Quantités observées à la fin d’une journée

Pendant le jour $t$, le site affiche un seul produit $A_t \in \mathcal A$.

À la fin du jour $t$, on observe :

- $N_t$ : le nombre de visiteurs exposés au produit affiché ;
- $Q_t$ : le nombre d’achats de ce produit ;
- le **taux de conversion observé**

$$
c_t = \frac{Q_t}{N_t}, \qquad \text{si } N_t>0.
$$

Le scalaire injecté dans l’algorithme est donc $c_t$, et non le chiffre d’affaires $CA_t$.

### 2.3 Cas dégénéré $N_t=0$

Si aucun visiteur ne se présente au jour $t$, alors le taux de conversion n’est pas défini. Pour que la spécification soit complète, on adopte la convention suivante :

- si $N_t=0$, la journée est **non informative** ;
- aucune mise à jour statistique n’est effectuée ;
- aucune alarme de rupture n’est générée ;
- le produit courant est conservé pour le lendemain, sous réserve de la mécanique normale du cooldown.

Autrement dit, une journée sans trafic ne doit ni favoriser ni pénaliser artificiellement un bras.

### 2.4 Objectif

L’objectif est de maximiser la conversion, pas la valeur monétaire. Deux formulations sont équivalentes sur le plan opérationnel.

La première consiste à maximiser le **taux de conversion global** sur l’horizon :

$$
J_T^{\mathrm{CVR}}(\pi) 
= \mathbb E\left[\frac{\sum_{t=1}^T Q_t}{\sum_{t=1}^T N_t}\right].
$$

La seconde, plus pratique pour l’analyse séquentielle, consiste à maximiser le nombre attendu de conversions sous trafic exogène :

$$
\max_\pi \; \mathbb E\left[\sum_{t=1}^T N_t\,p_{A_t,t}\right],
$$

où $p_{a,t}$ désigne la probabilité de conversion du bras $a$ au jour $t$.

Comme $N_t$ est exogène et ne dépend pas de l’action, le bras optimal au jour $t$ est simplement celui qui maximise $p_{a,t}$. L’algorithme cherche donc à suivre le produit dont la **probabilité d’achat par visite** est actuellement la plus élevée.

### 2.5 Conséquence économique

Dans cette version, le prix et la marge unitaire sont volontairement ignorés. Il faut donc assumer explicitement la chose suivante :

> si un produit convertit davantage mais rapporte moins par vente, l’algorithme préférera quand même ce produit, car la cible d’optimisation est la conversion et non le revenu.

## 3. Convention temporelle

La convention temporelle est la suivante :

- pendant le jour $t$, le site affiche le produit $A_t$ ;
- à la fin du jour $t$, on observe $(N_t,Q_t)$ ;
- si $N_t>0$, on calcule $c_t = Q_t/N_t$ ;
- à partir de cette information, l’algorithme décide $A_{t+1}$, le produit affiché le jour suivant.

L’algorithme implémente donc une politique

$$
A_{t+1}=\pi_\theta(H_t),
\qquad
H_t=(A_1,N_1,Q_1,\dots,A_t,N_t,Q_t),
$$

paramétrée par un vecteur d’hyperparamètres $\theta$.

## 4. Hyperparamètres

L’algorithme dépend des hyperparamètres suivants.

### 4.1 Coefficient de mémoire

$$
\alpha \in (0,1]
$$

contrôle la vitesse d’oubli de l’estimateur EWMA du taux de conversion et de la variance EWMA.

- $\alpha$ grand : adaptation rapide mais plus grande nervosité ;
- $\alpha$ petit : adaptation lente mais plus grande stabilité.

### 4.2 Multiplicateur du seuil de stop-loss

$$
x > 0
$$

contrôle la sensibilité du seuil de rupture.

- petit $x$ : détection rapide mais nombreuses fausses alertes ;
- grand $x$ : peu de fausses alertes mais détection tardive.

### 4.3 Cooldown

$$
K \in \mathbb N
$$

est le nombre minimal de jours pendant lesquels l’algorithme s’interdit de re-switcher après un changement de produit.

### 4.4 Taille de warm-up par bras

$$
m_0 \ge 2
$$

est le nombre minimal de **journées informatives** par bras utilisées pour initialiser les statistiques.

### 4.5 Plancher de variance

$$
v_{\min} > 0
$$

évite qu’une variance estimée trop faible au démarrage rende le seuil artificiellement trop serré.

Dans le cas du taux de conversion, comme la variable est bornée dans $[0,1]$, un plancher très petit suffit généralement.

Le vecteur d’hyperparamètres est donc :

$$
\theta = (\alpha, x, K, m_0, v_{\min}).
$$

## 5. État interne de l’algorithme

Les statistiques sont maintenues **séparément pour chaque bras**. C’est indispensable : la crème et le parapluie n’ont pas la même dynamique de conversion, et une EMA globale n’aurait aucune signification interprétable.

Pour chaque bras $a \in \{C,U\}$, l’algorithme maintient à la fin du jour $t$ :

- $n_{a,t}$ : le nombre de journées **informatives** du bras $a$, c’est-à-dire le nombre de jours où ce bras a été joué avec $N_t>0$ ;
- $\hat p_{a,t}$ : l’estimation EWMA du taux de conversion moyen du bras $a$ ;
- $\hat v_{a,t}$ : l’estimation EWMA de la variance des résidus du bras $a$ ;
- $\hat\sigma_{a,t}=\sqrt{\hat v_{a,t}}$ : l’écart-type local estimé du bras $a$.

L’algorithme maintient aussi :

- $A_t$ : le bras affiché pendant le jour $t$ ;
- $d_t$ : le compteur de cooldown au **début** du jour $t$.

On note enfin le bras opposé par

$$
\bar C = U,
\qquad
\bar U = C.
$$

## 6. Phase d’initialisation (warm-up)

Une spécification complète doit traiter le **cold start**. Au démarrage, ni le taux de conversion moyen ni la volatilité locale ne sont connus.

### 6.1 Politique de warm-up

Pendant la phase d’initialisation, on alterne les produits jusqu’à obtenir exactement $m_0$ **journées informatives** pour chaque bras.

Une politique simple est :

$$
C,U,C,U,\dots
$$

jusqu’à ce que chaque bras ait accumulé $m_0$ jours avec $N_t>0$.

Si un jour de warm-up satisfait $N_t=0$, il ne compte pas comme observation informative et le warm-up est prolongé.

### 6.2 Données de warm-up

Pour chaque bras $a$, on collecte les couples

$$
(N_{a,1},Q_{a,1}), \dots, (N_{a,m_0},Q_{a,m_0}),
$$

avec les taux journaliers associés

$$
c_{a,i}=\frac{Q_{a,i}}{N_{a,i}}, \qquad i=1,\dots,m_0.
$$

### 6.3 Initialisation du taux de conversion moyen

Pour initialiser le niveau moyen, la formule la plus propre est d’utiliser la conversion empirique **pondérée par l’exposition** :

$$
\hat p_{a,2m_0} = 
\frac{\sum_{i=1}^{m_0} Q_{a,i}}{\sum_{i=1}^{m_0} N_{a,i}}.
$$

Cette formule est préférable à la simple moyenne des $c_{a,i}$ lorsque le trafic varie d’un jour à l’autre, car elle tient compte du fait qu’un jour à 1000 visiteurs est statistiquement plus informatif qu’un jour à 20 visiteurs.

### 6.4 Initialisation de la variance locale

On initialise ensuite la variance des résidus à partir des taux journaliers de warm-up :

$$
\hat v_{a,2m_0}
=
\max\left\{
\frac{1}{m_0-1}\sum_{i=1}^{m_0}(c_{a,i}-\hat p_{a,2m_0})^2,
\; v_{\min}
\right\}.
$$

Puis

$$
\hat\sigma_{a,2m_0}=\sqrt{\hat v_{a,2m_0}}.
$$

Enfin,

$$
n_{a,2m_0}=m_0.
$$

### 6.5 Choix du premier bras après warm-up

À la fin du warm-up, on initialise la décision opérationnelle par

$$
A_{2m_0+1} = \arg\max_{a\in\{C,U\}} \hat p_{a,2m_0},
\qquad
d_{2m_0+1}=0.
$$

En cas d’égalité, on peut conserver le dernier bras joué ou fixer une convention arbitraire.

## 7. Boucle principale de l’algorithme

Pour chaque jour $t \ge 2m_0+1$, l’algorithme exécute les opérations suivantes.

### 7.1 Exposition du bras actif

Le site affiche le produit

$$
A_t = a.
$$

### 7.2 Observation de la journée

À la fin du jour $t$, l’algorithme observe :

$$
N_t, Q_t.
$$

Deux cas doivent être distingués.

#### Cas A : journée informative $(N_t>0)$

On calcule le taux de conversion observé

$$
c_t = \frac{Q_t}{N_t}.
$$

#### Cas B : journée non informative $(N_t=0)$

Aucun taux de conversion n’est calculable. Dans ce cas :

- aucune mise à jour des statistiques n’est faite ;
- aucune alarme n’est générée ;
- le bras courant est conservé pour $t+1$, avec décrément éventuel du cooldown.

Ce cas est traité explicitement en section 7.7.

### 7.3 Résidu de prédiction

Sur une journée informative, le résidu est calculé à partir des statistiques **pré-update** du bras actif :

$$
e_t = c_t - \hat p_{a,t-1}.
$$

Ce résidu mesure l’écart entre la conversion observée du jour et la conversion attendue sous le régime récemment estimé pour ce même produit.

### 7.4 Seuil de rupture

Le seuil de stop-loss du bras actif au jour $t$ est défini par

$$
\tau_t = \max\{0,\; \hat p_{a,t-1} - x\hat\sigma_{a,t-1}\}.
$$

Le clipping à 0 est naturel car un taux de conversion ne peut pas être négatif.

La règle d’alarme est unilatérale à la baisse :

$$
\mathrm{alarm}_t = \mathbf 1\{c_t < \tau_t\}.
$$

Cette étape doit être effectuée **avant** la mise à jour des estimateurs. Sinon, le choc du jour serait partiellement absorbé par l’EMA et par la variance avant même d’être testé.

### 7.5 Mise à jour du bras actif

Sur une journée informative, les statistiques du bras joué sont mises à jour comme suit.

#### Mise à jour du niveau moyen

Comme la variable observée est un taux dans $[0,1]$, il est préférable d’écrire la mise à jour sous forme convexe :

$$
\hat p_{a,t} = (1-\alpha)\hat p_{a,t-1} + \alpha c_t.
$$

Cette écriture garantit automatiquement

$$
\hat p_{a,t} \in [0,1]
$$

si $\hat p_{a,t-1}\in[0,1]$ et $c_t\in[0,1]$.

#### Mise à jour de la variance EWMA

$$
\hat v_{a,t} = (1-\alpha)\hat v_{a,t-1} + \alpha e_t^2.
$$

#### Mise à jour de la volatilité locale

$$
\hat\sigma_{a,t} = \sqrt{\max\{\hat v_{a,t}, v_{\min}\}}.
$$

#### Comptage des observations informatives

$$
n_{a,t} = n_{a,t-1}+1.
$$

### 7.6 État du bras non joué

Pour le bras $\bar a$, aucune observation nouvelle n’est disponible. Les statistiques sont donc laissées inchangées :

$$
\hat p_{\bar a,t}=\hat p_{\bar a,t-1},
\qquad
\hat v_{\bar a,t}=\hat v_{\bar a,t-1},
\qquad
\hat\sigma_{\bar a,t}=\hat\sigma_{\bar a,t-1},
\qquad
n_{\bar a,t}=n_{\bar a,t-1}.
$$

Cela ne signifie pas que le bras non joué n’a pas de valeur potentielle ; cela signifie seulement que l’algorithme ne reçoit **aucune nouvelle information** à son sujet tant qu’il n’est pas réessayé.

### 7.7 Décision pour le jour suivant

La règle de décision dépend à la fois du caractère informatif ou non de la journée et de l’état du cooldown.

#### Cas 1 : journée non informative $(N_t=0)$

Aucune alarme n’est disponible. Le produit courant est conservé :

$$
A_{t+1}=a.
$$

Le cooldown évolue naturellement avec le temps :

$$
d_{t+1}=\max(d_t-1,0).
$$

#### Cas 2 : journée informative et cooldown actif

Si $N_t>0$ et

$$
d_t>0,
$$

alors le switch est interdit, même si une alarme a été déclenchée. On impose :

$$
A_{t+1}=a,
\qquad
d_{t+1}=\max(d_t-1,0).
$$

#### Cas 3 : journée informative et cooldown inactif

Si $N_t>0$ et

$$
d_t=0,
$$

alors :

- si $\mathrm{alarm}_t=1$, on bascule vers l’autre bras ;
- sinon, on conserve le bras courant.

Formellement,

$$
A_{t+1}=
\begin{cases}
\bar a, & \text{si } d_t=0 \text{ et } c_t < \hat p_{a,t-1}-x\hat\sigma_{a,t-1},\\
a, & \text{sinon.}
\end{cases}
$$

et

$$
d_{t+1}=
\begin{cases}
K, & \text{si } A_{t+1}=\bar a,\\
0, & \text{si } A_{t+1}=a \text{ et } d_t=0.
\end{cases}
$$

### 7.8 Interprétation du cooldown

Si un switch est déclenché à la fin du jour $t$, alors le nouveau produit est forcé pendant les $K$ jours suivants. Avec $K=2$, un nouveau switch ne peut donc pas se produire aux fins des journées $t+1$ et $t+2$.

## 8. Pseudo-code

```text
Entrées : alpha, x, K, m0, v_min
Actions : C, U

Warm-up :
    Jouer alternativement C, U, C, U, ...
    Ne compter que les jours avec N > 0
    Jusqu'à obtenir m0 jours informatifs par bras

    Pour chaque bras a in {C, U} :
        p_hat[a] <- (somme des achats observés pour a) / (somme des visiteurs exposés à a)
        v_hat[a] <- max(variance empirique des taux journaliers de a, v_min)
        sigma_hat[a] <- sqrt(v_hat[a])
        n[a] <- m0

    A <- argmax_a p_hat[a]
    d <- 0

Pour chaque jour t >= 2m0+1 :
    Afficher le bras A pendant le jour t
    Observer N et Q
    a <- A

    Si N == 0 :
        # journée non informative
        A <- a
        d <- max(d - 1, 0)
        Passer au jour suivant

    c <- Q / N
    e <- c - p_hat[a]
    threshold <- max(0, p_hat[a] - x * sigma_hat[a])
    alarm <- (c < threshold)

    p_hat[a] <- (1 - alpha) * p_hat[a] + alpha * c
    v_hat[a] <- (1 - alpha) * v_hat[a] + alpha * e^2
    v_hat[a] <- max(v_hat[a], v_min)
    sigma_hat[a] <- sqrt(v_hat[a])
    n[a] <- n[a] + 1

    Si d > 0 :
        A <- a
        d <- d - 1
    Sinon :
        Si alarm est vrai :
            A <- bras opposé de a
            d <- K
        Sinon :
            A <- a
            d <- 0
```

## 9. Signification statistique des estimateurs

La quantité centrale n’est plus une moyenne de revenu, mais une moyenne locale de **probabilité de conversion observée**.

- $\hat p_{a,t}$ est une estimation à mémoire courte du taux de conversion du bras $a$ lorsqu’il est joué ;
- $\hat v_{a,t}$ mesure la variabilité locale des écarts entre conversion observée et conversion anticipée ;
- $\hat\sigma_{a,t}$ sert d’échelle pour décider si une baisse du taux de conversion est simplement du bruit ou un signal possible de changement de régime.

Il est important de comprendre que l’algorithme ne modélise pas explicitement la loi binomiale $Q_t \sim \mathrm{Bin}(N_t,p_{a,t})$. Il utilise seulement les taux observés $c_t$ et leur stabilité locale.

## 10. Pourquoi ce changement modifie réellement l’algorithme

Passer du chiffre d’affaires au taux de conversion ne consiste pas seulement à renommer la récompense. Cela change la nature même de la grandeur suivie.

### 10.1 La cible devient une probabilité

Le signal suivi est maintenant borné :

$$
0 \le c_t \le 1.
$$

L’interprétation de l’EMA devient donc directement comportementale : elle estime une probabilité d’achat moyenne récente.

### 10.2 Le trafic brut est normalisé

Deux journées ayant des volumes de trafic différents deviennent comparables une fois ramenées à leur taux de conversion. Cela évite qu’un fort trafic gonfle artificiellement l’importance d’une journée simplement parce qu’elle a généré plus de ventes absolues.

### 10.3 Les signaux faibles sont plus visibles

Une baisse nette de l’appétence produit peut être détectée même si le trafic global augmente. Avec le chiffre d’affaires, une hausse du trafic pourrait masquer une dégradation du taux de conversion.

### 10.4 L’objectif économique change

L’algorithme ne cherche plus le produit qui rapporte le plus, mais celui qui convainc le plus de visiteurs. Ce choix est cohérent si la finalité du projet est l’optimisation du funnel ou de la probabilité d’achat, et non de la marge.

## 11. Choix recommandés des hyperparamètres

Les valeurs exactes doivent être déterminées par backtesting, mais les ordres de grandeur suivants constituent un bon point de départ.

### 11.1 Coefficient de mémoire $\alpha$

Un intervalle raisonnable est :

$$
\alpha \in [0.05,0.3].
$$

La demi-vie mémoire approximative vaut

$$
h_{1/2} \approx \frac{\ln(0.5)}{\ln(1-\alpha)}.
$$

Par exemple, pour $\alpha=0.2$, on obtient une demi-vie d’environ 3.1 jours.

### 11.2 Multiplicateur $x$

Un intervalle de départ raisonnable est :

$$
x \in [1.5,3].
$$

Sous une approximation gaussienne unilatérale, les probabilités de faux déclenchement valent environ :

- $x=1$ : 15.9 % ;
- $x=2$ : 2.3 % ;
- $x=3$ : 0.13 %.

Dans le cas du taux de conversion, cette lecture doit rester **heuristique** : la variable est bornée et la distribution empirique peut être asymétrique, surtout à faible trafic.

### 11.3 Cooldown $K$

Une plage pratique est

$$
K \in \{0,1,2,3\}.
$$

### 11.4 Warm-up $m_0$

Un bon choix de départ est

$$
m_0 \in \{2,3,5\}.
$$

### 11.5 Plancher de variance $v_{\min}$

Comme le signal est dans $[0,1]$, un ordre de grandeur pratique peut être

$$
v_{\min} \in [10^{-6},10^{-4}].
$$

Le réglage exact dépendra du niveau de bruit observé dans le simulateur.

## 12. Variante recommandée si le trafic varie fortement

La version de base ci-dessus traite chaque **journée informative** comme une observation de même poids, quelle que soit la taille de l’échantillon $N_t$. Cela est simple et cohérent, mais pas toujours statistiquement optimal.

Si $N_t$ varie fortement, une amélioration naturelle consiste à rendre l’update plus sensible aux journées riches en trafic. On peut, par exemple, remplacer $\alpha$ par un coefficient effectif

$$
\alpha_t = 1-(1-\alpha)^{N_t/N_{\mathrm{ref}}},
$$

où $N_{\mathrm{ref}}$ est un niveau de trafic de référence.

Les mises à jour deviennent alors

$$
\hat p_{a,t} = (1-\alpha_t)\hat p_{a,t-1}+\alpha_t c_t,
$$

$$
\hat v_{a,t} = (1-\alpha_t)\hat v_{a,t-1}+\alpha_t e_t^2.
$$

Cette variante ne change pas la logique de l’algorithme ; elle améliore simplement l’utilisation de l’information lorsque le nombre de visiteurs varie fortement d’une journée à l’autre.

## 13. Limites structurelles

### 13.1 L’algorithme n’infère pas explicitement l’état latent

Il ne reconstruit ni la météo ni un régime caché. Il réagit uniquement à la série observée des taux de conversion du bras actif.

### 13.2 Les statistiques du bras inactif peuvent devenir obsolètes

Comme aucune observation n’est disponible pour le produit non affiché, son estimateur peut devenir ancien et ne plus refléter le régime courant.

### 13.3 Le seuil repose sur une approximation locale de type gaussien

Cette approximation est utile pour calibrer intuitivement $x$, mais elle n’est pas une description exacte d’un taux de conversion borné dérivé d’un échantillonnage binomial.

### 13.4 L’objectif ignore la marge unitaire

Cette propriété est intentionnelle dans la présente version, mais elle doit être explicitée dans le rapport pour éviter toute ambiguïté d’interprétation.

## 14. Spécification condensée

L’algorithme est une politique déterministe à deux bras qui maintient, pour chaque produit, une estimation EWMA de son **taux de conversion** et de la volatilité locale de ses résidus ; à la fin de chaque journée informative, il compare le taux de conversion observé au seuil $\hat p - x\hat\sigma$, puis bascule vers l’autre produit si une rupture baissière est détectée et qu’aucun cooldown n’est actif.

## 15. Formulation prête à intégrer dans le rapport

> Nous proposons un algorithme de détection de changement à deux bras fondé sur une moyenne exponentiellement pondérée du taux de conversion et sur une estimation locale de la volatilité des résidus. À la fin de chaque journée, l’algorithme observe le nombre de visiteurs et le nombre d’achats du produit affiché, calcule le taux de conversion journalier, puis le compare à un seuil de rupture unilatéral de type $\hat p - x\hat\sigma$, où $\hat p$ est l’estimation EWMA du taux de conversion courant du produit et $\hat\sigma$ une mesure locale de dispersion. Si le taux observé passe sous ce seuil et qu’aucun cooldown n’est actif, l’algorithme bascule vers l’autre produit pour la journée suivante ; sinon il conserve le produit courant. Les statistiques sont maintenues séparément pour chaque bras, mises à jour uniquement lorsqu’une journée informative est observée, et initialisées par une courte phase de warm-up. L’algorithme cherche ainsi à maximiser la conversion plutôt que le chiffre d’affaires, en détectant rapidement les ruptures de régime dans l’appétence des visiteurs pour le produit affiché.
