#!/usr/bin/env python3
"""
Applique la table de correspondance manuelle des groupes politiques
et enrichit les statistiques avec les vrais noms
"""

import pandas as pd
from pathlib import Path


def apply_manual_mapping(stats_csv: str, mapping_csv: str, output_csv: str):
    """
    Applique la correspondance manuelle et crée les stats enrichies
    """
    print("Chargement des données...")
    stats = pd.read_csv(stats_csv)
    mapping = pd.read_csv(mapping_csv, comment='#')
    
    print(f"  - {len(stats)} groupes dans les stats")
    print(f"  - {len(mapping)} correspondances manuelles")
    
    # Joindre avec le mapping
    stats_enrichi = stats.merge(
        mapping,
        left_on='groupe_politique_uid',
        right_on='code_po',
        how='left'
    )
    
    # Réorganiser les colonnes
    cols = ['groupe_politique_uid', 'nom_complet', 'abreviation', 'famille_politique',
            'nb_deputes_actifs', 'nb_amendements_total', 
            'nb_amendements_adoptes', 'nb_amendements_rejetes',
            'nb_amendements_retires', 'nb_amendements_irrecevables',
            'taux_adoption_pct', 'taux_rejet_pct', 'taux_irrecevable_pct',
            'moyenne_amendements_par_depute', 'moyenne_cosignataires']
    
    stats_enrichi = stats_enrichi[cols]
    
    # Trier par nombre d'amendements
    stats_enrichi = stats_enrichi.sort_values('nb_amendements_total', ascending=False)
    
    # Sauvegarder
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats_enrichi.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n✓ Statistiques enrichies exportées vers {output_csv}")
    
    # Afficher le résultat
    print("\n" + "="*100)
    print("STATISTIQUES PAR GROUPE POLITIQUE - LÉGISLATURE 17")
    print("="*100)
    print(stats_enrichi[['abreviation', 'nom_complet', 'nb_deputes_actifs', 
                          'nb_amendements_total', 'taux_adoption_pct',
                          'moyenne_amendements_par_depute']].to_string(index=False))
    
    # Statistiques par famille politique
    print("\n" + "="*100)
    print("AGRÉGATION PAR FAMILLE POLITIQUE")
    print("="*100)
    
    famille_stats = stats_enrichi.groupby('famille_politique').agg({
        'nb_deputes_actifs': 'sum',
        'nb_amendements_total': 'sum',
        'nb_amendements_adoptes': 'sum',
        'taux_adoption_pct': 'mean',
        'moyenne_amendements_par_depute': 'mean'
    }).round(2)
    
    print(famille_stats.to_string())


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    
    stats_csv = base_dir / "data" / "stats" / "stats_par_groupe.csv"
    mapping_csv = base_dir / "data" / "groupes_politiques_l17_manuel.csv"
    output_csv = base_dir / "data" / "stats" / "stats_par_groupe_avec_noms.csv"
    
    apply_manual_mapping(str(stats_csv), str(mapping_csv), str(output_csv))
    
    print("\n" + "="*100)
    print("✓ CORRESPONDANCE APPLIQUÉE")
    print("="*100)
    print(f"\nFichier généré: {output_csv}")
    print("Ce fichier contient les statistiques par groupe avec les noms complets et les familles politiques.")
