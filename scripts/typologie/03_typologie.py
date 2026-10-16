"""
Étape 3 : classer les unités en types homogènes, à la fois électoraux et sociologiques.

Méthode, classique en géographie électorale :
1. Analyse factorielle multiple (AFM). C'est une analyse en composantes principales
   qui équilibre deux groupes de variables : le vote et la sociologie. Sans cet
   équilibrage, le groupe le plus nombreux pèserait davantage dans le résultat.
2. Classification ascendante hiérarchique (CAH, critère de Ward) sur les axes de l'AFM :
   on regroupe pas à pas les unités les plus proches, jusqu'à obtenir k types.
3. Consolidation par les k-moyennes : chaque unité est réaffectée au type
   dont le centre est le plus proche.

Usage : python 03_typologie.py [nombre_de_types]
Sorties (data/typologie/) : typologie_unites.csv, profils_types.csv,
choix_nombre_types.csv, typologie.geojson
"""

import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans

from commun import DOSSIER_TYPOLOGIE

VARIABLES_VOTE = ["abstention_euro24", "abstention_legi24", "blancs_nuls_euro24", "glucksmann",
                  "hayer", "bardella", "aubry", "toussaint", "bellamy", "marechal", "autres_listes"]
VARIABLES_SOCIO = ["niveau_vie_moyen", "menages_pauvres", "proprietaires", "logements_sociaux",
                   "logements_collectifs", "menages_1_personne", "familles_monoparentales",
                   "jeunes_18_24", "seniors_65_plus", "cadres", "professions_intermediaires",
                   "employes", "ouvriers", "diplomes_bac5", "sans_diplome", "etudiants",
                   "chomage", "immigres"]
PART_INERTIE_CONSERVEE = 0.85


def centrer_reduire(tableau):
    return (tableau - tableau.mean()) / tableau.std(ddof=0)


def afm(groupes):
    """Renvoie les coordonnées des unités sur les axes de l'AFM et la part d'inertie de chaque axe."""
    blocs = []
    for tableau in groupes:
        z = centrer_reduire(tableau)
        premiere_valeur_propre = np.linalg.svd(z.values, compute_uv=False)[0] ** 2 / len(z)
        blocs.append(z / np.sqrt(premiere_valeur_propre))
    x = pd.concat(blocs, axis=1)
    u, valeurs, _ = np.linalg.svd(x.values, full_matrices=False)
    coordonnees = pd.DataFrame(u * valeurs, index=x.index)
    inertie = valeurs ** 2 / (valeurs ** 2).sum()
    return coordonnees, inertie


def main(nombre_types=None):
    resultats = pd.read_csv(DOSSIER_TYPOLOGIE / "resultats_unites.csv", index_col="unite")
    socio = pd.read_csv(DOSSIER_TYPOLOGIE / "sociologie_unites.csv", index_col="unite")
    donnees = resultats.join(socio, how="inner")

    coordonnees, inertie = afm([donnees[VARIABLES_VOTE], donnees[VARIABLES_SOCIO]])
    nb_axes = int(np.searchsorted(np.cumsum(inertie), PART_INERTIE_CONSERVEE)) + 1
    axes = coordonnees.iloc[:, :nb_axes]
    print("Inertie des 5 premiers axes de l'AFM (%) :", np.round(100 * inertie[:5], 1))
    print(f"{nb_axes} axes conservés ({100 * inertie[:nb_axes].sum():.0f} % de l'information)")

    # Part de la variance totale expliquée par les types, pour k = 2 à 12
    arbre = linkage(axes.values, method="ward")
    inertie_totale = ((axes - axes.mean()) ** 2).values.sum()
    choix = []
    for k in range(2, 13):
        classes = fcluster(arbre, k, criterion="maxclust")
        intra = sum(((axes[classes == c] - axes[classes == c].mean()) ** 2).values.sum()
                    for c in np.unique(classes))
        choix.append({"nombre_types": k, "part_expliquee": round(100 * (1 - intra / inertie_totale), 1)})
    choix = pd.DataFrame(choix)
    choix.to_csv(DOSSIER_TYPOLOGIE / "choix_nombre_types.csv", index=False)
    print(choix.to_string(index=False))
    if nombre_types is None:
        return

    # CAH puis consolidation par les k-moyennes
    classes = fcluster(arbre, nombre_types, criterion="maxclust")
    centres = axes.groupby(classes).mean().values
    kmeans = KMeans(n_clusters=nombre_types, init=centres, n_init=1).fit(axes.values)
    donnees["type"] = kmeans.labels_ + 1

    # Les types sont numérotés du plus à gauche au plus à droite (vote Bardella croissant).
    ordre = donnees.groupby("type")["bardella"].mean().sort_values().index
    donnees["type"] = donnees["type"].map({ancien: nouveau for nouveau, ancien in enumerate(ordre, 1)})

    # Profils : moyenne de chaque variable par type, pondérée par les inscrits
    variables = VARIABLES_VOTE + VARIABLES_SOCIO
    def moyenne_ponderee(groupe):
        return pd.Series(np.average(groupe[variables], weights=groupe["inscrits_2024"], axis=0),
                         index=variables)
    profils = donnees.groupby("type").apply(moyenne_ponderee)
    profils.loc["metropole"] = moyenne_ponderee(donnees)
    profils.insert(0, "nombre_unites", donnees.groupby("type").size())
    profils.insert(1, "inscrits", donnees.groupby("type")["inscrits_2024"].sum())
    profils.loc["metropole", ["nombre_unites", "inscrits"]] = [len(donnees), donnees["inscrits_2024"].sum()]
    profils.round(2).to_csv(DOSSIER_TYPOLOGIE / "profils_types.csv")

    for i in range(2):
        donnees[f"axe_{i + 1}"] = coordonnees[i]
    donnees.round(3).to_csv(DOSSIER_TYPOLOGIE / "typologie_unites.csv")

    unites = gpd.read_file(DOSSIER_TYPOLOGIE / "unites.geojson").set_index("unite")
    unites = unites[["code_commune", "commune", "geometry"]].join(donnees, how="inner")
    unites.reset_index().to_file(DOSSIER_TYPOLOGIE / "typologie.geojson", driver="GeoJSON")

    print(f"\nTypologie en {nombre_types} types")
    print(profils.round(1).T.to_string())


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
