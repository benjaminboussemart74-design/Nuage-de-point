"""
Estime le poids de chaque génération (année de naissance) dans les votants
des présidentielles 2022 (observée) et 2027 (projetée).

Pour chaque année de naissance :
    votants = population × taux d'inscription × taux de participation

Sources (INSEE, téléchargées automatiquement si absentes) :
1. Population au 1er janvier par âge détaillé (POP3, bilan démographique, juin 2026).
2. Inscrits sur les listes principales par âge (Répertoire électoral unique) :
   Insee Focus n° 264 (9 mars 2022) et n° 378 (11 février 2026).
3. Participation par âge à la présidentielle 2022 (enquête sur la participation électorale) :
   Insee Première n° 1928 (au moins un tour, par tranche de 5 ans)
   et n° 1929 (chaque tour, pour les 18-29, 30-64 et 65 ans ou plus).

Utilisation :
    python scripts/construire_cohortes_electorales.py
"""

import json
import urllib.request
from pathlib import Path

import openpyxl

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_BRUT = RACINE / "data" / "brut" / "telechargements" / "insee_cohortes"
FICHIER_SORTIE = RACINE / "data" / "cohortes" / "cohortes_electorales.json"
# Copie des mêmes données, chargée directement par la page de l'application.
FICHIER_APPLICATION = RACINE / "cohortes-presidentielle" / "donnees.js"

URLS = {
    "pop3.xlsx": "https://www.insee.fr/fr/statistiques/fichier/8999013/3_Pop1janv_age.xlsx",
    "if264.xlsx": "https://www.insee.fr/fr/statistiques/fichier/6322895/if264.xlsx",
    "if378.xlsx": "https://www.insee.fr/fr/statistiques/fichier/8888278/if378.xlsx",
    "ip1928.xlsx": "https://www.insee.fr/fr/statistiques/fichier/6658145/ip1928.xlsx",
    "ip1929.xlsx": "https://www.insee.fr/fr/statistiques/fichier/6658143/ip1929.xlsx",
}

# Tranches de 5 ans utilisées par l'INSEE pour la participation et les inscrits 2022.
TRANCHES = [(18, 24), (25, 29), (30, 34), (35, 39), (40, 44), (45, 49), (50, 54),
            (55, 59), (60, 64), (65, 69), (70, 74), (75, 79), (80, 84), (85, 89), (90, 200)]
# Grandes tranches pour lesquelles l'INSEE publie la participation à chaque tour.
GRANDES_TRANCHES = [(18, 29), (30, 64), (65, 200)]
# Tranches des inscrits publiées pour 2026.
TRANCHES_2026 = [(18, 24), (25, 39), (40, 54), (55, 64), (65, 79), (80, 200)]


def telecharger():
    DOSSIER_BRUT.mkdir(parents=True, exist_ok=True)
    for nom, url in URLS.items():
        chemin = DOSSIER_BRUT / nom
        if not chemin.exists():
            print(f"Téléchargement de {nom}")
            urllib.request.urlretrieve(url, chemin)


def lignes(nom_fichier, feuille):
    """Renvoie les lignes d'une feuille, sans les cellules vides."""
    classeur = openpyxl.load_workbook(DOSSIER_BRUT / nom_fichier, data_only=True)
    return [[c for c in ligne if c is not None] for ligne in classeur[feuille].iter_rows(values_only=True)]


def tranche_de(age, tranches):
    return next(t for t in tranches if t[0] <= age <= t[1])


def population(annee):
    """Population de la France entière au 1er janvier : {âge: (année de naissance, effectif)}."""
    classeur = openpyxl.load_workbook(DOSSIER_BRUT / "pop3.xlsx", data_only=True)
    resultat = {}
    for ligne in classeur[str(annee)].iter_rows(values_only=True):
        naissance, age = str(ligne[0] or "").strip(), str(ligne[1] or "").strip()
        if naissance.isdigit() and age.split()[0].isdigit():
            # La dernière ligne regroupe les « 100 ans ou plus » (née en ... ou avant).
            resultat[int(age.split()[0])] = (int(naissance), ligne[5])
    return resultat


def valeurs_par_tranche(nom_fichier, feuille, colonne):
    """Lit un tableau INSEE dont la première colonne est une tranche d'âge (« 18-24 ans »...)."""
    resultat = []
    for ligne in lignes(nom_fichier, feuille):
        if ligne and isinstance(ligne[0], str) and "ans" in ligne[0] and len(ligne) > colonne:
            if isinstance(ligne[colonne], (int, float)):
                resultat.append(ligne[colonne])
    return resultat


def taux_inscription(pop, inscrits, tranches):
    """Rapport inscrits / population pour chaque tranche."""
    taux = {}
    for tranche, nb_inscrits in zip(tranches, inscrits):
        effectif = sum(n for age, (_, n) in pop.items() if tranche[0] <= age <= tranche[1])
        taux[tranche] = nb_inscrits / effectif
    return taux


