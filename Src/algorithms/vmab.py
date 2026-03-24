import numpy as np

"""nous possédons un site internet qui peut vendre des crèmes solaires ou des parapluies.
Malheuresement, en raison de moyens très limités, nous ne pouvons mettre en avant sur ce site qu'un produit à la fois. 
Le but de l'algo est de choisir à chaque fois le produit à mettre en avant, en se basant sur les données d'achat précédentes.

Nous choisissons d'utiliser une technique courante en finance : la stratégie de breakout basée sur les moyennes mobiles exponentielles (EMA).
L'idée est de calculer une EMA du CA quotidien du site et à chaque fois que le CA quotidien franchit à la baisse l'EMA, nous changeons de produit à mettre en avant.

Les conditions météo déterminent les proba d'achat de chaque produit :
- Parapluie : 0.55 en cas de pluie, 0.3 en cas de beau temps
- Crème solaire : 0.6 en cas de beau temps, 0.1 en cas de pluie

Comment on sait sur 100 clients, combien de parapluies ont été vendus ? 
"""


#formule utilisé en finance 

beau_temps = 1
pluie = 0

def alpha(n):
    return 1 / (n + 1)

def ema(series, n):
    ema_values = np.zeros(len(series))
    ema_values[0] = series[0]
    for i in range(1, len(series)):
        ema_values[i] = alpha(n) * series[i] + (1 - alpha(n)) * ema_values[i - 1]
    return ema_values
    
def vente_parapluies(n_visiteurs, meteo, produit_en_vente):
    if produit_en_vente == 'parapluie':
        if meteo == beau_temps:
            vente = np.random.binomial(n_visiteurs, 0.3)
        elif meteo == pluie:
            vente = np.random.binomial(n_visiteurs, 0.55)
        else: 
            raise RuntimeError('meteo doit etre egal à 1 ou 0')
    elif produit_en_vente == 'creme':
        vente = 0
    else:
        raise RuntimeError('Produit doit être crème ou parapluie')
    return vente

def vente_creme(n_visiteurs, meteo, produit_en_vente):
    if produit_en_vente == 'creme':
        if meteo == beau_temps:
            vente = np.random.binomial(n_visiteurs, 0.6)
        elif meteo == pluie:
            vente = np.random.binomial(n_visiteurs, 0.1)
        else: 
            raise RuntimeError('meteo doit etre egal à 1 ou 0')
    elif produit_en_vente == 'parapluie':
        vente = 0
    else:
        raise RuntimeError('Produit doit être crème ou parapluie')
    return vente

def vente_total(n_visiteurs, meteo, produit_en_vente):
    return vente_parapluies(n_visiteurs, meteo, produit_en_vente) + vente_creme(n_visiteurs, meteo, produit_en_vente)

 
print(vente_total(100, beau_temps, 'parapluie'))
print(vente_total(100, pluie, 'creme'))
print(vente_total(100, beau_temps, 'creme'))
print(vente_total(100, pluie, 'parapluie'))

#def produit_a_mettre_en_avant(