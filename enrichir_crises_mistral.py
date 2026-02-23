"""
Script pour enrichir le fichier CSV des séismes avec les données manquantes
en utilisant l'API Mistral AI pour trouver la population touchée et l'accessibilité
"""

import pandas as pd
import requests
import json
import time
from pathlib import Path
import sys

# Clé API Mistral
MISTRAL_API_KEY = "CoBK5gQ3NjhBqEytd3CSqgU3pCvIoM8y"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def appeler_mistral(prompt):
    """
    Fait un appel à l'API Mistral pour obtenir une réponse
    
    Args:
        prompt (str): Le prompt à envoyer à l'IA
    
    Returns:
        str: La réponse de l'IA
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1  # Faible température pour des réponses plus précises
    }
    
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"⚠ Réponse inattendue de l'API: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API: {e}")
        return None

def extraire_donnees_crise(crise_info, reponse_ia):
    """
    Extrait les données (latitude, longitude, accessibilité, intensité et source) de la réponse de l'IA
    
    Args:
        crise_info (dict): Informations sur la crise
        reponse_ia (str): Réponse de l'IA
    
    Returns:
        tuple: (latitude, longitude, accessibilite, intensite, source) ou (None, None, None, None, None) si échec
    """
    try:
        import re
        
        latitude = None
        longitude = None
        accessibilite = None
        intensite = None
        source = None
        
        # Recherche de la latitude (nombre décimal ou entier, positif ou négatif)
        lat_match = re.search(r'latitude\s*[:\s]\s*(-?\d+(?:\.\d+)?)', reponse_ia, re.IGNORECASE)
        if lat_match:
            latitude = float(lat_match.group(1))
        
        # Recherche de la longitude (nombre décimal ou entier, positif ou négatif)
        lon_match = re.search(r'longitude\s*[:\s]\s*(-?\d+(?:\.\d+)?)', reponse_ia, re.IGNORECASE)
        if lon_match:
            longitude = float(lon_match.group(1))
        
        # Recherche de l'intensité (nombre décimal ou entier)
        int_match = re.search(r'intensit[eé]\s*[:\s]\s*(-?\d+(?:\.\d+)?)', reponse_ia, re.IGNORECASE)
        if int_match:
            intensite = float(int_match.group(1))
        
        # Recherche de l'accessibilité (nombre décimal ou entier)
        acc_match = re.search(r'accessibilit[eé]\s*[:\s]\s*(-?\d+(?:\.\d+)?)', reponse_ia, re.IGNORECASE)
        if acc_match:
            accessibilite = float(acc_match.group(1))
        
        # Recherche de la source (TEXTE, pas un nombre)
        source_match = re.search(r'source\s*[:\s]\s*(.+)', reponse_ia, re.IGNORECASE)
        if source_match:
            source = source_match.group(1).strip()
            # Nettoie la source (enlève les guillemets si présents)
            source = source.strip('"\'')
        
        # Si on n'a pas trouvé toutes les valeurs, essaie de parser un JSON
        if any(v is None for v in [latitude, longitude, intensite, source, accessibilite]):
            # Cherche un bloc JSON (peut contenir des retours à la ligne)
            json_match = re.search(r'\{[^}]+\}', reponse_ia, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if latitude is None and 'latitude' in data:
                        latitude = float(data['latitude'])
                    if longitude is None and 'longitude' in data:
                        longitude = float(data['longitude'])
                    if intensite is None and 'intensite' in data:
                        intensite = float(data['intensite'])
                    if intensite is None and 'intensité' in data:
                        intensite = float(data['intensité'])
                    if source is None and 'source' in data:
                        source = str(data['source'])
                    if accessibilite is None and 'accessibilite' in data:
                        accessibilite = float(data['accessibilite'])
                    if accessibilite is None and 'accessibilité' in data:
                        accessibilite = float(data['accessibilité'])
                except (json.JSONDecodeError, ValueError):
                    pass
        
        return latitude, longitude, accessibilite, intensite, source
        
    except Exception as e:
        print(f"⚠ Erreur lors de l'extraction des données: {e}")
        return None, None, None, None, None

def creer_prompt_crise(crise):
    """
    Crée un prompt pour l'IA basé sur les informations de la crise
    
    Args:
        crise (pandas.Series): Ligne du DataFrame avec les informations de la crise
    
    Returns:
        str: Le prompt à envoyer à l'IA
    """
    # Construit le prompt avec toutes les informations disponibles
    prompt = f"""Tu es un expert en gestion de crises humanitaires.

Pour la crise suivante, je dois connaître 5 informations précises sous forme de nombres :

