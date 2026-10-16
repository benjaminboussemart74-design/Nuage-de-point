"""
Étape 4 : produire la page web de la typologie (carte, nuage de points, profils).

Le gabarit gabarit_carte.html contient la mise en page ; ce script y insère les données :
- les contours simplifiés et projetés en coordonnées d'écran (SVG) ;
- les résultats et indicateurs de chaque unité ;
- le profil moyen de chaque type.

Sortie : data/typologie/carte_typologie.html
"""

import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from commun import DOSSIER_TYPOLOGIE, LAMBERT93, TELECHARGEMENTS

GABARIT = Path(__file__).with_name("gabarit_carte.html")
LARGEUR_SVG = 1000
TOLERANCE_SIMPLIFICATION = 12  # mètres

# Noms et portraits des types, rédigés à partir de profils_types.csv
TYPES = {
    1: ("Centres urbains de la gauche diplômée",
        "Quartiers d'immeubles du centre et des faubourgs de Rennes, peuplés de cadres et de "
        "jeunes actifs diplômés vivant souvent seuls. Le vote socialiste et écologiste y est "
        "le plus élevé de la métropole, la France insoumise y dépasse 17 %."),
    2: ("Centre bourgeois et étudiant",
        "Cœur historique et quartiers étudiants de Rennes : la plus forte part de diplômés "
        "de niveau bac+5 et d'étudiants. La gauche y reste en tête, mais la droite "
        "(Bellamy, Maréchal) y obtient ses meilleurs scores urbains."),
    3: ("Couronne aisée du bloc central",
        "Communes et quartiers pavillonnaires les plus aisés, à Cesson-Sévigné et Saint-Grégoire "
        "surtout. Propriétaires et retraités y sont nombreux, la participation y est la plus "
        "forte. La liste de Valérie Hayer y arrive en tête, Les Républicains y dépassent 13 %."),
    4: ("Quartiers populaires mixtes",
        "Quartiers rennais et de Saint-Jacques-de-la-Lande mêlant logement social et copropriétés, "
        "aux revenus inférieurs à la moyenne. La gauche y domine nettement, avec un vote insoumis "
        "élevé, et l'abstention y dépasse la moyenne métropolitaine."),
    5: ("Bourgs résidentiels des classes moyennes",
        "Communes de la première couronne, propriétaires et familles de classes moyennes, très peu "
        "de pauvreté. Le vote se partage entre la gauche socialiste et le bloc central, "
        "le Rassemblement national y obtient un score proche de la moyenne."),
    6: ("Grands ensembles en retrait des urnes",
        "Grands ensembles rennais, au Blosne et à Maurepas notamment : près des deux tiers "
        "des logements sont sociaux, un ménage sur trois vit sous le seuil de pauvreté. "
        "L'abstention y atteint 59 %, la France insoumise y est la première force."),
    7: ("Périurbain populaire, premier vote RN",
        "Communes périurbaines de la deuxième couronne, ouvriers, employés et professions "
        "intermédiaires propriétaires de leur maison. C'est le seul type où la liste de "
        "Jordan Bardella arrive en tête, devant celle de Raphaël Glucksmann."),
}


def chemin_svg(geometrie, transformer):
    """Convertit un polygone en commande de tracé SVG (« d »)."""
    polygones = geometrie.geoms if geometrie.geom_type == "MultiPolygon" else [geometrie]
    morceaux = []
    for polygone in polygones:
        for anneau in [polygone.exterior, *polygone.interiors]:
            points = [transformer(x, y) for x, y in anneau.coords]
            morceaux.append("M" + "L".join(f"{px:.1f},{py:.1f}" for px, py in points) + "Z")
    return "".join(morceaux)


def lieux_de_vote():
    """Associe chaque bureau (« 35238_0111 ») au bâtiment où l'on vote."""
    centres = json.load(open(TELECHARGEMENTS / "rm_centres.geojson", encoding="utf-8"))["features"]
    lieux = {}
    for centre in centres:
        p = centre["properties"]
        batiment = (p["loc_bat"] or p["c_nom"]).strip()
        for numero in re.findall(r"\d+", p["burx_liste"] or ""):
            lieux[f"{p['code_insee']}_{int(numero):04d}"] = batiment
    return lieux


def main():
    unites = gpd.read_file(DOSSIER_TYPOLOGIE / "typologie.geojson").to_crs(LAMBERT93)
    profils = pd.read_csv(DOSSIER_TYPOLOGIE / "profils_types.csv", index_col=0)
    lieux = lieux_de_vote()

    minx, miny, maxx, maxy = unites.total_bounds
    echelle = LARGEUR_SVG / (maxx - minx)
    hauteur = (maxy - miny) * echelle

    def transformer(x, y):
        return (x - minx) * echelle, (maxy - y) * echelle

    def cadre(formes):
        x0, y0, x1, y1 = formes.total_bounds
        return [round((x0 - minx) * echelle, 1), round((maxy - y1) * echelle, 1),
                round((x1 - x0) * echelle, 1), round((y1 - y0) * echelle, 1)]

    simplifiees = unites.geometry.simplify(TOLERANCE_SIMPLIFICATION, preserve_topology=True)
    communes = unites.dissolve(by="code_commune").geometry.simplify(TOLERANCE_SIMPLIFICATION)

    colonnes = ["abstention_euro24", "glucksmann", "hayer", "bardella", "aubry", "toussaint",
                "bellamy", "marechal", "autres_listes", "niveau_vie_moyen", "cadres", "ouvriers",
                "logements_sociaux", "diplomes_bac5", "proprietaires", "axe_1", "axe_2"]
    donnees_unites = []
    for (_, u), forme in zip(unites.iterrows(), simplifiees):
        commune_entiere = u["unite"].endswith("_COMMUNE")
        donnees_unites.append({
            "id": u["unite"],
            "commune": u["commune"],
            "bureau": None if commune_entiere else int(u["unite"][-4:]),
            "lieu": None if commune_entiere else lieux.get(u["unite"]),
            "type": int(u["type"]),
            "inscrits": int(u["inscrits_2024"]),
            "d": chemin_svg(forme, transformer),
            **{c: round(float(u[c]), 2) for c in colonnes},
        })

    donnees = {
        "largeur": LARGEUR_SVG,
        "hauteur": round(hauteur, 1),
        "cadreRennes": cadre(unites[unites["code_commune"] == "35238"]),
        "communes": [chemin_svg(g, transformer) for g in communes],
        "unites": donnees_unites,
        "types": [{"num": t, "nom": nom, "texte": texte} for t, (nom, texte) in TYPES.items()],
        "profils": {str(k): {c: round(float(v), 2) for c, v in ligne.items()}
                    for k, ligne in profils.iterrows()},
    }

    page = GABARIT.read_text(encoding="utf-8").replace(
        "/*DONNEES*/null", json.dumps(donnees, ensure_ascii=False, separators=(",", ":")))
    sortie = DOSSIER_TYPOLOGIE / "carte_typologie.html"
    sortie.write_text(page, encoding="utf-8")
    print(f"Page écrite : {sortie} ({sortie.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
