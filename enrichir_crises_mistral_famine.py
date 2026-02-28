"""
Script pour enrichir le fichier CSV des famines avec les informations :
- population_touchee
- latitude
- longitude
- accessibilite
- intensite
- source
en utilisant l'API Mistral AI.
"""

import pandas as pd
import requests
import json
import time
from pathlib import Path
import sys
import re

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

def _parse_nombre(valeur):
    """
    Convertit une valeur texte/numérique en float.
    """
    if valeur is None:
        return None
    texte = str(valeur).strip().replace(" ", "").replace(",", ".")
    if not texte:
        return None
    try:
        return float(texte)
    except ValueError:
        return None


def extraire_donnees_famine(reponse_ia):
    """
    Extrait les données demandées (population_touchee, latitude, longitude, accessibilite, intensite, source)
    de la réponse de l'IA.
    
    Args:
        reponse_ia (str): Réponse de l'IA
    
    Returns:
        tuple: (population_touchee, latitude, longitude, accessibilite, intensite, source)
        ou (None, None, None, None, None, None) si échec.
    """
    try:
        population_touchee = None
        latitude = None
        longitude = None
        accessibilite = None
        intensite = None
        source = None

        texte = reponse_ia.strip()
        texte = re.sub(r"^```(?:json)?\s*", "", texte, flags=re.IGNORECASE)
        texte = re.sub(r"\s*```$", "", texte)

        data = None
        try:
            data = json.loads(texte)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", reponse_ia, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    data = None

        if isinstance(data, dict):
            if data.get("population_touchee") not in [None, ""]:
                pop = _parse_nombre(data.get("population_touchee"))
                if pop is not None:
                    population_touchee = int(pop)
            if data.get("latitude") not in [None, ""]:
                latitude = _parse_nombre(data.get("latitude"))
            if data.get("longitude") not in [None, ""]:
                longitude = _parse_nombre(data.get("longitude"))
            if data.get("accessibilite") not in [None, ""]:
                accessibilite = _parse_nombre(data.get("accessibilite"))
            if data.get("intensite") not in [None, ""]:
                intensite = _parse_nombre(data.get("intensite"))
            if data.get("source") not in [None, ""]:
                source = str(data.get("source")).strip()

        if population_touchee is None:
            pop_match = re.search(r"population[_\s]?touch[eé]e\s*[:=]\s*([-\d\s,.]+)", reponse_ia, re.IGNORECASE)
            if pop_match:
                pop = _parse_nombre(pop_match.group(1))
                if pop is not None:
                    population_touchee = int(pop)

        if latitude is None:
            lat_match = re.search(r"latitude\s*[:=]\s*(-?\d+(?:[.,]\d+)?)", reponse_ia, re.IGNORECASE)
            if lat_match:
                latitude = _parse_nombre(lat_match.group(1))

        if longitude is None:
            lon_match = re.search(r"longitude\s*[:=]\s*(-?\d+(?:[.,]\d+)?)", reponse_ia, re.IGNORECASE)
            if lon_match:
                longitude = _parse_nombre(lon_match.group(1))

        if accessibilite is None:
            acc_match = re.search(r"accessibilit[eé]\s*[:=]\s*(-?\d+(?:\.\d+)?)", reponse_ia, re.IGNORECASE)
            if acc_match:
                accessibilite = _parse_nombre(acc_match.group(1))

        if intensite is None:
            int_match = re.search(r"intensit[eé]\s*[:=]\s*(-?\d+(?:\.\d+)?)", reponse_ia, re.IGNORECASE)
            if int_match:
                intensite = _parse_nombre(int_match.group(1))

        if source is None:
            source_match = re.search(r"source\s*[:=]\s*(.+)", reponse_ia, re.IGNORECASE)
            if source_match:
                source = source_match.group(1).strip().strip("\"'")

        return population_touchee, latitude, longitude, accessibilite, intensite, source
        
    except Exception as e:
        print(f"⚠ Erreur lors de l'extraction des données: {e}")
        return None, None, None, None, None, None

