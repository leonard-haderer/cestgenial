"""
Script principal du projet CGénial - Allocation de ressources en cas de crise
Auteur: Projet CGénial 2025

Ce script lance l'interface de menu interactif permettant de:
- Charger et visualiser les données de crises
- Allouer des ressources selon un algorithme glouton (crises actuelles uniquement)
- Visualiser les crises sur une carte interactive
- Faire des prédictions sur de nouvelles crises
"""

import sys
from pathlib import Path

# Ajoute le dossier src au chemin Python pour permettre les imports
dossier_projet = Path(__file__).parent
sys.path.insert(0, str(dossier_projet))

from src.menu_interactif import menu_principal


def main():
    """
    Fonction principale qui lance l'application
    """
    print("\n" + "="*70)
    print(" " * 10 + "PROJET CGÉNIAL - ALLOCATION DE RESSOURCES EN CAS DE CRISE")
    print(" " * 20 + "Système Intelligent de Gestion Humanitaire")
    print("="*70)
    print("\n⚠ IMPORTANT: L'allocation ne considère que les crises actuelles (en_cours=True)")
    print("   Les crises passées sont exclues de l'allocation des ressources.")
    print("\nChargement de l'application...")
    
    try:
        # Lance le menu interactif
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur. Au revoir!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


