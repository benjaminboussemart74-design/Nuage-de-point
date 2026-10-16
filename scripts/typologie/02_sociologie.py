"""
Étape 2 : estimer le profil sociologique de chaque unité d'analyse.

Les données de l'INSEE ne sont pas publiées par bureau de vote. On passe donc par
les carreaux de 200 m de Filosofi 2019, qui donnent la population de chaque carreau :
1. chaque carreau est rattaché à l'unité qui contient son centre ;
2. les revenus, logements et âges de Filosofi sont additionnés par unité ;
3. les données du recensement 2021, publiées par IRIS (quartier d'environ 2 000 habitants),
   sont réparties entre les carreaux de l'IRIS au prorata de leur population,
   puis additionnées par unité. C'est une méthode dite « dasymétrique ».

Sortie : data/typologie/sociologie_unites.csv
"""

import geopandas as gpd
import pandas as pd

from commun import DOSSIER_TYPOLOGIE, LAMBERT93, TELECHARGEMENTS

# Variables du recensement à répartir, par fichier
RECENSEMENT = {
    "evol-struct-pop": ["P21_POP", "C21_POP15P", "C21_POP15P_CS3", "C21_POP15P_CS4",
                        "C21_POP15P_CS5", "C21_POP15P_CS6", "C21_POP15P_CS7", "P21_POP_IMM"],
    "diplomes-formation": ["P21_NSCOL15P", "P21_NSCOL15P_DIPLMIN", "P21_NSCOL15P_SUP5"],
    "activite-residents": ["P21_POP1564", "P21_ETUD1564", "P21_ACT1564", "P21_CHOM1564"],
}

COLONNES_RECENSEMENT = sum(RECENSEMENT.values(), [])

# Les contours IRIS de l'IGN sont plus récents que le recensement 2021 :
# l'IRIS rennais 0903 a depuis été scindé en Cleunay Est (0906) et La Courrouze (0907).
IRIS_SCINDES = {"352380906": "352380903", "352380907": "352380903"}

FILOSOFI = ["ind", "men", "men_pauv", "men_1ind", "men_prop", "men_fmp", "men_coll",
            "ind_snv", "log_soc", "ind_18_24", "ind_65_79", "ind_80p"]


def lire_recensement(codes_communes):
    tableaux = []
    for fichier, colonnes in RECENSEMENT.items():
        t = pd.read_csv(TELECHARGEMENTS / f"base-ic-{fichier}-2021.CSV", sep=";",
                        dtype={"IRIS": str, "COM": str}, usecols=["IRIS", "COM"] + colonnes)
        tableaux.append(t[t["COM"].isin(codes_communes)].set_index("IRIS")[colonnes])
    return pd.concat(tableaux, axis=1).apply(pd.to_numeric, errors="coerce")


def main():
    unites = gpd.read_file(DOSSIER_TYPOLOGIE / "unites.geojson").to_crs(LAMBERT93)
    iris = gpd.read_file(TELECHARGEMENTS / "iris_rm.geojson").to_crs(LAMBERT93)
    recensement = lire_recensement(set(unites["code_commune"]))

    carreaux = gpd.read_file(TELECHARGEMENTS / "carreaux_200m_met.gpkg",
                             bbox=tuple(unites.total_bounds), columns=FILOSOFI)
    carreaux["geometry"] = carreaux.geometry.centroid

    # Chaque centre de carreau reçoit son unité et son IRIS.
    carreaux = gpd.sjoin(carreaux, unites[["unite", "geometry"]], predicate="within", how="inner")
    carreaux = carreaux.drop(columns="index_right")
    carreaux = gpd.sjoin(carreaux, iris[["code_iris", "geometry"]], predicate="within", how="left")
    carreaux["code_iris"] = carreaux["code_iris"].replace(IRIS_SCINDES)
    print(f"{len(carreaux)} carreaux habités, {int(carreaux['ind'].sum())} habitants (Filosofi 2019)")

    # Poids de chaque carreau dans la population de son IRIS
    carreaux["poids"] = carreaux["ind"] / carreaux.groupby("code_iris")["ind"].transform("sum")
    absents = set(carreaux["code_iris"].dropna()) - set(recensement.index)
    if absents:
        print(f"IRIS sans données du recensement : {sorted(absents)}")
    reparti = recensement.reindex(carreaux["code_iris"]).mul(carreaux["poids"].values, axis=0)
    reparti.index = carreaux.index
    carreaux = carreaux.join(reparti)

    s = carreaux.groupby("unite")[FILOSOFI + COLONNES_RECENSEMENT].sum()

    socio = pd.DataFrame(index=s.index)
    socio["population"] = s["ind"]
    socio["niveau_vie_moyen"] = s["ind_snv"] / s["ind"]
    socio["menages_pauvres"] = 100 * s["men_pauv"] / s["men"]
    socio["proprietaires"] = 100 * s["men_prop"] / s["men"]
    socio["logements_sociaux"] = 100 * s["log_soc"] / s["men"]
    socio["logements_collectifs"] = 100 * s["men_coll"] / s["men"]
    socio["menages_1_personne"] = 100 * s["men_1ind"] / s["men"]
    socio["familles_monoparentales"] = 100 * s["men_fmp"] / s["men"]
    socio["jeunes_18_24"] = 100 * s["ind_18_24"] / s["ind"]
    socio["seniors_65_plus"] = 100 * (s["ind_65_79"] + s["ind_80p"]) / s["ind"]
    socio["cadres"] = 100 * s["C21_POP15P_CS3"] / s["C21_POP15P"]
    socio["professions_intermediaires"] = 100 * s["C21_POP15P_CS4"] / s["C21_POP15P"]
    socio["employes"] = 100 * s["C21_POP15P_CS5"] / s["C21_POP15P"]
    socio["ouvriers"] = 100 * s["C21_POP15P_CS6"] / s["C21_POP15P"]
    socio["diplomes_bac5"] = 100 * s["P21_NSCOL15P_SUP5"] / s["P21_NSCOL15P"]
    socio["sans_diplome"] = 100 * s["P21_NSCOL15P_DIPLMIN"] / s["P21_NSCOL15P"]
    socio["etudiants"] = 100 * s["P21_ETUD1564"] / s["P21_POP1564"]
    socio["chomage"] = 100 * s["P21_CHOM1564"] / s["P21_ACT1564"]
    socio["immigres"] = 100 * s["P21_POP_IMM"] / s["P21_POP"]

    manquantes = set(unites["unite"]) - set(socio.index)
    if manquantes:
        print(f"Unités sans carreau habité : {sorted(manquantes)}")
    socio.round(2).to_csv(DOSSIER_TYPOLOGIE / "sociologie_unites.csv")
    print(f"{len(socio)} unités décrites")


if __name__ == "__main__":
    main()