def creer_prompt_famine(famine):
    """
    Crée un prompt pour l'IA basé sur les informations de la famine.
    
    Args:
        famine (pandas.Series): Ligne du DataFrame avec les informations de la famine
    
    Returns:
        str: Le prompt à envoyer à l'IA
    """
    prompt = """Tu es un expert en crises humanitaires.

Pour la famine suivante, estime les informations suivantes :
1) population_touchee : nombre entier de personnes
2) latitude : nombre décimal
3) longitude : nombre décimal
4) accessibilite : nombre entre 0 et 1 (0 = très difficile d'accès, 1 = facile d'accès)
5) intensite : nombre entre 0 et 10
6) source : source principale utilisée (nom du site + URL si possible)

Important : donne population_touchee même si une colonne du CSV contient déjà une estimation.

Famine :
"""

    for col in famine.index:
        if pd.notna(famine[col]) and str(famine[col]).strip():
            prompt += f"- {col}: {famine[col]}\n"

    prompt += """

Réponds UNIQUEMENT avec un JSON valide, sans texte additionnel :
{
  "population_touchee": 123456,
  "latitude": 12.34,
  "longitude": 56.78,
  "accessibilite": 0.5,
  "intensite": 6.0,
  "source": "Nom de la source - https://..."
}

Si une information exacte manque, donne la meilleure estimation plausible.
"""
    
    return prompt

def enrichir_crises():
    """
    Fonction principale pour enrichir le fichier CSV des famines.
    """
    # Chemin du fichier CSV des famines
    chemin_csv = Path(__file__).parent / 'data' / 'famines.csv'
    
    if not chemin_csv.exists():
        print(f"❌ Fichier non trouvé: {chemin_csv}")
        return
    
    print(f"📖 Lecture du fichier: {chemin_csv}")
    df = pd.read_csv(chemin_csv, sep=';', encoding='utf-8', on_bad_lines='skip')
    
    print(f"✓ {len(df)} famines trouvées dans le fichier")

    # Vérifie la présence des colonnes ciblées et les crée si besoin
    for col in ['population_touchee', 'latitude', 'longitude', 'accessibilite', 'intensite', 'source']:
        if col not in df.columns:
            df[col] = None

    def est_manquant(valeur):
        """True si la valeur est absente (NaN ou chaîne vide)."""
        if pd.isna(valeur):
            return True
        if isinstance(valeur, str) and not valeur.strip():
            return True
        return False
       
    # Traite chaque famine
    total = len(df)
    traites = 0
    reussis = 0
    echecs = 0
    
    for idx, famine in df.iterrows():
        traites += 1

        # Vérifie quels champs sont manquants
        champs_cibles = ['population_touchee', 'latitude', 'longitude', 'accessibilite', 'intensite', 'source']
        champs_manquants = [c for c in champs_cibles if est_manquant(famine.get(c))]
        # population_touchee est toujours redemandée à Mistral (même si présente ailleurs)
        force_population = 'population_touchee'
        if force_population not in champs_manquants:
            champs_manquants.append(force_population)

        # Si tout est déjà renseigné, passe à la suite
        if not champs_manquants:
            print(f"[{traites}/{total}] ✓ Famine {idx+1} déjà complétée, passage à la suivante...")
            continue
        
        print(f"\n[{traites}/{total}] 🔍 Traitement de la famine {idx+1}...")
        
        # Affiche les informations de la famine
        print(f"   Année: {famine.get('Année', 'N/A')} | Pays: {famine.get('Pays', 'N/A')}")
        print(f"   Champs manquants: {', '.join(champs_manquants)}")
        
        # Crée le prompt
        prompt = creer_prompt_famine(famine)
        
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
        population_touchee, latitude, longitude, accessibilite, intensite, source = extraire_donnees_famine(reponse)

        # Met à jour uniquement les champs manquants et récupérés
        champs_mis_a_jour = []
        if population_touchee is not None:
            df.at[idx, 'population_touchee'] = int(population_touchee)
            champs_mis_a_jour.append(f"population_touchee={int(population_touchee)}")
        if 'latitude' in champs_manquants and latitude is not None:
            df.at[idx, 'latitude'] = latitude
            champs_mis_a_jour.append(f"latitude={latitude}")
        if 'longitude' in champs_manquants and longitude is not None:
            df.at[idx, 'longitude'] = longitude
            champs_mis_a_jour.append(f"longitude={longitude}")
        if 'accessibilite' in champs_manquants and accessibilite is not None:
            df.at[idx, 'accessibilite'] = accessibilite
            champs_mis_a_jour.append(f"accessibilite={accessibilite}")
        if 'intensite' in champs_manquants and intensite is not None:
            df.at[idx, 'intensite'] = intensite
            champs_mis_a_jour.append(f"intensite={intensite}")
        if 'source' in champs_manquants and source is not None and str(source).strip():
            df.at[idx, 'source'] = source
            champs_mis_a_jour.append(f"source={source}")

        if champs_mis_a_jour:
            print(f"   ✓ Données mises à jour: {', '.join(champs_mis_a_jour)}")
            reussis += 1
        else:
            print(f"   ⚠ Impossible d'extraire les champs demandés depuis la réponse")
            print(f"   Réponse complète: {reponse}")
            echecs += 1
        
        # Sauvegarde périodique
        if traites % 25 == 0:
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

