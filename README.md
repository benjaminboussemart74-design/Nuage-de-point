# Nuage-de-point
Nuage de points pour traiter les données de la 17ème législature

Ce dépôt contient des données extraites (au format JSON) relatives aux amendements et aux acteurs (députés, organes, mandats, etc.) de la 17ème législature. Les fichiers de données sont volumineux et sont ignorés par Git via le `.gitignore` du projet.

## Structure principale

- `.gitignore` : règles pour ignorer les gros dossiers de données et fichiers macOS (`.DS_Store`).
- `Amendements/` : dossier racine contenant des sous-dossiers organisés par référence de texte (ex. `DLR5L15N43846/`) puis par identifiants d'examen (ex. `PIONANR5L17B1105/`). Chaque feuille contient de nombreux fichiers JSON décrivant un amendement.
- `Députés et organes.json/` : arborescence contenant des fichiers JSON structurés pour les entités suivantes :
  - `acteur/` : fiches individuelles des députés (ex. `PA840979.json`) contenant des champs tels que `uid`, `etatCivil` (nom, prénom, date de naissance), `profession`, `adresses`, etc.
  - `mandat/`, `organe/`, `deport/`, `pays/` : autres informations structurées liées aux mandats, organes et pays.
- `LICENSE`, `README.md` : fichiers du dépôt.

## Contenu des fichiers (exemples)

- Amendements (extrait d'un fichier JSON d'amendement) — champs fréquents :
  - `amendement.uid` : identifiant unique de l'amendement
  - `amendement.legislature` : numéro de la législature
  - `amendement.identification` : numéros et références internes
  - `amendement.signataires` : auteur et cosignataires (références aux acteurs)
  - `amendement.pointeurFragmentTexte` : position dans le texte (article, division)
  - `amendement.corps` : texte du cartouche informatif / contenu
  - `amendement.cycleDeVie` : dates de dépôt et publication, états de traitement
  - `amendement.representations` : liens vers versions PDF, statut, URI

- Acteurs (exemple `Députés et organes.json/acteur/PA840979.json`) — champs fréquents :
  - `acteur.uid` : identifiant de l'acteur (ex. `PA840979`)
  - `acteur.etatCivil.ident` : civilité, prénom, nom, trigramme
  - `acteur.etatCivil.infoNaissance` : date et lieu de naissance
  - `acteur.profession` : libellé de la profession
  - `acteur.adresses` : adresses postales et emails

Ces JSON sont structurés et contiennent souvent des sous-objets complexes (références croisées entre amendements et acteurs). Ils sont prêts à être ingérés par des scripts (Python, Node.js, jq) pour extraction, transformation ou visualisation.

## Utilité et suggestions d'utilisation

- Archivage et recherche : indexer les JSON dans une base NoSQL (MongoDB, Elasticsearch) pour pouvoir rechercher rapidement par député, numéro d'amendement, article, etc.
- Analyse : écrire des scripts Python (pandas) ou Node.js pour agréger les signataires, états des amendements, dates, etc.
- Génération de rapports/PDF : utiliser les champs `representations` pour récupérer les documents PDF associés.

## Remarques sur la taille des données

Les dossiers `Amendements/` et `Députés et organes.json/` contiennent de très nombreux fichiers JSON (chacun représentant une entité). Pour éviter d'alourdir l'historique Git, ces dossiers sont exclus du suivi par `.gitignore`. Si vous souhaitez versionner certains fichiers volumineux, je recommande :

- Git LFS (pour fichiers binaires ou très volumineux)
- ou un dépôt séparé / stockage cloud pour les jeux de données bruts, et ne garder dans ce dépôt que les scripts et métadonnées légères.

## Exemples rapides d'utilisation

Afficher un exemple d'acteur (avec `jq`) :

```bash
# Afficher le nom et l'email du fichier acteur
jq '.acteur.etatCivil.ident, .acteur.adresses.adresse[] | select(.typeLibelle=="Mèl")?.valElec' "Députés et organes.json/acteur/PA840979.json"
```

Lister les fichiers d'un examen d'amendements :

```bash
ls -1 "Amendements/DLR5L15N43846/PIONANR5L17B1105/" | head
```

---

Si vous voulez, je peux :
- ajouter dans le README un exemple de script Python pour parser les fichiers JSON ;
- configurer Git LFS et migrer certains fichiers ;
- ou créer une page de documentation plus détaillée (structure des JSON, schéma des champs).

Dites-moi ce que vous préférez que j'ajoute ensuite.
