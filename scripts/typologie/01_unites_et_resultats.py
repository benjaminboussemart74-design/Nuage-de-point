"""
Étape 1 : construire les unités géographiques et leur associer les résultats de 2024.

Le découpage des contours et celui des résultats de 2024 ne coïncident pas partout :
- à Rennes, deux bureaux (263 et 423) ont été créés pour 2026 ; chacun est fusionné
  avec le bureau voisin du même centre de vote dont il a été détaché ;
- cinq communes ont créé des bureaux après 2022 sans que les contours nationaux
  aient été mis à jour : elles sont traitées comme une seule unité communale.

Sorties (data/typologie/) :
- unites.geojson : une forme par unité d'analyse
- resultats_unites.csv : participation et parts de voix par unité
"""

import geopandas as gpd
import pandas as pd

from commun import (DOSSIER_TYPOLOGIE, ELECTION_EUROPEENNES, ELECTION_LEGISLATIVES,
                    FICHIER_BUREAUX, FICHIER_COMMUNES, LAMBERT93, TELECHARGEMENTS)

CODE_RENNES = "35238"

# Listes des européennes de 2024, repérées par leur nuance officielle.
LISTES_EUROPEENNES = {
    "LUG": "glucksmann",   # Réveiller l'Europe (PS-Place publique)
    "LENS": "hayer",       # Besoin d'Europe (Renaissance et alliés)
    "LRN": "bardella",     # La France revient (RN)
    "LFI": "aubry",        # La France insoumise
    "LVEC": "toussaint",   # Europe Écologie
    "LLR": "bellamy",      # Les Républicains
    "LREC": "marechal",    # Reconquête
}


def charger_resultats(election, codes_communes):
    generaux = pd.read_parquet(
        TELECHARGEMENTS / "general_results.parquet",
        filters=[("id_election", "==", election), ("code_departement", "==", "35")],
    )
    generaux = generaux[generaux["code_commune"].isin(codes_communes)].copy()
    generaux["bureau"] = generaux["code_commune"] + "_" + generaux["code_bv"].str.zfill(4)

    candidats = pd.read_parquet(
        TELECHARGEMENTS / "candidats_results.parquet",
        filters=[("id_election", "==", election), ("code_departement", "==", "35")],
        columns=["code_commune", "code_bv", "nuance", "voix"],
    )
    candidats = candidats[candidats["code_commune"].isin(codes_communes)].copy()
    candidats["bureau"] = candidats["code_commune"] + "_" + candidats["code_bv"].str.zfill(4)
    return generaux, candidats


def voisin_le_plus_proche(bureaux, code):
    """Renvoie le bureau du même centre de vote qui partage la plus longue frontière."""
    # À Rennes, le bureau 0263 appartient au centre 26 : ses voisins de centre
    # partagent le même début de code, « 35238_026 ».
    forme = bureaux.loc[code, "geometry"]
    candidats = bureaux[(bureaux.index.str[:-1] == code[:-1]) & (bureaux.index != code)]
    frontieres = candidats.geometry.apply(lambda g: g.intersection(forme.boundary).length)
    return frontieres.idxmax()


def main():
    communes = pd.read_csv(FICHIER_COMMUNES, sep=";", dtype=str)
    codes_communes = set(communes["code_insee"])

    bureaux = gpd.read_file(FICHIER_BUREAUX).to_crs(LAMBERT93).set_index("codeBureauVote")
    euro, euro_voix = charger_resultats(ELECTION_EUROPEENNES, codes_communes)
    legi, _ = charger_resultats(ELECTION_LEGISLATIVES, codes_communes)

    contours = set(bureaux.index)
    resultats = set(euro["bureau"])

    # 1. Correspondance « bureau du contour » -> « unité d'analyse »
    unite = pd.Series(bureaux.index, index=bureaux.index)
    communes_regroupees = sorted({
        b[:5] for b in resultats - contours if not b.startswith(CODE_RENNES)
    })
    for code in communes_regroupees:
        unite[unite.index.str.startswith(code)] = f"{code}_COMMUNE"

    for code in sorted(contours - resultats):
        if code.startswith(CODE_RENNES):
            voisin = voisin_le_plus_proche(bureaux, code)
            unite[code] = voisin
            print(f"Rennes : bureau {code} (créé en 2026) fusionné avec {voisin}")

    # Côté résultats, chaque bureau rejoint l'unité de son contour, ou de sa commune.
    def unite_du_resultat(b):
        if b[:5] in communes_regroupees:
            return f"{b[:5]}_COMMUNE"
        return unite.get(b)

    for tableau in (euro, legi, euro_voix):
        tableau["unite"] = tableau["bureau"].map(unite_du_resultat)
    sans_contour = euro[euro["unite"].isna()]
    for _, b in sans_contour.iterrows():
        print(f"Exclu (aucun territoire) : {b['libelle_commune']} bureau {b['code_bv']} "
              f"({b['inscrits']} inscrits)")

    # 2. Formes des unités : on fusionne les contours d'une même unité.
    bureaux["unite"] = unite
    unites = bureaux.dissolve(by="unite", aggfunc={"codeCommune": "first", "nomCommune": "first"})
    unites = unites.rename(columns={"codeCommune": "code_commune", "nomCommune": "commune"})

    # 3. Résultats agrégés par unité
    comptes = ["inscrits", "votants", "exprimes", "blancs", "nuls"]
    e = euro.dropna(subset=["unite"]).groupby("unite")[comptes].sum()
    l = legi.dropna(subset=["unite"]).groupby("unite")[["inscrits", "votants"]].sum()

    voix = euro_voix.dropna(subset=["unite"]).copy()
    voix["liste"] = voix["nuance"].map(LISTES_EUROPEENNES).fillna("autres_listes")
    voix = voix.pivot_table(index="unite", columns="liste", values="voix", aggfunc="sum")

    tableau = pd.DataFrame(index=e.index)
    tableau["inscrits_2024"] = e["inscrits"]
    tableau["abstention_euro24"] = 100 * (1 - e["votants"] / e["inscrits"])
    tableau["abstention_legi24"] = 100 * (1 - l["votants"] / l["inscrits"])
    tableau["blancs_nuls_euro24"] = 100 * (e["blancs"] + e["nuls"]) / e["votants"]
    for liste in list(LISTES_EUROPEENNES.values()) + ["autres_listes"]:
        tableau[liste] = 100 * voix[liste] / e["exprimes"]

    DOSSIER_TYPOLOGIE.mkdir(parents=True, exist_ok=True)
    unites = unites.join(tableau[["inscrits_2024"]])
    unites.reset_index().to_file(DOSSIER_TYPOLOGIE / "unites.geojson", driver="GeoJSON")
    tableau.round(2).to_csv(DOSSIER_TYPOLOGIE / "resultats_unites.csv")

    print(f"Communes traitées comme une seule unité : {', '.join(communes_regroupees)}")
    print(f"{len(unites)} unités d'analyse, {int(tableau['inscrits_2024'].sum())} inscrits")


if __name__ == "__main__":
    main()
