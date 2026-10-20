"""
Estime le poids de chaque génération (année de naissance) dans les votants
de la présidentielle 2022, des européennes 2024 et de la présidentielle 2027 (projetée),
et prépare le simulateur de scores selon la participation par âge.

Pour chaque année de naissance :
    votants = population × taux d'inscription × taux de participation

Sources (INSEE, téléchargées automatiquement si absentes) :
1. Population au 1er janvier par âge détaillé (POP3, bilan démographique, juin 2026).
2. Inscrits sur les listes principales par âge (Répertoire électoral unique) :
   Insee Focus n° 264 (9 mars 2022) et n° 378 (11 février 2026).
3. Participation par âge à la présidentielle 2022 (enquête sur la participation électorale) :
   Insee Première n° 1928 (au moins un tour, par tranche de 5 ans)
   et n° 1929 (chaque tour, pour les 18-29, 30-64 et 65 ans ou plus).
4. Européennes 2024 : inscrits par âge (Insee Focus n° 328, 8 mai 2024).

Sources Ipsos, transcrites à la main dans data/cohortes/ :
5. vote_par_age_ipsos.csv : vote par tranche d'âge (Ipsos, « Sociologie des électorats »,
   1er tour de la présidentielle 2022 et européennes 2024), avec les résultats officiels.
6. participation_par_age_ipsos.csv : participation par tranche d'âge, utilisée pour 2024,
   faute d'enquête de l'INSEE sur ce scrutin.
7. vote_par_age_odoxa_2027.csv : intentions de vote au 1er tour de la présidentielle 2027,
   hypothèse Édouard Philippe candidat, par tranche d'âge (Odoxa-Backbone pour la Presse régionale,
   Public Sénat et Le Nouvel Obs, 12 005 personnes interrogées du 24 septembre au 7 octobre 2026).
   La colonne « officiel » reprend l'intention de vote d'ensemble du sondage.

Utilisation :
    python scripts/construire_cohortes_electorales.py
"""

import csv
import json
import urllib.request
from pathlib import Path

import openpyxl

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_BRUT = RACINE / "data" / "brut" / "telechargements" / "insee_cohortes"
DOSSIER_COHORTES = RACINE / "data" / "cohortes"
FICHIER_SORTIE = DOSSIER_COHORTES / "cohortes_electorales.json"
FICHIER_VOTE_IPSOS = DOSSIER_COHORTES / "vote_par_age_ipsos.csv"
FICHIER_VOTE_2027 = DOSSIER_COHORTES / "vote_par_age_odoxa_2027.csv"
FICHIER_PARTICIPATION_IPSOS = DOSSIER_COHORTES / "participation_par_age_ipsos.csv"
# Copie des mêmes données, chargée directement par la page de l'application.
FICHIER_APPLICATION = RACINE / "cohortes-presidentielle" / "donnees.js"

URLS = {
    "pop3.xlsx": "https://www.insee.fr/fr/statistiques/fichier/8999013/3_Pop1janv_age.xlsx",
    "if264.xlsx": "https://www.insee.fr/fr/statistiques/fichier/6322895/if264.xlsx",
    "if378.xlsx": "https://www.insee.fr/fr/statistiques/fichier/8888278/if378.xlsx",
    "if328.xlsx": "https://www.insee.fr/fr/statistiques/fichier/8192479/IF328.xlsx",
    "ip1928.xlsx": "https://www.insee.fr/fr/statistiques/fichier/6658145/ip1928.xlsx",
    "ip1929.xlsx": "https://www.insee.fr/fr/statistiques/fichier/6658143/ip1929.xlsx",
}

# Tranches de 5 ans utilisées par l'INSEE pour la participation et les inscrits 2022.
TRANCHES = [(18, 24), (25, 29), (30, 34), (35, 39), (40, 44), (45, 49), (50, 54),
            (55, 59), (60, 64), (65, 69), (70, 74), (75, 79), (80, 84), (85, 89), (90, 200)]
