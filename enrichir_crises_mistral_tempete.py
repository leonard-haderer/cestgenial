"""
Script pour enrichir le fichier CSV des tempêtes IBTrACS avec les informations :
- type_tempete (ouragan, typhon, cyclone, autre)
- pays_concerne
- population_touchee
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

def normaliser_type_tempete(valeur):
    """
    Normalise le type de tempête dans l'ensemble attendu.
    """
    if valeur is None:
        return None

    texte = str(valeur).strip().lower()
    if not texte:
        return None

    if "ouragan" in texte or "hurricane" in texte:
        return "ouragan"
    if "typhon" in texte or "typhoon" in texte:
        return "typhon"
    if "cyclone" in texte:
        return "cyclone"
    return "autre"


def extraire_donnees_tempete(reponse_ia):
    """
    Extrait les données demandées (type_tempete, pays_concerne, population_touchee,
    accessibilite, intensite, source)
    de la réponse de l'IA.
    
    Args:
        reponse_ia (str): Réponse de l'IA
    
    Returns:
        tuple: (type_tempete, pays_concerne, population_touchee, accessibilite, intensite, source)
        ou (None, None, None, None, None, None) si échec.
    """
    try:
        type_tempete = None
        pays_concerne = None
        population_touchee = None
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
            type_tempete = normaliser_type_tempete(
                data.get("type_tempete") or data.get("type") or data.get("categorie")
            )
            if data.get("pays_concerne") not in [None, ""]:
                pays_concerne = str(data.get("pays_concerne")).strip()
            if pays_concerne is None and data.get("pays") not in [None, ""]:
                pays_concerne = str(data.get("pays")).strip()
            if data.get("population_touchee") not in [None, ""]:
                population_touchee = int(float(str(data.get("population_touchee")).replace(" ", "")))
            if data.get("accessibilite") not in [None, ""]:
                accessibilite = float(data.get("accessibilite"))
            if data.get("intensite") not in [None, ""]:
                intensite = float(data.get("intensite"))
            if data.get("source") not in [None, ""]:
                source = str(data.get("source")).strip()

        if type_tempete is None:
            type_match = re.search(r"type[_\s]?temp[eê]te\s*[:=]\s*([^\n,]+)", reponse_ia, re.IGNORECASE)
            if type_match:
                type_tempete = normaliser_type_tempete(type_match.group(1).strip())

        if population_touchee is None:
            pop_match = re.search(r"population[_\s]?touch[eé]e\s*[:=]\s*([\d\s]+)", reponse_ia, re.IGNORECASE)
            if pop_match:
                population_touchee = int(pop_match.group(1).replace(" ", ""))

        if pays_concerne is None:
            pays_match = re.search(r"pays[_\s]?concern[eé]\s*[:=]\s*([^\n,]+)", reponse_ia, re.IGNORECASE)
            if pays_match:
                pays_concerne = pays_match.group(1).strip()
        if pays_concerne is None:
            pays_simple_match = re.search(r"pays\s*[:=]\s*([^\n,]+)", reponse_ia, re.IGNORECASE)
            if pays_simple_match:
                pays_concerne = pays_simple_match.group(1).strip()

        if accessibilite is None:
            acc_match = re.search(r"accessibilit[eé]\s*[:=]\s*(-?\d+(?:\.\d+)?)", reponse_ia, re.IGNORECASE)
            if acc_match:
                accessibilite = float(acc_match.group(1))

        if intensite is None:
            int_match = re.search(r"intensit[eé]\s*[:=]\s*(-?\d+(?:\.\d+)?)", reponse_ia, re.IGNORECASE)
            if int_match:
                intensite = float(int_match.group(1))

        if source is None:
            source_match = re.search(r"source\s*[:=]\s*(.+)", reponse_ia, re.IGNORECASE)
            if source_match:
                source = source_match.group(1).strip().strip("\"'")

        return type_tempete, pays_concerne, population_touchee, accessibilite, intensite, source
        
    except Exception as e:
        print(f"⚠ Erreur lors de l'extraction des données: {e}")
        return None, None, None, None, None, None

def creer_prompt_tempete(tempete):
    """
    Crée un prompt pour l'IA basé sur les informations de la tempête.
    
    Args:
        tempete (pandas.Series): Ligne du DataFrame avec les informations de la tempête
    
    Returns:
        str: Le prompt à envoyer à l'IA
    """
    prompt = """Tu es un expert en risques climatiques et crises humanitaires.

