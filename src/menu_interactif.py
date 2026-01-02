"""
Module de menu interactif en console pour le projet CGénial
Auteur: Projet CGénial 2025
"""

import os
import sys
from pathlib import Path

# Ajoute le dossier src au chemin Python pour permettre les imports
dossier_projet = Path(__file__).parent.parent
sys.path.insert(0, str(dossier_projet))


def afficher_menu():
    """
    Affiche le menu principal de l'application
    """
    print("\n" + "="*70)
    print(" " * 15 + "PROJET CGÉNIAL - ALLOCATION DE RESSOURCES EN CAS DE CRISE")
    print("="*70)
    print("\nMenu principal:")
    print("  1. Afficher les données sources (crises et besoins)")
    print("  2. Lancer l'allocation gloutonne des ressources")
    print("  3. Visualiser les crises sur la carte interactive")
    print("  4. Faire des prédictions (type et intensité de crise)")
    print("  5. Statistiques et analyses")
    print("  6. Quitter")
    print("\n" + "="*70)


def afficher_donnees_sources():
    """
    Affiche les données sources chargées
    """
    print("\n" + "="*70)
    print("AFFICHAGE DES DONNÉES SOURCES")
    print("="*70)
    
    try:
        from src.chargement_donnees import charger_crises, charger_besoins, afficher_statistiques_crises
        
        # Charge et affiche les crises
        print("\n[1] Chargement des crises...")
        crises = charger_crises()
        afficher_statistiques_crises(crises)
        
        # Affiche un aperçu des données
        print("\nAperçu des crises (5 premières):")
        print(crises[['nom_crise', 'type_crise', 'pays', 'intensite', 'date']].head().to_string())
        
        # Affiche les crises actuelles
        if 'en_cours' in crises.columns:
            crises_actuelles = crises[crises['en_cours'] == True]
            print(f"\n[2] Crises actuelles (en cours): {len(crises_actuelles)}")
            if len(crises_actuelles) > 0:
                print(crises_actuelles[['nom_crise', 'type_crise', 'pays', 'date']].to_string())
        
        # Charge et affiche les besoins
        print("\n[3] Chargement des besoins en ressources...")
        besoins = charger_besoins()
        print("\nBesoins par type de crise:")
        print(besoins.to_string())
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour continuer...")


def lancer_allocation():
    """
    Lance l'algorithme glouton d'allocation des ressources
    """
    print("\n" + "="*70)
    print("ALLOCATION GLOUTONNE DES RESSOURCES")
    print("="*70)
    
    try:
        from src.chargement_donnees import charger_crises, charger_besoins
        from src.allocation_gloutonne import allouer_ressources_glouton, afficher_resume_allocation
        from src.allocation_gloutonne import exporter_allocation_csv, exporter_allocation_excel
        
        # Charge les données
        print("\nChargement des données...")
        crises = charger_crises()
        besoins = charger_besoins()
        
        # Affiche le nombre de crises actuelles
        if 'en_cours' in crises.columns:
            nb_actuelles = crises['en_cours'].sum()
            print(f"\n⚠ IMPORTANT: {nb_actuelles} crise(s) actuelle(s) seront prises en compte pour l'allocation.")
            print("   Les crises passées (en_cours=False) seront exclues.")
        
        # Demande à l'utilisateur de définir le stock disponible
        print("\nDéfinition du stock disponible:")
        print("(Appuyez sur Entrée pour utiliser les valeurs par défaut)")
        
        stock = {}
        ressources = [col for col in besoins.columns if col != 'type_crise']
        
        for ressource in ressources:
            valeur_defaut = {
                'eau_potable_litres': 50000000,
                'tentes': 10000,
                'medicaments_doses': 500000,
                'hopitaux_campagne': 100,
                'generateurs': 300,
                'vehicules_urgence': 200,
                'personnel_medical': 3000,
                'denrees_alimentaires_kg': 10000000
            }.get(ressource, 1000)
            
            reponse = input(f"  {ressource} (défaut: {valeur_defaut:,}): ").strip()
            if reponse:
                try:
                    stock[ressource] = int(reponse)
                except ValueError:
                    print(f"    ⚠ Valeur invalide, utilisation de la valeur par défaut")
                    stock[ressource] = valeur_defaut
            else:
                stock[ressource] = valeur_defaut
        
        # Lance l'allocation (seulement crises actuelles par défaut)
        print("\nLancement de l'algorithme glouton...")
        print("(Seules les crises actuelles seront considérées)")
        allocation, stock_restant = allouer_ressources_glouton(crises, besoins, stock, seulement_actuelles=True)
        
        # Affiche le résumé
        afficher_resume_allocation(allocation, stock_restant)
        
        # Propose d'exporter les résultats
        print("\nSouhaitez-vous exporter les résultats?")
        print("  1. CSV")
        print("  2. Excel")
        print("  3. Les deux")
        print("  4. Non")
        
        choix_export = input("Votre choix (1-4): ").strip()
        
        if choix_export in ['1', '3']:
            exporter_allocation_csv(allocation)
        if choix_export in ['2', '3']:
            try:
                exporter_allocation_excel(allocation)
            except Exception as e:
                print(f"⚠ Erreur lors de l'export Excel: {e}")
                print("   (Assurez-vous que openpyxl est installé: pip install openpyxl)")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'allocation: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour continuer...")


