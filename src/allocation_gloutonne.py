"""
Module d'allocation proportionnelle des ressources en cas de crise
Auteur: Projet CGénial 2025

Algorithme d'allocation proportionnelle: 
- Filtre uniquement les crises actuelles (en_cours=True)
- Calcule un score d'urgence pour chaque crise
- Réserve 25% des ressources (non utilisées)
- Alloue les 75% restants proportionnellement au score d'urgence de chaque crise
- Respecte les besoins réels de chaque crise (ne dépasse pas le besoin)
"""

import pandas as pd
import numpy as np
from pathlib import Path


def calculer_score_urgence(crise):
    """
    Calcule le score d'urgence d'une crise
    Score = intensité × population touchée × (1 - accessibilité)
    Plus le score est élevé, plus la crise est urgente
    
    Args:
        crise (pandas.Series): Une ligne du DataFrame des crises
    
    Returns:
        float: Score d'urgence de la crise
    """
    # Récupère les valeurs nécessaires
    intensite = crise['intensite']
    population = crise['population_touchee']
    accessibilite = crise['accessibilite']
    
    # Calcule le score: intensité × population × (1 - accessibilité)
    # (1 - accessibilité) car une faible accessibilité augmente l'urgence
    score = intensite * population * (1 - accessibilite)
    
    return score


