"""
Script pour enrichir le fichier CSV des crises avec les données manquantes
en utilisant l'API OpenAI (ChatGPT) pour trouver la population touchée et l'accessibilité
"""

import pandas as pd
import requests
import json
import time
from pathlib import Path
import sys
import os

# Clé API OpenAI - À définir dans les variables d'environnement ou ici
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "VOTRE_CLE_API_OPENAI_ICI")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def appeler_chatgpt(prompt):
    """
    Fait un appel à l'API OpenAI (ChatGPT) pour obtenir une réponse
    avec population touchée, accessibilité et source en une seule fois
    
    Args:
        prompt (str): Le prompt à envoyer à l'IA
    
    Returns:
        str: La réponse complète de l'IA contenant toutes les informations
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": "gpt-4",  # Utilise GPT-4 pour de meilleures réponses
        "messages": [
            {
                "role": "system",
                "content": "Tu es un expert en gestion de crises humanitaires et en analyse de données géographiques. Tu fournis des estimations précises basées sur des sources fiables."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1  # Faible température pour des réponses plus précises
    }
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            reponse = result['choices'][0]['message']['content']
            return reponse
        else:
            print(f"⚠ Réponse inattendue de l'API: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API: {e}")
        return None

def extraire_donnees_crise(crise_info, reponse_ia):
    """
    Extrait les données (population touchée, accessibilité et source) de la réponse de l'IA
    en une seule fois
    
    Args:
        crise_info (dict): Informations sur la crise
        reponse_ia (str): Réponse de l'IA
    
    Returns:
        tuple: (population_touchee, accessibilite, source) ou (None, None, None) si échec
    """
    try:
        import re
        population_touchee = None
        accessibilite = None
        source = None
        
        # Essaie d'abord de parser un JSON complet (peut être multi-lignes)
        # Cherche un bloc JSON qui peut contenir des retours à la ligne
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', reponse_ia, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                if 'population_touchee' in data:
                    population_touchee = int(data['population_touchee'])
                if 'accessibilite' in data:
                    accessibilite = float(data['accessibilite'])
                    if accessibilite > 1:
                        accessibilite = accessibilite / 100.0
                    accessibilite = max(0.0, min(1.0, accessibilite))
                if 'source' in data:
                    source = str(data['source']).strip()
            except json.JSONDecodeError:
                # Si le JSON est mal formé, essaie de le nettoyer
                try:
                    # Enlève les retours à la ligne et espaces superflus
                    json_clean = re.sub(r'\s+', ' ', json_match.group(0))
                    data = json.loads(json_clean)
                    if 'population_touchee' in data:
                        population_touchee = int(data['population_touchee'])
                    if 'accessibilite' in data:
                        accessibilite = float(data['accessibilite'])
                        if accessibilite > 1:
                            accessibilite = accessibilite / 100.0
                        accessibilite = max(0.0, min(1.0, accessibilite))
                    if 'source' in data:
                        source = str(data['source']).strip()
                except:
                    pass
            except:
                pass
        
        # Si pas de JSON, essaie d'extraire les valeurs une par une
        if population_touchee is None:
            pop_match = re.search(r'population[_\s]touch[ée]e?[:\s]+(\d+)', reponse_ia, re.IGNORECASE)
            if pop_match:
                population_touchee = int(pop_match.group(1))
            else:
                pop_match = re.search(r'population[:\s]+(\d+)', reponse_ia, re.IGNORECASE)
                if pop_match:
                    population_touchee = int(pop_match.group(1))
        
        if accessibilite is None:
            acc_match = re.search(r'accessibilit[ée][:\s]+([0-9.]+)', reponse_ia, re.IGNORECASE)
            if acc_match:
                accessibilite = float(acc_match.group(1))
                if accessibilite > 1:
                    accessibilite = accessibilite / 100.0
                accessibilite = max(0.0, min(1.0, accessibilite))
            else:
                acc_match = re.search(r'accessibility[:\s]+([0-9.]+)', reponse_ia, re.IGNORECASE)
                if acc_match:
                    accessibilite = float(acc_match.group(1))
                    if accessibilite > 1:
                        accessibilite = accessibilite / 100.0
                    accessibilite = max(0.0, min(1.0, accessibilite))
        
        if source is None:
            # Cherche la source dans la réponse
            source_match = re.search(r'source[:\s]+(.+?)(?:\n|$)', reponse_ia, re.IGNORECASE)
            if source_match:
                source = source_match.group(1).strip()
            else:
                # Source par défaut si non trouvée
                source = f"ChatGPT (GPT-4) - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return population_touchee, accessibilite, source
        
    except Exception as e:
        print(f"⚠ Erreur lors de l'extraction des données: {e}")
        return None, None, None

def creer_prompt_crise(crise):
    """
    Crée un prompt pour l'IA basé sur les informations de la crise
    
    Args:
        crise (pandas.Series): Ligne du DataFrame avec les informations de la crise
    
    Returns:
        str: Le prompt à envoyer à l'IA
    """
    type_crise = crise.get('type_crise', 'crise')
    nom = crise.get('nom_crise', 'Crise inconnue')
    pays = crise.get('pays', 'Pays inconnu')
    date = crise.get('date', 'Date inconnue')
    intensite = crise.get('intensite', 'N/A')
    latitude = crise.get('latitude', 'N/A')
    longitude = crise.get('longitude', 'N/A')
    description = crise.get('description', '')
    
    # Construit le prompt avec toutes les informations disponibles
    prompt = f"""Tu es un expert en gestion de crises humanitaires et en analyse géographique.

