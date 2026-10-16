"""
Extrait les contours des bureaux de vote de Rennes Métropole
à partir du fichier national publié sur data.gouv.fr.

Source : « Proposition de contours des bureaux de vote » (Etalab / INSEE, REU)
https://www.data.gouv.fr/datasets/proposition-de-contours-des-bureaux-de-vote/

Utilisation :
    python scripts/extraire_contours_rennes.py chemin/vers/contours-france.geojson
"""

import csv
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FICHIER_COMMUNES = RACINE / "data" / "brut" / "communes_rennes_metropole.csv"
FICHIER_SORTIE = RACINE / "data" / "geo" / "bureaux_vote_rennes_metropole.geojson"


def lire_codes_communes():
    """Renvoie l'ensemble des codes INSEE des 43 communes de la métropole."""
    with open(FICHIER_COMMUNES, encoding="utf-8") as f:
        return {ligne["code_insee"] for ligne in csv.DictReader(f, delimiter=";")}


def main(fichier_national):
    codes = lire_codes_communes()

    with open(fichier_national, encoding="utf-8") as f:
        france = json.load(f)

    bureaux = [
        feature
        for feature in france["features"]
        if feature["properties"]["codeCommune"] in codes
    ]

    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": bureaux}, f, ensure_ascii=False)

    communes_trouvees = {b["properties"]["codeCommune"] for b in bureaux}
    print(f"{len(bureaux)} bureaux de vote extraits pour {len(communes_trouvees)} communes")
    for code in sorted(codes - communes_trouvees):
        print(f"Commune absente du fichier national : {code}")
    print(f"Fichier écrit : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main(sys.argv[1])
