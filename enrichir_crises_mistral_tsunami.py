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
    Extrait la population touchée de la réponse de l'IA
    
    Args:
        crise_info (dict): Informations sur la crise
        reponse_ia (str): Réponse de l'IA
    
    Returns:
        float | None: population_touchee extraite, ou None si échec
    """
    try:
        import re
        
        population_touchee = None
        
        # Recherche de la population touchée (entier ou décimal)
        pop_match = re.search(
            r'population[_\s]*touch[eé]e?\s*[:=\s]\s*(-?\d+(?:\.\d+)?)',
            reponse_ia,
            re.IGNORECASE
        )
        if pop_match:
            population_touchee = float(pop_match.group(1))
        
        # Si non trouvé via regex, essaie un JSON
        if population_touchee is None:
            # Cherche un bloc JSON (peut contenir des retours à la ligne)
            json_match = re.search(r'\{[^}]+\}', reponse_ia, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if 'population_touchee' in data:
                        population_touchee = float(data['population_touchee'])
                    elif 'population touchée' in data:
                        population_touchee = float(data['population touchée'])
                    elif 'population' in data:
                        population_touchee = float(data['population'])
                except (json.JSONDecodeError, ValueError):
                    pass

        return population_touchee
        
    except Exception as e:
        print(f"⚠ Erreur lors de l'extraction des données: {e}")
        return None

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

Pour la crise suivante, je dois connaître la population touchée :

Informations de la crise :
"""
    
    # Ajoute toutes les colonnes disponibles
    for col in crise.index:
        if pd.notna(crise[col]) and str(crise[col]).strip():
            prompt += f"- {col}: {crise[col]}\n"
    
    prompt += """
Je dois obtenir :
1. population_touchee (nombre de personnes touchées)

Réponds UNIQUEMENT avec ce format (sans texte supplémentaire) :
population_touchee: [nombre]

Si tu ne peux pas trouver l'information exacte, donne ta meilleure estimation chiffrée.
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
        
        # Ne traite que les tsunamis avec population manquante
        if str(crise.get('type_crise', '')).strip().lower() != 'tsunami':
            continue
        if pd.notna(crise.get('population_touchee')):
            print(f"[{traites}/{total}] ✓ Crise {idx+1} (tsunami) déjà complétée, passage au suivant...")
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
        
        # Extrait la population touchée
        population_touchee = extraire_donnees_crise(crise, reponse)

        if population_touchee is not None:
            df.at[idx, 'population_touchee'] = population_touchee
            print(f"   ✓ Population touchée extraite: {population_touchee:,.0f}")
            reussis += 1
        else:
            print(f"   ⚠ Impossible d'extraire la population touchée de la réponse")
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

