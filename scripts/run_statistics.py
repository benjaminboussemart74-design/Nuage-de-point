#!/usr/bin/env python3
"""
Script principal pour calculer toutes les statistiques
Exécute les analyses par député et par groupe politique
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from compute_depute_stats import compute_depute_stats
from compute_groupe_stats import compute_groupe_stats


def main():
    """Exécute le calcul complet des statistiques"""
    base_dir = Path(__file__).parent.parent
    
    print("="*70)
    print("CALCUL DES STATISTIQUES PARLEMENTAIRES - LÉGISLATURE 17")
    print("="*70)
    print()
    
    # Vérifier que les CSV normalisés existent
    csv_dir = base_dir / "data" / "csv"
    required_files = ['amendements.csv', 'acteurs.csv', 'organes.csv', 'mandats.csv']
    
    for filename in required_files:
        if not (csv_dir / filename).exists():
            print(f"❌ Erreur: {filename} non trouvé dans {csv_dir}")
            print("\nVeuillez d'abord exécuter la normalisation:")
            print("  python scripts/run_normalization.py")
            return
    
    # 1. Statistiques par député
    print("\n[1/2] Calcul des statistiques par député...")
    print("-" * 70)
    compute_depute_stats(
        str(csv_dir / "amendements.csv"),
        str(csv_dir / "acteurs.csv"),
        str(csv_dir / "mandats.csv"),
        str(base_dir / "data" / "stats" / "stats_par_depute.csv")
    )
    
    # 2. Statistiques par groupe politique
    print("\n[2/2] Calcul des statistiques par groupe politique...")
    print("-" * 70)
    compute_groupe_stats(
        str(csv_dir / "amendements.csv"),
        str(csv_dir / "organes.csv"),
        str(base_dir / "data" / "stats" / "stats_par_groupe.csv")
    )
    
    print("\n" + "="*70)
    print("✓ CALCUL DES STATISTIQUES TERMINÉ")
    print("="*70)
    print(f"\nFichiers de statistiques générés dans: {base_dir / 'data' / 'stats'}")
    print("\nFichiers créés:")
    print("  - stats_par_depute.csv : Statistiques individuelles par député")
    print("  - stats_par_groupe.csv : Statistiques agrégées par groupe politique")
    print("\nCes fichiers sont prêts pour l'intégration dans vos algorithmes !")
    print()


if __name__ == '__main__':
    main()