def allouer_ressources_glouton(df_crises, df_besoins, stock_disponible, seulement_actuelles=True):
    """
    Alloue les ressources disponibles aux crises selon un algorithme proportionnel au produit (score d'urgence × population touchée)
    - 25% des ressources sont réservées (non utilisées)
    - 75% des ressources sont allouées proportionnellement au produit (score d'urgence × population touchée) de chaque crise
    Ne considère que les crises actuelles (en_cours=True) par défaut
    
    Args:
        df_crises (pandas.DataFrame): DataFrame des crises
        df_besoins (pandas.DataFrame): DataFrame des besoins par type de crise
        stock_disponible (dict): Dictionnaire des ressources disponibles
                                 Ex: {'eau_potable_litres': 10000000, 'tentes': 5000, ...}
        seulement_actuelles (bool): Si True, ne considère que les crises en cours
    
    Returns:
        tuple: (df_allocation, stock_restant, stock_reserve) - DataFrame avec allocations, stocks restants et stocks réservés
    """
    # Filtre les crises actuelles si demandé
    if seulement_actuelles:
        if 'en_cours' in df_crises.columns:
            df_crises_filtre = df_crises[df_crises['en_cours'] == True].copy()
            if len(df_crises_filtre) == 0:
                print("⚠ Aucune crise actuelle trouvée. Vérifiez la colonne 'en_cours' dans les données.")
                # Calcule le stock réservé (25%)
                stock_reserve = {k: int(v * 0.25) for k, v in stock_disponible.items()}
                return pd.DataFrame(), stock_disponible, stock_reserve
        else:
            print("⚠ Colonne 'en_cours' non trouvée. Toutes les crises seront considérées.")
            df_crises_filtre = df_crises.copy()
    else:
        df_crises_filtre = df_crises.copy()
    
    # Crée une copie du DataFrame des crises pour ne pas modifier l'original
    df_allocation = df_crises_filtre.copy()
    
    if len(df_allocation) == 0:
        print("⚠ Aucune crise à traiter.")
        # Calcule le stock réservé (25%)
        stock_reserve = {k: int(v * 0.25) for k, v in stock_disponible.items()}
        return df_allocation, stock_disponible, stock_reserve
    
    # Calcule le score d'urgence pour chaque crise
    df_allocation['score_urgence'] = df_allocation.apply(calculer_score_urgence, axis=1)
    
    # Calcule le produit (score d'urgence × population touchée) pour chaque crise
    df_allocation['produit_score_population'] = df_allocation['score_urgence'] * df_allocation['population_touchee']
    
    # Trie les crises par score d'urgence décroissant (les plus urgentes en premier)
    df_allocation = df_allocation.sort_values('score_urgence', ascending=False).reset_index(drop=True)
    
    # Calcule la somme totale des produits (score × population) pour la proportionnalité
    somme_produits = df_allocation['produit_score_population'].sum()
    
    # Initialise les colonnes d'allocation pour chaque type de ressource
    ressources = [col for col in df_besoins.columns if col != 'type_crise']
    
    # Calcule le stock réservé (25% de chaque ressource)
    stock_reserve = {}
    stock_allouable = {}
    for ressource in ressources:
        if ressource in stock_disponible:
            stock_reserve[ressource] = int(stock_disponible[ressource] * 0.25)
            stock_allouable[ressource] = stock_disponible[ressource] - stock_reserve[ressource]
        else:
            stock_reserve[ressource] = 0
            stock_allouable[ressource] = 0
    
    # Crée un dictionnaire pour suivre les stocks alloués (pour vérification)
    stock_alloue_total = {ressource: 0 for ressource in ressources}
    
    # Initialise toutes les allocations à 0
    for ressource in ressources:
        df_allocation[f'allocation_{ressource}'] = 0
        df_allocation[f'besoin_{ressource}'] = 0
        df_allocation[f'pourcentage_satisfait_{ressource}'] = 0.0
    
    # Calcule les allocations proportionnelles pour chaque crise
    for idx, crise in df_allocation.iterrows():
        # Calcule les besoins pour cette crise
        besoins_crise = calculer_besoins_crise(crise, df_besoins)
        
        # Pour chaque ressource, calcule l'allocation proportionnelle
        for ressource in ressources:
            # Enregistre le besoin total
            besoin = besoins_crise.get(ressource, 0)
            df_allocation.at[idx, f'besoin_{ressource}'] = besoin
            
            if ressource in stock_allouable and somme_produits > 0:
                # Calcule la part proportionnelle au produit (score d'urgence × population touchée)
                produit_crise = crise['produit_score_population']
                part_proportionnelle = (produit_crise / somme_produits) * stock_allouable[ressource]
                
                # L'allocation est le minimum entre :
                # 1. La part proportionnelle calculée
                # 2. Le besoin réel de la crise
                # 3. Le stock allouable restant (pour éviter de dépasser)
                allocation = min(part_proportionnelle, besoin, stock_allouable[ressource] - stock_alloue_total[ressource])
                
                # S'assure que l'allocation n'est pas négative
                allocation = max(0, int(allocation))
                
                df_allocation.at[idx, f'allocation_{ressource}'] = allocation
                stock_alloue_total[ressource] += allocation
                
                # Calcule le pourcentage de besoin satisfait
                if besoin > 0:
                    pourcentage = (allocation / besoin) * 100
                    df_allocation.at[idx, f'pourcentage_satisfait_{ressource}'] = round(pourcentage, 2)
    
    # Calcule le stock restant (stock allouable - stock alloué)
    stock_restant = {}
    for ressource in ressources:
        if ressource in stock_allouable:
            stock_restant[ressource] = stock_allouable[ressource] - stock_alloue_total[ressource]
        else:
            stock_restant[ressource] = 0
    
    # Ajoute une colonne avec le score d'urgence normalisé (pour affichage)
    score_max = df_allocation['score_urgence'].max()
    if score_max > 0:
        df_allocation['score_urgence_normalise'] = (df_allocation['score_urgence'] / score_max * 100).round(2)
    else:
        df_allocation['score_urgence_normalise'] = 0
    
    return df_allocation, stock_restant, stock_reserve


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
    
    # Si le type n'est pas trouvé, retourne un dictionnaire vide
    if besoins_type.empty:
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


def exporter_allocation_csv(df_allocation, chemin_fichier=None):
    """
    Exporte les résultats d'allocation dans un fichier CSV
    
    Args:
        df_allocation (pandas.DataFrame): DataFrame avec les allocations
        chemin_fichier (str): Chemin du fichier de sortie. Si None, utilise un nom par défaut.
    """
    if chemin_fichier is None:
        dossier_projet = Path(__file__).parent.parent
        dossier_outputs = dossier_projet / "outputs"
        dossier_outputs.mkdir(exist_ok=True)
        chemin_fichier = dossier_outputs / "allocation_ressources.csv"
    
    # Exporte le DataFrame en CSV
    df_allocation.to_csv(chemin_fichier, index=False, encoding='utf-8-sig')
    print(f"✓ Allocation exportée vers {chemin_fichier}")
    
    return chemin_fichier


