# Spécification complète du problème

Ton scénario se spécifie naturellement comme un **bandit stochastique non stationnaire à 2 bras, piecewise-stationary, avec état latent**. Dans le vocabulaire du cours, ce n’est pas vraiment un problème de **volatile arms** — car les deux produits restent toujours disponibles — mais un cas de **restless bandit / non-stationary bandit**, puisque la **distribution potentielle de récompense** associée à chaque bras peut changer au cours du temps, y compris pour un bras non sélectionné. Autrement dit, ce qui évolue n’est pas un chiffre d’affaires effectivement observé pour le produit non affiché, mais la loi du chiffre d’affaires **qu’il produirait s’il était affiché ce jour-là**.

## 1. Définition canonique du problème

On considère un horizon fini de $T$ jours, indexés par $t = 1,\dots,T$.

À chaque jour $t$, l’agent choisit **un seul** produit à afficher sur le site :

$$
\mathcal A = \{C,U\}
$$

où $C$ désigne la crème solaire et $U$ le parapluie.

Le choix est fait à partir de l’historique observé jusqu’au jour précédent. Mathématiquement, on écrit :

$$
A_t \in \mathcal A.
$$

Pour éviter l’ambiguïté « décision à la clôture pour les 24 h suivantes », on adopte la convention standard suivante : le choix $A_t$ est fait **au début** du jour $t$, puis la récompense du jour $t$ est observée **à la fin** du jour $t$. C’est strictement équivalent à ton protocole, à un simple décalage d’indice près.

## 2. État caché de l’environnement

L’environnement possède un état latent

$$
Z_t \in \{S,R\},
$$

où :

- $S$ = beau temps / soleil ;
- $R$ = pluie.

Cet état **n’est jamais observé** par l’agent.

Le cadre naturel ici est **piecewise-stationary** : il existe des temps de rupture

$$
1=\tau_0 < \tau_1 < \cdots < \tau_{\Upsilon_T} < \tau_{\Upsilon_T+1}=T+1
$$

tels que $Z_t$ reste constant sur chaque intervalle

$$
[\tau_j,\tau_{j+1}-1].
$$

Autrement dit, l’environnement évolue par régimes successifs.

Dans ton cas, la spécification la plus simple est :

- les régimes alternent soleil / pluie ;
- la longueur de chaque régime est d’environ 100 jours.

Pour que le simulateur soit **entièrement spécifié**, il faut choisir une loi explicite pour ces longueurs. Par exemple :

$$
L_j = \tau_{j+1}-\tau_j \sim \mathcal U\{90,\dots,110\}
$$

ou, plus simplement encore,

$$
L_j \equiv 100.
$$

## 3. Récompenses potentielles, contre-factuelles et récompense observée

Dans la formalisation standard des bandits non stationnaires, on définit pour chaque jour $t$ et chaque bras $a \in \mathcal A$ une variable de récompense potentielle

$$
X_t(a),
$$

où $X_t(a)$ représente **la récompense qui serait obtenue au jour $t$ si l’action $a$ était choisie à cette date**.

L’agent ne choisissant qu’un seul bras par jour, il n’observe que

$$
R_t = X_t(A_t).
$$

Autrement dit :

- si $A_t=C$, l’agent observe $X_t(C)$ ;
- si $A_t=U$, l’agent observe $X_t(U)$ ;
- la récompense potentielle de l’autre bras existe comme objet de modélisation, mais elle reste **non observée**.

### Remarque importante

Le bras non joué ne génère **pas** de ventes observées ce jour-là. Il serait donc incorrect de dire qu’il “réalise un chiffre d’affaires”. En revanche, dans la modélisation bandit, on lui associe une récompense potentielle $X_t(a)$, c’est-à-dire le chiffre d’affaires **qu’il aurait généré s’il avait été affiché**. Quand on dit que « la distribution de récompense d’un bras non joué peut changer », on parle de la loi de cette variable potentielle, pas d’un chiffre d’affaires effectivement observé.

## 4. Modèle probabiliste au niveau visiteur

Soit $N_t$ le nombre de visiteurs du site au jour $t$.

Pour chaque visiteur $n \in \{1,\dots,N_t\}$ et pour chaque action $a \in \{C,U\}$, on définit une variable binaire potentielle d’achat

$$
Y_{t,n}(a) \in \{0,1\},
$$

où $Y_{t,n}(a)=1$ signifie que le visiteur $n$ achèterait le produit $a$ **si ce produit lui était proposé** au jour $t$.

Conditionnellement à l’état météo $Z_t$, la probabilité d’achat dépend du produit considéré :

$$
\mathbb P(Y_{t,n}(C)=1 \mid Z_t=S)=0.6,
\qquad
\mathbb P(Y_{t,n}(C)=1 \mid Z_t=R)=0.1,
$$

$$
\mathbb P(Y_{t,n}(U)=1 \mid Z_t=S)=0.3,
\qquad
\mathbb P(Y_{t,n}(U)=1 \mid Z_t=R)=0.55.
$$

Autrement dit, la matrice des probabilités d’achat est