# Grandes tranches pour lesquelles l'INSEE publie la participation à chaque tour.
GRANDES_TRANCHES = [(18, 29), (30, 64), (65, 200)]
# Tranches des inscrits publiées pour 2024 et 2026.
TRANCHES_REU = [(18, 24), (25, 39), (40, 54), (55, 64), (65, 79), (80, 200)]
# Tranches d'âge des enquêtes Ipsos.
TRANCHES_IPSOS = [(18, 24), (25, 34), (35, 49), (50, 59), (60, 69), (70, 200)]
COLONNES_IPSOS = ["18-24", "25-34", "35-49", "50-59", "60-69", "70+"]

# Chaque sondage a ses propres tranches d'âge.
SONDAGES = {
    "2022": (FICHIER_VOTE_IPSOS, TRANCHES_IPSOS, COLONNES_IPSOS),
    "2024": (FICHIER_VOTE_IPSOS, TRANCHES_IPSOS, COLONNES_IPSOS),
    "2027": (FICHIER_VOTE_2027, [(18, 24), (25, 34), (35, 49), (50, 64), (65, 74), (75, 200)],
             ["18-24", "25-34", "35-49", "50-64", "65-74", "75+"]),
}


def nom_tranche(t):
    return f"{t[0]} ans et plus" if t[1] >= 200 else f"{t[0]}-{t[1]} ans"


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


def inscription_recalee(pop, fichier, pop22, inscription22):
    """
    Taux d'inscription par âge pour une année où le REU n'est publié que sur six tranches :
    on garde la forme de 2022 à l'intérieur de chaque tranche et on la recale sur le niveau observé.
    """
    inscrits = valeurs_par_tranche(fichier, "Figure 2a", 3)[:len(TRANCHES_REU)]
    niveau = taux_inscription(pop, inscrits, TRANCHES_REU)
    niveau22 = {T: sum(pop22[a][1] * inscription22[tranche_de(a, TRANCHES)] for a in pop22 if T[0] <= a <= T[1])
                / sum(pop22[a][1] for a in pop22 if T[0] <= a <= T[1]) for T in TRANCHES_REU}

    def taux(age):
        T = tranche_de(age, TRANCHES_REU)
        return min(1.0, inscription22[tranche_de(age, TRANCHES)] * niveau[T] / niveau22[T])
    return taux


def generations(pop, inscription, participation):
    """Une ligne par année de naissance des adultes : population, part inscrite et participation."""
    resultat = []
    for age in sorted(pop, reverse=True):
        if age < 18:
            continue
        naissance, effectif = pop[age]
        ligne = {"naissance": naissance, "age": age, "population": round(effectif),
                 "inscription": round(inscription(age), 4)}
        for tour, taux in participation.items():
            ligne[tour] = round(taux(age), 4)
        resultat.append(ligne)
    return resultat


def participation_europeennes(pop, inscription, participation22):
    """
    Participation par âge aux européennes 2024. Ipsos donne le niveau dans six tranches ;
    la forme à l'intérieur de chaque tranche reprend celle du 1er tour de 2022 (INSEE).
    """
    with open(FICHIER_PARTICIPATION_IPSOS, encoding="utf-8") as f:
        ipsos = next(l for l in csv.DictReader(f, delimiter=";") if l["election"] == "2024")
    forme = lambda a: participation22["t1"][tranche_de(a, TRANCHES)]
    inscrits = lambda a: pop[a][1] * inscription(a)
    facteurs = {}
    for T, colonne in zip(TRANCHES_IPSOS, COLONNES_IPSOS):
        ages = [a for a in pop if T[0] <= a <= T[1]]
        moyenne = sum(forme(a) * inscrits(a) for a in ages) / sum(inscrits(a) for a in ages)
        facteurs[T] = float(ipsos[colonne]) / 100 / moyenne
    return lambda a: min(1.0, forme(a) * facteurs[tranche_de(a, TRANCHES_IPSOS)])


