# Pipeline de Normalisation et Analyse des Données Parlementaires

Ce dossier contient les scripts Python pour normaliser les données JSON de la 17ème législature vers des fichiers CSV cohérents, puis calculer des statistiques par député et par groupe politique.

## Architecture du pipeline

```
scripts/
├── normalize_acteurs.py        # Normalisation des députés
├── normalize_organes.py        # Normalisation des organes (groupes, commissions)
├── normalize_mandats.py        # Normalisation des mandats (relations acteur-organe)
├── normalize_amendements.py   # Normalisation des amendements
├── run_normalization.py       # Script principal de normalisation
├── compute_depute_stats.py    # Calcul des statistiques par député
├── compute_groupe_stats.py    # Calcul des statistiques par groupe politique
└── run_statistics.py          # Script principal de calcul de stats
```

## 🚀 Installation et utilisation

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Normalisation des données JSON → CSV

Cette étape transforme les milliers de fichiers JSON en 4 fichiers CSV normalisés :

```bash
python scripts/run_normalization.py
```

**Fichiers CSV générés** (dans `data/csv/`) :
- `acteurs.csv` : Députés avec informations personnelles (nom, prénom, profession, email, etc.)
- `organes.csv` : Groupes politiques, commissions, délégations
- `mandats.csv` : Relations acteur ↔ organe (qui fait partie de quoi, quand, avec quel rôle)
- `amendements.csv` : Amendements avec métadonnées (auteur, groupe, sort, dates, etc.)

⚠️ **Note** : Le traitement des amendements peut prendre plusieurs minutes (il y a des dizaines de milliers de fichiers).

**Pour un test rapide**, éditez `scripts/normalize_amendements.py` ligne 95 et décommentez :
```python
normalize_amendements(str(input_dir), str(output_csv), limit=5000)
```

### 3. Calcul des statistiques

Une fois les CSV normalisés créés, calculez les statistiques :

```bash
python scripts/run_statistics.py
```

**Fichiers de statistiques générés** (dans `data/stats/`) :
- `stats_par_depute.csv` : Statistiques individuelles par député
- `stats_par_groupe.csv` : Statistiques agrégées par groupe politique

## 📊 Statistiques calculées

### Par député (`stats_par_depute.csv`)

| Métrique | Description |
|----------|-------------|
| `nb_amendements_total` | Nombre total d'amendements déposés (comme auteur) |
| `nb_amendements_adoptes` | Nombre d'amendements adoptés |
| `nb_amendements_rejetes` | Nombre d'amendements rejetés |
| `nb_amendements_retires` | Nombre d'amendements retirés |
| `nb_amendements_irrecevables` | Nombre d'amendements irrecevables |
| `taux_adoption_pct` | Taux d'adoption (%) |
| `taux_rejet_pct` | Taux de rejet (%) |
| `taux_irrecevable_pct` | Taux d'irrecevabilité (%) |
| `moyenne_cosignataires` | Nombre moyen de cosignataires par amendement |
| `nb_amendements_article40` | Nombre d'amendements soumis à l'article 40 (irrecevabilité financière) |

### Par groupe politique (`stats_par_groupe.csv`)

| Métrique | Description |
|----------|-------------|
| `nb_deputes_actifs` | Nombre de députés ayant déposé au moins 1 amendement |
| `nb_amendements_total` | Nombre total d'amendements déposés par le groupe |
| `nb_amendements_adoptes` | Nombre d'amendements adoptés |
| `nb_amendements_rejetes` | Nombre d'amendements rejetés |
| `taux_adoption_pct` | Taux d'adoption moyen du groupe (%) |
| `taux_rejet_pct` | Taux de rejet moyen (%) |
| `moyenne_amendements_par_depute` | Moyenne d'amendements par député du groupe |
| `moyenne_cosignataires` | Nombre moyen de cosignataires par amendement |

## 🔗 Schéma relationnel des CSV