Pour la tempête suivante, estime les informations suivantes :
1) type_tempete : "ouragan", "typhon", "cyclone" ou "autre" (si vraiment le type n'est pas clair, choisis "autre")
2) pays_concerne : pays principalement impacté
3) population_touchee : nombre entier de personnes
4) accessibilite : nombre entre 0 et 1 (0 = très difficile d'accès, 1 = facile d'accès)
5) intensite : nombre entre 0 et 10 
6) source : source principale utilisée (nom du site + URL si possible)

Tempête :
"""

    for col in tempete.index:
        if pd.notna(tempete[col]) and str(tempete[col]).strip():
            prompt += f"- {col}: {tempete[col]}\n"

    prompt += """

Réponds UNIQUEMENT avec un JSON valide, sans texte additionnel :
{
  "type_tempete": "ouragan|typhon|cyclone|autre",
  "pays_concerne": "Nom du pays",
  "population_touchee": 123456,
  "accessibilite": 0.5,
  "intensite": 6.0,
  "source": "Nom de la source - https://..."
}

Si une information exacte manque, donne la meilleure estimation plausible.
"""
    
    return prompt

def enrichir_crises():
    """
    Fonction principale pour enrichir le fichier CSV des crises
    """
    # Chemin du fichier CSV IBTrACS filtré
    chemin_csv = Path(__file__).parent / 'data' / 'ibtracs.ALL.list.v04r01_filtered.csv'
    
    if not chemin_csv.exists():
        print(f"❌ Fichier non trouvé: {chemin_csv}")
        return
    
    print(f"📖 Lecture du fichier: {chemin_csv}")
    df = pd.read_csv(chemin_csv, sep=';', encoding='utf-8', on_bad_lines='skip')
    
    print(f"✓ {len(df)} tempêtes trouvées dans le fichier")

    # Vérifie la présence des colonnes ciblées et les crée si besoin
    for col in ['type_tempete', 'pays_concerne', 'population_touchee', 'accessibilite', 'intensite', 'source']:
        if col not in df.columns:
            df[col] = None

    def est_manquant(valeur):
        """True si la valeur est absente (NaN ou chaîne vide)."""
        if pd.isna(valeur):
            return True
        if isinstance(valeur, str) and not valeur.strip():
            return True
        return False
       
    # Traite chaque tempête
    total = len(df)
    traites = 0
    reussis = 0
    echecs = 0
    
    for idx, tempete in df.iterrows():
        traites += 1

        # Vérifie quels champs sont manquants
        champs_cibles = ['type_tempete', 'pays_concerne', 'population_touchee', 'accessibilite', 'intensite', 'source']
        champs_manquants = [c for c in champs_cibles if est_manquant(tempete.get(c))]

        # Si tout est déjà renseigné, passe à la suite
        if not champs_manquants:
            print(f"[{traites}/{total}] ✓ Tempête {idx+1} déjà complétée, passage à la suivante...")
            continue
        
        print(f"\n[{traites}/{total}] 🔍 Traitement de la tempête {idx+1}...")
        
        # Affiche les informations de la tempête
        print(f"   SID: {tempete.get('SID', 'N/A')} | Nom: {tempete.get('NAME', 'N/A')}")
        print(f"   Champs manquants: {', '.join(champs_manquants)}")
        
        # Crée le prompt
        prompt = creer_prompt_tempete(tempete)
        
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
        type_tempete, pays_concerne, population_touchee, accessibilite, intensite, source = extraire_donnees_tempete(reponse)

        # Met à jour uniquement les champs manquants et récupérés
        champs_mis_a_jour = []
        if 'type_tempete' in champs_manquants and type_tempete is not None:
            df.at[idx, 'type_tempete'] = type_tempete
            champs_mis_a_jour.append(f"type_tempete={type_tempete}")
        if 'pays_concerne' in champs_manquants and pays_concerne is not None and str(pays_concerne).strip():
            df.at[idx, 'pays_concerne'] = pays_concerne
            champs_mis_a_jour.append(f"pays_concerne={pays_concerne}")
        if 'population_touchee' in champs_manquants and population_touchee is not None:
            df.at[idx, 'population_touchee'] = int(population_touchee)
            champs_mis_a_jour.append(f"population_touchee={int(population_touchee)}")
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

