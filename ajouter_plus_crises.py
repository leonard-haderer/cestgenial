import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

dossier = Path(__file__).parent
chemin_fichier = dossier / 'data' / 'Base_Crises_TresTres_Enrichie_CGenial.csv'

types_crises = ['Séisme', 'Tsunami', 'Ouragan', 'Inondation', 'Famine', 'Cyclone', 
                'Éruption volcanique', 'Incendie', 'Typhon', 'Pandémie', 'Guerre']

pays_coords = {
    'Chine': (35.8617, 104.1954), 'Inde': (20.5937, 78.9629), 'États-Unis': (37.0902, -95.7129),
    'Indonésie': (-0.7893, 113.9213), 'Brésil': (-14.2350, -51.9253), 'Pakistan': (30.3753, 69.3451),
    'Bangladesh': (23.6850, 90.3563), 'Nigeria': (9.0820, 8.6753), 'Russie': (61.5240, 105.3188),
    'Japon': (36.2048, 138.2529), 'Mexique': (23.6345, -102.5528), 'Philippines': (12.8797, 121.7740),
    'Vietnam': (14.0583, 108.2772), 'Turquie': (38.9637, 35.2433), 'Iran': (32.4279, 53.6880),
    'Irak': (33.2232, 43.6793), 'Afghanistan': (33.9391, 67.7100), 'Thaïlande': (15.8700, 100.9925),
    'Myanmar': (21.9162, 95.9560), 'Éthiopie': (9.1450, 38.7667), 'Kenya': (-0.0236, 37.9062),
    'Soudan': (12.8628, 30.2176), 'Ouganda': (1.3733, 32.2903), 'Tanzanie': (-6.3690, 34.8888),
    'Colombie': (4.5709, -74.2973), 'Venezuela': (6.4238, -66.5897), 'Pérou': (-9.1900, -75.0152),
    'Argentine': (-38.4161, -63.6167), 'Chili': (-35.6751, -71.5430), 'Équateur': (-1.8312, -78.1834),
    'Guatemala': (15.7835, -90.2308), 'Honduras': (15.2000, -86.2419), 'Nicaragua': (12.2650, -85.2072),
    'Cuba': (21.5218, -77.7812), 'République dominicaine': (18.7357, -70.1627), 'Jamaïque': (18.1096, -77.2975),
    'Algérie': (28.0339, 1.6596), 'Maroc': (31.7917, -7.0926), 'Égypte': (26.0975, 31.2357),
    'Tunisie': (33.8869, 9.5375), 'Libye': (26.3351, 17.2283), 'Soudan du Sud': (6.8770, 31.3070),
    'République centrafricaine': (6.6111, 20.9394), 'Cameroun': (7.3697, 12.3547), 'Ghana': (7.9465, -1.0232),
    'Mali': (17.5707, -3.9962), 'Niger': (17.6078, 8.0817), 'Tchad': (15.4542, 18.7322),
    'Mauritanie': (21.0079, -10.9408), 'Sénégal': (14.4974, -14.4524), 'Côte d\'Ivoire': (7.5400, -5.5471),
    'Burkina Faso': (12.2383, -1.5616)
}

noms_crises = {
    'Séisme': ['Séisme', 'Tremblement de terre', 'Séisme majeur'],
    'Tsunami': ['Tsunami', 'Raz-de-marée'], 'Ouragan': ['Ouragan', 'Tempête tropicale'],
    'Inondation': ['Inondation', 'Crues', 'Déluge'], 'Famine': ['Famine', 'Crise alimentaire', 'Sécheresse'],
    'Cyclone': ['Cyclone', 'Tempête cyclonique'], 'Éruption volcanique': ['Éruption volcanique', 'Éruption'],
    'Incendie': ['Incendie', 'Feux de forêt'], 'Typhon': ['Typhon', 'Super typhon'],
    'Pandémie': ['Pandémie', 'Épidémie'], 'Guerre': ['Guerre', 'Conflit armé', 'Guerre civile']
}