$$
P =
\begin{pmatrix}
0.6 & 0.1 \\
0.3 & 0.55
\end{pmatrix}
$$

avec lignes $C,U$ et colonnes $S,R$.

Une hypothèse standard est que, conditionnellement à $(Z_t,N_t)$, pour un bras fixé $a$, les variables

$$
Y_{t,1}(a), \dots, Y_{t,N_t}(a)
$$

sont indépendantes et identiquement distribuées selon une loi de Bernoulli de paramètre $p_{a,Z_t}$. Il n’est pas nécessaire de spécifier la dépendance éventuelle entre $Y_{t,n}(C)$ et $Y_{t,n}(U)$, puisqu’une seule action est effectivement jouée.

On définit alors le **nombre potentiel** de ventes du bras $a$ au jour $t$ par

$$
Q_t(a) = \sum_{n=1}^{N_t} Y_{t,n}(a).
$$

Donc, conditionnellement à $(Z_t=z,N_t)$,

$$
Q_t(a)\mid (Z_t=z,N_t) \sim \mathrm{Binomial}(N_t,p_{a,z}).
$$

Le nombre de ventes effectivement observé au jour $t$ est ensuite

$$
Q_t = Q_t(A_t).
$$

## 5. Définition exacte de la récompense

Ici il faut être rigoureux : tu dis que la récompense est le **CA quotidien**, pas simplement le nombre de ventes.

Soit donc :

- $m_C >0$ : revenu unitaire pour une crème vendue ;
- $m_U >0$ : revenu unitaire pour un parapluie vendu.

On définit la **récompense potentielle** du bras $a$ au jour $t$ par

$$
X_t(a) = m_a\,Q_t(a).
$$

La récompense effectivement observée est alors

$$
R_t = X_t(A_t).
$$

Conditionnellement à $(Z_t=z,N_t)$, on a donc

$$
X_t(a)\mid (Z_t=z,N_t) \sim m_a \cdot \mathrm{Binomial}(N_t,p_{a,z}).
$$

Son espérance conditionnelle vaut

$$
\mu_t(a) = \mathbb E[X_t(a)\mid Z_t=z,N_t]
= m_a N_t p_{a,z}.
$$

Sa variance conditionnelle vaut

$$
\mathrm{Var}(X_t(a)\mid Z_t=z,N_t)
= m_a^2 N_t p_{a,z}(1-p_{a,z}).
$$

### Point très important

Si tu gardes le **CA** comme récompense, alors les seules probabilités d’achat ne suffisent pas à définir quel bras est optimal : il faut aussi fixer $m_C$ et $m_U$.

Par exemple :

- au soleil, la crème est optimale si

$$
0.6\,m_C > 0.3\,m_U
\quad\Longleftrightarrow\quad
m_C > 0.5\,m_U ;
$$

- sous la pluie, le parapluie est optimal si

$$
0.55\,m_U > 0.1\,m_C
\quad\Longleftrightarrow\quad
m_U > 0.1818\,m_C.
$$

Donc si tu veux une instance **sans ambiguïté**, il faut choisir explicitement :

1. soit $m_C = m_U = 1$, et alors la récompense devient simplement le nombre de ventes ;
2. soit des valeurs réelles précises pour $m_C$ et $m_U$.

Pour un mini-projet, la version la plus propre est souvent :

$$
m_C = m_U = 1,
\qquad
R_t = Q_t.
$$

## 6. Information disponible à l’agent

À la fin du jour $t$, l’agent observe uniquement :

- l’action jouée $A_t$ ;
- la récompense réalisée $R_t$.

Il **n’observe pas** :