def participation_par_tour(pop, inscription):
    """
    Taux de vote par tranche de 5 ans, pour chaque tour.

    L'INSEE donne, par tranche de 5 ans, la part des inscrits ayant voté à au moins un tour,
    et, pour trois grandes tranches, la participation à chaque tour. On garde la forme fine
    de la première série et on la recale sur le niveau de chaque tour dans chaque grande tranche.
    """
    au_moins_un = dict(zip(TRANCHES, [v / 100 for v in valeurs_par_tranche("ip1928.xlsx", "Figure 3", 1)]))
    # Figure 5 : les lignes de 2022 donnent, dans l'ordre, le 1er puis le 2d tour de la présidentielle
    # (colonnes : ensemble, 18-29 ans, 30-64 ans, 65 ans ou plus).
    lignes_2022 = [ligne for ligne in lignes("ip1929.xlsx", "Figure 5") if len(ligne) >= 5 and ligne[-5] == 2022]
    tours = {"t1": [v / 100 for v in lignes_2022[0][-3:]], "t2": [v / 100 for v in lignes_2022[1][-3:]]}
    inscrits_tranche = {t: sum(n for age, (_, n) in pop.items() if t[0] <= age <= t[1]) * inscription[t]
                        for t in TRANCHES}
    resultat = {}
    for tour, niveaux in tours.items():
        resultat[tour] = {}
        for grande, niveau in zip(GRANDES_TRANCHES, niveaux):
            fines = [t for t in TRANCHES if grande[0] <= t[0] and t[1] <= grande[1]]
            moyenne = sum(au_moins_un[t] * inscrits_tranche[t] for t in fines) / sum(inscrits_tranche[t] for t in fines)
            for t in fines:
                resultat[tour][t] = au_moins_un[t] * niveau / moyenne
    return resultat


def main():
    telecharger()

    pop22, pop25, pop26 = population(2022), population(2025), population(2026)

    # Inscription 2022 : directement par tranche de 5 ans.
    inscrits22 = valeurs_par_tranche("if264.xlsx", "Figure 2a", 3)[:len(TRANCHES)]
    inscription22 = taux_inscription(pop22, inscrits22, TRANCHES)

    # Inscription 2026 : six tranches seulement. On garde la forme de 2022 à l'intérieur
    # de chacune et on la recale sur le niveau observé en 2026.
    inscrits26 = valeurs_par_tranche("if378.xlsx", "Figure 2a", 3)[:len(TRANCHES_2026)]
    inscription26_large = taux_inscription(pop26, inscrits26, TRANCHES_2026)
    inscrits22_large = {T: sum(pop22[a][1] * inscription22[tranche_de(a, TRANCHES)]
                               for a in pop22 if T[0] <= a <= T[1]) for T in TRANCHES_2026}
    pop22_large = {T: sum(pop22[a][1] for a in pop22 if T[0] <= a <= T[1]) for T in TRANCHES_2026}

    def inscription27(age):
        T = tranche_de(age, TRANCHES_2026)
        return min(1.0, inscription22[tranche_de(age, TRANCHES)]
                   * inscription26_large[T] / (inscrits22_large[T] / pop22_large[T]))

    participation = participation_par_tour(pop22, inscription22)

    # Projection au 1er janvier 2027 : chaque génération vieillit d'un an et évolue
    # comme elle l'a fait entre 2025 et 2026 (décès et migrations).
    age_max = max(pop26)
    pop27 = {}
    for age in range(17, age_max):
        naissance, effectif = pop26[age]
        evolution = pop26[age + 1][1] / pop25[age][1] if age + 1 < age_max else 1.0
        pop27[age + 1] = (naissance, effectif * evolution)
    # Les « 100 ans ou plus » de 2026 restent dans la dernière ligne avec ceux qui les rejoignent.
    pop27[age_max] = (pop26[age_max - 1][0], pop27[age_max][1] + pop26[age_max][1] * pop26[age_max][1] / pop25[age_max][1])

    def generations(pop, inscription):
        resultat = []
        for age in sorted(pop, reverse=True):
            if age < 18:
                continue
            naissance, effectif = pop[age]
            tranche = tranche_de(age, TRANCHES)
            resultat.append({
                "naissance": naissance,
                "age": age,
                "population": round(effectif),
                "inscription": round(inscription(age), 4),
                "t1": round(participation["t1"][tranche], 4),
                "t2": round(participation["t2"][tranche], 4),
            })
        return resultat

    sortie = {
        "2022": generations(pop22, lambda a: min(1.0, inscription22[tranche_de(a, TRANCHES)])),
        "2027": generations(pop27, inscription27),
    }
    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_SORTIE.write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    FICHIER_APPLICATION.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_APPLICATION.write_text(
        "// Fichier généré par scripts/construire_cohortes_electorales.py : ne pas modifier à la main.\n"
        f"window.DONNEES = {json.dumps(sortie, ensure_ascii=False, separators=(',', ':'))};\n",
        encoding="utf-8")

    for annee, gens in sortie.items():
        inscrits = sum(g["population"] * g["inscription"] for g in gens)
        votants = sum(g["population"] * g["inscription"] * g["t1"] for g in gens)
        print(f"{annee} : {sum(g['population'] for g in gens):,.0f} adultes, "
              f"{inscrits:,.0f} inscrits, {votants:,.0f} votants au 1er tour ({votants / inscrits:.1%})")
    print(f"Fichier écrit : {FICHIER_SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
