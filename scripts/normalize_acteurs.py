#!/usr/bin/env python3
"""
Normalisation des fichiers acteurs JSON vers CSV
Extrait les députés avec leurs informations de base
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Any


def extract_acteur_data(json_file: Path) -> Dict[str, Any]:
    """Extrait les données pertinentes d'un fichier acteur JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    acteur = data.get('acteur', {})
    uid = acteur.get('uid', {}).get('#text', '') if isinstance(acteur.get('uid'), dict) else acteur.get('uid', '')
    
    etat_civil = acteur.get('etatCivil', {})
    ident = etat_civil.get('ident', {})
    info_naissance = etat_civil.get('infoNaissance', {})
    
    profession = acteur.get('profession', {})
    
    # Extraire l'adresse email
    email = None
    adresses = acteur.get('adresses', {}).get('adresse', [])
    if not isinstance(adresses, list):
        adresses = [adresses]
    
    for adresse in adresses:
        if adresse.get('typeLibelle') == 'Mèl':
            email = adresse.get('valElec')
            break
    
    return {
        'acteur_uid': uid,
        'civilite': ident.get('civ', ''),
        'prenom': ident.get('prenom', ''),
        'nom': ident.get('nom', ''),
        'nom_alpha': ident.get('alpha', ''),
        'trigramme': ident.get('trigramme', ''),
        'date_naissance': info_naissance.get('dateNais', ''),
        'ville_naissance': info_naissance.get('villeNais', ''),
        'departement_naissance': info_naissance.get('depNais', ''),
        'pays_naissance': info_naissance.get('paysNais', ''),
        'date_deces': etat_civil.get('dateDeces', ''),
        'profession_libelle': profession.get('libelleCourant', ''),
        'email': email or '',
        'uri_hatvp': acteur.get('uri_hatvp', '') or ''
    }


def normalize_acteurs(input_dir: str, output_csv: str):
    """Normalise tous les fichiers acteurs vers un CSV"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Erreur: le dossier {input_dir} n'existe pas")
        return
    
    acteurs = []
    json_files = list(input_path.glob('*.json'))
    
    print(f"Traitement de {len(json_files)} fichiers acteurs...")
    
    for i, json_file in enumerate(json_files, 1):
        try:
            acteur_data = extract_acteur_data(json_file)
            acteurs.append(acteur_data)
            
            if i % 100 == 0:
                print(f"  Traité {i}/{len(json_files)} fichiers...")
        except Exception as e:
            print(f"Erreur avec {json_file.name}: {e}")
    
    # Écrire le CSV
    if acteurs:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = acteurs[0].keys()
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(acteurs)
        
        print(f"\n✓ {len(acteurs)} acteurs exportés vers {output_csv}")
    else:
        print("Aucun acteur trouvé")


if __name__ == '__main__':
    # Chemins relatifs au projet
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "Députés et organes.json" / "acteur"
    output_csv = base_dir / "data" / "csv" / "acteurs.csv"
    
    normalize_acteurs(str(input_dir), str(output_csv))