Informations de la crise :
"""
    
    # Ajoute toutes les colonnes disponibles
    for col in crise.index:
        if pd.notna(crise[col]) and str(crise[col]).strip():
            prompt += f"- {col}: {crise[col]}\n"
    
    prompt += """
Je dois obtenir :
1. La latitude et la longitude 
2. L'accessibilité (niveau d'accessibilité de la zone, entre 0 et 1 où 0 = très difficile d'accès, 1 = facile d'accès) : un nombre décimal entre 0 et 1
3. L'intensité de la crise (0-10, 10 = la plus intense)
4. La source de l'information si tu en as une avec l'url du site web

Réponds UNIQUEMENT avec les quatre informations au format suivant (sans texte supplémentaire) :
latitude: [nombre]
longitude: [nombre]
accessibilite: [nombre entre 0 et 1]
intensite: [nombre entre 0 et 10]
source: [texte avec l'url du site web]

Si tu ne peux pas trouver ces informations, Donne moi ta meilleure estimation
"""
    
    return prompt

def enrichir_crises():
    """
    Fonction principale pour enrichir le fichier CSV des crises
    """
    # Chemin du fichier CSV
    chemin_csv = Path(__file__).parent / 'data' / 'Base_Crises_TresTres_Enrichie_CGenial.csv'
    
    if not chemin_csv.exists():
        print(f"❌ Fichier non trouvé: {chemin_csv}")
        return
    
    print(f"📖 Lecture du fichier: {chemin_csv}")
    # Le fichier utilise le point-virgule comme séparateur
    df = pd.read_csv(chemin_csv, sep=';', encoding='utf-8', on_bad_lines='skip')
    
    print(f"✓ {len(df)} crises trouvées dans le fichier")
       
    # Traite chaque crise
    total = len(df)
    traites = 0
    reussis = 0
    echecs = 0
    
    for idx, crise in df.iterrows():
        traites += 1
        
        # Vérifie si les données sont déjà présentes
        if pd.notna(crise.get('latitude')) and pd.notna(crise.get('longitude')) and pd.notna(crise.get('intensite')):
            print(f"[{traites}/{total}] ✓ Crise {idx+1} déjà complété, passage au suivant...")
            continue
        
        print(f"\n[{traites}/{total}] 🔍 Traitement de la crise {idx+1}...")
        
        # Affiche les informations de la crise
        print(f"   Nom: {crise.get('nom_crise')}")
        
        # Crée le prompt
        prompt = creer_prompt_crise(crise)
        
        # Appelle l'API Mistral
        print("   📡 Appel à l'API Mistral...")
        reponse = appeler_mistral(prompt)
        
        if reponse is None:
            print("   ❌ Échec de l'appel API")
            echecs += 1
            time.sleep(2)  # Pause avant le prochain appel
            continue
        
        print(f"   ✓ Réponse reçue: {reponse[:100]}...")
        
        # Extrait les données
        latitude, longitude, accessibilite, intensite, source = extraire_donnees_crise(crise, reponse)
        
        if latitude is not None and longitude is not None and accessibilite is not None and intensite is not None and source is not None:
            df.at[idx, 'latitude'] = latitude
            df.at[idx, 'longitude'] = longitude
            df.at[idx, 'accessibilite'] = accessibilite
            df.at[idx, 'intensite'] = intensite
            df.at[idx, 'source'] = source
            print(f"   ✓ Données extraites: latitude={latitude}, longitude={longitude}, accessibilité={accessibilite:.2f}, intensité={intensite}, source={source}")
            reussis += 1
        else:
            print(f"   ⚠ Impossible d'extraire les données de la réponse")
            print(f"   Réponse complète: {reponse}")
            echecs += 1
        
        # Sauvegarde périodique (tous les 10 séismes)
        if traites % 10 == 0:
            df.to_csv(chemin_csv, index=False, sep=';', encoding='utf-8')
            print(f"   💾 Sauvegarde intermédiaire effectuée")
        
        # Pause entre les appels pour éviter de surcharger l'API
        time.sleep(1)
    
    # Sauvegarde finale
    print(f"\n💾 Sauvegarde finale du fichier...")
    df.to_csv(chemin_csv, index=False, sep=';', encoding='utf-8')
    
    print(f"\n✅ Traitement terminé !")
    print(f"   - Total traité: {traites}")
    print(f"   - Réussis: {reussis}")
    print(f"   - Échecs: {echecs}")
    print(f"   - Fichier sauvegardé: {chemin_csv}")

if __name__ == "__main__":
    try:
        enrichir_crises()
    except KeyboardInterrupt:
        print("\n⚠ Interruption par l'utilisateur. Les données déjà traitées ont été sauvegardées.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