def visualiser_carte():
    """
    Crée et affiche la carte interactive
    """
    print("\n" + "="*70)
    print("VISUALISATION DE LA CARTE INTERACTIVE")
    print("="*70)
    
    try:
        from src.chargement_donnees import charger_crises
        from src.visualisation_carte import creer_carte_interactive, exporter_carte_html
        from src.allocation_gloutonne import allouer_ressources_glouton
        from src.chargement_donnees import charger_besoins
        
        # Charge les données
        print("\nChargement des données...")
        crises = charger_crises()
        besoins = charger_besoins()
        
        # Demande si l'utilisateur veut inclure les allocations
        print("\nSouhaitez-vous afficher les allocations de ressources sur la carte?")
        print("  1. Oui (nécessite de lancer l'allocation d'abord)")
        print("  2. Non (afficher seulement les crises)")
        
        choix = input("Votre choix (1-2): ").strip()
        
        df_allocation = None
        if choix == '1':
            # Définit un stock par défaut pour l'allocation
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
            print("\nCalcul des allocations (crises actuelles uniquement)...")
            df_allocation, _ = allouer_ressources_glouton(crises, besoins, stock, seulement_actuelles=True)
        
        # Crée la carte
        print("\nCréation de la carte interactive...")
        carte = creer_carte_interactive(crises, df_allocation)
        
        # Exporte la carte
        chemin_html = exporter_carte_html(carte)
        
        print(f"\n✓ Carte créée avec succès!")
        print(f"  Fichier: {chemin_html}")
        print(f"\n  Pour visualiser la carte:")
        print(f"  - Ouvrez le fichier {chemin_html} dans votre navigateur web")
        print(f"  - Ou utilisez la commande: start {chemin_html}")
        
        # Propose d'ouvrir automatiquement
        print("\nSouhaitez-vous ouvrir la carte maintenant? (o/n): ", end='')
        if input().strip().lower() == 'o':
            import webbrowser
            webbrowser.open(f'file://{Path(chemin_html).absolute()}')
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la carte: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour continuer...")


