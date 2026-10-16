# Typologie des bureaux de vote de Rennes Métropole

Classement des 291 unités d'analyse (bureaux de vote, et 5 communes entières) de la métropole
selon leurs votes de 2024 et le profil social de leurs habitants.

## Lancer la chaîne de traitement

Les fichiers sources (voir `commun.py` pour les adresses) doivent être placés dans
`data/brut/telechargements/`, qui n'est pas versionné. Puis, depuis ce dossier :

```bash
python 01_unites_et_resultats.py   # unités géographiques et résultats 2024
python 02_sociologie.py            # profil social estimé par carreaux de 200 m
python 03_typologie.py             # compare les découpages de 2 à 12 types
python 03_typologie.py 7           # typologie retenue en 7 types
python 04_export_carte.py          # page web data/typologie/carte_typologie.html
```

## Fichiers produits (`data/typologie/`)

| Fichier | Contenu |
|---|---|
| `unites.geojson` | contours des 291 unités |
| `resultats_unites.csv` | participation et parts de voix (européennes et législatives 2024) |
| `sociologie_unites.csv` | 18 indicateurs sociaux par unité |
| `choix_nombre_types.csv` | part des écarts expliquée selon le nombre de types |
| `typologie_unites.csv` | type et coordonnées factorielles de chaque unité |
| `profils_types.csv` | moyennes de chaque type, pondérées par les inscrits |
| `typologie.geojson` | contours et données réunis, pour un logiciel de cartographie |
| `carte_typologie.html` | page de présentation (carte, nuage de points, portraits) |

## Les sept types

1. Centres urbains de la gauche diplômée
2. Centre bourgeois et étudiant
3. Couronne aisée du bloc central
4. Quartiers populaires mixtes
5. Bourgs résidentiels des classes moyennes
6. Grands ensembles en retrait des urnes
7. Périurbain populaire, premier vote RN
