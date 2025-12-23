#!/usr/bin/env python3
"""
Script principal pour normaliser toutes les données JSON vers CSV
Exécute tous les scripts de normalisation dans le bon ordre
"""

import sys
from pathlib import Path

# Ajouter le dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent))

from normalize_acteurs import normalize_acteurs
from normalize_organes import normalize_organes
from normalize_mandats import normalize_mandats
from normalize_amendements import normalize_amendements


def main():
    """Exécute la normalisation complète de toutes les données"""
    base_dir = Path(__file__).parent.parent
    
    print("="*70)
    print("NORMALISATION DES DONNÉES PARLEMENTAIRES - LÉGISLATURE 17")
    print("="*70)
    print()
    
    # 1. Acteurs (députés)
    print("\n[1/4] Normalisation des acteurs (députés)...")
    print("-" * 70)
    acteurs_input = base_dir / "Députés et organes.json" / "acteur"
    acteurs_output = base_dir / "data" / "csv" / "acteurs.csv"
    normalize_acteurs(str(acteurs_input), str(acteurs_output))
    
    # 2. Organes (groupes politiques, commissions)
    print("\n[2/4] Normalisation des organes (groupes, commissions)...")
    print("-" * 70)
    organes_input = base_dir / "Députés et organes.json" / "organe"
    organes_output = base_dir / "data" / "csv" / "organes.csv"
    normalize_organes(str(organes_input), str(organes_output))
    
    # 3. Mandats (relations acteur-organe)
    print("\n[3/4] Normalisation des mandats (relations)...")
    print("-" * 70)
    mandats_input = base_dir / "Députés et organes.json" / "mandat"
    mandats_output = base_dir / "data" / "csv" / "mandats.csv"
    normalize_mandats(str(mandats_input), str(mandats_output))
    
    # 4. Amendements
    print("\n[4/4] Normalisation des amendements...")
    print("-" * 70)
    print("⚠️  Cette étape peut prendre plusieurs minutes...")
    amendements_input = base_dir / "Amendements"
    amendements_output = base_dir / "data" / "csv" / "amendements.csv"
    
    # Pour un test rapide, décommenter:
    # normalize_amendements(str(amendements_input), str(amendements_output), limit=5000)
    
    # Pour traiter tous les amendements:
    normalize_amendements(str(amendements_input), str(amendements_output))
    
    print("\n" + "="*70)
    print("✓ NORMALISATION TERMINÉE")
    print("="*70)
    print(f"\nFichiers CSV générés dans: {base_dir / 'data' / 'csv'}")
    print("\nFichiers créés:")
    print("  - acteurs.csv      : Députés et leurs informations personnelles")
    print("  - organes.csv      : Groupes politiques, commissions, délégations")
    print("  - mandats.csv      : Relations acteur ↔ organe (qui, où, quand)")
    print("  - amendements.csv  : Amendements avec métadonnées et sort")
    print("\nPrêt pour l'analyse statistique !")
    print()


if __name__ == '__main__':
    main()
