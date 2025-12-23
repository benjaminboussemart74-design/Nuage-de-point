#!/usr/bin/env python3
"""
Normalisation des fichiers mandats JSON vers CSV
Établit les relations entre acteurs et organes (qui fait partie de quoi, quand)
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any


def extract_mandat_data(json_file: Path) -> Dict[str, Any]:
    """Extrait les données pertinentes d'un fichier mandat JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mandat = data.get('mandat', {})
    infos_qualite = mandat.get('infosQualite', {})
    organes = mandat.get('organes', {})
    
    # Gérer organeRef qui peut être une chaîne ou une liste
    organe_ref = organes.get('organeRef', '')
    if isinstance(organe_ref, list):
        organe_ref = organe_ref[0] if organe_ref else ''
    
    return {
        'mandat_uid': mandat.get('uid', ''),
        'acteur_uid': mandat.get('acteurRef', ''),
        'legislature': mandat.get('legislature', ''),
        'type_organe': mandat.get('typeOrgane', ''),
        'date_debut': mandat.get('dateDebut', ''),
        'date_fin': mandat.get('dateFin', ''),
        'date_publication': mandat.get('datePublication', ''),
        'preseance': mandat.get('preseance', ''),
        'nomin_principale': mandat.get('nominPrincipale', ''),
        'code_qualite': infos_qualite.get('codeQualite', ''),
        'lib_qualite': infos_qualite.get('libQualite', ''),
        'lib_qualite_sex': infos_qualite.get('libQualiteSex', ''),
        'organe_uid': organe_ref
    }


def normalize_mandats(input_dir: str, output_csv: str):
    """Normalise tous les fichiers mandats vers un CSV"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Erreur: le dossier {input_dir} n'existe pas")
        return
    
    mandats = []
    json_files = list(input_path.glob('*.json'))
    
    print(f"Traitement de {len(json_files)} fichiers mandats...")
    
    for i, json_file in enumerate(json_files, 1):
        try:
            mandat_data = extract_mandat_data(json_file)
            mandats.append(mandat_data)
            
            if i % 500 == 0:
                print(f"  Traité {i}/{len(json_files)} fichiers...")
        except Exception as e:
            print(f"Erreur avec {json_file.name}: {e}")
    
    # Écrire le CSV
    if mandats:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = mandats[0].keys()
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mandats)
        
        print(f"\n✓ {len(mandats)} mandats exportés vers {output_csv}")
    else:
        print("Aucun mandat trouvé")


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "Députés et organes.json" / "mandat"
    output_csv = base_dir / "data" / "csv" / "mandats.csv"
    
    normalize_mandats(str(input_dir), str(output_csv))
