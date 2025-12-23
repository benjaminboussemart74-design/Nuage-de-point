#!/usr/bin/env python3
"""
Normalisation des fichiers amendements JSON vers CSV
Extrait les amendements avec leur métadonnées principales
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
import os


def extract_amendement_data(json_file: Path) -> Dict[str, Any]:
    """Extrait les données pertinentes d'un fichier amendement JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    amendement = data.get('amendement', {})
    identification = amendement.get('identification', {})
    signataires = amendement.get('signataires', {})
    auteur = signataires.get('auteur', {})
    cycle_de_vie = amendement.get('cycleDeVie', {})
    etat_traitements = cycle_de_vie.get('etatDesTraitements', {})
    etat = etat_traitements.get('etat', {})
    sous_etat = etat_traitements.get('sousEtat', {})
    pointeur = amendement.get('pointeurFragmentTexte', {})
    division = pointeur.get('division', {})
    
    # Extraire les cosignataires
    cosignataires_refs = signataires.get('cosignataires', {}).get('acteurRef', [])
    if not isinstance(cosignataires_refs, list):
        cosignataires_refs = [cosignataires_refs] if cosignataires_refs else []
    
    nb_cosignataires = len(cosignataires_refs)
    
    return {
        'amendement_uid': amendement.get('uid', ''),
        'legislature': amendement.get('legislature', ''),
        'numero_long': identification.get('numeroLong', ''),
        'numero_ordre_depot': identification.get('numeroOrdreDepot', ''),
        'prefixe_organe_examen': identification.get('prefixeOrganeExamen', ''),
        'numero_rect': identification.get('numeroRect', ''),
        'examen_ref': amendement.get('examenRef', ''),
        'texte_legislatif_ref': amendement.get('texteLegislatifRef', ''),
        'auteur_acteur_uid': auteur.get('acteurRef', ''),
        'auteur_type': auteur.get('typeAuteur', ''),
        'auteur_groupe_politique_uid': auteur.get('groupePolitiqueRef', ''),
        'nb_cosignataires': nb_cosignataires,
        'date_depot': cycle_de_vie.get('dateDepot', ''),
        'date_publication': cycle_de_vie.get('datePublication', ''),
        'date_sort': cycle_de_vie.get('dateSort', ''),
        'soumis_article40': cycle_de_vie.get('soumisArticle40', ''),
        'etat_code': etat.get('code', ''),
        'etat_libelle': etat.get('libelle', ''),
        'sous_etat_code': sous_etat.get('code', ''),
        'sous_etat_libelle': sous_etat.get('libelle', ''),
        'sort': cycle_de_vie.get('sort', ''),
        'article_designation': division.get('articleDesignation', ''),
        'article_designation_courte': division.get('articleDesignationCourte', ''),
        'division_titre': division.get('titre', ''),
        'division_type': division.get('type', ''),
        'article_additionnel': division.get('articleAdditionnel', ''),
        'article99': amendement.get('article99', ''),
    }


def normalize_amendements(input_dir: str, output_csv: str, limit: int = None):
    """
    Normalise les fichiers amendements vers un CSV
    
    Args:
        input_dir: Dossier racine Amendements/
        output_csv: Fichier CSV de sortie
        limit: Limite optionnelle du nombre d'amendements à traiter (pour tests)
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Erreur: le dossier {input_dir} n'existe pas")
        return
    
    amendements = []
    
    # Parcourir récursivement tous les fichiers JSON
    json_files = list(input_path.rglob('AMAN*.json'))
    
    if limit:
        json_files = json_files[:limit]
        print(f"Mode TEST: traitement limité à {limit} amendements")
    
    print(f"Traitement de {len(json_files)} fichiers amendements...")
    
    for i, json_file in enumerate(json_files, 1):
        try:
            amendement_data = extract_amendement_data(json_file)
            amendements.append(amendement_data)
            
            if i % 1000 == 0:
                print(f"  Traité {i}/{len(json_files)} fichiers...")
        except Exception as e:
            print(f"Erreur avec {json_file.name}: {e}")
    
    # Écrire le CSV
    if amendements:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = amendements[0].keys()
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(amendements)
        
        print(f"\n✓ {len(amendements)} amendements exportés vers {output_csv}")
    else:
        print("Aucun amendement trouvé")


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "Amendements"
    output_csv = base_dir / "data" / "csv" / "amendements.csv"
    
    # Pour un test rapide, décommentez la ligne suivante:
    # normalize_amendements(str(input_dir), str(output_csv), limit=5000)
    
    # Pour traiter tous les amendements:
    normalize_amendements(str(input_dir), str(output_csv))
