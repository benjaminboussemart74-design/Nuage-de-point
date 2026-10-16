"""
Chemins et paramètres partagés par les scripts de la typologie des bureaux de vote.

Les fichiers sources volumineux sont attendus dans data/brut/telechargements/ :
- general_results.parquet et candidats_results.parquet
  « Données des élections agrégées » (data.gouv.fr, ministère de l'Intérieur)
  https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/elections/general_results.parquet
  https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/elections/candidats_results.parquet
- carreaux_200m_met.gpkg : revenus Filosofi 2019 par carreaux de 200 m (INSEE)
  https://www.insee.fr/fr/statistiques/7655475
- base-ic-*-2021.CSV : recensement 2021 par IRIS (INSEE)
  https://www.insee.fr/fr/statistiques/8268806 (population), 8268838 (logement),
  8268843 (activité), 8268840 (diplômes)
- iris_rm.geojson : contours IRIS des 43 communes (IGN, couche STATISTICALUNITS.IRIS:contours_iris)
"""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
TELECHARGEMENTS = RACINE / "data" / "brut" / "telechargements"
FICHIER_COMMUNES = RACINE / "data" / "brut" / "communes_rennes_metropole.csv"
FICHIER_BUREAUX = RACINE / "data" / "geo" / "bureaux_vote_rennes_metropole.geojson"
DOSSIER_TYPOLOGIE = RACINE / "data" / "typologie"

# Projection officielle française (Lambert 93) : distances et surfaces en mètres.
LAMBERT93 = "EPSG:2154"

ELECTION_EUROPEENNES = "2024_euro_t1"
ELECTION_LEGISLATIVES = "2024_legi_t1"