Pour la {type_crise} suivante, je dois connaître deux informations précises sous forme de nombres :

Informations de la crise :
- Nom: {nom}
- Type: {type_crise}
- Pays: {pays}
- Date: {date}
- Intensité: {intensite}
- Coordonnées: Latitude {latitude}, Longitude {longitude}
- Description: {description}

Je dois obtenir trois informations en une seule réponse :
1. La population touchée (nombre de personnes affectées par cette crise) : un nombre entier
2. L'accessibilité (niveau d'accessibilité de la zone touchée, entre 0 et 1 où 0 = très difficile d'accès, 1 = facile d'accès) : un nombre décimal entre 0 et 1
3. La source (origine des données utilisées pour cette estimation) : une description courte de la source (ex: "ONU - Rapport 2024", "Wikipedia", "ChatGPT estimation basée sur données historiques", etc.)

Réponds UNIQUEMENT avec les trois valeurs au format JSON suivant (sans texte supplémentaire) :
{
  "population_touchee": [nombre],
  "accessibilite": [nombre entre 0 et 1],
  "source": "[description de la source]"
}

Si tu ne peux pas trouver ces informations exactes, donne ta meilleure estimation basée sur :
- Le type de crise et son intensité
- La localisation géographique (pays, coordonnées)
- La date de la crise
- Les données historiques similaires

