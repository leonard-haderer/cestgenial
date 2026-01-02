"""
Module de prédiction des crises utilisant des modèles d'apprentissage automatique
Auteur: Projet CGénial 2025

Utilise SVM (Support Vector Machine) ou Random Forest pour prédire:
- Le type de crise
- L'intensité d'une crise
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def preparer_donnees_prediction(df_crises):
    """
    Prépare les données pour l'entraînement des modèles de prédiction
    
    Args:
        df_crises (pandas.DataFrame): DataFrame des crises
    
    Returns:
        tuple: (X, y_type, y_intensite) - Features, labels pour type et intensité
    """
    # Sélectionne les features (caractéristiques) pour la prédiction
    # On utilise: latitude, longitude, population_touchee, accessibilite
    features = ['latitude', 'longitude', 'population_touchee', 'accessibilite']
    X = df_crises[features].copy()
    
    # Cible 1: Type de crise (classification)
    y_type = df_crises['type_crise'].copy()
    
    # Cible 2: Intensité (régression)
    y_intensite = df_crises['intensite'].copy()
    
    return X, y_type, y_intensite


def entrainer_modele_type_crise(X, y_type, modele_type='random_forest'):
    """
    Entraîne un modèle pour prédire le type de crise
    
    Args:
        X (pandas.DataFrame): Features (latitude, longitude, population, accessibilité)
        y_type (pandas.Series): Types de crises (labels)
        modele_type (str): 'svm' ou 'random_forest'
    
    Returns:
        tuple: (modele, scaler, label_encoder, score_accuracy)
    """
    # Encode les labels de type (convertit les chaînes en nombres)
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y_type)
    
    # Normalise les features (important pour SVM)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Divise les données en ensemble d'entraînement et de test (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42
    )
    
    # Crée et entraîne le modèle selon le type choisi
    if modele_type == 'svm':
        modele = SVC(kernel='rbf', probability=True, random_state=42)
    else:  # random_forest par défaut
        modele = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # Entraîne le modèle
    modele.fit(X_train, y_train)
    
    # Évalue le modèle
    y_pred = modele.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✓ Modèle {modele_type} entraîné - Précision: {accuracy*100:.2f}%")
    
    return modele, scaler, label_encoder, accuracy


def entrainer_modele_intensite(X, y_intensite, modele_type='random_forest'):
    """
    Entraîne un modèle pour prédire l'intensité d'une crise
    
    Args:
        X (pandas.DataFrame): Features (latitude, longitude, population, accessibilité)
        y_intensite (pandas.Series): Intensités des crises
        modele_type (str): 'svm' ou 'random_forest'
    
    Returns:
        tuple: (modele, scaler, score_r2, rmse)
    """
    # Normalise les features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Divise les données en ensemble d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_intensite, test_size=0.2, random_state=42
    )
    
    # Crée et entraîne le modèle
    if modele_type == 'svm':
        modele = SVR(kernel='rbf')
    else:  # random_forest par défaut
        modele = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # Entraîne le modèle
    modele.fit(X_train, y_train)
    
    # Évalue le modèle
    y_pred = modele.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"✓ Modèle {modele_type} entraîné - R²: {r2:.3f}, RMSE: {rmse:.2f}")
    
    return modele, scaler, r2, rmse


def predire_crise(nouvelle_crise, modele_type, scaler_type, label_encoder, 
                  modele_intensite, scaler_intensite):
    """
    Prédit le type et l'intensité d'une nouvelle crise
    
    Args:
        nouvelle_crise (dict): Dictionnaire avec les features de la crise
                              {'latitude': float, 'longitude': float, 
                               'population_touchee': int, 'accessibilite': float}
        modele_type: Modèle entraîné pour prédire le type
        scaler_type: Scaler utilisé pour normaliser les features (type)
        label_encoder: LabelEncoder pour décoder les types prédits
        modele_intensite: Modèle entraîné pour prédire l'intensité
        scaler_intensite: Scaler utilisé pour normaliser les features (intensité)
    
    Returns:
        dict: Dictionnaire avec les prédictions et intervalles de confiance
    """
    # Prépare les features
    features = ['latitude', 'longitude', 'population_touchee', 'accessibilite']
    X = pd.DataFrame([nouvelle_crise])[features]
    
    # Prédit le type de crise
    X_scaled_type = scaler_type.transform(X)
    
    # Utilise predict_proba si disponible (plus fiable) sinon predict
    if hasattr(modele_type, 'predict_proba'):
        probas = modele_type.predict_proba(X_scaled_type)[0]
        # Utilise la classe avec la probabilité la plus élevée
        type_pred_encoded = np.argmax(probas)
        confiance_type = probas.max() * 100
        types_possibles = label_encoder.classes_
        
        # S'assure que le nombre de probabilités correspond au nombre de classes
        n_probas = len(probas)
        n_classes = len(types_possibles)
        
        if n_probas == n_classes:
            probas_dict = {types_possibles[i]: probas[i]*100 for i in range(n_classes)}
        else:
            # Si incohérence, crée un dictionnaire avec les probabilités disponibles
            probas_dict = {types_possibles[i]: probas[i]*100 if i < n_probas else 0.0 
                          for i in range(n_classes)}
    else:
        # Si pas de predict_proba, utilise predict directement
        type_pred_encoded = modele_type.predict(X_scaled_type)[0]
        confiance_type = None
        probas_dict = None
    
    # Vérifie que la valeur prédite est dans la plage valide des classes
    n_classes = len(label_encoder.classes_)
    if type_pred_encoded < 0 or type_pred_encoded >= n_classes:
        # Si la valeur est hors limites, utilise la première classe par défaut
        print(f"⚠ Avertissement: Valeur prédite {type_pred_encoded} hors limites, utilisation de la classe 0")
        type_pred_encoded = 0
    
    # Décode la prédiction en toute sécurité
    try:
        type_pred = label_encoder.inverse_transform([type_pred_encoded])[0]
    except (ValueError, IndexError) as e:
        # En cas d'erreur, utilise la première classe disponible
        print(f"⚠ Erreur lors du décodage: {e}, utilisation de la première classe")
        type_pred = label_encoder.classes_[0] if len(label_encoder.classes_) > 0 else "Inconnu"
    
    # Prédit l'intensité
    X_scaled_intensite = scaler_intensite.transform(X)
    intensite_pred = modele_intensite.predict(X_scaled_intensite)[0]
    
    # Calcule un intervalle de confiance approximatif pour l'intensité
    # (en utilisant l'écart-type des prédictions sur l'ensemble de test)
    # Pour simplifier, on utilise un intervalle fixe de ±1.0
    intervalle_confiance = 1.0
    
    resultat = {
        'type_pred': type_pred,
        'intensite_pred': round(intensite_pred, 2),
        'confiance_type': round(confiance_type, 2) if confiance_type else None,
        'probabilites_types': probas_dict,
        'intensite_min': round(intensite_pred - intervalle_confiance, 2),
        'intensite_max': round(intensite_pred + intervalle_confiance, 2)
    }
    
    return resultat


def afficher_prediction(resultat):
    """
    Affiche les résultats de prédiction de manière lisible
    
    Args:
        resultat (dict): Dictionnaire avec les prédictions
    """
    print("\n" + "="*60)
    print("RÉSULTATS DE LA PRÉDICTION")
    print("="*60)
    print(f"Type de crise prédit: {resultat['type_pred']}")
    if resultat['confiance_type']:
        print(f"Confiance: {resultat['confiance_type']:.2f}%")
    
    print(f"\nIntensité prédite: {resultat['intensite_pred']}")
    print(f"Intervalle de confiance: [{resultat['intensite_min']}, {resultat['intensite_max']}]")
    
    if resultat['probabilites_types']:
        print("\nProbabilités pour chaque type de crise:")
        # Trie par probabilité décroissante
        types_tries = sorted(resultat['probabilites_types'].items(), 
                           key=lambda x: x[1], reverse=True)
        for type_crise, proba in types_tries[:5]:  # Affiche les 5 premiers
            print(f"  {type_crise}: {proba:.2f}%")
    
    print("="*60 + "\n")


def charger_donnees_pays(chemin_fichier=None):
    """
    Charge les données des pays (coordonnées et population)
    
    Args:
        chemin_fichier (str): Chemin vers le fichier CSV. Si None, utilise le fichier par défaut.
    
    Returns:
        pandas.DataFrame: DataFrame contenant les données des pays
    """
    if chemin_fichier is None:
        dossier_projet = Path(__file__).parent.parent
        chemin_fichier = dossier_projet / "data" / "pays_donnees.csv"
    
    if not Path(chemin_fichier).exists():
        raise FileNotFoundError(f"Le fichier {chemin_fichier} n'existe pas.")
    
    df_pays = pd.read_csv(chemin_fichier, encoding='utf-8')
    print(f"✓ {len(df_pays)} pays chargés depuis {chemin_fichier}")
    
    return df_pays


def rechercher_pays(nom_pays, df_pays):
    """
    Recherche un pays dans la base de données
    
    Args:
        nom_pays (str): Nom du pays à rechercher
        df_pays (pandas.DataFrame): DataFrame des pays
    
    Returns:
        dict ou None: Dictionnaire avec les données du pays ou None si non trouvé
    """
    # Recherche insensible à la casse et aux accents
    nom_pays_lower = nom_pays.lower().strip()
    
    # Essaie une correspondance exacte
    pays_trouve = df_pays[df_pays['pays'].str.lower().str.strip() == nom_pays_lower]
    
    if not pays_trouve.empty:
        pays = pays_trouve.iloc[0]
        return {
            'pays': pays['pays'],
            'latitude': float(pays['latitude']),
            'longitude': float(pays['longitude']),
            'population': int(pays['population'])
        }
    
    # Recherche partielle
    pays_trouve = df_pays[df_pays['pays'].str.lower().str.contains(nom_pays_lower, na=False)]
    
    if not pays_trouve.empty:
        if len(pays_trouve) == 1:
            pays = pays_trouve.iloc[0]
            return {
                'pays': pays['pays'],
                'latitude': float(pays['latitude']),
                'longitude': float(pays['longitude']),
                'population': int(pays['population'])
            }
        else:
            # Plusieurs correspondances
            print(f"\nPlusieurs pays correspondent à '{nom_pays}':")
            for idx, row in pays_trouve.iterrows():
                print(f"  - {row['pays']}")
            return None
    
    return None


def obtenir_types_risques(df_besoins):
    """
    Obtient la liste des types de risques disponibles
    
    Args:
        df_besoins (pandas.DataFrame): DataFrame des besoins par type de crise
    
    Returns:
        list: Liste des types de crises disponibles
    """
    return df_besoins['type_crise'].tolist()


def calculer_besoins_ressources(type_crise, intensite, population, df_besoins):
    """
    Calcule les besoins en ressources pour une crise donnée
    
    Args:
        type_crise (str): Type de crise
        intensite (float): Intensité de la crise (0-10)
        population (int): Population touchée
        df_besoins (pandas.DataFrame): DataFrame des besoins par type
    
    Returns:
        dict: Dictionnaire avec les besoins en ressources
    """
    # Trouve les besoins de base pour ce type de crise
    besoins_base = df_besoins[df_besoins['type_crise'] == type_crise]
    
    if besoins_base.empty:
        return {}
    
    besoins = besoins_base.iloc[0].to_dict()
    
    # Ajuste selon l'intensité
    facteur_intensite = intensite / 5.0
    
    # Ajuste selon la population (proportionnellement)
    # Utilise une population de référence de 10 millions
    facteur_population = min(population / 10000000.0, 10.0)  # Limite à 10x
    
    # Calcule les besoins ajustés
    besoins_ajustes = {}
    for ressource, quantite in besoins.items():
        if ressource != 'type_crise':
            besoins_ajustes[ressource] = int(quantite * facteur_intensite * facteur_population)
    
    return besoins_ajustes


def calculer_couts_pourcentages(besoins, budget_total=100000000):
    """
    Calcule les coûts et pourcentages du budget pour chaque ressource
    
    Args:
        besoins (dict): Dictionnaire des besoins en ressources
        budget_total (float): Budget total disponible (par défaut 100 millions)
    
    Returns:
        dict: Dictionnaire avec les coûts et pourcentages
    """
    # Coûts unitaires approximatifs (en euros/dollars)
    couts_unitaires = {
        'eau_potable_litres': 0.001,  # 1€ pour 1000 litres
        'tentes': 200,  # 200€ par tente
        'medicaments_doses': 5,  # 5€ par dose
        'hopitaux_campagne': 50000,  # 50000€ par hôpital
        'generateurs': 3000,  # 3000€ par générateur
        'vehicules_urgence': 25000,  # 25000€ par véhicule
        'personnel_medical': 5000,  # 5000€ par personne (salaire/mois)
        'denrees_alimentaires_kg': 2  # 2€ par kg
    }
    
    resultats = {}
    cout_total = 0
    
    for ressource, quantite in besoins.items():
        if ressource in couts_unitaires:
            cout = quantite * couts_unitaires[ressource]
            pourcentage = (cout / budget_total) * 100
            cout_total += cout
            
            resultats[ressource] = {
                'quantite': quantite,
                'cout': cout,
                'pourcentage': pourcentage
            }
    
    resultats['cout_total'] = cout_total
    resultats['pourcentage_total'] = (cout_total / budget_total) * 100
    
    return resultats


def calculer_distance_geographique(lat1, lon1, lat2, lon2):
    """
    Calcule la distance géographique entre deux points (formule de Haversine)
    
    Args:
        lat1, lon1: Coordonnées du premier point
        lat2, lon2: Coordonnées du deuxième point
    
    Returns:
        float: Distance en kilomètres
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Rayon de la Terre en kilomètres
    R = 6371.0
    
    # Convertit en radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Différences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Formule de Haversine
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    
    return distance


