"""
Module de visualisation interactive des crises sur une carte avec Folium
Auteur: Projet CGénial 2025
"""

import folium
from folium import plugins
import pandas as pd
import numpy as np
from pathlib import Path
import math

# Dictionnaire des couleurs et icônes par type de crise
COULEURS_CRISES = {
    'Séisme': 'red',
    'Tsunami': 'blue',
    'Ouragan': 'purple',
    'Inondation': 'lightblue',
    'Famine': 'orange',
    'Cyclone': 'darkblue',
    'Éruption volcanique': 'darkred',
    'Incendie': 'darkorange',
    'Typhon': 'cadetblue',
    'Pandémie': 'purple',
    'Guerre': 'black'
}

ICONES_CRISES = {
    'Séisme': 'exclamation-triangle',
    'Tsunami': 'tint',
    'Ouragan': 'cloud',
    'Inondation': 'tint',
    'Famine': 'cutlery',
    'Cyclone': 'cloud',
    'Éruption volcanique': 'fire',
    'Incendie': 'fire',
    'Typhon': 'cloud',
    'Pandémie': 'heartbeat',
    'Guerre': 'shield'
}


def creer_carte_interactive(df_crises, df_allocation=None, titre="Crises et Allocation de Ressources"):
    """
    Crée une carte interactive avec Folium montrant les crises et leurs allocations
    
    Args:
        df_crises (pandas.DataFrame): DataFrame des crises
        df_allocation (pandas.DataFrame): DataFrame avec les allocations (optionnel)
        titre (str): Titre de la carte
    
    Returns:
        folium.Map: Objet carte Folium
    """
    # Calcule le centre de la carte (moyenne des latitudes et longitudes)
    centre_lat = df_crises['latitude'].mean()
    centre_lon = df_crises['longitude'].mean()
    
    # Crée la carte centrée sur la moyenne des coordonnées
    carte = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=2,
        tiles='OpenStreetMap'
    )
    
    # Ajoute une couche de tuiles satellite (optionnelle)
    folium.TileLayer('CartoDB positron').add_to(carte)
    
    # Groupe de marqueurs par type de crise (pour la légende)
    groupes_par_type = {}
    
    # Parcourt chaque crise pour ajouter un marqueur
    for idx, crise in df_crises.iterrows():
        # Récupère le type de crise
        type_crise = crise['type_crise']
        
        # Détermine la couleur et l'icône
        couleur = COULEURS_CRISES.get(type_crise, 'gray')
        icone = ICONES_CRISES.get(type_crise, 'info-sign')
        
        # Indicateur si la crise est actuelle
        en_cours = ''
        if 'en_cours' in crise and crise['en_cours']:
            # Vérifie si c'est une crise de 2025 pour un indicateur spécial
            date_crise = pd.to_datetime(crise['date'])
            if date_crise.year == 2025:
                en_cours = '<p><b style="color: red; font-size: 14px;">⚠ CRISE ACTUELLE 2025</b></p>'
            else:
                en_cours = '<p><b style="color: red;">⚠ CRISE ACTUELLE</b></p>'
        
        # Crée le texte du popup avec les informations de la crise
        popup_html = f"""
        <div style="width: 250px;">
            <h4>{crise['nom_crise']}</h4>
            {en_cours}
            <p><b>Type:</b> {type_crise}</p>
            <p><b>Pays:</b> {crise['pays']}</p>
            <p><b>Date:</b> {crise['date']}</p>
            <p><b>Intensité:</b> {crise['intensite']}</p>
            <p><b>Population touchée:</b> {crise['population_touchee']:,}</p>
            <p><b>Accessibilité:</b> {crise['accessibilite']:.2f}</p>
        """
        
        # Si des données d'allocation sont disponibles, les ajoute au popup
        if df_allocation is not None and idx < len(df_allocation):
            allocation = df_allocation.iloc[idx]
            popup_html += "<hr><h5>Allocation de ressources:</h5>"
            
            # Liste les ressources allouées
            colonnes_allocation = [col for col in allocation.index if col.startswith('allocation_')]
            for col in colonnes_allocation:
                ressource = col.replace('allocation_', '').replace('_', ' ').title()
                quantite = allocation[col]
                if quantite > 0:
                    popup_html += f"<p><b>{ressource}:</b> {quantite:,}</p>"
        
        popup_html += "</div>"
        
        # Crée l'icône du marqueur
        # Pour les crises de 2025, utilise une couleur plus vive
        date_crise = pd.to_datetime(crise['date'])
        if 'en_cours' in crise and crise['en_cours'] and date_crise.year == 2025:
            # Crises de 2025 : couleur plus vive et icône différente
            icon_marker = folium.Icon(
                icon=icone,
                prefix='fa',
                color='red',  # Fond rouge pour les crises 2025
                icon_color='white'  # Icône blanche pour contraste
            )
        else:
            icon_marker = folium.Icon(
                icon=icone,
                prefix='fa',
                color='white',
                icon_color=couleur
            )
        
        # Crée le marqueur
        marqueur = folium.Marker(
            location=[crise['latitude'], crise['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{crise['nom_crise']} ({type_crise})",
            icon=icon_marker
        )
        
        # Crée ou récupère le groupe pour ce type de crise
        if type_crise not in groupes_par_type:
            groupes_par_type[type_crise] = folium.FeatureGroup(name=type_crise)
        
        # Ajoute le marqueur au groupe correspondant
        marqueur.add_to(groupes_par_type[type_crise])
    
    # Ajoute tous les groupes à la carte
    for groupe in groupes_par_type.values():
        groupe.add_to(carte)
    
    # Ajoute le contrôle des couches (pour activer/désactiver les types de crises)
    folium.LayerControl().add_to(carte)
    
    # Ajoute une légende personnalisée
    legende_html = creer_legende_html()
    carte.get_root().html.add_child(folium.Element(legende_html))
    
    # Ajoute un titre
    titre_html = f"""
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size: 16px; font-weight: bold;">
        {titre}
    </div>
    """
    carte.get_root().html.add_child(folium.Element(titre_html))
    
    # Ajoute le champ de recherche de coordonnées
    ajouter_recherche_coordonnees(carte)
    
    return carte


def creer_legende_html():
    """
    Crée le code HTML pour la légende de la carte
    
    Returns:
        str: Code HTML de la légende
    """
    legende_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 250px; height: auto; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size: 12px;">
        <h4 style="margin-top: 0;">Légende</h4>
    """
    
    # Ajoute chaque type de crise avec sa couleur
    for type_crise, couleur in COULEURS_CRISES.items():
        legende_html += f"""
        <p>
            <i class="fa fa-circle" style="color: {couleur};"></i>
            {type_crise}
        </p>
        """
    
    legende_html += """
        <hr>
        <p><small>Cliquez sur les marqueurs pour plus d'informations</small></p>
    </div>
    """
    
    return legende_html


def ajouter_recherche_coordonnees(carte):
    """
    Ajoute un champ de recherche avec latitude et longitude à la carte
    Permet de rechercher un emplacement et d'afficher un marqueur
    
    Args:
        carte (folium.Map): Carte Folium à modifier
    """
    # Récupère l'ID unique de la carte pour le JavaScript
    map_id = carte._id
    
    # Code HTML et JavaScript pour le champ de recherche
    recherche_html = f"""
    <div id="search-panel" style="position: fixed; 
                top: 80px; left: 50px; width: 300px; 
                background-color: white; z-index:10000; 
                border:2px solid #007bff; padding: 15px;
                border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin-top: 0; color: #007bff;">🔍 Recherche de coordonnees</h4>
        <form id="search-form" onsubmit="return false;">
            <div style="margin-bottom: 10px;">
                <label for="lat-input-{map_id}" style="display: block; margin-bottom: 5px; font-weight: bold;">
                    Latitude:
                </label>
                <input type="number" id="lat-input-{map_id}" step="any" 
                       placeholder="Ex: 35.0" 
                       style="width: 100%; padding: 5px; border: 1px solid #ccc; border-radius: 3px;">
            </div>
            <div style="margin-bottom: 10px;">
                <label for="lon-input-{map_id}" style="display: block; margin-bottom: 5px; font-weight: bold;">
                    Longitude:
                </label>
                <input type="number" id="lon-input-{map_id}" step="any" 
                       placeholder="Ex: 139.0" 
                       style="width: 100%; padding: 5px; border: 1px solid #ccc; border-radius: 3px;">
            </div>
            <button type="button" id="search-btn-{map_id}" 
                    style="width: 100%; padding: 8px; background-color: #007bff; 
                           color: white; border: none; border-radius: 3px; 
                           cursor: pointer; font-weight: bold;">
                🔍 Rechercher
            </button>
            <button type="button" id="clear-btn-{map_id}" 
                    style="width: 100%; padding: 8px; margin-top: 5px; 
                           background-color: #dc3545; color: white; 
                           border: none; border-radius: 3px; cursor: pointer;">
                ✖ Effacer
            </button>
        </form>
        <div id="search-result-{map_id}" style="margin-top: 10px; font-size: 12px; color: #666;"></div>
    </div>
    
    <script>
        var searchMarker_{map_id} = null;
        var foliumMap_{map_id} = null;
        
        // Fonction pour obtenir la reference a la carte Folium
        function getFoliumMap_{map_id}() {{
            if (foliumMap_{map_id}) {{
                return foliumMap_{map_id};
            }}
            
            // Methode 1: Cherche via le conteneur DOM (la plus fiable)
            var mapDiv = document.querySelector('.folium-map');
            if (mapDiv) {{
                // Leaflet stocke la reference de la carte dans le conteneur
                if (mapDiv._leaflet_id) {{
                    var mapId = mapDiv._leaflet_id;
                    // Cherche dans toutes les variables globales
                    for (var key in window) {{
                        try {{
                            var obj = window[key];
                            if (obj instanceof L.Map && obj._container === mapDiv) {{
                                foliumMap_{map_id} = obj;
                                return foliumMap_{map_id};
                            }}
                        }} catch(e) {{
                            // Continue
                        }}
                    }}
                }}
            }}
            
            // Methode 2: Cherche dans toutes les variables globales (toutes les instances L.Map)
            var allMaps = [];
            for (var key in window) {{
                try {{
                    if (window[key] instanceof L.Map) {{
                        allMaps.push(window[key]);
                    }}
                }} catch(e) {{
                    // Continue la recherche
                }}
            }}
            
            // Si on trouve une seule carte, c est probablement la bonne
            if (allMaps.length === 1) {{
                foliumMap_{map_id} = allMaps[0];
                return foliumMap_{map_id};
            }}
            
            // Si plusieurs cartes, essaie de trouver celle qui correspond au conteneur
            if (allMaps.length > 1 && mapDiv) {{
                for (var i = 0; i < allMaps.length; i++) {{
                    try {{
                        if (allMaps[i]._container === mapDiv) {{
                            foliumMap_{map_id} = allMaps[i];
                            return foliumMap_{map_id};
                        }}
                    }} catch(e) {{
                        // Continue
                    }}
                }}
            }}
            
            // Methode 3: Utilise la premiere carte trouvee si aucune correspondance
            if (allMaps.length > 0) {{
                foliumMap_{map_id} = allMaps[0];
                return foliumMap_{map_id};
            }}
            
            return null;
        }}
        
        function rechercherCoordonnees_{map_id}() {{
            // Verifie que Leaflet est charge
            if (typeof L === 'undefined') {{
                var resultDiv = document.getElementById('search-result-{map_id}');
                resultDiv.innerHTML = '<span style="color: red;">⚠ Leaflet n est pas charge. Attendez quelques secondes.</span>';
                return;
            }}
            
            var lat = parseFloat(document.getElementById('lat-input-{map_id}').value);
            var lon = parseFloat(document.getElementById('lon-input-{map_id}').value);
            var resultDiv = document.getElementById('search-result-{map_id}');
            
            // Validation des coordonnees
            if (isNaN(lat) || isNaN(lon)) {{
                resultDiv.innerHTML = '<span style="color: red;">⚠ Veuillez entrer des coordonnees valides</span>';
                return;
            }}
            
            if (lat < -90 || lat > 90) {{
                resultDiv.innerHTML = '<span style="color: red;">⚠ Latitude doit etre entre -90 et 90</span>';
                return;
            }}
            
            if (lon < -180 || lon > 180) {{
                resultDiv.innerHTML = '<span style="color: red;">⚠ Longitude doit etre entre -180 et 180</span>';
                return;
            }}
            
            // Obtient la reference a la carte
            var map = getFoliumMap_{map_id}();
            
            if (!map) {{
                // Essaie une derniere fois apres un court delai
                resultDiv.innerHTML = '<span style="color: orange;">⚠ Recherche de la carte...</span>';
                setTimeout(function() {{
                    map = getFoliumMap_{map_id}();
                    if (map) {{
                        rechercherCoordonnees_{map_id}();
                    }} else {{
                        resultDiv.innerHTML = '<span style="color: red;">⚠ Carte non trouvee. Verifiez la console pour plus de details.</span>';
                        console.error('Carte Folium non trouvee. Variables globales:', Object.keys(window).filter(k => window[k] instanceof L.Map));
                    }}
                }}, 500);
                return;
            }}
            
            try {{
                // Efface le marqueur precedent s il existe
                if (searchMarker_{map_id}) {{
                    try {{
                        if (map.hasLayer && map.hasLayer(searchMarker_{map_id})) {{
                            map.removeLayer(searchMarker_{map_id});
                        }}
                    }} catch(e) {{
                        // Ignore les erreurs de suppression
                    }}
                    searchMarker_{map_id} = null;
                }}
                
                // Cree un nouveau marqueur (utilise l icone par defaut de Leaflet pour plus de fiabilite)
                searchMarker_{map_id} = L.marker([lat, lon]);
                
                // Ajoute le marqueur a la carte
                searchMarker_{map_id}.addTo(map);
                
                // Ajoute un popup
                var popupContent = '<b>📍 Emplacement recherche</b><br>Latitude: ' + lat.toFixed(4) + '<br>Longitude: ' + lon.toFixed(4);
                searchMarker_{map_id}.bindPopup(popupContent);
                
                // Centre la carte sur le marqueur avec un zoom approprie
                var currentZoom = map.getZoom();
                var targetZoom = currentZoom > 10 ? currentZoom : 10;
                map.setView([lat, lon], targetZoom);
                
                // Ouvre le popup apres un court delai pour s assurer que le marqueur est bien ajoute
                setTimeout(function() {{
                    try {{
                        if (searchMarker_{map_id} && map.hasLayer(searchMarker_{map_id})) {{
                            searchMarker_{map_id}.openPopup();
                        }}
                    }} catch(e) {{
                        console.warn('Impossible d ouvrir le popup:', e);
                    }}
                }}, 200);
                
                resultDiv.innerHTML = '<span style="color: green;">✓ Marqueur ajoute a (' + lat.toFixed(4) + ', ' + lon.toFixed(4) + ')</span>';
                console.log('Marqueur ajoute avec succes a:', lat, lon);
            }} catch(error) {{
                resultDiv.innerHTML = '<span style="color: red;">⚠ Erreur: ' + error.message + '</span>';
                console.error('Erreur lors de l ajout du marqueur:', error);
                console.error('Map object:', map);
                console.error('Map type:', typeof map);
                console.error('L.Map check:', map instanceof L.Map);
            }}
        }}
        
        function effacerMarqueur_{map_id}() {{
            var resultDiv = document.getElementById('search-result-{map_id}');
            
            if (searchMarker_{map_id}) {{
                var map = getFoliumMap_{map_id}();
                if (map) {{
                    map.removeLayer(searchMarker_{map_id});
                    searchMarker_{map_id} = null;
                    resultDiv.innerHTML = '<span style="color: blue;">✓ Marqueur efface</span>';
                }} else {{
                    resultDiv.innerHTML = '<span style="color: orange;">⚠ Impossible d effacer le marqueur</span>';
                }}
            }} else {{
                resultDiv.innerHTML = '<span style="color: #666;">Aucun marqueur a effacer</span>';
            }}
        }}
        
        // Initialise les event listeners une fois le DOM charge
        (function() {{
            function initSearch_{map_id}() {{
                var searchBtn = document.getElementById('search-btn-{map_id}');
                var clearBtn = document.getElementById('clear-btn-{map_id}');
                var latInput = document.getElementById('lat-input-{map_id}');
                var lonInput = document.getElementById('lon-input-{map_id}');
                
                if (searchBtn) {{
                    searchBtn.addEventListener('click', rechercherCoordonnees_{map_id});
                }}
                
                if (clearBtn) {{
                    clearBtn.addEventListener('click', effacerMarqueur_{map_id});
                }}
                
                if (latInput) {{
                    latInput.addEventListener('keypress', function(e) {{
                        if (e.key === 'Enter') {{
                            rechercherCoordonnees_{map_id}();
                        }}
                    }});
                }}
                
                if (lonInput) {{
                    lonInput.addEventListener('keypress', function(e) {{
                        if (e.key === 'Enter') {{
                            rechercherCoordonnees_{map_id}();
                        }}
                    }});
                }}
            }}
            
            // Essaie d initialiser immediatement
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', initSearch_{map_id});
            }} else {{
                // DOM deja charge
                setTimeout(initSearch_{map_id}, 100);
            }}
        }})();
    </script>
    """
    
    # Ajoute le HTML à la carte
    carte.get_root().html.add_child(folium.Element(recherche_html))


def exporter_carte_html(carte, chemin_fichier=None):
    """
    Exporte la carte en fichier HTML
    
    Args:
        carte (folium.Map): Carte Folium à exporter
        chemin_fichier (str): Chemin du fichier de sortie. Si None, utilise un nom par défaut.
    
    Returns:
        str: Chemin du fichier créé
    """
    if chemin_fichier is None:
        dossier_projet = Path(__file__).parent.parent
        dossier_maps = dossier_projet / "maps"
        dossier_maps.mkdir(exist_ok=True)
        chemin_fichier = dossier_maps / "carte_crises.html"
    
    # Sauvegarde la carte en HTML
    carte.save(str(chemin_fichier))
    print(f"✓ Carte exportée vers {chemin_fichier}")
    
    return chemin_fichier

def generer_matrice_terre_mer(points_grille, lat_min=-60, lat_max=80, lon_min=-180, lon_max=180):
    """
    Génère une matrice binaire (1=terre, 0=mer) à partir de l'image mapmonde.jpg
    
    Args:
        points_grille (matrice 2 dimensions): Liste de points de la grille
        lat_min (float): Latitude minimale (défaut: -60)
        lat_max (float): Latitude maximale (défaut: 80)
        lon_min (float): Longitude minimale (défaut: -180)
        lon_max (float): Longitude maximale (défaut: 180)
    
    Returns:
        numpy.ndarray: Matrice 2D de 1 (terre) et 0 (mer), dimensions (nb_lat, nb_lon)
        dict: Dictionnaire avec les informations de la grille (lat_min, lat_max, lon_min, lon_max, resolution)
    """
    from PIL import Image
    import numpy as np
    from pathlib import Path
    
    # Chemin vers l'image
    chemin_image = Path(__file__).parent.parent / 'data' / 'mapmonde.jpg'
    
    if not chemin_image.exists():
        raise FileNotFoundError(f"Image non trouvée: {chemin_image}")
    
    # Charge l'image
    img = Image.open(chemin_image)
    img_array = np.array(img)
    
    # Convertit en niveaux de gris si nécessaire
    if len(img_array.shape) == 3:
        # Prend la moyenne des canaux RGB pour obtenir un niveau de gris
        img_gray = np.mean(img_array, axis=2)
    else:
        img_gray = img_array
    
    # Normalise entre 0 et 1
    img_gray = img_gray / 255.0
    
    # Seuil pour déterminer terre/mer
    # Les pixels sombres (océans) < 0.5, les pixels clairs (terres) >= 0.5
    seuil = 0.5
    matrice_binaire = (img_gray > seuil).astype(int)
    
    # Calcule les dimensions de la grille pour la résolution donnée
    nb_lat = len(points_grille)
    nb_lon = len(points_grille[0])
    
    # Obtient les dimensions de l'image originale
    img_width, img_height = img.size
  
    # Calcule la valeur du pixels pour chaque point de la grille
    step_lat = img_height / nb_lat
    step_lon = img_width / nb_lon
    matrice_terre_mer = []
    for i in range(nb_lat):
        matrice_terre_mer.append([])
        for j in range(nb_lon):
            matrice_terre_mer[i].append(matrice_binaire[int(i*step_lat), int(j*step_lon)])

    # Inverse la matrice verticalement (pôle nord en haut, pôle sud en bas)
    return np.flipud(matrice_terre_mer)

def decalage_latitude_mecrator(latitude_actuelle_degres, delta_y, R=1):
    """
    Calcule la nouvelle latitude après un déplacement fixe vers le sud sur une carte Mercator.

    :param latitude_actuelle_degres: Latitude actuelle en degrés.
    :param delta_y: Distance fixe à parcourir vers le sud sur la carte (en % de la carte).
    :param R: Rayon ou facteur d'échelle (par défaut 1).
    :return: Nouvelle latitude en degrés.
    """
    # Convertir la latitude en radians
    phi = math.radians(latitude_actuelle_degres)
    # Calculer y pour la latitude actuelle
    y = R * math.log(math.tan(phi / 2 + math.pi / 4))
    # Calculer la nouvelle position y
    y_nouveau = y + delta_y / 100
    # Résoudre pour la nouvelle latitude
    phi_nouveau = 2 * math.atan(math.exp(y_nouveau / R)) - math.pi / 2
    # Convertir en degrés
    return math.degrees(phi_nouveau) - latitude_actuelle_degres

def decalage_latitude(lat, resolution):
    """
    Calcul le decalage en latitude en fonction de la latitude pour que l'espacement reste constant sur la carte
    Utilisation d'un fonction lineaire croissante jusqu'a "decalage_latitude(0) = 3 * resolution" puis decroissante
    """
    if (lat < 0):
        return min(0.5, (1/32 * lat + 3) * resolution)
    else:
        return min(0.5, (-1/32 * lat + 3) * resolution)

def generer_grille_de_points(lat_min, lat_max, lon_min, lon_max, resolution):
    """
    Génère une grille de points régulièrement espacés sur la carte
    
    Args:
        lat_min, lat_max: Limites de latitude
        lon_min, lon_max: Limites de longitude
        espacement_km: Espacement entre les points en kilomètres
    
    Returns:
        list: Liste de tuples (lat, lon) pour chaque point de la grille
    """
    points = []

    # Le decalage en longitude est constant et vaut le decalage en latitude pour latitude = 0
    espacement_lon = decalage_latitude_mecrator(0, 2 * resolution)

    # Génère les latitudes et les latitudes
    lat = lat_min
    while lat <= lat_max:
        print(f"latitude: {lat}")
        points.append([])
        lon = lon_min
        while lon <= lon_max:
            points[-1].append((lat, lon))
            lon += espacement_lon
        
        espacement_lat = decalage_latitude_mecrator(lat, 2 * resolution)
        lat += espacement_lat
    
    return points

def ajouter_heatmap_probabilite(carte, df_crises, type_crise, intensite=7.0, resolution=3.0):
    """
    Ajoute une carte de chaleur (heatmap) montrant la probabilité qu'une crise se produise
    à différents endroits du globe (uniquement sur les continents)
    
    Utilise la même logique que calculer_probabilite_evenement() avec :
    - Impact maximal pour crises historiques < 100 km
    - Décroissance rapide entre 100-500 km et 500-1000 km
    - Impact nul au-delà de 1000 km
    - Prise en compte de la fréquence du type, intensité similaire, etc.
    
    Args:
        carte (folium.Map): Carte Folium à modifier
        df_crises (pandas.DataFrame): DataFrame des crises historiques
        type_crise (str): Type de crise à analyser
        intensite (float): Intensité de la crise (0-10)
        resolution (float): Résolution abstraite de la grille (1-5, où 1=peu de points, 5=beaucoup de points)
    
    Returns:
        folium.Map: Carte avec la heatmap ajoutée
    """
    from src.prediction_crises import calculer_probabilite_evenement
    
    print(f"Calcul de la heatmap de probabilité pour {type_crise} (intensité {intensite})...")
    print("Utilisation de la logique de calcul de probabilité avec décroissance rapide de la distance...")
    print("Génération de la grille avec espacement régulier sur la carte mercator ...")
    
    # Crée une grille de points géographiques
    # Limites du globe
    lat_min, lat_max = -60, 80  # Exclut les pôles
    lon_min, lon_max = -180, 180
        
    # Génère une grille régulièrement espacée en distance sur la carte mercator
    points_grille = generer_grille_de_points(lat_min, lat_max, lon_min, lon_max, resolution)
    print(f"✓ {len(points_grille) * len(points_grille[0])} points générés dans la grille")
    
    # Génère la matrice terre/mer pour la détection
    # On utilise la grille de points deja creee
    matrice_terre_mer = generer_matrice_terre_mer(points_grille, lat_min, lat_max, lon_min, lon_max)
    print(f"✓ Matrice terre/mer générée: {len(matrice_terre_mer)}x{len(matrice_terre_mer[0])}")
    
    # Génère les points de la heatmap
    points_heatmap = []
    total_points = 0
    points_filtres = 0
    
    for i in range(len(points_grille)):
        for j in range(len(points_grille[i])):
            lat, lon = points_grille[i][j]
            total_points += 1
            print(f"Point {total_points} : {lat}, {lon}")

            # Si c'est la mer (0), on ignore ce point
            if matrice_terre_mer[i][j] == 0:
                points_filtres += 1
                continue
            
            # Calcule la probabilité pour ce point en utilisant la fonction calculer_probabilite_evenement
            # Cette fonction utilise la nouvelle logique avec décroissance rapide de la distance :
            # - Impact maximal < 100 km
            # - Décroissance 100-500 km et 500-1000 km
            # - Impact nul > 1000 km
            resultat = calculer_probabilite_evenement(lat, lon, type_crise, intensite, df_crises)
            probabilite = resultat['probabilite']
            
            # Multiplie la probabilité par la valeur terre/mer (1 pour terre, 0 pour mer)
            # Cela garantit que les zones marines ont une probabilité de 0
            probabilite_finale = probabilite * matrice_terre_mer[i][j]
            
            # Si la probabilité finale est 0 (mer), on n'ajoute pas le point
            if probabilite_finale == 0:
                points_filtres += 1
                continue
            
            # Stocke le point avec sa probabilité réelle (0-100)
            points_heatmap.append([lat, lon, probabilite_finale])
        
    print(f"✓ {total_points} points analysés, {points_filtres} points océaniques exclus, {len(points_heatmap)} points continentaux calculés")
    
    if not points_heatmap:
        print("⚠ Aucun point à afficher")
        return carte
    
    # Définit les seuils de probabilité avec des couleurs fixes
    # Ces seuils sont absolus et ne dépendent pas des valeurs min/max
    def obtenir_couleur_probabilite(prob):
        """
        Retourne la couleur en fonction de la probabilité absolue
        Utilise des seuils fixes pour garantir la cohérence visuelle
        """
        if prob < 15:
            return '#00ff00'  # Vert clair - Très faible probabilité
        elif prob < 30:
            return '#80ff00'  # Vert-jaune - Faible probabilité
        elif prob < 50:
            return '#ffff00'  # Jaune - Probabilité modérée
        elif prob < 70:
            return '#ff8000'  # Orange - Probabilité élevée
        else:
            return '#8b0000'  # Rouge foncé - Très élevée probabilité
    
    def obtenir_opacite_probabilite(prob):
        """
        Retourne l'opacité en fonction de la probabilité
        Plus la probabilité est élevée, plus l'opacité est forte
        """
        # Opacité minimale de 0.2 pour les faibles probabilités
        # Opacité maximale de 0.8 pour les hautes probabilités
        return min(0.8, max(0.2, prob / 100.0 * 0.6 + 0.2))
    
    def obtenir_rayon_probabilite(prob):
        """
        Retourne le rayon du cercle en fonction de la probabilité
        Plus la probabilité est élevée, plus le cercle est grand
        """
        # Rayon minimal de 3 pixels, maximal de 12 pixels
        return min(12, max(3, prob / 100.0 * 9 + 3))
    
    # Crée un FeatureGroup pour les cercles de probabilité
    groupe_probabilite = folium.FeatureGroup(name=f'Probabilité {type_crise}')
    
    # Ajoute chaque point comme un cercle coloré
    for lat, lon, prob in points_heatmap:
        couleur = obtenir_couleur_probabilite(prob)
        opacite = obtenir_opacite_probabilite(prob)
        rayon = obtenir_rayon_probabilite(prob)
        
        # Crée un cercle pour ce point
        cercle = folium.CircleMarker(
            location=[lat, lon],
            radius=rayon,
            popup=f"Probabilité: {prob:.1f}% lat {lat:.4f} lon {lon:.4f}",
            tooltip=f"Probabilité: {prob:.1f}% lat {lat:.4f} lon {lon:.4f}",
            color=couleur,
            fillColor=couleur,
            fillOpacity=opacite,
            weight=1,
            opacity=opacite
        )
        cercle.add_to(groupe_probabilite)
    
    # Ajoute le groupe à la carte
    groupe_probabilite.add_to(carte)
    
    # Ajoute une légende pour les probabilités
    legende_prob_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: auto; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size: 11px;">
        <h4 style="margin-top: 0; font-size: 12px;">Probabilité {type_crise}</h4>
        <p style="margin: 2px 0;"><span style="color: #00ff00;">●</span> &lt; 15% (Très faible)</p>
        <p style="margin: 2px 0;"><span style="color: #80ff00;">●</span> 15-30% (Faible)</p>
        <p style="margin: 2px 0;"><span style="color: #ffff00;">●</span> 30-50% (Modérée)</p>
        <p style="margin: 2px 0;"><span style="color: #ff8000;">●</span> 50-70% (Élevée)</p>
        <p style="margin: 2px 0;"><span style="color: #8b0000;">●</span> &gt; 70% (Très élevée)</p>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(legende_prob_html))
    
    print(f"✓ {len(points_heatmap)} cercles de probabilité ajoutés à la carte (uniquement sur les continents)")
    
    return carte


def creer_carte_avec_heatmap(df_crises, type_crise, intensite=7.0, resolution=3.0, titre="Carte de Probabilité de Crise"):
    """
    Crée une carte interactive avec une heatmap de probabilité pour un type de crise
    
    Args:
        df_crises (pandas.DataFrame): DataFrame des crises historiques
        type_crise (str): Type de crise à analyser
        intensite (float): Intensité de la crise (0-10)
        resolution (float): Résolution de la grille en degrés
        titre (str): Titre de la carte
    
    Returns:
        folium.Map: Carte avec heatmap
    """
    # Calcule le centre de la carte
    centre_lat = df_crises['latitude'].mean()
    centre_lon = df_crises['longitude'].mean()
    
    # Crée la carte
    carte = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=2,
        tiles='OpenStreetMap'
    )
    
    # Ajoute une couche de tuiles satellite
    folium.TileLayer('CartoDB positron').add_to(carte)
    
    # Ajoute la heatmap de probabilité
    ajouter_heatmap_probabilite(carte, df_crises, type_crise, intensite, resolution)
    
    # Ajoute les crises historiques du même type comme marqueurs
    crises_type = df_crises[df_crises['type_crise'] == type_crise].copy()
    if not crises_type.empty:
        for idx, crise in crises_type.iterrows():
            couleur = COULEURS_CRISES.get(type_crise, 'gray')
            icone = ICONES_CRISES.get(type_crise, 'info-sign')
            
            popup_html = f"""
            <div style="width: 200px;">
                <h5>{crise['nom_crise']}</h5>
                <p><b>Type:</b> {type_crise}</p>
                <p><b>Pays:</b> {crise['pays']}</p>
                <p><b>Date:</b> {crise['date']}</p>
                <p><b>Intensité:</b> {crise['intensite']}</p>
            </div>
            """
            
            icon_marker = folium.Icon(
                icon=icone,
                prefix='fa',
                color='white',
                icon_color=couleur
            )
            
            folium.Marker(
                location=[crise['latitude'], crise['longitude']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{crise['nom_crise']}",
                icon=icon_marker
            ).add_to(carte)
    
    # Ajoute le contrôle des couches
    folium.LayerControl().add_to(carte)
    
    # Ajoute une légende pour la heatmap
    legende_html = f"""
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: auto; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size: 12px;">
        <h5 style="margin-top: 0;">Probabilité {type_crise}</h5>
        <div style="height: 20px; background: linear-gradient(to right, #00ff00, #80ff00, #ffff00, #ff8000, #ff4000, #8b0000); 
                    border: 1px solid #ccc; margin-bottom: 5px;"></div>
        <div style="display: flex; justify-content: space-between; font-size: 10px;">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
        </div>
        <p style="margin-top: 10px; font-size: 10px;"><small>Intensité: {intensite}/10</small></p>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(legende_html))
    
    # Ajoute un titre
    titre_html = f"""
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; z-index:9999; 
                border:2px solid grey; padding: 10px;
                font-size: 16px; font-weight: bold;">
        {titre} - {type_crise}
    </div>
    """
    carte.get_root().html.add_child(folium.Element(titre_html))
    
    return carte


if __name__ == "__main__":
    # Test du module
    print("Test du module de visualisation...")
    from src.chargement_donnees import charger_crises
    
    crises = charger_crises()
    carte = creer_carte_interactive(crises)
    exporter_carte_html(carte)
    print("✓ Carte créée avec succès!")


