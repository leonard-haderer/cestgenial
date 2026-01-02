"""
Script pour lancer le serveur web Flask
Auteur: Projet CGénial 2025
"""

import sys
from pathlib import Path

# Ajoute le dossier src au chemin Python
dossier_projet = Path(__file__).parent
sys.path.insert(0, str(dossier_projet))

from src.app_web import app

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" " * 15 + "PROJET CGÉNIAL - SERVEUR WEB")
    print("="*70)
    print("\n🌐 Serveur démarré sur http://localhost:8080")
    print("📊 Interface web disponible")
    print("⚠ L'allocation ne considère que les crises actuelles (en_cours=True)")
    print("\nAppuyez sur Ctrl+C pour arrêter le serveur\n")
    
    app.run(host='0.0.0.0', port=8080, debug=True)