def exporter_allocation_excel(df_allocation, chemin_fichier=None):
    """
    Exporte les résultats d'allocation dans un fichier Excel
    
    Args:
        df_allocation (pandas.DataFrame): DataFrame avec les allocations
        chemin_fichier (str): Chemin du fichier de sortie. Si None, utilise un nom par défaut.
    """
    try:
        # Importe openpyxl pour l'export Excel (nécessite: pip install openpyxl)
        import openpyxl
    except ImportError:
        print("⚠ openpyxl n'est pas installé. Installation de openpyxl...")
        import subprocess
        subprocess.check_call(["pip", "install", "openpyxl"])
    
    if chemin_fichier is None:
        dossier_projet = Path(__file__).parent.parent
        dossier_outputs = dossier_projet / "outputs"
        dossier_outputs.mkdir(exist_ok=True)
        chemin_fichier = dossier_outputs / "allocation_ressources.xlsx"
    
    # Exporte le DataFrame en Excel
    df_allocation.to_excel(chemin_fichier, index=False, engine='openpyxl')
    print(f"✓ Allocation exportée vers {chemin_fichier}")
    
    return chemin_fichier


def afficher_resume_allocation(df_allocation, stock_restant, stock_reserve=None):
    """
    Affiche un résumé de l'allocation des ressources
    
    Args:
        df_allocation (pandas.DataFrame): DataFrame avec les allocations
        stock_restant (dict): Dictionnaire des stocks restants
        stock_reserve (dict): Dictionnaire des stocks réservés (25%)
    """
    print("\n" + "="*60)
    print("RÉSUMÉ DE L'ALLOCATION DES RESSOURCES")
    print("="*60)
    
    if len(df_allocation) == 0:
        print("⚠ Aucune crise actuelle à traiter.")
        return
    
    # Affiche le nombre de crises actuelles traitées
    print(f"\nNombre de crises actuelles traitées: {len(df_allocation)}")
    
    # Affiche les 5 crises les plus prioritaires
    print("\nTop 5 des crises les plus urgentes:")
    top5 = df_allocation.head(5)[['nom_crise', 'type_crise', 'pays', 'score_urgence_normalise']]
    for idx, row in top5.iterrows():
        print(f"  {idx+1}. {row['nom_crise']} ({row['type_crise']}, {row['pays']}) - Score: {row['score_urgence_normalise']:.2f}")
    
    # Affiche les stocks restants
    print("\nStocks restants après allocation:")
    for ressource, quantite in stock_restant.items():
        print(f"  {ressource}: {quantite:,}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test du module
    print("Test du module d'allocation gloutonne...")
    from src.chargement_donnees import charger_crises, charger_besoins
    
    crises = charger_crises()
    besoins = charger_besoins()
    
    # Définit un stock disponible (exemple)
    stock = {
        'eau_potable_litres': 50000000,
        'tentes': 10000,
        'medicaments_doses': 500000,
        'hopitaux_campagne': 100,
        'generateurs': 300,
        'vehicules_urgence': 200,
        'personnel_medical': 3000,
        'denrees_alimentaires_kg': 10000000
    }
    
    # Test avec seulement les crises actuelles
    print("\n=== Allocation pour les crises actuelles uniquement ===")
    allocation, stock_restant, stock_reserve = allouer_ressources_glouton(crises, besoins, stock, seulement_actuelles=True)
    afficher_resume_allocation(allocation, stock_restant, stock_reserve)
    
    # Test avec toutes les crises
    print("\n=== Allocation pour toutes les crises ===")
    allocation_toutes, stock_restant_toutes, stock_reserve_toutes = allouer_ressources_glouton(crises, besoins, stock, seulement_actuelles=False)
    afficher_resume_allocation(allocation_toutes, stock_restant_toutes, stock_reserve_toutes)


