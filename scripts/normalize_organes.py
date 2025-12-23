#!/usr/bin/env python3
"""
Normalisation des fichiers organes JSON vers CSV
Extrait les groupes politiques, commissions, délégations, etc.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any


def extract_organe_data(json_file: Path) -> Dict[str, Any]:
    """Extrait les données pertinentes d'un fichier organe JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    organe = data.get('organe', {})
    
    uid = organe.get('uid', '')
    vim_ode = organe.get('viMoDe', {})
    
    return {
        'organe_uid': uid,
        'code_type': organe.get('codeType', ''),
        'libelle': organe.get('libelle', ''),
        'libelle_edition': organe.get('libelleEdition', ''),
        'libelle_abrege': organe.get('libelleAbrege', ''),
        'libelle_abrev': organe.get('libelleAbrev', ''),
        'date_debut': vim_ode.get('dateDebut', ''),
        'date_fin': vim_ode.get('dateFin', ''),
        'date_agrement': vim_ode.get('dateAgrement', ''),
        'organe_parent': organe.get('organeParent', ''),
        'chambre': organe.get('chambre', ''),
        'regime': organe.get('regime', ''),
        'legislature': organe.get('legislature', ''),
        'regime_juridique': organe.get('regimeJuridique', ''),
        'site_internet': organe.get('siteInternet', ''),
        'nombre_reunions_annuelles': organe.get('nombreReunionsAnnuelles', '')
    }


def normalize_organes(input_dir: str, output_csv: str):
    """Normalise tous les fichiers organes vers un CSV"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Erreur: le dossier {input_dir} n'existe pas")
        return
    
    organes = []
    json_files = list(input_path.glob('*.json'))
    
    print(f"Traitement de {len(json_files)} fichiers organes...")
    
    for i, json_file in enumerate(json_files, 1):
        try:
            organe_data = extract_organe_data(json_file)
            organes.append(organe_data)
            
            if i % 100 == 0:
                print(f"  Traité {i}/{len(json_files)} fichiers...")
        except Exception as e:
            print(f"Erreur avec {json_file.name}: {e}")
    
    # Écrire le CSV
    if organes:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = organes[0].keys()
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(organes)
        
        print(f"\n✓ {len(organes)} organes exportés vers {output_csv}")
    else:
        print("Aucun organe trouvé")


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "Députés et organes.json" / "organe"
    output_csv = base_dir / "data" / "csv" / "organes.csv"
    
    normalize_organes(str(input_dir), str(output_csv))
