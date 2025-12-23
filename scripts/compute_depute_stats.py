#!/usr/bin/env python3
"""
Calcul de statistiques par député
Agrège les amendements et calcule des métriques d'activité parlementaire
"""

import pandas as pd
from pathlib import Path
from typing import Dict


def compute_depute_stats(amendements_csv: str, acteurs_csv: str, mandats_csv: str, output_csv: str):
    """
    Calcule les statistiques d'activité par député
    
    Métriques calculées:
    - Nombre total d'amendements déposés (comme auteur)
    - Nombre d'amendements adoptés
    - Nombre d'amendements rejetés
    - Nombre d'amendements retirés
    - Taux d'adoption (%)
    - Taux de rejet (%)
    - Moyenne de cosignataires par amendement
    - Nombre d'amendements soumis à l'article 40
    """
    print("Chargement des données...")
    
    # Charger les CSV
    amendements = pd.read_csv(amendements_csv)
    acteurs = pd.read_csv(acteurs_csv)
    mandats = pd.read_csv(mandats_csv)
    
    print(f"  - {len(amendements)} amendements")
    print(f"  - {len(acteurs)} acteurs")
    print(f"  - {len(mandats)} mandats")
    
    # Filtrer les amendements déposés par des députés (auteur_type = "Député")
    amendements_deputes = amendements[amendements['auteur_type'] == 'Député'].copy()
    
    print(f"\nCalcul des statistiques pour {amendements_deputes['auteur_acteur_uid'].nunique()} députés...")
    
    # Grouper par député auteur
    stats_list = []
    
    for acteur_uid, group in amendements_deputes.groupby('auteur_acteur_uid'):
        # Compter les amendements par sort
        total = len(group)
        
        # Compter par état/sort
        adoptes = len(group[group['sort'].str.contains('Adopt|adopt', na=False, case=False)])
        rejetes = len(group[group['sort'].str.contains('Rejet|rejet', na=False, case=False)])
        retires = len(group[group['sort'].str.contains('Retir|retir', na=False, case=False)])
        irrecevables = len(group[group['etat_code'].str.contains('IRR', na=False)])
        non_soutenus = len(group[group['sort'].str.contains('Non soutenu|non soutenu', na=False, case=False)])
        tombes = len(group[group['sort'].str.contains('Tomb|tomb|Caduque|caduque', na=False, case=False)])
        
        # Calculs dérivés
        taux_adoption = (adoptes / total * 100) if total > 0 else 0
        taux_rejet = (rejetes / total * 100) if total > 0 else 0
        taux_irrecevable = (irrecevables / total * 100) if total > 0 else 0
        
        # Moyenne de cosignataires
        moyenne_cosignataires = group['nb_cosignataires'].mean()
        
        # Article 40
        article40_count = len(group[group['soumis_article40'] == 'true'])
        
        # Récupérer le groupe politique le plus récent du député
        mandats_depute = mandats[mandats['acteur_uid'] == acteur_uid]
        mandats_depute = mandats_depute.sort_values('date_debut', ascending=False)
        groupe_politique_uid = mandats_depute.iloc[0]['organe_uid'] if len(mandats_depute) > 0 else ''
        
        stats_list.append({
            'acteur_uid': acteur_uid,
            'groupe_politique_uid': groupe_politique_uid,
            'nb_amendements_total': total,
            'nb_amendements_adoptes': adoptes,
            'nb_amendements_rejetes': rejetes,
            'nb_amendements_retires': retires,
            'nb_amendements_irrecevables': irrecevables,
            'nb_amendements_non_soutenus': non_soutenus,
            'nb_amendements_tombes': tombes,
            'taux_adoption_pct': round(taux_adoption, 2),
            'taux_rejet_pct': round(taux_rejet, 2),
            'taux_irrecevable_pct': round(taux_irrecevable, 2),
            'moyenne_cosignataires': round(moyenne_cosignataires, 2),
            'nb_amendements_article40': article40_count
        })
    
    # Créer DataFrame des stats
    stats_df = pd.DataFrame(stats_list)
    
    # Joindre avec les infos acteurs (nom, prénom, etc.)
    stats_df = stats_df.merge(
        acteurs[['acteur_uid', 'civilite', 'prenom', 'nom', 'trigramme', 'profession_libelle']],
        on='acteur_uid',
        how='left'
    )
    
    # Réorganiser les colonnes
    cols = ['acteur_uid', 'civilite', 'prenom', 'nom', 'trigramme', 'groupe_politique_uid',
            'nb_amendements_total', 'nb_amendements_adoptes', 'nb_amendements_rejetes',
            'nb_amendements_retires', 'nb_amendements_irrecevables', 
            'nb_amendements_non_soutenus', 'nb_amendements_tombes',
            'taux_adoption_pct', 'taux_rejet_pct', 'taux_irrecevable_pct',
            'moyenne_cosignataires', 'nb_amendements_article40', 'profession_libelle']
    
    stats_df = stats_df[cols]
    
    # Trier par nombre d'amendements décroissant
    stats_df = stats_df.sort_values('nb_amendements_total', ascending=False)
    
    # Sauvegarder
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n✓ Statistiques de {len(stats_df)} députés exportées vers {output_csv}")
    
    # Afficher quelques stats globales
    print("\n" + "="*70)
    print("APERÇU DES STATISTIQUES")
    print("="*70)
    print(f"Nombre de députés ayant déposé au moins 1 amendement: {len(stats_df)}")
    print(f"Nombre total d'amendements analysés: {stats_df['nb_amendements_total'].sum()}")
    print(f"Moyenne d'amendements par député: {stats_df['nb_amendements_total'].mean():.1f}")
    print(f"Médiane d'amendements par député: {stats_df['nb_amendements_total'].median():.0f}")
    print(f"\nTop 10 des députés les plus actifs:")
    print(stats_df[['nom', 'prenom', 'nb_amendements_total', 'taux_adoption_pct']].head(10).to_string(index=False))


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    
    amendements_csv = base_dir / "data" / "csv" / "amendements.csv"
    acteurs_csv = base_dir / "data" / "csv" / "acteurs.csv"
    mandats_csv = base_dir / "data" / "csv" / "mandats.csv"
    output_csv = base_dir / "data" / "stats" / "stats_par_depute.csv"
    
    compute_depute_stats(
        str(amendements_csv),
        str(acteurs_csv),
        str(mandats_csv),
        str(output_csv)
    )
