#!/usr/bin/env python3
"""
Crée une table de correspondance entre les codes organes (PO) et les noms des groupes politiques
"""

import pandas as pd
from pathlib import Path


def create_groupe_mapping(organes_csv: str, output_csv: str):
    """
    Crée une table de correspondance PO code → nom du groupe politique
    Filtre uniquement les groupes politiques de la 17ème législature
    """
    print("Chargement des organes...")
    organes = pd.read_csv(organes_csv)
    
    print(f"  - {len(organes)} organes au total")
    
    # Filtrer les groupes politiques (code_type commence souvent par GP ou GROUPES)
    # et ceux de la 17ème législature
    groupes = organes[
        (organes['legislature'] == '17') | 
        (organes['code_type'].str.contains('GP|ASSEMBLEE', na=False, case=False))
    ].copy()
    
    # Sélectionner les colonnes pertinentes
    mapping = groupes[['organe_uid', 'code_type', 'libelle', 'libelle_abrege', 
                       'legislature', 'date_debut', 'date_fin']].copy()
    
    # Trier par date de début (les plus récents en premier)
    mapping = mapping.sort_values('date_debut', ascending=False)
    
    # Supprimer les doublons (garder le plus récent)
    mapping = mapping.drop_duplicates(subset=['organe_uid'], keep='first')
    
    # Sauvegarder
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n✓ {len(mapping)} groupes/organes exportés vers {output_csv}")
    
    # Afficher les groupes politiques principaux
    print("\n" + "="*70)
    print("GROUPES POLITIQUES - LÉGISLATURE 17")
    print("="*70)
    
    # Filtrer ceux de la législature 17
    groupes_l17 = mapping[mapping['legislature'] == '17'].copy()
    
    if len(groupes_l17) > 0:
        print(f"\nGroupes de la 17ème législature ({len(groupes_l17)}):")
        print(groupes_l17[['organe_uid', 'libelle_abrege', 'libelle']].to_string(index=False))
    
    # Afficher aussi les autres organes qui pourraient être des groupes
    autres = mapping[mapping['legislature'] != '17'].copy()
    if len(autres) > 0:
        print(f"\n\nAutres organes/groupes ({len(autres)}):")
        print(autres[['organe_uid', 'code_type', 'libelle_abrege', 'libelle']].head(20).to_string(index=False))


def create_enhanced_groupe_mapping(organes_csv: str, stats_groupe_csv: str, output_csv: str):
    """
    Crée une table enrichie en joignant les stats avec les noms des groupes
    """
    print("\nCréation de la table enrichie stats + noms des groupes...")
    
    organes = pd.read_csv(organes_csv)
    stats = pd.read_csv(stats_groupe_csv)
    
    # Joindre stats avec organes pour avoir les noms
    stats_enrichi = stats.merge(
        organes[['organe_uid', 'code_type', 'libelle', 'libelle_abrege', 'legislature']],
        left_on='groupe_politique_uid',
        right_on='organe_uid',
        how='left',
        suffixes=('', '_organes')
    )
    
    # Utiliser les infos d'organes si libelle est vide dans stats
    stats_enrichi['libelle_final'] = stats_enrichi['libelle'].combine_first(stats_enrichi['libelle_organes'])
    stats_enrichi['libelle_abrege_final'] = stats_enrichi['libelle_abrege'].combine_first(stats_enrichi['libelle_abrege_organes'])
    
    # Sélectionner et réorganiser les colonnes
    cols = ['groupe_politique_uid', 'libelle_final', 'libelle_abrege_final', 'code_type', 'legislature',
            'nb_deputes_actifs', 'nb_amendements_total', 'nb_amendements_adoptes', 
            'nb_amendements_rejetes', 'nb_amendements_retires', 'nb_amendements_irrecevables',
            'taux_adoption_pct', 'taux_rejet_pct', 'taux_irrecevable_pct',
            'moyenne_amendements_par_depute', 'moyenne_cosignataires']
    
    stats_enrichi = stats_enrichi[cols]
    stats_enrichi = stats_enrichi.rename(columns={
        'libelle_final': 'libelle',
        'libelle_abrege_final': 'libelle_abrege'
    })
    
    # Trier par nombre d'amendements
    stats_enrichi = stats_enrichi.sort_values('nb_amendements_total', ascending=False)
    
    # Sauvegarder
    output_path = Path(output_csv)
    stats_enrichi.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"✓ Table enrichie exportée vers {output_csv}")
    
    # Afficher le résultat
    print("\n" + "="*70)
    print("STATS PAR GROUPE AVEC NOMS COMPLETS")
    print("="*70)
    print(stats_enrichi[['groupe_politique_uid', 'libelle_abrege', 'libelle', 
                          'nb_deputes_actifs', 'nb_amendements_total', 
                          'taux_adoption_pct']].to_string(index=False, max_colwidth=50))


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    
    organes_csv = base_dir / "data" / "csv" / "organes.csv"
    stats_groupe_csv = base_dir / "data" / "stats" / "stats_par_groupe.csv"
    
    # Table de correspondance simple
    mapping_output = base_dir / "data" / "csv" / "groupes_politiques_mapping.csv"
    create_groupe_mapping(str(organes_csv), str(mapping_output))
    
    # Table enrichie (stats + noms)
    stats_enrichi_output = base_dir / "data" / "stats" / "stats_par_groupe_enrichi.csv"
    create_enhanced_groupe_mapping(str(organes_csv), str(stats_groupe_csv), str(stats_enrichi_output))
    
    print("\n" + "="*70)
    print("✓ TABLES DE CORRESPONDANCE CRÉÉES")
    print("="*70)
    print(f"\nFichiers générés:")
    print(f"  1. {mapping_output}")
    print(f"     → Table complète: PO code → nom du groupe")
    print(f"  2. {stats_enrichi_output}")
    print(f"     → Stats par groupe avec noms lisibles")
