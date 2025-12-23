#!/usr/bin/env python3
"""
Calcul de statistiques par groupe politique
Agrège les amendements par groupe et calcule des métriques collectives
"""

import pandas as pd
from pathlib import Path


def compute_groupe_stats(amendements_csv: str, organes_csv: str, output_csv: str):
    """
    Calcule les statistiques d'activité par groupe politique
    
    Métriques calculées:
    - Nombre de députés actifs (ayant déposé au moins 1 amendement)
    - Nombre total d'amendements déposés par le groupe
    - Nombre d'amendements adoptés
    - Nombre d'amendements rejetés
    - Taux d'adoption moyen du groupe (%)
    - Taux de rejet moyen (%)
    - Moyenne d'amendements par député du groupe
    """
    print("Chargement des données...")
    
    amendements = pd.read_csv(amendements_csv)
    organes = pd.read_csv(organes_csv)
    
    print(f"  - {len(amendements)} amendements")
    print(f"  - {len(organes)} organes")
    
    # Filtrer les amendements par des députés avec groupe politique
    amendements_groupes = amendements[
        (amendements['auteur_type'] == 'Député') & 
        (amendements['auteur_groupe_politique_uid'].notna()) &
        (amendements['auteur_groupe_politique_uid'] != '')
    ].copy()
    
    print(f"\nCalcul des statistiques pour {amendements_groupes['auteur_groupe_politique_uid'].nunique()} groupes politiques...")
    
    stats_list = []
    
    for groupe_uid, group in amendements_groupes.groupby('auteur_groupe_politique_uid'):
        # Nombre de députés différents dans ce groupe
        nb_deputes_actifs = group['auteur_acteur_uid'].nunique()
        
        # Comptages
        total = len(group)
        adoptes = len(group[group['sort'].str.contains('Adopt|adopt', na=False, case=False)])
        rejetes = len(group[group['sort'].str.contains('Rejet|rejet', na=False, case=False)])
        retires = len(group[group['sort'].str.contains('Retir|retir', na=False, case=False)])
        irrecevables = len(group[group['etat_code'].str.contains('IRR', na=False)])
        
        # Taux
        taux_adoption = (adoptes / total * 100) if total > 0 else 0
        taux_rejet = (rejetes / total * 100) if total > 0 else 0
        taux_irrecevable = (irrecevables / total * 100) if total > 0 else 0
        
        # Moyenne par député
        moyenne_par_depute = total / nb_deputes_actifs if nb_deputes_actifs > 0 else 0
        
        # Moyenne de cosignataires
        moyenne_cosignataires = group['nb_cosignataires'].mean()
        
        stats_list.append({
            'groupe_politique_uid': groupe_uid,
            'nb_deputes_actifs': nb_deputes_actifs,
            'nb_amendements_total': total,
            'nb_amendements_adoptes': adoptes,
            'nb_amendements_rejetes': rejetes,
            'nb_amendements_retires': retires,
            'nb_amendements_irrecevables': irrecevables,
            'taux_adoption_pct': round(taux_adoption, 2),
            'taux_rejet_pct': round(taux_rejet, 2),
            'taux_irrecevable_pct': round(taux_irrecevable, 2),
            'moyenne_amendements_par_depute': round(moyenne_par_depute, 2),
            'moyenne_cosignataires': round(moyenne_cosignataires, 2)
        })
    
    # Créer DataFrame
    stats_df = pd.DataFrame(stats_list)
    
    # Joindre avec les infos organes
    stats_df = stats_df.merge(
        organes[['organe_uid', 'libelle', 'libelle_abrege']],
        left_on='groupe_politique_uid',
        right_on='organe_uid',
        how='left'
    )
    
    # Réorganiser les colonnes
    cols = ['groupe_politique_uid', 'libelle', 'libelle_abrege', 'nb_deputes_actifs',
            'nb_amendements_total', 'nb_amendements_adoptes', 'nb_amendements_rejetes',
            'nb_amendements_retires', 'nb_amendements_irrecevables',
            'taux_adoption_pct', 'taux_rejet_pct', 'taux_irrecevable_pct',
            'moyenne_amendements_par_depute', 'moyenne_cosignataires']
    
    stats_df = stats_df[cols]
    
    # Trier par nombre d'amendements
    stats_df = stats_df.sort_values('nb_amendements_total', ascending=False)
    
    # Sauvegarder
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n✓ Statistiques de {len(stats_df)} groupes politiques exportées vers {output_csv}")
    
    # Afficher aperçu
    print("\n" + "="*70)
    print("APERÇU DES STATISTIQUES PAR GROUPE POLITIQUE")
    print("="*70)
    print(f"Nombre de groupes politiques actifs: {len(stats_df)}")
    print(f"Nombre total d'amendements: {stats_df['nb_amendements_total'].sum()}")
    print(f"\nClassement des groupes par activité:")
    print(stats_df[['libelle_abrege', 'nb_deputes_actifs', 'nb_amendements_total', 
                     'moyenne_amendements_par_depute', 'taux_adoption_pct']].to_string(index=False))


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    
    amendements_csv = base_dir / "data" / "csv" / "amendements.csv"
    organes_csv = base_dir / "data" / "csv" / "organes.csv"
    output_csv = base_dir / "data" / "stats" / "stats_par_groupe.csv"
    
    compute_groupe_stats(
        str(amendements_csv),
        str(organes_csv),
        str(output_csv)
    )
