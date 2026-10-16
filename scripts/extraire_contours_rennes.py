"""
Construit les contours des bureaux de vote de Rennes Métropole en combinant deux sources.

1. Ville de Rennes : couche officielle du SIG de Rennes Métropole (découpage en vigueur).
   https://public.sig.rennesmetropole.fr/geoserver (couche eq_educ:v_election_perim_bureau)
2. Les 42 autres communes : « Proposition de contours des bureaux de vote » (Etalab / INSEE, REU).
   https://www.data.gouv.fr/datasets/proposition-de-contours-des-bureaux-de-vote/
   Ces contours sont calculés à partir des adresses des électeurs : ils sont approximatifs.

Utilisation :
    python scripts/extraire_contours_rennes.py chemin/vers/contours-france.geojson
"""

import csv
import json
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FICHIER_COMMUNES = RACINE / "data" / "brut" / "communes_rennes_metropole.csv"
FICHIER_SORTIE = RACINE / "data" / "geo" / "bureaux_vote_rennes_metropole.geojson"

CODE_RENNES = "35238"
URL_SIG_RENNES = (
    "https://public.sig.rennesmetropole.fr/geoserver/ows?service=WFS&version=2.0.0"
    "&request=GetFeature&typeNames=eq_educ:v_election_perim_bureau"
    "&outputFormat=application/json&srsName=EPSG:4326"
)


def lire_communes():
    """Renvoie un dictionnaire {code INSEE: nom} des 43 communes de la métropole."""
    with open(FICHIER_COMMUNES, encoding="utf-8") as f:
        return {ligne["code_insee"]: ligne["nom"] for ligne in csv.DictReader(f, delimiter=";")}


def bureau(code_commune, nom_commune, numero, geometrie, source, nb_electeurs=None):
    """Fabrique un bureau de vote avec les mêmes propriétés quelle que soit la source."""
    numero = str(numero).zfill(4)
    return {
        "type": "Feature",
        "properties": {
            "codeCommune": code_commune,
            "nomCommune": nom_commune,
            "numeroBureauVote": numero,
            "codeBureauVote": f"{code_commune}_{numero}",
            "nbElecteurs": nb_electeurs,
            "source": source,
        },
        "geometry": geometrie,
    }


def bureaux_rennes():
    """Télécharge les périmètres officiels des bureaux de la ville de Rennes."""
    with urllib.request.urlopen(URL_SIG_RENNES, timeout=120) as reponse:
        couche = json.load(reponse)
    return [
        bureau(CODE_RENNES, "Rennes", f["properties"]["num_bureau"], f["geometry"],
               "SIG Rennes Métropole", f["properties"]["nb_elec"])
        for f in couche["features"]
    ]


def bureaux_autres_communes(fichier_national, communes):
    """Extrait du fichier national les bureaux des communes de la métropole, hors Rennes."""
    with open(fichier_national, encoding="utf-8") as f:
        france = json.load(f)
    return [
        bureau(p["codeCommune"], communes[p["codeCommune"]], p["numeroBureauVote"],
               f["geometry"], "Etalab (REU)")
        for f in france["features"]
        if (p := f["properties"])["codeCommune"] in communes and p["codeCommune"] != CODE_RENNES
    ]


def main(fichier_national):
    communes = lire_communes()
    rennes = bureaux_rennes()
    autres = bureaux_autres_communes(fichier_national, communes)
    bureaux = sorted(rennes + autres, key=lambda b: b["properties"]["codeBureauVote"])

    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": bureaux}, f, ensure_ascii=False)

    communes_trouvees = {b["properties"]["codeCommune"] for b in bureaux}
    print(f"Rennes : {len(rennes)} bureaux (SIG Rennes Métropole)")
    print(f"Autres communes : {len(autres)} bureaux (Etalab)")
    print(f"Total : {len(bureaux)} bureaux pour {len(communes_trouvees)} communes")
    for code in sorted(set(communes) - communes_trouvees):
        print(f"Commune absente : {code}")
    print(f"Fichier écrit : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main(sys.argv[1])
