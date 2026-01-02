# Interface Web - Projet CGénial

## 🚀 Lancement du Serveur Web

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Démarrage du serveur

```bash
python run_web.py
```

Le serveur sera accessible sur : **http://localhost:8080**

## 📋 Fonctionnalités de l'Interface Web

### 1. **Tableau de Bord**
- Statistiques globales (nombre de crises, crises actuelles, intensité moyenne, population touchée)
- Graphique de répartition par type de crise
- Vue d'ensemble du système
- Indicateur du nombre de crises actuelles

### 2. **Gestion des Crises**
- Liste complète de toutes les crises historiques
- Filtre pour afficher uniquement les crises actuelles
- Tableau interactif avec détails (type, pays, date, intensité, population)
- Badge indiquant si la crise est actuelle ou passée

### 3. **Allocation Gloutonne**
- ⚠ **Important** : Seules les crises actuelles sont prises en compte
- Configuration du stock disponible pour chaque ressource
- Calcul automatique de l'allocation optimale
- Affichage des 5 crises les plus prioritaires
- Stocks restants après allocation
- Message d'avertissement si aucune crise actuelle n'est trouvée

### 4. **Carte Interactive**
- Génération de carte interactive avec Folium
- Option pour inclure les allocations de ressources
- Visualisation géographique des crises
- Indicateur visuel pour les crises actuelles
- Recherche de coordonnées intégrée (latitude/longitude)
- Affichage dans une iframe

### 5. **Prédiction de Crises**
- Recherche de pays avec données automatiques (latitude, longitude, population)
- Sélection du type de risque
- **Calcul de la probabilité** que l'événement se produise dans le pays
- Configuration de l'intensité et du budget
- Besoins en ressources avec pourcentages du budget
- Barres de progression visuelles

## 🎨 Design

L'interface utilise :
- **Bootstrap 5** pour le design responsive
- **Font Awesome** pour les icônes
- **Chart.js** pour les graphiques
- Design moderne avec dégradés et animations
- Couleurs distinctives pour les crises actuelles

## 🔧 Structure des Fichiers

```
Projet CGénial/
├── templates/
│   └── index.html          # Interface web principale
├── static/
│   ├── js/
│   │   └── app.js          # JavaScript de l'application
│   └── maps/               # Cartes HTML générées
├── src/
│   └── app_web.py          # Serveur Flask
└── run_web.py              # Script de lancement
```

## 🌐 API Endpoints

L'application expose plusieurs endpoints API :

- `GET /api/crises?actuelles=true` - Liste des crises (optionnel: seulement actuelles)
- `GET /api/besoins` - Besoins par type de crise
- `GET /api/statistiques` - Statistiques globales (inclut crises actuelles vs passées)
- `POST /api/allocation` - Calcul d'allocation (seulement crises actuelles par défaut)
- `GET /api/carte` - Génération de carte
- `GET /api/pays` - Recherche de pays
- `GET /api/types-risques` - Types de risques disponibles
- `POST /api/prediction` - Calcul de prédiction avec probabilité

## ⚠️ Comportement de l'Allocation

Par défaut, l'API `/api/allocation` ne considère que les crises actuelles (`en_cours=True`).
Pour inclure toutes les crises, passez `seulement_actuelles: false` dans le body de la requête.

## 📝 Notes

- Le serveur écoute sur le port **8080** par défaut
- Mode debug activé pour le développement
- Les cartes sont générées dans `maps/` et copiées dans `static/maps/`
- Toutes les fonctionnalités de l'interface console sont disponibles via l'interface web
- L'allocation est automatiquement filtrée pour ne considérer que les crises actuelles

## 🐛 Dépannage

**Erreur : Port déjà utilisé**
- Changez le port dans `run_web.py` ou `src/app_web.py`

**Erreur : Module non trouvé**
- Vérifiez que Flask est installé : `pip install flask`

**Carte ne s'affiche pas**
- Vérifiez que le dossier `static/maps/` existe
- Vérifiez les permissions d'écriture

**Aucune crise actuelle trouvée**
- Vérifiez que certaines crises ont `en_cours=True` dans le CSV
- Le système affichera un message d'avertissement

---

**Bon projet ! 🎓**