```
acteurs.csv
    ├── acteur_uid (PK)
    └── (nom, prénom, profession, email, etc.)

organes.csv
    ├── organe_uid (PK)
    └── (libelle, type, dates, etc.)

mandats.csv
    ├── mandat_uid (PK)
    ├── acteur_uid (FK → acteurs)
    ├── organe_uid (FK → organes)
    └── (dates, qualité, etc.)

amendements.csv
    ├── amendement_uid (PK)
    ├── auteur_acteur_uid (FK → acteurs)
    ├── auteur_groupe_politique_uid (FK → organes)
    ├── texte_legislatif_ref
    └── (dates, sort, état, etc.)
```

## 💡 Utilisation des statistiques pour des algorithmes

Les fichiers CSV de statistiques sont prêts à être utilisés comme features pour des algorithmes de machine learning :

### Exemples d'utilisation

**1. Prédiction de vote / classification de députés**
```python
import pandas as pd

stats = pd.read_csv('data/stats/stats_par_depute.csv')

# Features pour clustering ou classification
features = stats[[
    'nb_amendements_total',
    'taux_adoption_pct',
    'taux_rejet_pct',
    'moyenne_cosignataires'
]]

# Joindre avec groupe politique
# ... clustering K-means, DBSCAN, etc.
```

**2. Analyse comparative des groupes politiques**
```python
groupes = pd.read_csv('data/stats/stats_par_groupe.csv')

# Comparer productivité vs efficacité
import matplotlib.pyplot as plt

plt.scatter(
    groupes['moyenne_amendements_par_depute'],
    groupes['taux_adoption_pct'],
    s=groupes['nb_deputes_actifs']*10
)
plt.xlabel('Moyenne amendements par député')
plt.ylabel('Taux d\'adoption (%)')
plt.show()
```

**3. Système de recommandation / scoring**
```python
# Créer un score d'activité parlementaire
stats['score_activite'] = (
    stats['nb_amendements_total'] * 0.4 +
    stats['taux_adoption_pct'] * 0.3 +
    stats['moyenne_cosignataires'] * 0.3
)

top_deputes = stats.nlargest(20, 'score_activite')
```

## 📝 Notes techniques

- **Encodage** : Tous les CSV sont encodés en UTF-8
- **Séparateur** : Virgule (`,`)
- **Valeurs manquantes** : Chaînes vides (`''`) ou `NaN` pour pandas
- **Relations** : Les colonnes `*_uid` permettent de faire des jointures entre tables
- **Performance** : Le traitement complet peut prendre 5-15 minutes selon le nombre d'amendements

## 🛠️ Personnalisation

Pour ajouter de nouvelles métriques, éditez :
- `scripts/compute_depute_stats.py` pour les stats par député
- `scripts/compute_groupe_stats.py` pour les stats par groupe

Les scripts utilisent pandas pour faciliter l'ajout de calculs supplémentaires (groupby, merge, etc.).

## 📊 Exemples de requêtes SQL (si import en base de données)

Si vous importez les CSV dans une base SQL (SQLite, PostgreSQL, etc.), voici quelques requêtes utiles :

```sql
-- Top 10 députés les plus actifs
SELECT nom, prenom, nb_amendements_total, taux_adoption_pct
FROM stats_par_depute
ORDER BY nb_amendements_total DESC
LIMIT 10;

-- Députés avec le meilleur taux d'adoption (min 50 amendements)
SELECT nom, prenom, nb_amendements_total, taux_adoption_pct
FROM stats_par_depute
WHERE nb_amendements_total >= 50
ORDER BY taux_adoption_pct DESC
LIMIT 10;

-- Comparaison des groupes politiques
SELECT libelle_abrege, nb_deputes_actifs, nb_amendements_total,
       moyenne_amendements_par_depute, taux_adoption_pct
FROM stats_par_groupe
ORDER BY nb_amendements_total DESC;
```

## 🔄 Pipeline complet (commandes)

```bash
# 1. Installation
pip install -r requirements.txt

# 2. Normalisation JSON → CSV
python scripts/run_normalization.py

# 3. Calcul des statistiques
python scripts/run_statistics.py

# Les fichiers sont maintenant prêts dans data/csv/ et data/stats/
```
