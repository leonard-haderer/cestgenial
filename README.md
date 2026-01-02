# Projet CGénial - Allocation de Ressources en Cas de Crise

## 🎯 Description du Projet

Ce projet est un système intelligent de gestion humanitaire qui utilise l'intelligence artificielle et la science des données pour :
- **Analyser** des crises humanitaires passées et actuelles
- **Allouer** efficacement des ressources limitées selon un algorithme glouton (crises actuelles uniquement)
- **Visualiser** les crises et leurs allocations sur une carte interactive
- **Prédire** le type et l'intensité de nouvelles crises potentielles

## ⚠️ Fonctionnalité Importante : Actualité des Crises

**L'allocation des ressources ne considère que les crises actuelles** (marquées avec `en_cours=True` dans la base de données). Les crises passées sont automatiquement exclues de l'allocation pour garantir que les ressources sont allouées uniquement aux situations d'urgence en cours.

## 📋 Fonctionnalités

### 1. Chargement et Analyse des Données
- Chargement de données de crises historiques et actuelles
- Colonne `en_cours` pour distinguer les crises actuelles des passées
- Chargement des besoins en ressources par type de crise
- Statistiques et analyses descriptives

### 2. Allocation Gloutonne des Ressources
- **Filtre automatique** : Seules les crises actuelles sont considérées
- Calcul d'un score d'urgence : `intensité × population touchée × (1 - accessibilité)`
- Allocation prioritaire des ressources aux crises les plus urgentes
- Export des résultats en CSV ou Excel

### 3. Visualisation Interactive
- Carte interactive HTML créée avec Folium
- Marqueurs colorés par type de crise
- Indicateur visuel pour les crises actuelles
- Popups avec informations détaillées
- Champ de recherche de coordonnées (latitude/longitude)
- Filtres par type de crise (via LayerControl)
- Légende et titre dynamiques

### 4. Prédiction par Machine Learning
- Recherche de pays avec données automatiques (latitude, longitude, population)
- Sélection du type de risque
- **Calcul de probabilité** que l'événement se produise dans le pays choisi
- Prédiction de l'intensité avec intervalle de confiance
- Calcul des besoins en ressources avec pourcentages du budget

### 5. Interface Web Moderne
- Interface web complète avec Bootstrap 5
- API REST pour toutes les fonctionnalités
- Graphiques interactifs (Chart.js)
- Design moderne et responsive

### 6. Interface Menu Console
- Menu console convivial
- Navigation simple entre les différentes fonctionnalités
- Guides pas à pas pour chaque opération

## 📁 Structure du Projet

```
Projet CGénial/
│
├── data/                          # Dossier des données
│   ├── Base_Crises_TresTres_Enrichie_CGenial.csv
│   ├── Besoins_Crises_Passees.csv
│   └── pays_donnees.csv
│
├── src/                           # Code source
│   ├── __init__.py
│   ├── chargement_donnees.py      # Module de chargement (avec filtre en_cours)
│   ├── allocation_gloutonne.py    # Algorithme glouton (crises actuelles uniquement)
│   ├── visualisation_carte.py     # Création de cartes interactives
│   ├── prediction_crises.py       # Modèles de prédiction ML + probabilité
│   ├── menu_interactif.py         # Interface menu console
│   └── app_web.py                 # Application web Flask
│
├── templates/                     # Templates HTML
│   └── index.html
│
├── static/                        # Fichiers statiques
│   ├── js/
│   │   └── app.js
│   └── maps/
│
├── outputs/                       # Résultats d'allocation (CSV/Excel)
├── maps/                          # Cartes HTML générées
│
├── main.py                        # Script principal (console)
├── run_web.py                     # Script de lancement serveur web
├── requirements.txt               # Dépendances Python
└── README.md                      # Ce fichier
```

## 🚀 Installation

### Prérequis
- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

   Ou installer manuellement :
   ```bash
   pip install pandas numpy folium matplotlib scikit-learn openpyxl flask
   ```

3. **Vérifier l'installation** :
   ```bash
   python main.py
   ```

## 💻 Utilisation

### Interface Console

```bash
python main.py
```

### Interface Web

```bash
python run_web.py
```

Puis ouvrez votre navigateur sur : **http://localhost:8080**

## 📊 Format des Données

### Fichier des Crises (`Base_Crises_TresTres_Enrichie_CGenial.csv`)

Colonnes requises :
- `nom_crise` : Nom de la crise
- `type_crise` : Type (Séisme, Tsunami, Pandémie, Guerre, etc.)
- `pays` : Pays concerné
- `latitude` : Latitude (décimal)
- `longitude` : Longitude (décimal)
- `intensite` : Intensité (0-10)
- `date` : Date au format YYYY-MM-DD
- `population_touchee` : Nombre de personnes touchées
- `accessibilite` : Accessibilité (0-1, où 0 = très difficile, 1 = facile)
- `en_cours` : **True** si la crise est actuelle, **False** si passée
- `date_fin` : Date de fin (optionnel, format YYYY-MM-DD)