- la météo $Z_t$ ;
- la récompense potentielle du bras non joué $X_t(a')$, qui reste contrefactuelle et non observée ;
- les achats contre-factuels qui auraient eu lieu si l’autre produit avait été affiché.

L’historique disponible avant de prendre la décision au jour $t$ est donc

$$
H_{t-1} = (A_1,R_1,\dots,A_{t-1},R_{t-1}).
$$

Une politique est une suite d’applications

$$
\pi_t : H_{t-1} \mapsto \Delta(\mathcal A),
$$

où $\Delta(\mathcal A)$ désigne l’ensemble des distributions sur les actions. Si la politique est déterministe, alors

$$
A_t = \pi_t(H_{t-1}).
$$

## 7. Objectif de l’agent

L’objectif est de maximiser la récompense cumulée attendue :

$$
J_T(\pi) = \mathbb E_\pi\left[\sum_{t=1}^T R_t\right].
$$

Comme l’environnement est non stationnaire, le bon benchmark n’est pas « le meilleur bras moyen global », mais **le meilleur bras à chaque date**.

On définit donc le bras oracle instantané :

$$
a_t^\star = \arg\max_{a\in\mathcal A} \mu_t(a).
$$

Le **regret dynamique** est alors

$$
\mathrm{Reg}_T(\pi)
=
\mathbb E_\pi\left[\sum_{t=1}^T \big(\mu_t(a_t^\star)-\mu_t(A_t)\big)\right].
$$

Cette quantité mesure exactement la perte causée par le fait de ne pas suivre immédiatement le meilleur produit lorsque le régime météo change.

## 8. Hypothèses structurelles du problème

La spécification complète inclut les hypothèses suivantes :

$$
\textbf{(H1)} \quad \text{Les deux bras sont toujours disponibles.}
$$

$$
\textbf{(H2)} \quad Z_t \text{ est exogène et n’est pas influencé par l’action } A_t.
$$

$$
\textbf{(H3)} \quad \text{Les distributions potentielles de récompense } \nu_{t,a}=\mathcal L(X_t(a)) \text{ peuvent changer aux breakpoints pour les deux bras,}
$$
$$
\text{y compris pour celui qui n’est pas sélectionné et reste donc non observé.}
$$

$$
\textbf{(H4)} \quad \text{Conditionnellement à }(Z_t,N_t), \text{ les récompenses journalières potentielles sont générées stochastiquement.}
$$

$$
\textbf{(H5)} \quad \text{L’agent n’observe aucun contexte explicite.}
$$

Ces hypothèses font de ton problème un **bandit non stationnaire à contexte latent**.

## 9. Ce qui appartient au problème, et ce qui n’y appartient pas

La **spécification du problème** contient :

- l’horizon $T$ ;
- les actions $\{C,U\}$ ;
- l’état caché $\{S,R\}$ ;
- la loi d’évolution de $Z_t$ ;
- la matrice des probabilités d’achat ;
- le nombre de visiteurs $N_t$ ou sa loi ;
- les revenus unitaires $m_C,m_U$ ;
- la structure d’observation partielle ;
- l’objectif et le regret.

En revanche, **n’appartiennent pas à la spécification du problème** :

- l’EMA ;
- le seuil $x$ ;
- le paramètre $\alpha$ ;
- l’ATR / volatilité EWMA ;
- le cooldown ;
- le stop-loss.

Tout cela relève de la **spécification de l’algorithme**.

## 10. Version minimale entièrement instanciée pour le simulateur

Si tu veux une instance simple, complètement fermée, sans degré de liberté restant, prends :

$$
T \text{ fixé},
\qquad
\mathcal A=\{C,U\},
\qquad
Z_t \in \{S,R\},
$$

$$
L_j \equiv 100 \text{ jours et alternance stricte } S,R,S,R,\dots
$$

$$
N_t \equiv N \text{ constant},
\qquad
m_C = m_U = 1.
$$

Alors, pour chaque jour $t$ et chaque bras $a$, la récompense potentielle $X_t(a)$ vérifie :

$$
X_t(C)\mid Z_t=S \sim \mathrm{Bin}(N,0.6),
\qquad
X_t(C)\mid Z_t=R \sim \mathrm{Bin}(N,0.1),
$$

$$
X_t(U)\mid Z_t=S \sim \mathrm{Bin}(N,0.3),
\qquad
X_t(U)\mid Z_t=R \sim \mathrm{Bin}(N,0.55),
$$

et l’agent observe seulement

$$
R_t = X_t(A_t).
$$

Dans cette version, l’oracle est :

- $a_t^\star = C$ si $Z_t=S$ ;
- $a_t^\star = U$ si $Z_t=R$.

## 11. Formulation compacte prête à mettre dans le rapport

> Nous considérons un bandit stochastique non stationnaire à deux bras, piecewise-stationary, avec état latent. À chaque jour $t \in \{1,\dots,T\}$, l’agent choisit un bras $A_t \in \{C,U\}$, où $C$ désigne la crème solaire et $U$ le parapluie. L’environnement possède un état caché $Z_t \in \{S,R\}$ représentant respectivement le soleil et la pluie. L’état $Z_t$ reste constant sur des intervalles successifs séparés par des breakpoints inconnus. Pour chaque bras $a$, on définit une récompense potentielle $X_t(a)$, c’est-à-dire la récompense qui serait obtenue si $a$ était joué au temps $t$. Conditionnellement à $Z_t$, cette récompense suit une loi binomiale pondérée par le revenu unitaire : $X_t(a)\sim m_a\mathrm{Bin}(N_t,p_{a,Z_t})$, avec $p_{C,S}=0.6$, $p_{C,R}=0.1$, $p_{U,S}=0.3$, $p_{U,R}=0.55$. L’agent n’observe que la récompense du bras joué, $R_t=X_t(A_t)$. Une politique $\pi$ choisit $A_t$ à partir de l’historique $H_{t-1}=(A_1,R_1,\dots,A_{t-1},R_{t-1})$. L’objectif est de maximiser $\mathbb E[\sum_{t=1}^T R_t]$, ou de manière équivalente de minimiser le regret dynamique $\mathbb E[\sum_{t=1}^T(\mu_t(a_t^\star)-\mu_t(A_t))]$, où $a_t^\star$ est le bras d’espérance instantanée maximale. Ce problème relève d’un cadre de bandit non stationnaire/restless, et non d’un cadre volatile-arms, car les bras restent toujours disponibles alors que leurs distributions potentielles de récompense évoluent dans le temps sous l’effet d’un état latent exogène.

## Sources mobilisées

- `mini_projet.pdf`
- `Piecewise_Stationary_Bandits.pdf`