def faire_predictions():
    """
    Permet de faire des prédictions sur de nouvelles crises basées sur un pays
    """
    print("\n" + "="*70)
    print("PRÉDICTION DE CRISES PAR PAYS")
    print("="*70)
    
    try:
        from src.chargement_donnees import charger_besoins, charger_crises
        from src.prediction_crises import (charger_donnees_pays, rechercher_pays,
                                          obtenir_types_risques, calculer_besoins_ressources,
                                          calculer_couts_pourcentages, calculer_probabilite_evenement)
        
        # Charge les données
        print("\nChargement des données...")
        df_pays = charger_donnees_pays()
        df_besoins = charger_besoins()
        df_crises = charger_crises()
        types_risques = obtenir_types_risques(df_besoins)
        
        # Boucle principale
        while True:
            print("\n" + "-"*70)
            print("Étape 1: Recherche du pays")
            print("(Appuyez sur Entrée sans valeur pour quitter)")
            
            nom_pays = input("  Nom du pays: ").strip()
            if not nom_pays:
                break
            
            # Recherche le pays
            donnees_pays = rechercher_pays(nom_pays, df_pays)
            
            if not donnees_pays:
                print(f"❌ Pays '{nom_pays}' non trouvé dans la base de données.")
                continue
            
            # Affiche les données du pays
            print("\n" + "="*70)
            print("DONNÉES DU PAYS")
            print("="*70)
            print(f"Pays: {donnees_pays['pays']}")
            print(f"Latitude: {donnees_pays['latitude']}")
            print(f"Longitude: {donnees_pays['longitude']}")
            print(f"Population: {donnees_pays['population']:,} habitants")
            
            # Étape 2: Choix du type de risque
            print("\n" + "="*70)
            print("Étape 2: Choix du type de risque")
            print("="*70)
            print("\nTypes de risques disponibles:")
            for idx, risque in enumerate(types_risques, 1):
                print(f"  {idx}. {risque}")
            
            while True:
                try:
                    choix_risque = input(f"\nChoisissez un risque (1-{len(types_risques)}): ").strip()
                    if not choix_risque:
                        break
                    
                    idx_risque = int(choix_risque) - 1
                    if 0 <= idx_risque < len(types_risques):
                        type_risque = types_risques[idx_risque]
                        break
                    else:
                        print(f"❌ Veuillez choisir un nombre entre 1 et {len(types_risques)}")
                except ValueError:
                    print("❌ Veuillez entrer un nombre valide")
            
            if not choix_risque:
                continue
            
            # Étape 3: Intensité de la crise
            print("\n" + "="*70)
            print("Étape 3: Intensité de la crise")
            print("="*70)
            
            while True:
                try:
                    intensite_str = input("  Intensité de la crise (0-10, défaut: 7.0): ").strip()
                    if not intensite_str:
                        intensite = 7.0
                        break
                    intensite = float(intensite_str)
                    if 0 <= intensite <= 10:
                        break
                    else:
                        print("❌ L'intensité doit être entre 0 et 10")
                except ValueError:
                    print("❌ Veuillez entrer un nombre valide")
            
            # Étape 4: Budget disponible
            print("\n" + "="*70)
            print("Étape 4: Budget disponible")
            print("="*70)
            
            while True:
                try:
                    budget_str = input("  Budget total disponible en euros (défaut: 100 000 000): ").strip()
                    if not budget_str:
                        budget = 100000000
                        break
                    budget = float(budget_str.replace(' ', '').replace(',', ''))
                    if budget > 0:
                        break
                    else:
                        print("❌ Le budget doit être positif")
                except ValueError:
                    print("❌ Veuillez entrer un nombre valide")
            
            # Calcule la probabilité de l'événement
            print("\nCalcul de la probabilité de l'événement...")
            probabilite = calculer_probabilite_evenement(
                donnees_pays['latitude'],
                donnees_pays['longitude'],
                type_risque,
                intensite,
                df_crises
            )
            
            # Calcule les besoins
            print("Calcul des besoins en ressources...")
            besoins = calculer_besoins_ressources(
                type_risque, 
                intensite, 
                donnees_pays['population'],
                df_besoins
            )
            
            # Calcule les coûts et pourcentages
            couts = calculer_couts_pourcentages(besoins, budget)
            
            # Affiche les résultats
            print("\n" + "="*70)
            print("ANALYSE DE RISQUE ET ALLOCATION BUDGÉTAIRE")
            print("="*70)
            print(f"\nPays: {donnees_pays['pays']}")
            print(f"Type de risque: {type_risque}")
            print(f"Intensité: {intensite}")
            print(f"Population touchée: {donnees_pays['population']:,} habitants")
            print(f"Budget total: {budget:,.0f} €")
            
            # Affiche la probabilité
            print("\n" + "-"*70)
            print("PROBABILITÉ DE L'ÉVÉNEMENT")
            print("-"*70)
            print(f"Probabilité: {probabilite['probabilite']:.2f}%")
            print(f"Niveau de risque: {probabilite['niveau']}")
            print(f"Explication: {probabilite['explication']}")
            if probabilite['distance_min'] < 10000:
                print(f"Crise historique la plus proche: {probabilite['distance_min']:.0f} km")
            
            print("\n" + "-"*70)
            print("DÉTAIL DES RESSOURCES NÉCESSAIRES:")
            print("-"*70)
            
            noms_ressources = {
                'eau_potable_litres': 'Eau potable',
                'tentes': 'Tentes',
                'medicaments_doses': 'Médicaments',
                'hopitaux_campagne': 'Hôpitaux de campagne',
                'generateurs': 'Générateurs',
                'vehicules_urgence': 'Véhicules d urgence',
                'personnel_medical': 'Personnel médical',
                'denrees_alimentaires_kg': 'Denrées alimentaires'
            }
            
            for ressource, infos in couts.items():
                if ressource not in ['cout_total', 'pourcentage_total']:
                    nom = noms_ressources.get(ressource, ressource.replace('_', ' ').title())
                    print(f"\n{nom}:")
                    print(f"  Quantité: {infos['quantite']:,}")
                    print(f"  Coût: {infos['cout']:,.2f} €")
                    print(f"  Pourcentage du budget: {infos['pourcentage']:.2f}%")
            
            print("\n" + "-"*70)
            print(f"COÛT TOTAL: {couts['cout_total']:,.2f} €")
            print(f"POURCENTAGE TOTAL DU BUDGET: {couts['pourcentage_total']:.2f}%")
            print("-"*70)
            
            if couts['pourcentage_total'] > 100:
                print("\n⚠ ATTENTION: Le budget disponible est insuffisant!")
                print(f"   Budget nécessaire: {couts['cout_total']:,.2f} €")
                print(f"   Budget disponible: {budget:,.2f} €")
                print(f"   Déficit: {couts['cout_total'] - budget:,.2f} €")
            else:
                reste = budget - couts['cout_total']
                print(f"\n✓ Budget suffisant. Reste disponible: {reste:,.2f} € ({100 - couts['pourcentage_total']:.2f}%)")
        
    except Exception as e:
        print(f"❌ Erreur lors des prédictions: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour continuer...")


