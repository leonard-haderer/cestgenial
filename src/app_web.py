"""
Application web Flask pour le projet CGénial - Allocation de ressources en cas de crise
Auteur: Projet CGénial 2025
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os

# Import des modules du projet
from src.chargement_donnees import charger_crises, charger_besoins, afficher_statistiques_crises
from src.allocation_gloutonne import allouer_ressources_glouton, exporter_allocation_csv, exporter_allocation_excel
from src.visualisation_carte import creer_carte_interactive, exporter_carte_html
from src.prediction_crises import (charger_donnees_pays, rechercher_pays, obtenir_types_risques,
                                   calculer_besoins_ressources, calculer_couts_pourcentages,
                                   calculer_probabilite_evenement)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cgenial-2025-secret-key'

# Dossiers pour les fichiers statiques et templates
dossier_projet = Path(__file__).parent.parent
app.template_folder = str(dossier_projet / 'templates')
app.static_folder = str(dossier_projet / 'static')

# Crée les dossiers nécessaires au démarrage
(dossier_projet / 'templates').mkdir(exist_ok=True)
(dossier_projet / 'static').mkdir(exist_ok=True)
(dossier_projet / 'static' / 'maps').mkdir(exist_ok=True, parents=True)
(dossier_projet / 'static' / 'js').mkdir(exist_ok=True, parents=True)


@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/api/crises')
def api_crises():
    """API pour obtenir les données des crises"""
    try:
        seulement_actuelles = request.args.get('actuelles', 'false').lower() == 'true'
        crises = charger_crises(seulement_actuelles=seulement_actuelles)
        
        # Convertit les dates en chaînes de caractères pour la sérialisation JSON
        crises_copy = crises.copy()
        if 'date' in crises_copy.columns:
            crises_copy['date'] = crises_copy['date'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None
            )
        if 'date_fin' in crises_copy.columns:
            crises_copy['date_fin'] = crises_copy['date_fin'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None
            )
        
        # Convertit les booléens en Python natifs (pandas peut utiliser numpy.bool_)
        if 'en_cours' in crises_copy.columns:
            crises_copy['en_cours'] = crises_copy['en_cours'].astype(bool)
        
        # Convertit en dictionnaire et nettoie les valeurs NaN
        data = []
        for _, row in crises_copy.iterrows():
            record = {}
            for col, val in row.items():
                # Gère les valeurs NaN et NaT
                if pd.isna(val) or val is pd.NaT:
                    record[col] = None
                # Convertit les types numpy en types Python natifs
                elif isinstance(val, (np.integer, np.int64)):
                    record[col] = int(val)
                elif isinstance(val, (np.floating, np.float64)):
                    record[col] = float(val)
                elif isinstance(val, np.bool_):
                    record[col] = bool(val)
                elif isinstance(val, str) and val == 'NaT':
                    record[col] = None
                else:
                    record[col] = val
            data.append(record)
        
        return jsonify({
            'success': True,
            'data': data,
            'actuelles': seulement_actuelles
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/besoins')
def api_besoins():
    """API pour obtenir les besoins par type de crise"""
    try:
        besoins = charger_besoins()
        return jsonify({
            'success': True,
            'data': besoins.to_dict('records')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/statistiques')
def api_statistiques():
    """API pour obtenir les statistiques des crises"""
    try:
        crises = charger_crises()
        crises_actuelles = charger_crises(seulement_actuelles=True)
        
        stats = {
            'total_crises': len(crises),
            'crises_actuelles': len(crises_actuelles),
            'crises_passees': len(crises) - len(crises_actuelles),
            'par_type': crises['type_crise'].value_counts().to_dict(),
            'par_pays': crises['pays'].value_counts().head(10).to_dict(),
            'intensite_moyenne': float(crises['intensite'].mean()),
            'intensite_min': float(crises['intensite'].min()),
            'intensite_max': float(crises['intensite'].max()),
            'population_totale': int(crises['population_touchee'].sum())
        }
        
        # Statistiques des crises actuelles
        if len(crises_actuelles) > 0:
            stats['par_type_actuelles'] = crises_actuelles['type_crise'].value_counts().to_dict()
            stats['intensite_moyenne_actuelles'] = float(crises_actuelles['intensite'].mean())
            stats['population_totale_actuelles'] = int(crises_actuelles['population_touchee'].sum())
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/allocation', methods=['POST'])
def api_allocation():
    """API pour calculer l'allocation gloutonne (uniquement crises actuelles)"""
    try:
        data = request.json or {}
        stock = data.get('stock', {})
        seulement_actuelles = data.get('seulement_actuelles', True)  # Par défaut, seulement actuelles
        
        crises = charger_crises()
        besoins = charger_besoins()
        
        # Valeurs par défaut si non fournies
        stock_defaut = {
            'eau_potable_litres': 50000000,
            'tentes': 10000,
            'medicaments_doses': 500000,
            'hopitaux_campagne': 100,
            'generateurs': 300,
            'vehicules_urgence': 200,
            'personnel_medical': 3000,
            'denrees_alimentaires_kg': 10000000
        }
        
        # Fusionne avec les valeurs par défaut
        stock_final = {**stock_defaut, **stock}
        
        allocation, stock_restant = allouer_ressources_glouton(
            crises, besoins, stock_final, 
            seulement_actuelles=seulement_actuelles
        )
        
        # Convertit les dates et types pour la sérialisation JSON
        if len(allocation) > 0:
            allocation_copy = allocation.copy()
            for col in allocation_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(allocation_copy[col]):
                    allocation_copy[col] = allocation_copy[col].dt.strftime('%Y-%m-%d')
            
            # Convertit en dictionnaire et nettoie les valeurs
            allocation_dict = []
            for _, row in allocation_copy.iterrows():
                record = {}
                for col, val in row.items():
                    if pd.isna(val):
                        record[col] = None
                    elif isinstance(val, (np.integer, np.int64)):
                        record[col] = int(val)
                    elif isinstance(val, (np.floating, np.float64)):
                        record[col] = float(val)
                    elif isinstance(val, np.bool_):
                        record[col] = bool(val)
                    else:
                        record[col] = val
                allocation_dict.append(record)
            
            top5_dict = allocation_dict[:5] if len(allocation_dict) > 0 else []
        else:
            allocation_dict = []
            top5_dict = []
        
        return jsonify({
            'success': True,
            'allocation': allocation_dict,
            'stock_restant': stock_restant,
            'top5': top5_dict,
            'nb_crises_traitees': len(allocation),
            'seulement_actuelles': seulement_actuelles
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/carte')
def api_carte():
    """API pour générer la carte interactive"""
    try:
        seulement_actuelles = request.args.get('actuelles', 'false') == 'true'
        crises = charger_crises(seulement_actuelles=seulement_actuelles)
        allocation = None
        
        # Vérifie si on doit inclure les allocations
        include_allocation = request.args.get('allocation', 'false') == 'true'
        
        if include_allocation:
            besoins = charger_besoins()
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
            allocation, _ = allouer_ressources_glouton(crises, besoins, stock, seulement_actuelles=True)
        
        carte = creer_carte_interactive(crises, allocation)
        dossier_maps = dossier_projet / 'maps'
        dossier_maps.mkdir(exist_ok=True)
        chemin_html = exporter_carte_html(carte, str(dossier_maps / "carte_crises_web.html"))
        
        # Copie aussi dans static pour l'accès web
        dossier_static_maps = dossier_projet / 'static' / 'maps'
        dossier_static_maps.mkdir(exist_ok=True, parents=True)
        import shutil
        shutil.copy(chemin_html, str(dossier_static_maps / "carte_crises_web.html"))
        
        return jsonify({
            'success': True,
            'url': '/static/maps/carte_crises_web.html'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pays')
def api_pays():
    """API pour rechercher un pays"""
    try:
        nom_pays = request.args.get('nom', '')
        if not nom_pays:
            return jsonify({'success': False, 'error': 'Nom de pays requis'}), 400
        
        df_pays = charger_donnees_pays()
        donnees_pays = rechercher_pays(nom_pays, df_pays)
        
        if donnees_pays:
            return jsonify({'success': True, 'data': donnees_pays})
        else:
            return jsonify({'success': False, 'error': 'Pays non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/types-risques')
def api_types_risques():
    """API pour obtenir les types de risques disponibles"""
    try:
        besoins = charger_besoins()
        types = obtenir_types_risques(besoins)
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prediction', methods=['POST'])
def api_prediction():
    """API pour calculer la prédiction et les besoins"""
    try:
        data = request.json
        nom_pays = data.get('pays')
        type_risque = data.get('type_risque')
        intensite = float(data.get('intensite', 7.0))
        budget = float(data.get('budget', 100000000))
        
        # Charge les données
        df_pays = charger_donnees_pays()
        df_besoins = charger_besoins()
        df_crises = charger_crises()
        
        # Recherche le pays
        donnees_pays = rechercher_pays(nom_pays, df_pays)
        if not donnees_pays:
            return jsonify({'success': False, 'error': 'Pays non trouvé'}), 404
        
        # Calcule la probabilité
        probabilite = calculer_probabilite_evenement(
            donnees_pays['latitude'],
            donnees_pays['longitude'],
            type_risque,
            intensite,
            df_crises
        )
        
        # Calcule les besoins
        besoins = calculer_besoins_ressources(
            type_risque,
            intensite,
            donnees_pays['population'],
            df_besoins
        )
        
        # Calcule les coûts
        couts = calculer_couts_pourcentages(besoins, budget)
        
        # Prépare les résultats
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
        
        ressources = []
        for ressource, infos in couts.items():
            if ressource not in ['cout_total', 'pourcentage_total']:
                ressources.append({
                    'nom': noms_ressources.get(ressource, ressource.replace('_', ' ').title()),
                    'quantite': infos['quantite'],
                    'cout': infos['cout'],
                    'pourcentage': infos['pourcentage']
                })
        
        return jsonify({
            'success': True,
            'pays': donnees_pays,
            'probabilite': probabilite,
            'ressources': ressources,
            'cout_total': couts['cout_total'],
            'pourcentage_total': couts['pourcentage_total'],
            'budget': budget
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print(" " * 15 + "PROJET CGÉNIAL - SERVEUR WEB")
    print("="*70)
    print("\n🌐 Serveur démarré sur http://localhost:8080")
    print("📊 Interface web disponible")
    print("⚠ L'allocation ne considère que les crises actuelles (en_cours=True)")
    print("\nAppuyez sur Ctrl+C pour arrêter le serveur\n")
    
    app.run(host='0.0.0.0', port=8080, debug=True)


