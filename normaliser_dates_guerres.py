"""
Normalise les dates et la population des crises de type "Guerre" dans le fichier principal.

Règles appliquées sur les colonnes de date (date, date_fin) :
- Si seule une année est présente (ex: 1947) -> 01/01/1947
- Si plusieurs années sont présentes (ex: 1990-1991) -> 01/01/1990
- Si la date est déjà complète (JJ/MM/AAAA) -> inchangée

Règle appliquée sur la population (population_touchee) :
- Convertit tout format texte en une seule valeur numérique
- Si plusieurs nombres sont présents, garde le premier (borne basse)

Le script crée une sauvegarde .bak avant écriture.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pandas as pd


CSV_PATH = Path(__file__).parent / "data" / "Base_Crises_TresTres_Enrichie_CGenial - Copie (4).csv"


def normaliser_date_guerre(valeur_date: object) -> str:
    """Retourne une date normalisée au format JJ/MM/AAAA selon les règles demandées."""
    if pd.isna(valeur_date):
        return ""

    texte = str(valeur_date).replace("\xa0", " ").strip()
    if not texte:
        return ""

    # Déjà une date complète au format JJ/MM/AAAA
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", texte):
        return texte

    # Extrait toutes les années à 4 chiffres trouvées dans la chaîne
    annees = re.findall(r"(?:19|20)\d{2}", texte)
    if annees:
        return f"01/01/{annees[0]}"

    # Aucun format exploitable : on laisse tel quel
    return texte


def normaliser_population_guerre(valeur_population: object) -> object:
    """
    Retourne une seule valeur numérique de population.

    Exemples:
    - "200 000 à 2 000 000" -> 1100000
    - "au moins 506 000[11]" -> 506000
    - "160+" -> 160
    """
    print("Pierre")
    if pd.isna(valeur_population):
        return valeur_population

    texte = str(valeur_population).strip()
    if not texte:
        print("Pierre1")
        return valeur_population

    # Déjà numérique
    try:
        return float(texte)
    except ValueError:
        pass

    # Normalise les espaces spéciaux fréquemment présents dans les sources web
    # (NBSP, espace fine, etc.)
    texte = (
        texte.replace("\xa0", " ")
        .replace("\u202f", " ")
        .replace("\u2009", " ")
        .replace("\u2007", " ")
    )
    # Supprime les références de type [12], [a], [47],[48], etc.
    texte = re.sub(r"\[[^\]]*\]", "", texte)

    # Récupère les nombres utiles :
    # ex "200 000 à 2 000 000" -> ["200 000", "2 000 000"]
    # ex "au moins 506 000" -> ["506 000"]
    # ex "160+" -> ["160"]
    nombres = re.findall(r"\d+(?:[ \.,]\d+)*", texte)
    if not nombres:
        print("Pierre2")
        return valeur_population

    def _to_int(nombre_texte: str) -> int | None:
        compact = re.sub(r"\s+", "", nombre_texte)
        # Gère les cas "1,400,000" ou "1.400.000" -> 1400000
        if compact.count(",") > 1 and "." not in compact:
            compact = compact.replace(",", "")
        if compact.count(".") > 1 and "," not in compact:
            compact = compact.replace(".", "")
        # Pour la population, on traite les séparateurs comme des milliers
        compact = compact.replace(",", "").replace(".", "")
        try:
            return int(compact)
        except ValueError:
            return None

    valeurs = [_to_int(n) for n in nombres]
    valeurs = [v for v in valeurs if v is not None]
    if not valeurs:
        print("Pierre3")
        return valeur_population

    # Si intervalle explicite (à / - / – / to) et au moins 2 bornes,
    # utilise la moyenne des 2 premières bornes.
    if len(valeurs) >= 2 and re.search(r"\bà\b|\bto\b|[-–]", texte, re.IGNORECASE):
        return int(round((valeurs[0] + valeurs[1]) / 2))

    # Sinon, garde la première valeur (cas "au moins", "+", valeur unique, etc.)
    print("Pierre4" + valeurs[0])
    return valeurs[0]


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable: {CSV_PATH}")

    print(f"Lecture: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8", on_bad_lines="skip")

    if "type_crise" not in df.columns:
        raise ValueError("Colonne 'type_crise' absente du fichier.")
    if "date" not in df.columns and "date_fin" not in df.columns:
        raise ValueError("Aucune colonne de date ('date' ou 'date_fin') trouvée.")
    if "population_touchee" not in df.columns:
        raise ValueError("Colonne 'population_touchee' absente du fichier.")

    masque_guerres = df["type_crise"].astype(str).str.lower().str.contains("guerre", na=False)
    nb_guerres = int(masque_guerres.sum())
    print(f"Lignes 'Guerre' détectées: {nb_guerres}")

    if nb_guerres == 0:
        print("Aucune ligne Guerre à corriger.")
        return

    # Applique la normalisation uniquement sur les guerres
    modifications = 0
    colonnes_dates = [col for col in ("date", "date_fin") if col in df.columns]

    for col in colonnes_dates:
        avant = df.loc[masque_guerres, col].astype(str).tolist()
        df.loc[masque_guerres, col] = df.loc[masque_guerres, col].apply(normaliser_date_guerre)
        apres = df.loc[masque_guerres, col].astype(str).tolist()
        mod_col = sum(1 for a, b in zip(avant, apres) if a != b)
        modifications += mod_col
        print(f"Modifications sur '{col}': {mod_col}")

    print(f"Total dates modifiées: {modifications}")

    # Normalise la population pour les guerres
    avant_pop = df.loc[masque_guerres, "population_touchee"].astype(str).tolist()
    df.loc[masque_guerres, "population_touchee"] = df.loc[masque_guerres, "population_touchee"].apply(
        normaliser_population_guerre
    )
    apres_pop = df.loc[masque_guerres, "population_touchee"].astype(str).tolist()
    mod_pop = sum(1 for a, b in zip(avant_pop, apres_pop) if a != b)
    print(f"Modifications sur 'population_touchee': {mod_pop}")

    # Contrôle rapide : compte les valeurs guerre qui restent non numériques
    pop_guerres = df.loc[masque_guerres, "population_touchee"]
    pop_non_numeriques = pd.to_numeric(pop_guerres, errors="coerce").isna().sum()
    print(f"Valeurs 'population_touchee' non numériques restantes (Guerre): {int(pop_non_numeriques)}")

    # Sauvegarde de sécurité
    backup_path = CSV_PATH.with_suffix(CSV_PATH.suffix + ".bak")
    shutil.copy2(CSV_PATH, backup_path)
    print(f"Sauvegarde créée: {backup_path}")

    df.to_csv(CSV_PATH, sep=";", index=False, encoding="utf-8")
    print("Fichier mis à jour avec succès.")


if __name__ == "__main__":
    main()