def simulation(election, lignes_election):
    """
    Vote par tranche d'âge pour le simulateur de scores.

    Les pourcentages d'Ipsos sont arrondis et pondérés sur son propre échantillon. On les ajuste
    (méthode du calage itératif) pour que, avec les votants estimés de chaque tranche, on retrouve
    exactement les résultats officiels, tout en gardant la composition du vote de chaque tranche.
    """
    fichier, tranches, colonnes = SONDAGES[election]
    with open(fichier, encoding="utf-8") as f:
        candidats = [l for l in csv.DictReader(f, delimiter=";") if l["election"] == election]
    votants = [sum(l["population"] * l["inscription"] * l["t1"] for l in lignes_election if T[0] <= l["age"] <= T[1])
               for T in tranches]
    total = sum(votants)
    officiel = [float(c["officiel"]) for c in candidats]
    officiel = [o / sum(officiel) for o in officiel]
    # Matrice des voix : une ligne par candidat, une colonne par tranche d'âge.
    voix = [[max(float(c[col]), 0.2) / 100 * v for col, v in zip(colonnes, votants)] for c in candidats]
    for _ in range(200):
        for i, ligne in enumerate(voix):
            facteur = officiel[i] * total / sum(ligne)
            voix[i] = [x * facteur for x in ligne]
        for j, v in enumerate(votants):
            facteur = v / sum(ligne[j] for ligne in voix)
            for ligne in voix:
                ligne[j] *= facteur
    return {
        "tranches": [nom_tranche(T) for T in tranches],
        "bornes": [[T[0], T[1]] for T in tranches],
        "candidats": [{
            "id": c["id"], "nom": c["candidat"], "etiquette": c["etiquette"],
            "officiel": round(o, 5),
            "ipsos": [float(c[col]) / 100 for col in colonnes],
            "parTranche": [round(voix[i][j] / votants[j], 5) for j in range(len(votants))],
        } for i, (c, o) in enumerate(zip(candidats, officiel))],
    }


def main():
    telecharger()

    pop22, pop24, pop25, pop26 = population(2022), population(2024), population(2025), population(2026)

    # Inscription 2022 : directement par tranche de 5 ans.
    inscrits22 = valeurs_par_tranche("if264.xlsx", "Figure 2a", 3)[:len(TRANCHES)]
    inscription22 = taux_inscription(pop22, inscrits22, TRANCHES)
    participation22 = participation_par_tour(pop22, inscription22)

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

    inscription24 = inscription_recalee(pop24, "if328.xlsx", pop22, inscription22)
    inscription27 = inscription_recalee(pop26, "if378.xlsx", pop22, inscription22)

    # À âge égal, on vote en 2027 comme en 2022.
    par_tour = {tour: (lambda t: lambda a: t[tranche_de(a, TRANCHES)])(taux) for tour, taux in participation22.items()}
    elections = {
        "2022": generations(pop22, lambda a: min(1.0, inscription22[tranche_de(a, TRANCHES)]), par_tour),
        "2024": generations(pop24, inscription24, {"t1": participation_europeennes(pop24, inscription24, participation22)}),
        "2027": generations(pop27, inscription27, par_tour),
    }
    sortie = {
        "elections": elections,
        "simulation": {annee: simulation(annee, elections[annee]) for annee in ("2022", "2024", "2027")},
    }

    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_SORTIE.write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    FICHIER_APPLICATION.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_APPLICATION.write_text(
        "// Fichier généré par scripts/construire_cohortes_electorales.py : ne pas modifier à la main.\n"
        f"window.DONNEES = {json.dumps(sortie, ensure_ascii=False, separators=(',', ':'))};\n",
        encoding="utf-8")

    for annee, gens in elections.items():
        inscrits = sum(g["population"] * g["inscription"] for g in gens)
        votants = sum(g["population"] * g["inscription"] * g["t1"] for g in gens)
        print(f"{annee} : {sum(g['population'] for g in gens):,.0f} adultes, "
              f"{inscrits:,.0f} inscrits, {votants:,.0f} votants au 1er tour ({votants / inscrits:.1%})")
    print(f"Fichier écrit : {FICHIER_SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
