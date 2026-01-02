"""
Module de chargement des données de crises et de besoins en ressources
Auteur: Projet CGénial 2025
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime


def charger_crises(chemin_fichier=None, seulement_actuelles=False):
    """
    Charge les données des crises depuis un fichier CSV
    
    Args:
        chemin_fichier (str): Chemin vers le fichier CSV. Si None, utilise le fichier par défaut.
        seulement_actuelles (bool): Si True, ne charge que les crises en cours (en_cours=True)
    
    Returns:
        pandas.DataFrame: DataFrame contenant les données des crises
    """
    # Si aucun chemin n'est fourni, utilise le fichier par défaut dans le dossier data
    if chemin_fichier is None:
        # Obtient le chemin du répertoire parent (racine du projet)
        dossier_projet = Path(__file__).parent.parent
        chemin_fichier = dossier_projet / "data" / "Base_Crises_TresTres_Enrichie_CGenial.csv"
    
    # Vérifie que le fichier existe
    if not os.path.exists(chemin_fichier):
        raise FileNotFoundError(f"Le fichier {chemin_fichier} n'existe pas.")
    
    # Charge le fichier CSV dans un DataFrame pandas
    df_crises = pd.read_csv(chemin_fichier, encoding='utf-8')
    
    # Convertit la colonne date en format datetime pour faciliter les manipulations
    df_crises['date'] = pd.to_datetime(df_crises['date'])
    
    # Convertit la colonne en_cours en booléen si elle existe
    if 'en_cours' in df_crises.columns:
        df_crises['en_cours'] = df_crises['en_cours'].astype(bool)
    
    # Convertit date_fin en datetime si elle existe
    if 'date_fin' in df_crises.columns:
        df_crises['date_fin'] = pd.to_datetime(df_crises['date_fin'], errors='coerce')
    
    # Filtre les crises actuelles si demandé
    if seulement_actuelles:
        if 'en_cours' in df_crises.columns:
            df_crises = df_crises[df_crises['en_cours'] == True].copy()
        else:
            # Si pas de colonne en_cours, filtre par date (crises récentes)
            date_limite = datetime.now() - pd.Timedelta(days=365)
            df_crises = df_crises[df_crises['date'] >= date_limite].copy()
    
    # Affiche un message de confirmation
    if seulement_actuelles:
        print(f"✓ {len(df_crises)} crises actuelles chargées depuis {chemin_fichier}")
    else:
        print(f"✓ {len(df_crises)} crises chargées depuis {chemin_fichier}")
    
    return df_crises


def charger_besoins(chemin_fichier=None):
    """
    Charge les besoins en ressources par type de crise depuis un fichier CSV
    
    Args:
        chemin_fichier (str): Chemin vers le fichier CSV. Si None, utilise le fichier par défaut.
    
    Returns:
        pandas.DataFrame: DataFrame contenant les besoins par type de crise
    """
    # Si aucun chemin n'est fourni, utilise le fichier par défaut
    if chemin_fichier is None:
        dossier_projet = Path(__file__).parent.parent
        chemin_fichier = dossier_projet / "data" / "Besoins_Crises_Passees.csv"
    
    # Vérifie que le fichier existe
    if not os.path.exists(chemin_fichier):
        raise FileNotFoundError(f"Le fichier {chemin_fichier} n'existe pas.")
    
    # Charge le fichier CSV
    df_besoins = pd.read_csv(chemin_fichier, encoding='utf-8')
    
    # Affiche un message de confirmation
    print(f"✓ Besoins chargés pour {len(df_besoins)} types de crises depuis {chemin_fichier}")
    
    return df_besoins


def calculer_besoins_crise(crise, df_besoins):
    """
    Calcule les besoins en ressources pour une crise spécifique
    en fonction de son type et de son intensité
    
    Args:
        crise (pandas.Series): Une ligne du DataFrame des crises
        df_besoins (pandas.DataFrame): DataFrame des besoins par type
    
    Returns:
        dict: Dictionnaire contenant les besoins calculés
    """
    # Récupère le type de la crise
    type_crise = crise['type_crise']
    
    # Trouve les besoins correspondants à ce type de crise
    besoins_type = df_besoins[df_besoins['type_crise'] == type_crise]
    
    # Si le type n'est pas trouvé, retourne des besoins par défaut
    if besoins_type.empty:
        print(f"⚠ Avertissement: Type de crise '{type_crise}' non trouvé dans les besoins")
        return {}
    
    # Récupère la première ligne (normalement il n'y en a qu'une par type)
    besoins = besoins_type.iloc[0].to_dict()
    
    # Ajuste les besoins selon l'intensité de la crise
    # Plus l'intensité est élevée, plus les besoins sont importants
    facteur_intensite = crise['intensite'] / 5.0  # Normalise par rapport à une intensité moyenne de 5
    
    # Crée un dictionnaire des besoins ajustés
    besoins_ajustes = {}
    for ressource, quantite in besoins.items():
        # Ne multiplie pas le type_crise (c'est une chaîne de caractères)
        if ressource != 'type_crise':
            # Arrondit à l'entier le plus proche
            besoins_ajustes[ressource] = int(quantite * facteur_intensite)
    
    return besoins_ajustes


def afficher_statistiques_crises(df_crises):
    """
    Affiche des statistiques sur les crises chargées
    
    Args:
        df_crises (pandas.DataFrame): DataFrame des crises
    """
    print("\n" + "="*60)
    print("STATISTIQUES DES CRISES")
    print("="*60)
    print(f"Nombre total de crises: {len(df_crises)}")
    
    # Affiche le nombre de crises actuelles si la colonne existe
    if 'en_cours' in df_crises.columns:
        nb_actuelles = df_crises['en_cours'].sum()
        print(f"Nombre de crises actuelles: {nb_actuelles}")
        print(f"Nombre de crises passées: {len(df_crises) - nb_actuelles}")
    
    print(f"\nRépartition par type de crise:")
    print(df_crises['type_crise'].value_counts())
    print(f"\nRépartition par pays:")
    print(df_crises['pays'].value_counts().head(10))
    print(f"\nIntensité moyenne: {df_crises['intensite'].mean():.2f}")
    print(f"Intensité minimale: {df_crises['intensite'].min():.2f}")
    print(f"Intensité maximale: {df_crises['intensite'].max():.2f}")
    print(f"\nPopulation totale touchée: {df_crises['population_touchee'].sum():,}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test du module
    print("Test du module de chargement des données...")
    crises = charger_crises()
    besoins = charger_besoins()
    afficher_statistiques_crises(crises)
    
    print("\nCrises actuelles uniquement:")
    crises_actuelles = charger_crises(seulement_actuelles=True)
    print(f"Nombre de crises actuelles: {len(crises_actuelles)}")
    if len(crises_actuelles) > 0:
        print("\nListe des crises actuelles:")
        print(crises_actuelles[['nom_crise', 'type_crise', 'pays', 'date']].to_string())