### Fichier des Besoins (`Besoins_Crises_Passees.csv`)

Colonnes requises :
- `type_crise` : Type de crise
- `eau_potable_litres` : Besoin en eau potable
- `tentes` : Nombre de tentes
- `medicaments_doses` : Nombre de doses de médicaments
- `hopitaux_campagne` : Nombre d'hôpitaux de campagne
- `generateurs` : Nombre de générateurs
- `vehicules_urgence` : Nombre de véhicules d'urgence
- `personnel_medical` : Nombre de personnel médical
- `denrees_alimentaires_kg` : Quantité de denrées alimentaires (kg)

## 🧮 Algorithme Glouton

L'algorithme d'allocation fonctionne en plusieurs étapes :

1. **Filtrage** : Ne considère que les crises avec `en_cours=True`
2. **Calcul du score d'urgence** pour chaque crise :
   ```
   score = intensité × population_touchée × (1 - accessibilité)
   ```
3. **Tri des crises** par score décroissant (les plus urgentes en premier)
4. **Allocation gloutonne** : Pour chaque crise dans l'ordre de priorité :
   - Calcule les besoins selon le type de crise et l'intensité
   - Alloue les ressources disponibles (minimum entre besoin et stock)
   - Met à jour le stock restant

5. **Export des résultats** avec les allocations et pourcentages de satisfaction

## 🤖 Modèles de Prédiction

### Random Forest (Recommandé)
- **Type de crise** : Classification multi-classe
- **Intensité** : Régression
- **Probabilité d'événement** : Basée sur la proximité géographique et l'historique

### Calcul de Probabilité

La probabilité qu'un événement se produise dans un pays est calculée selon :
- **Proximité géographique** : Distance aux crises historiques similaires
- **Fréquence du type** : Nombre de crises de ce type dans l'historique
- **Intensité similaire** : Présence de crises d'intensité proche
- **Ajustement** : Les intensités très élevées sont légèrement moins probables

## 📈 Visualisation

La carte interactive inclut :
- **Marqueurs colorés** par type de crise
- **Indicateur visuel** pour les crises actuelles (⚠ CRISE ACTUELLE)
- **Icônes** différentes selon le type
- **Popups** avec informations détaillées
- **Champ de recherche** de coordonnées (latitude/longitude)
- **Contrôle des couches** pour filtrer par type
- **Légende** interactive
- **Titre** dynamique

## 🔧 Personnalisation

### Ajouter de nouvelles crises

Éditez le fichier `data/Base_Crises_TresTres_Enrichie_CGenial.csv` et ajoutez des lignes au format :
```csv
nom_crise,type_crise,pays,latitude,longitude,intensite,date,population_touchee,accessibilite,description,en_cours,date_fin
```

**Important** : Définissez `en_cours=True` pour les crises actuelles, `False` pour les passées.

### Modifier les besoins par type

Éditez le fichier `data/Besoins_Crises_Passees.csv` pour ajuster les besoins.

## 🐛 Dépannage

### Erreur : Module non trouvé
```bash
pip install -r requirements.txt
```

### Erreur : Fichier de données introuvable
Vérifiez que les fichiers CSV sont bien dans le dossier `data/`.

### Erreur : Aucune crise actuelle trouvée
Vérifiez que certaines crises ont `en_cours=True` dans le fichier CSV.

### Erreur : Port déjà utilisé (web)
Changez le port dans `run_web.py` ou `src/app_web.py`

## 📚 Ressources et Documentation

- **Pandas** : https://pandas.pydata.org/
- **Folium** : https://python-visualization.github.io/folium/
- **Scikit-learn** : https://scikit-learn.org/
- **Flask** : https://flask.palletsprojects.com/
- **NumPy** : https://numpy.org/

## 👥 Auteurs

Projet CGénial 2025 - Allocation de ressources en cas de crise

## 📝 Licence

Ce projet est destiné à un usage éducatif dans le cadre du concours CGénial.

## 🎓 Objectifs Pédagogiques

Ce projet permet d'aborder :
- La manipulation de données avec Pandas
- Les algorithmes gloutons
- Le machine learning (classification et régression)
- La visualisation de données géospatiales
- La programmation orientée objet en Python
- La gestion de projet et la structuration de code
- Les interfaces web avec Flask

## 🔮 Améliorations Futures

- [ ] Intégration d'API temps réel (EMDAT, ACLED)
- [ ] Optimisation multi-objectifs (au lieu de glouton simple)
- [ ] Prédiction temporelle (quand une crise va se produire)
- [ ] Simulation de scénarios de crise
- [ ] Export de rapports PDF automatiques
- [ ] Système de notifications pour nouvelles crises

---

**Bon projet et bonne chance pour le concours CGénial ! 🚀**

