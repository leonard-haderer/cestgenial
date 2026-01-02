"""
Script d'exemple pour tester rapidement les fonctionnalités du projet
Auteur: Projet CGénial 2025

Ce script peut être exécuté pour tester les modules sans passer par le menu interactif
"""

import sys
from pathlib import Path

# Ajoute le dossier src au chemin Python
dossier_projet = Path(__file__).parent
sys.path.insert(0, str(dossier_projet))

def exemple_chargement():
    """Exemple de chargement des données"""
    print("="*60)
    print("EXEMPLE 1: Chargement des données")
    print("="*60)
    
    from src.chargement_donnees import charger_crises, charger_besoins, afficher_statistiques_crises
    
    crises = charger_crises()
    besoins = charger_besoins()
    afficher_statistiques_crises(crises)
    
    print("\nBesoins par type de crise:")
    print(besoins.to_string())
    
    print("\nCrises actuelles uniquement:")
    crises_actuelles = charger_crises(seulement_actuelles=True)
    print(f"Nombre de crises actuelles: {len(crises_actuelles)}")
    if len(crises_actuelles) > 0:
        print("\nListe des crises actuelles:")
        print(crises_actuelles[['nom_crise', 'type_crise', 'pays', 'date']].to_string())


def exemple_allocation():
    """Exemple d'allocation gloutonne"""
    print("\n" + "="*60)
    print("EXEMPLE 2: Allocation gloutonne (crises actuelles uniquement)")
    print("="*60)
    
    from src.chargement_donnees import charger_crises, charger_besoins
    from src.allocation_gloutonne import allouer_ressources_glouton, afficher_resume_allocation
    
    crises = charger_crises()
    besoins = charger_besoins()
    
    # Stock disponible (exemple)
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
    
    # Allocation pour les crises actuelles uniquement
    allocation, stock_restant = allouer_ressources_glouton(crises, besoins, stock, seulement_actuelles=True)
    afficher_resume_allocation(allocation, stock_restant)


def exemple_carte():
    """Exemple de création de carte"""
    print("\n" + "="*60)
    print("EXEMPLE 3: Création de carte interactive")
    print("="*60)
    
    from src.chargement_donnees import charger_crises
    from src.visualisation_carte import creer_carte_interactive, exporter_carte_html
    
    crises = charger_crises()
    carte = creer_carte_interactive(crises, titre="Exemple de Carte - Crises")
    chemin = exporter_carte_html(carte, "maps/exemple_carte.html")
    print(f"Carte créée: {chemin}")


def exemple_prediction():
    """Exemple de prédiction"""
    print("\n" + "="*60)
    print("EXEMPLE 4: Prédiction de crise par pays")
    print("="*60)
    
    from src.chargement_donnees import charger_crises, charger_besoins
    from src.prediction_crises import (charger_donnees_pays, rechercher_pays,
                                      obtenir_types_risques, calculer_besoins_ressources,
                                      calculer_couts_pourcentages, calculer_probabilite_evenement)
    
    # Charge les données
    df_pays = charger_donnees_pays()
    df_besoins = charger_besoins()
    df_crises = charger_crises()
    
    # Recherche un pays
    donnees_pays = rechercher_pays("France", df_pays)
    if donnees_pays:
        print(f"\nPays trouvé: {donnees_pays['pays']}")
        print(f"Latitude: {donnees_pays['latitude']}, Longitude: {donnees_pays['longitude']}")
        print(f"Population: {donnees_pays['population']:,}")
        
        # Calcule la probabilité pour une pandémie d'intensité 8.0
        probabilite = calculer_probabilite_evenement(
            donnees_pays['latitude'],
            donnees_pays['longitude'],
            'Pandémie',
            8.0,
            df_crises
        )
        
        print(f"\nProbabilité d'une pandémie d'intensité 8.0: {probabilite['probabilite']}%")
        print(f"Niveau: {probabilite['niveau']}")
        print(f"Explication: {probabilite['explication']}")
        
        # Calcule les besoins
        besoins = calculer_besoins_ressources('Pandémie', 8.0, donnees_pays['population'], df_besoins)
        couts = calculer_couts_pourcentages(besoins, 100000000)
        
        print(f"\nCoût total: {couts['cout_total']:,.2f} €")
        print(f"Pourcentage du budget: {couts['pourcentage_total']:.2f}%")


def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print(" " * 15 + "EXEMPLES D'UTILISATION DU PROJET CGÉNIAL")
    print("="*70)
    
    try:
        exemple_chargement()
        exemple_allocation()
        exemple_carte()
        exemple_prediction()
        
        print("\n" + "="*70)
        print("✓ Tous les exemples ont été exécutés avec succès!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