def afficher_statistiques():
    """
    Affiche des statistiques et analyses avancées
    """
    print("\n" + "="*70)
    print("STATISTIQUES ET ANALYSES")
    print("="*70)
    
    try:
        from src.chargement_donnees import charger_crises, charger_besoins
        import pandas as pd
        
        crises = charger_crises()
        besoins = charger_besoins()
        
        print("\n[1] Analyse par type de crise:")
        stats_type = crises.groupby('type_crise').agg({
            'intensite': ['mean', 'min', 'max'],
            'population_touchee': ['sum', 'mean'],
            'accessibilite': 'mean'
        }).round(2)
        print(stats_type)
        
        print("\n[2] Top 10 des crises les plus intenses:")
        top10 = crises.nlargest(10, 'intensite')[['nom_crise', 'type_crise', 'pays', 'intensite']]
        print(top10.to_string(index=False))
        
        print("\n[3] Top 10 des crises par population touchée:")
        top10_pop = crises.nlargest(10, 'population_touchee')[['nom_crise', 'type_crise', 'pays', 'population_touchee']]
        print(top10_pop.to_string(index=False))
        
        print("\n[4] Répartition temporelle:")
        crises['annee'] = crises['date'].dt.year
        repartition_annee = crises.groupby('annee').size()
        print(repartition_annee)
        
        # Statistiques sur les crises actuelles
        if 'en_cours' in crises.columns:
            print("\n[5] Crises actuelles vs passées:")
            crises_actuelles = crises[crises['en_cours'] == True]
            crises_passees = crises[crises['en_cours'] == False]
            print(f"  Crises actuelles: {len(crises_actuelles)}")
            print(f"  Crises passées: {len(crises_passees)}")
            if len(crises_actuelles) > 0:
                print("\n  Répartition des crises actuelles par type:")
                print(crises_actuelles['type_crise'].value_counts())
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour continuer...")


def menu_principal():
    """
    Boucle principale du menu interactif
    """
    while True:
        # Nettoie l'écran (fonctionne sur Windows et Unix)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Affiche le menu
        afficher_menu()
        
        # Demande le choix de l'utilisateur
        choix = input("\nVotre choix (1-6): ").strip()
        
        # Exécute l'action correspondante
        if choix == '1':
            afficher_donnees_sources()
        elif choix == '2':
            lancer_allocation()
        elif choix == '3':
            visualiser_carte()
        elif choix == '4':
            faire_predictions()
        elif choix == '5':
            afficher_statistiques()
        elif choix == '6':
            print("\nAu revoir! Merci d'avoir utilisé le système d'allocation de ressources.")
            break
        else:
            print("\n❌ Choix invalide. Veuillez choisir un nombre entre 1 et 6.")
            input("Appuyez sur Entrée pour continuer...")


if __name__ == "__main__":
    menu_principal()


