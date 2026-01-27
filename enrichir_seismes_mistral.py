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

def extraire_donnees_seisme(seisme_info, reponse_ia):
    """
    Extrait les données (population touchée et accessibilité) de la réponse de l'IA
    
    Args:
        seisme_info (dict): Informations sur le séisme
        reponse_ia (str): Réponse de l'IA
    
    Returns:
        tuple: (population_touchee, accessibilite) ou (None, None) si échec
    """
    try:
        # Essaie d'extraire les valeurs numériques de la réponse
        # Format attendu: "population_touchee: XXXX, accessibilite: Y.YY"
        population_touchee = None
        accessibilite = None
        
        # Recherche de la population touchée
        import re
        pop_match = re.search(r'population[_\s]touch[ée]e?[:\s]+(\d+)', reponse_ia, re.IGNORECASE)
        if pop_match:
            population_touchee = int(pop_match.group(1))
        else:
            # Essaie d'autres formats
            pop_match = re.search(r'population[:\s]+(\d+)', reponse_ia, re.IGNORECASE)
            if pop_match:
                population_touchee = int(pop_match.group(1))
        
        # Recherche de l'accessibilité (valeur entre 0 et 1)
        acc_match = re.search(r'accessibilit[ée][:\s]+([0-9.]+)', reponse_ia, re.IGNORECASE)
        if acc_match:
            accessibilite = float(acc_match.group(1))
            # S'assure que l'accessibilité est entre 0 et 1
            if accessibilite > 1:
                accessibilite = accessibilite / 100.0  # Si donné en pourcentage
            accessibilite = max(0.0, min(1.0, accessibilite))
        else:
            # Essaie d'autres formats
            acc_match = re.search(r'accessibility[:\s]+([0-9.]+)', reponse_ia, re.IGNORECASE)
            if acc_match:
                accessibilite = float(acc_match.group(1))
                if accessibilite > 1:
                    accessibilite = accessibilite / 100.0
                accessibilite = max(0.0, min(1.0, accessibilite))
        
        # Si on n'a pas trouvé les valeurs, essaie de parser un JSON
        if population_touchee is None or accessibilite is None:
            json_match = re.search(r'\{[^}]+\}', reponse_ia)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if population_touchee is None and 'population_touchee' in data:
                        population_touchee = int(data['population_touchee'])
                    if accessibilite is None and 'accessibilite' in data:
                        accessibilite = float(data['accessibilite'])
                        if accessibilite > 1:
                            accessibilite = accessibilite / 100.0
                        accessibilite = max(0.0, min(1.0, accessibilite))
                except:
                    pass
        
        return population_touchee, accessibilite
        
    except Exception as e:
        print(f"⚠ Erreur lors de l'extraction des données: {e}")
        return None, None

def creer_prompt_seisme(seisme):
    """
    Crée un prompt pour l'IA basé sur les informations du séisme
    
    Args:
        seisme (pandas.Series): Ligne du DataFrame avec les informations du séisme
    
    Returns:
        str: Le prompt à envoyer à l'IA
    """
    # Construit le prompt avec toutes les informations disponibles
    prompt = f"""Tu es un expert en sismologie et en gestion de crises humanitaires.

Pour le séisme suivant, je dois connaître deux informations précises sous forme de nombres :

Informations du séisme :
"""
    
    # Ajoute toutes les colonnes disponibles
    for col in seisme.index:
        if pd.notna(seisme[col]) and str(seisme[col]).strip():
            prompt += f"- {col}: {seisme[col]}\n"
    
    prompt += """
Je dois obtenir :
1. La population touchée (nombre de personnes affectées) : un nombre entier
2. L'accessibilité (niveau d'accessibilité de la zone, entre 0 et 1 où 0 = très difficile d'accès, 1 = facile d'accès) : un nombre décimal entre 0 et 1

Réponds UNIQUEMENT avec les deux valeurs au format suivant (sans texte supplémentaire) :
population_touchee: [nombre]
accessibilite: [nombre entre 0 et 1]

Si tu ne peux pas trouver ces informations, réponds :
Donne moi ta meilleure estimation
"""
    
    return prompt

def enrichir_seismes():
    """
    Fonction principale pour enrichir le fichier CSV des séismes
    """
    # Chemin du fichier CSV
    chemin_csv = Path(__file__).parent / 'data' / 'seismes1950-2026.csv'
    
    if not chemin_csv.exists():
        print(f"❌ Fichier non trouvé: {chemin_csv}")
        return
    
    print(f"📖 Lecture du fichier: {chemin_csv}")
    # Le fichier utilise le point-virgule comme séparateur
    df = pd.read_csv(chemin_csv, sep=';', encoding='utf-8', on_bad_lines='skip')
    
    print(f"✓ {len(df)} séismes trouvés dans le fichier")
    
    # Vérifie si les colonnes existent déjà
    if 'population_touchee' not in df.columns:
        df['population_touchee'] = None
    if 'accessibilite' not in df.columns:
        df['accessibilite'] = None
    
    # Compte combien de séismes ont déjà des données
    deja_remplis = df['population_touchee'].notna().sum()
    print(f"📊 {deja_remplis} séismes ont déjà une population touchée")
    print(f"📊 {df['accessibilite'].notna().sum()} séismes ont déjà une accessibilité")
    
    # Traite chaque séisme
    total = len(df)
    traites = 0
    reussis = 0
    echecs = 0
    
    for idx, seisme in df.iterrows():
        traites += 1
        
        # Vérifie si les données sont déjà présentes
        if pd.notna(seisme.get('population_touchee')) and pd.notna(seisme.get('accessibilite')):
            print(f"[{traites}/{total}] ✓ Séisme {idx+1} déjà complété, passage au suivant...")
            continue
        
        print(f"\n[{traites}/{total}] 🔍 Traitement du séisme {idx+1}...")
        
        # Affiche les informations du séisme
        nom = seisme.get('nom', seisme.get('nom_crise', seisme.get('Location Name', f'Séisme {idx+1}')))
        date = f"{seisme.get('Year', '')}-{seisme.get('Month', ''):02d}-{seisme.get('Day', ''):02d}" if pd.notna(seisme.get('Year')) else "Date inconnue"
        magnitude = seisme.get('Mag', seisme.get('magnitude', 'N/A'))
        print(f"   Nom: {nom}")
        print(f"   Date: {date}, Magnitude: {magnitude}")
        
        # Crée le prompt
        prompt = creer_prompt_seisme(seisme)
        
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
        population_touchee, accessibilite = extraire_donnees_seisme(seisme, reponse)
        
        if population_touchee is not None and accessibilite is not None:
            df.at[idx, 'population_touchee'] = population_touchee
            df.at[idx, 'accessibilite'] = accessibilite
            print(f"   ✓ Données extraites: population={population_touchee}, accessibilité={accessibilite:.2f}")
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
        enrichir_seismes()
    except KeyboardInterrupt:
        print("\n⚠ Interruption par l'utilisateur. Les données déjà traitées ont été sauvegardées.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