crises = []
print("Génération de 200 crises historiques...")
for i in range(200):
    type_crise = random.choice(types_crises)
    pays = random.choice(list(pays_coords.keys()))
    lat, lon = pays_coords[pays]
    annee = random.randint(1950, 2023)
    mois = random.randint(1, 12)
    jour = random.randint(1, 28)
    date = f"{annee}-{mois:02d}-{jour:02d}"
    duree_mois = random.randint(1, 24)
    date_fin = datetime(annee, mois, jour) + timedelta(days=duree_mois*30)
    date_fin_str = date_fin.strftime("%Y-%m-%d")
    
    if type_crise in ['Guerre', 'Pandémie', 'Famine']:
        intensite = round(random.uniform(6.0, 10.0), 1)
    elif type_crise in ['Séisme', 'Tsunami']:
        intensite = round(random.uniform(5.0, 9.5), 1)
    else:
        intensite = round(random.uniform(4.0, 8.5), 1)
    
    if type_crise == 'Pandémie':
        population = random.randint(1000000, 50000000)
    elif type_crise == 'Guerre':
        population = random.randint(500000, 30000000)
    elif type_crise == 'Famine':
        population = random.randint(2000000, 20000000)
    else:
        population = random.randint(100000, 15000000)
    
    accessibilite = round(random.uniform(0.2, 0.8), 1)
    nom_base = random.choice(noms_crises[type_crise])
    nom_crise = f"{nom_base} {pays} {annee}"
    
    descriptions = {
        'Séisme': 'Séisme destructeur', 'Tsunami': 'Tsunami majeur', 'Ouragan': 'Ouragan de catégorie élevée',
        'Inondation': 'Inondations massives', 'Famine': 'Crise alimentaire majeure', 'Cyclone': 'Cyclone tropical intense',
        'Éruption volcanique': 'Éruption volcanique majeure', 'Incendie': 'Feux de forêt massifs',
        'Typhon': 'Typhon super destructeur', 'Pandémie': 'Pandémie mondiale', 'Guerre': 'Conflit armé majeur'
    }
    
    crises.append({
        'nom_crise': nom_crise, 'type_crise': type_crise, 'pays': pays, 'latitude': lat, 'longitude': lon,
        'intensite': intensite, 'date': date, 'population_touchee': population, 'accessibilite': accessibilite,
        'description': descriptions[type_crise], 'en_cours': False, 'date_fin': date_fin_str
    })

print("Génération de 5 crises actuelles de 2025...")
crises_2025 = [
    {'nom': 'Séisme', 'pays': 'Japon', 'coords': (36.2048, 138.2529), 'intensite': 7.5, 'population': 8000000, 'accessibilite': 0.7, 'date': '2025-01-15'},
    {'nom': 'Inondation', 'pays': 'Bangladesh', 'coords': (23.6850, 90.3563), 'intensite': 8.0, 'population': 12000000, 'accessibilite': 0.4, 'date': '2025-02-20'},
    {'nom': 'Cyclone', 'pays': 'Philippines', 'coords': (12.8797, 121.7740), 'intensite': 5.5, 'population': 15000000, 'accessibilite': 0.4, 'date': '2025-03-10'},
    {'nom': 'Famine', 'pays': 'Éthiopie', 'coords': (9.1450, 38.7667), 'intensite': 8.5, 'population': 10000000, 'accessibilite': 0.3, 'date': '2025-04-05'},
    {'nom': 'Éruption volcanique', 'pays': 'Indonésie', 'coords': (-0.7893, 113.9213), 'intensite': 6.8, 'population': 5000000, 'accessibilite': 0.5, 'date': '2025-05-12'}
]

for crise_2025 in crises_2025:
    type_crise = crise_2025['nom']
    pays = crise_2025['pays']
    lat, lon = crise_2025['coords']
    date = crise_2025['date']
    intensite = crise_2025['intensite']
    population = crise_2025['population']
    accessibilite = crise_2025['accessibilite']
    
    descriptions = {
        'Séisme': 'Séisme destructeur', 'Tsunami': 'Tsunami majeur', 'Ouragan': 'Ouragan de catégorie élevée',
        'Inondation': 'Inondations massives', 'Famine': 'Crise alimentaire majeure', 'Cyclone': 'Cyclone tropical intense',
        'Éruption volcanique': 'Éruption volcanique majeure', 'Incendie': 'Feux de forêt massifs',
        'Typhon': 'Typhon super destructeur', 'Pandémie': 'Pandémie mondiale', 'Guerre': 'Conflit armé majeur'
    }
    
    nom_crise = f"{type_crise} {pays} 2025"
    
    crises.append({
        'nom_crise': nom_crise, 'type_crise': type_crise, 'pays': pays, 'latitude': lat, 'longitude': lon,
        'intensite': intensite, 'date': date, 'population_touchee': population, 'accessibilite': accessibilite,
        'description': descriptions[type_crise], 'en_cours': True, 'date_fin': ''
    })

df_existant = pd.read_csv(chemin_fichier)
df_nouvelles = pd.DataFrame(crises)
df_combine = pd.concat([df_existant, df_nouvelles], ignore_index=True)
df_combine.to_csv(chemin_fichier, index=False, encoding='utf-8')
print(f"\n✓ {200} crises historiques supplémentaires ajoutées")
print(f"✓ {5} crises actuelles de 2025 ajoutées")
print(f"✓ Total: {len(df_combine)} crises dans le fichier")
print(f"✓ Crises actuelles: {df_combine['en_cours'].sum()}")




