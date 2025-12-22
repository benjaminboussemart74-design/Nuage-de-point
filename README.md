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

## Hiérarchie des sous-dossiers et signification des codes

### Dossier `Amendements/`

L'arborescence suit une organisation à 3 niveaux qui reflète la structure parlementaire :

**Niveau 1 : Dossiers législatifs (préfixe `DLR`)**
- Format : `DLR5L[législature]N[numéro]` (ex. `DLR5L17N50168`)
- Signification : 
  - `DLR` = Dossier Législatif de la République (5ème République)
  - `L17` = Législature 17
  - `N50168` = Numéro du dossier législatif
- Rôle : représente un **dossier législatif** complet (par exemple une proposition de loi, un projet de loi)

**Niveau 2 : Textes examinés (préfixe `PION`)**
- Format : `PIONANR5L[législature]B[numéro]` ou `PIONANR5L[législature]BTC[numéro]` (ex. `PIONANR5L17B0482`, `PIONANR5L17BTC0556`)
- Signification :
  - `PION` = Proposition (ou Projet) d'Initiative (Organe National)
  - `ANR5` = Assemblée Nationale, 5ème République
  - `L17` = Législature 17
  - `B0482` = numéro du texte de base (Bulletin)
  - `BTC` = probablement "Bulletin Texte Commission" (texte modifié en commission)
- Rôle : représente un **texte législatif** spécifique examiné dans le cadre du dossier parent (version initiale ou versions modifiées)

**Niveau 3 : Fichiers d'amendements (préfixe `AMAN`)**
- Format : `AMANR5L[législature]PO[session]B[texte]P[phase]D[discussion]N[numéro].json`
- Exemple : `AMANR5L17PO849323B0482P0D1N000001.json`
- Signification détaillée :
  - `AMAN` = AMendement Assemblée Nationale
  - `R5` = 5ème République
  - `L17` = Législature 17
  - `PO849323` = identifiant de la session/période d'examen
  - `B0482` = référence au texte (correspond au PION parent)
  - `P0D1` = phase et discussion (P = phase, D = discussion)
  - `N000001` = numéro séquentiel de l'amendement
- Rôle : chaque fichier JSON contient les **détails complets d'un amendement** (auteurs, texte, sort, dates, etc.)

**Exemple de parcours complet :**
```
Amendements/
└── DLR5L17N50168/              ← Dossier législatif n°50168 (17e législature)
    ├── PIONANR5L17B0482/        ← Texte n°0482 examiné dans ce dossier
    │   ├── AMANR5L17PO...N000001.json  ← Amendement n°1 sur ce texte
    │   ├── AMANR5L17PO...N000002.json  ← Amendement n°2
    │   └── ...
    └── PIONANR5L17BTC0556/      ← Texte commission n°0556 (version modifiée)
        └── ...
```

### Dossier `Députés et organes.json/`

Organisation par type d'entité parlementaire :

**`acteur/` : Députés et autres acteurs**
- Format des fichiers : `PA[numéro].json` (ex. `PA840979.json`)
- Signification :
  - `PA` = Personne/Acteur
  - Le numéro est un identifiant unique attribué à chaque député ou acteur parlementaire
- Contenu : état civil, profession, adresses, dates de mandat, etc.
- Rôle : fichier de **référence pour chaque député** (utilisé via `acteurRef` dans les amendements et mandats)

**`organe/` : Organes parlementaires**
- Format : `PO[numéro].json` (ex. `PO191887.json`, `PO845425.json`)
- Signification :
  - `PO` = organe POlitique/Parlementaire
  - Le numéro identifie l'organe (commission, groupe politique, délégation, etc.)
- Contenu : libellé de l'organe, type (commission, groupe, délégation), dates de fonctionnement, régime juridique
- Exemples d'organes :
  - Commissions permanentes (lois, finances, affaires étrangères, etc.)
  - Groupes politiques (ex. `PO845425` = groupe politique donné)
  - Délégations et missions d'information

**`mandat/` : Mandats parlementaires**
- Format : `PM[numéro].json` (ex. `PM115583.json`)
- Signification :
  - `PM` = Parlementaire Mandat
  - Le numéro identifie le mandat spécifique
- Contenu : lie un acteur (`acteurRef`) à un organe (`organeRef`) avec des dates de début/fin, qualité (membre, président, rapporteur), législature
- Rôle : table de **liaison acteur ↔ organe** (qui fait partie de quoi, quand, avec quel rôle)

**`deport/` et `pays/`**
- Rôle probable : informations complémentaires sur les déports (rattachements territoriaux ?) et pays (pour députés issus des territoires d'outre-mer ou liens internationaux)

**Exemple de relations entre entités :**
```
Amendement AMANR5L17PO...N000001.json
    ├── signataires.auteur.acteurRef = "PA795982"  → voir acteur/PA795982.json
    ├── signataires.auteur.groupePolitiqueRef = "PO845413"  → voir organe/PO845413.json
    └── acteur PA795982 a des mandats  → voir mandat/PM[xxx].json
            └── mandat.organeRef = "PO845413"  → relie l'acteur au groupe politique
```

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