Pour la source, indique d'où viennent tes données ou si c'est une estimation basée sur des critères similaires.
"""
    
    return prompt

def enrichir_crises():
    """
    Fonction principale pour enrichir le fichier CSV des crises
    Remplace les valeurs existantes de population_touchee et accessibilite
    et ajoute une colonne source
    """
    # Chemin du fichier CSV principal
    chemin_csv = Path(__file__).parent / 'data' / 'Base_Crises_TresTres_Enrichie_CGenial.csv'
    
    if not chemin_csv.exists():
        print(f"❌ Fichier non trouvé: {chemin_csv}")
        return
    
    # Vérifie la clé API
    if OPENAI_API_KEY == "VOTRE_CLE_API_OPENAI_ICI":
        print("⚠ ATTENTION: Veuillez définir votre clé API OpenAI dans le script ou via la variable d'environnement OPENAI_API_KEY")
        print("   Vous pouvez obtenir une clé sur: https://platform.openai.com/api-keys")
        reponse = input("Voulez-vous continuer quand même? (o/n): ")
        if reponse.lower() != 'o':
            return
    
    print(f"📖 Lecture du fichier: {chemin_csv}")
    df = pd.read_csv(chemin_csv, encoding='utf-8')
    
    print(f"✓ {len(df)} crises trouvées dans le fichier")
    
    # Vérifie si les colonnes existent déjà
    if 'population_touchee' not in df.columns:
        df['population_touchee'] = None
    if 'accessibilite' not in df.columns:
        df['accessibilite'] = None
    if 'source' not in df.columns:
        df['source'] = None
    
    # Compte combien de crises ont déjà des données
    deja_remplis = df['population_touchee'].notna().sum()
    print(f"📊 {deja_remplis} crises ont déjà une population touchée")
    print(f"📊 {df['accessibilite'].notna().sum()} crises ont déjà une accessibilité")
 
    # Traite chaque crise
    total = len(df)
    traites = 0
    reussis = 0
    echecs = 0
    
    for idx, crise in df.iterrows():
        traites += 1
        
        print(f"\n[{traites}/{total}] 🔍 Traitement de la crise {idx+1}...")
        
        # Affiche les informations de la crise
        nom = crise.get('nom_crise', f'Crise {idx+1}')
        type_crise = crise.get('type_crise', 'N/A')
        pays = crise.get('pays', 'N/A')
        date = crise.get('date', 'N/A')
        intensite = crise.get('intensite', 'N/A')
        print(f"   Nom: {nom}")
        print(f"   Type: {type_crise}, Pays: {pays}, Date: {date}, Intensité: {intensite}")
        
        # Affiche les valeurs actuelles
        pop_actuelle = crise.get('population_touchee', 'N/A')
        acc_actuelle = crise.get('accessibilite', 'N/A')
        print(f"   Valeurs actuelles - Population: {pop_actuelle}, Accessibilité: {acc_actuelle}")
        
        # Crée le prompt
        prompt = creer_prompt_crise(crise)
        
        # Appelle l'API ChatGPT (un seul appel pour obtenir toutes les données)
        print("   📡 Appel à l'API ChatGPT (population, accessibilité, source)...")
        reponse = appeler_chatgpt(prompt)
        
        if reponse is None:
            print("   ❌ Échec de l'appel API")
            echecs += 1
            time.sleep(2)  # Pause avant le prochain appel
            continue
        
        print(f"   ✓ Réponse reçue: {reponse[:100]}...")
        
        # Extrait toutes les données en une seule fois (population, accessibilité, source)
        population_touchee, accessibilite, source = extraire_donnees_crise(crise, reponse)
        
        if population_touchee is not None and accessibilite is not None and source is not None:
            # REMPLACE les valeurs existantes
            df.at[idx, 'population_touchee'] = population_touchee
            df.at[idx, 'accessibilite'] = accessibilite
            df.at[idx, 'source'] = source
            print(f"   ✓ Données mises à jour: population={population_touchee}, accessibilité={accessibilite:.2f}")
            print(f"   ✓ Source: {source}")
            reussis += 1
        else:
            print(f"   ⚠ Impossible d'extraire toutes les données de la réponse")
            print(f"   Réponse complète: {reponse}")
            echecs += 1
        
        # Sauvegarde périodique (tous les 10 crises)
        if traites % 10 == 0:
            df.to_csv(chemin_csv, index=False, encoding='utf-8')
            print(f"   💾 Sauvegarde intermédiaire effectuée")
        
        # Pause entre les appels pour éviter de surcharger l'API
        time.sleep(1)
    
    # Sauvegarde finale
    print(f"\n💾 Sauvegarde finale du fichier...")
    df.to_csv(chemin_csv, index=False, encoding='utf-8')
    
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