def calculer_probabilite_evenement(pays_lat, pays_lon, type_crise, intensite, df_crises):
    """
    Calcule la probabilité qu'un événement d'un type et d'une intensité donnés
    se produise dans un pays spécifique
    
    Args:
        pays_lat (float): Latitude du pays
        pays_lon (float): Longitude du pays
        type_crise (str): Type de crise
        intensite (float): Intensité de la crise (0-10)
        df_crises (pandas.DataFrame): DataFrame des crises historiques
    
    Returns:
        dict: Dictionnaire avec la probabilité et les détails
    """
    # Filtre les crises du même type
    crises_meme_type = df_crises[df_crises['type_crise'] == type_crise].copy()
    
    if crises_meme_type.empty:
        # Si aucune crise de ce type dans l'historique, probabilité faible
        return {
            'probabilite': 5.0,
            'niveau': 'Très faible',
            'explication': f'Aucune crise de type {type_crise} dans l historique'
        }
    
    # Calcule la distance entre le pays et chaque crise historique
    distances = []
    intensites_proches = []
    
    for idx, crise in crises_meme_type.iterrows():
        distance = calculer_distance_geographique(
            pays_lat, pays_lon,
            crise['latitude'], crise['longitude']
        )
        distances.append(distance)
        
        # Vérifie si l'intensité est proche
        diff_intensite = abs(crise['intensite'] - intensite)
        if diff_intensite <= 2.0:  # Intensité similaire (±2)
            intensites_proches.append(crise)
    
    # Facteur 1: Proximité géographique
    # Plus il y a de crises proches, plus la probabilité est élevée
    if distances:
        distance_min = min(distances)
        distance_moyenne = np.mean(distances)
        
        # Probabilité basée sur la distance (plus proche = plus probable)
        # Normalise entre 0 et 1 (distance de 0-5000 km)
        facteur_proximite = max(0, 1 - (distance_min / 5000))
    else:
        facteur_proximite = 0.1
        distance_min = 10000
        distance_moyenne = 10000
    
    # Facteur 2: Fréquence du type de crise
    frequence_type = len(crises_meme_type) / len(df_crises)
    
    # Facteur 3: Intensité similaire
    if intensites_proches:
        facteur_intensite = len(intensites_proches) / len(crises_meme_type)
    else:
        # Si aucune crise d'intensité similaire, réduit la probabilité
        facteur_intensite = 0.3
    
    # Facteur 4: Intensité demandée (plus intense = moins probable)
    facteur_intensite_demandee = 1 - (intensite / 10) * 0.3  # Réduit de 0-30%
    
    # Calcule la probabilité de base
    probabilite_base = 50.0  # 50% de base
    
    # Ajuste selon les facteurs
    probabilite = probabilite_base * facteur_proximite * (1 + frequence_type * 2) * facteur_intensite * facteur_intensite_demandee
    
    # Limite entre 1% et 95%
    probabilite = max(1.0, min(95.0, probabilite))
    
    # Détermine le niveau de probabilité
    if probabilite >= 70:
        niveau = 'Très élevée'
    elif probabilite >= 50:
        niveau = 'Élevée'
    elif probabilite >= 30:
        niveau = 'Modérée'
    elif probabilite >= 15:
        niveau = 'Faible'
    else:
        niveau = 'Très faible'
    
    # Crée l'explication
    nb_crises_proches = sum(1 for d in distances if d < 1000)
    explication = f"{len(crises_meme_type)} crise(s) de type {type_crise} dans l historique"
    if distance_min < 1000:
        explication += f", {nb_crises_proches} crise(s) à moins de 1000 km"
    else:
        explication += f", crise la plus proche à {distance_min:.0f} km"
    
    if intensites_proches:
        explication += f", {len(intensites_proches)} crise(s) d intensite similaire"
    
    return {
        'probabilite': round(probabilite, 2),
        'niveau': niveau,
        'explication': explication,
        'distance_min': round(distance_min, 0),
        'nb_crises_historiques': len(crises_meme_type),
        'nb_crises_proches': nb_crises_proches
    }


if __name__ == "__main__":
    # Test du module
    print("Test du module de prédiction...")
    from src.chargement_donnees import charger_crises
    
    crises = charger_crises()
    X, y_type, y_intensite = preparer_donnees_prediction(crises)
    
    # Entraîne les modèles
    modele_type, scaler_type, le, acc = entrainer_modele_type_crise(X, y_type, 'random_forest')
    modele_int, scaler_int, r2, rmse = entrainer_modele_intensite(X, y_intensite, 'random_forest')
    
    # Teste une prédiction
    nouvelle_crise = {
        'latitude': 35.0,
        'longitude': 139.0,
        'population_touchee': 1000000,
        'accessibilite': 0.7
    }
    
    resultat = predire_crise(nouvelle_crise, modele_type, scaler_type, le, 
                            modele_int, scaler_int)
    afficher_prediction(resultat)


