---
name: infographie-politique
description: Créer des infographies politiques web (one pages, dataviz, simulateurs, tableaux de bord parlementaires) dans un style éditorial sobre inspiré de la presse d'analyse (Le Grand Continent, Foreign Affairs). Utiliser ce skill dès que l'utilisateur demande de construire une interface, un composant, une page ou une visualisation liée à la politique française, au travail parlementaire, à la veille législative, aux résultats électoraux, à la sociologie électorale, à l'énergie-climat ou à la politique industrielle. Également utiliser quand l'utilisateur mentionne des mots comme infographie, one page, dataviz politique, simulateur électoral, carte électorale, hémicycle, Sankey, veille parlementaire, suivi législatif, ou toute interface affichant des données institutionnelles françaises. Ne PAS utiliser pour des sites marketing, des landing pages commerciales ou des interfaces sans rapport avec la politique ou les institutions.
---

# Infographies politiques — Système de design éditorial

Ce skill produit des infographies politiques web de qualité professionnelle : code fonctionnel, sobre, immédiatement utilisable, et qui ne ressemble pas à une page générée par une IA.

L'utilisateur fournit un besoin : un composant, une page, une visualisation ou une interface complète. Il peut préciser le sujet politique, les données à afficher ou le format souhaité. L'utilisateur est débutant en code : expliquer les choix en termes simples quand il le demande.

## Méthode : un plan de design avant le code

Une IA laissée sans consigne reproduit la moyenne de ce qu'elle a vu. Pour l'éviter, chaque page suit ces quatre étapes, dans l'ordre.

1. **Définir le sujet et la tâche.** En une phrase : de quoi parle la page, pour qui, et quelle est la seule chose que le lecteur doit pouvoir faire ou comprendre.
2. **Chercher dans le monde du sujet.** Relever au moins deux éléments propres à ce sujet, à utiliser comme contenu et non comme décor : ses unités réelles (voix, inscrits, points, sièges), ses documents (procès-verbal de dépouillement, feuille d'émargement, bulletin, hémicycle, carte des bureaux), son vocabulaire (exprimés, nuance, report de voix).
3. **Écrire le plan dans le fichier**, en commentaire au-dessus des variables CSS : le concept de mise en page en une ligne, la palette retenue, l'élément d'ouverture.
4. **Relire le plan contre la liste des automatismes** ci-dessous, corriger tout ce qui relève du réflexe, puis seulement coder.

L'ouverture de la page montre la chose la plus caractéristique du sujet : un résultat, une carte, un visage, une interaction. Pas une rangée de gros chiffres par défaut.

## Les automatismes à éviter

Ces procédés sont les marques les plus fréquentes d'une page générée. Chacun est autorisé une seule fois par page, et seulement s'il porte une information.

| Automatisme | Ce qu'on fait à la place |
|---|---|
| Un mot du titre en couleur ou en italique | Un titre entièrement composé dans la même couleur ; la force vient de la phrase. Le rouge reste réservé au filet de l'en-tête. |
| Une étiquette en capitales au-dessus de chaque bloc | Une étiquette seulement quand elle apporte une information absente du titre (source, date, unité). Écrite en petites capitales ou en bas de casse, jamais sur toutes les sections. |
| Une rangée de quatre gros chiffres en ouverture | Un ou deux chiffres intégrés à une phrase, ou un graphique qui les montre. |
| Des numéros 01, 02, 03 sur des blocs qui ne forment pas une suite | Des numéros uniquement pour une vraie séquence (étapes d'une méthode, tours de scrutin). |
| Des cartes identiques, encadrées, pour tout | Des filets et des alignements ; un encadré seulement pour l'élément qui doit se détacher. |
| Des phrases à tiret long, des formules « non pas X, mais Y » | Des phrases courtes, à la voix active, comme un journaliste qui explique. |

## Direction esthétique

Le ton est celui de la presse d'analyse haut de gamme. La densité d'information prime ; le design sert le contenu.

- **Sobriété** : pas d'ombre portée, pas de dégradé décoratif, pas de coins arrondis au-delà de 2px.
- **Hiérarchie par les filets** : la structure se crée par des filets fins (1px) et trois niveaux de fond (`--bg`, `--bg-card`, `--bg-sidebar`).
- **Transitions courtes** : 0,15s au plus, fonctionnelles uniquement. Les barres de résultats peuvent s'animer en 0,6s quand une donnée change.
- **Espace blanc contrôlé** : le contenu respire sans flotter.

**INTERDIT** : dégradés décoratifs, box-shadow, border-radius > 2px sur les composants, animations spectaculaires, fonds colorés vifs, emoji, polices génériques (Inter, Roboto, Arial, Poppins, Montserrat, Space Grotesk).

**SIGNATURE VISUELLE** : un filet rouge de 3px sous l'en-tête. C'est le seul usage décoratif du rouge.

## Tokens de design

Utiliser ces variables CSS systématiquement. Ne jamais coder une couleur en dur, sauf les couleurs partisanes dans les visualisations. Chaque token est d'abord défini sur `:root` (thème clair), puis redéfini pour le thème sombre dans `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { … } }` et dans `:root[data-theme="dark"]`.

```css
:root {
  --bg:            #FAFAF8;   /* Fond de page */
  --bg-card:       #FFFFFF;   /* Cartes, en-tête, conteneurs */
  --bg-sidebar:    #F2F2EE;   /* Panneaux latéraux, barre de source */
  --bg-hover:      #EEEEE9;   /* Survol */
  --border:        #DDDDD6;   /* Séparation standard (1px) */
  --border-mid:    #B8B8B0;   /* Éléments interactifs */
  --border-dark:   #2B2B2B;   /* Délimitation forte */
  --text:          #1A1A1A;
  --text-secondary:#595959;
  --text-muted:    #85857D;   /* Métadonnées ; assez contrasté pour l'accessibilité */
  --accent:        #1B3F7B;   /* Boutons, liens, onglets actifs */
  --accent-light:  #EEF2FA;
  --red:           #B01E28;   /* Filet de l'en-tête, alertes */
  --red-light:     #FAF0F1;
  --green-leg:     #1A7A4C;   /* Adopté, hausse */
  --green-light:   #EDFAF3;
  --amber-com:     #C27F20;   /* En cours d'examen */
  --amber-light:   #FFF8ED;
  --font-serif:    'Playfair Display', Georgia, 'Times New Roman', serif;
  --font-sans:     'DM Sans', system-ui, -apple-system, sans-serif;
  --font-mono:     'JetBrains Mono', 'Courier New', monospace;
}
```

### Couleurs partisanes

Uniquement dans les visualisations, jamais pour l'interface. En thème sombre, éclaircir les couleurs trop foncées (RN, LR, Reconquête) pour qu'elles restent lisibles.

```
LFI          #E8333A      PS / PP      #ED6F8B      EELV        #00A86B
DVG          #C75B7A      PCF          #B5121B      MoDem       #FF8C42
Renaissance  #3366CC      Horizons     #5B8FBF      LR          #1B3A6B
RN           #0A1833      Reconquête   #6B3A1F      DVD         #6B8EB5
Abstention   #B8B8B0
```

## Typographie

Trois voix, attribuées selon une règle fixe.

- **Playfair Display** (titres h1 et h2, marque de l'en-tête) : graisse 900 pour h1, 700 pour h2, `letter-spacing: -0.02em`, `text-wrap: balance`. Jamais pour le corps du texte ou les boutons.
- **JetBrains Mono** (chiffres isolés, pourcentages, codes) : `font-variant-numeric: tabular-nums` dès que des chiffres s'alignent en colonne.
- **DM Sans** (tout le reste) : corps 14 à 16px, interligne 1,6, graisses 400, 500 et 600.

Lignes de texte courant limitées à environ 65 caractères (`max-width: 65ch`).

## Photographies des personnalités

Un visage aide le lecteur à reconnaître un candidat plus vite qu'un nom. On l'utilise pour les principaux candidats ou têtes de liste, jamais pour décorer.

- **Source libre de droits obligatoire** : Wikimedia Commons (licences CC0, CC BY, CC BY-SA, domaine public) ou photothèques institutionnelles réutilisables avec mention (Parlement européen, Assemblée nationale). Ne jamais reprendre une photo de presse, d'un site de parti ou d'un réseau social sans licence.
- **Crédit visible** pour chaque photo, dans la barre de source ou une note : auteur, licence, lien vers la licence.
- **Traitement identique pour tous** : même cadrage (carré, du haut du crâne au haut des épaules), même taille, noir et blanc. Aucun candidat ne doit être avantagé par une meilleure photo.
- **Seuil explicite** : afficher les photos des candidats au-dessus d'un seuil clair (par exemple 5 % des exprimés) et le dire dans la méthode.
- **Fichiers locaux** : les images sont publiées avec la page (le CSP des Artifacts bloque les images externes), en JPEG d'environ 240px et 10 Ko.
- Toujours un texte alternatif : « Portrait de Jordan Bardella ».

## Architecture de page

### Ordinateur (≥ 768px)

En-tête de 52px sur `--bg-card`, filet rouge de 3px, puis soit une colonne éditoriale unique (pages narratives, simulateurs), soit une colonne latérale de 300px et une zone principale (tableaux de bord). Choisir selon la tâche, pas par habitude.

### Téléphone (< 768px)

En-tête de 48px, gouttière latérale d'au moins 16px (`padding-left: max(16px, env(safe-area-inset-left, 0px))`), tout sur une colonne. Une barre d'onglets en bas seulement si la page a plusieurs vues distinctes. Aucun défilement horizontal de la page ; seuls les tableaux et graphiques larges défilent dans leur propre conteneur.

Pour un outil interactif sur téléphone :
- **Garder le résultat visible.** Quand les réglages sont loin du résultat, une barre fixée en bas de l'écran (translucide, filet supérieur) rappelle le résultat principal et apparaît seulement quand le résultat complet est hors de l'écran.
- **Des rangées de choix qui défilent au doigt** (`overflow-x: auto`, `scroll-snap-type`) plutôt qu'une pile de boutons.
- **Des cibles adaptées au toucher** sous `@media (pointer: coarse)` : curseurs de 24 px, boutons d'au moins 40 px de haut, pas d'état de survol qui reste affiché.
- **Des graphiques redessinés pour la largeur**, avec des textes plus grands, au lieu d'un graphique d'ordinateur qu'il faut faire glisser.
- **Des chiffres qui glissent vers leur nouvelle valeur** (0,4 s environ), désactivés si le visiteur a demandé moins d'animations.

## Composants de référence

- **Barres horizontales** : hauteur 6px, piste `--bg-sidebar`, remplissage dans la couleur partisane ; nom à gauche (DM Sans 500, 12px), valeur à droite (JetBrains Mono 600, 12px). Un trait vertical fin marque la valeur de référence (résultat officiel, moyenne).
- **Donut** : SVG pur avec `stroke-dasharray`, épaisseur 18 à 20px, légende à pastilles carrées de 10px.
- **Hémicycle** : SVG, sièges en `<circle>` de rayon 2,8px, `viewBox="0 0 320 140"`.
- **Timeline législative** : ligne verticale de 1px, points de 10px colorés selon l'état (fait : vert ; en cours : accent ; à venir : bordure).
- **Encart d'alerte** : fond clair et filet gauche de 3px dans la couleur sémantique (ambre, rouge, vert, accent).
- **Carte électorale** : SVG des contours projetés, traits fins dans la couleur du fond pour séparer les unités, limites communales en trait plus foncé. Toujours une fiche de détail au survol et au toucher.
- **Point info** (à la place d'une section « Méthode » en bas de page) : un « i » cerclé suivi d'une question simple (« D'où vient le point de départ ? », « Comment ce score est-il calculé ? »), placé juste sous l'élément qu'il explique. Il déplie un encadré qui donne, dans cet ordre : l'explication en langage courant, un exemple de calcul avec de vrais chiffres, les limites, puis la source précise. Utiliser `<details>` et `<summary>` : accessible au clavier, sans script.
- **Barre de source** : toujours en pied de page, au format `Source : [organisme] via [canal] — [mention]`, crédits photo compris.

## Conventions éditoriales

- **Ministères** : majuscule au nom propre qui suit, minuscule à « ministère » hors début de phrase : « le ministère des Finances », « le ministère de l'Intérieur ».
- **Institutions** : « l'Assemblée nationale », « le Sénat », « le Haut Conseil pour le climat ».
- **Sigles** : capitales sans points (SNBC, PPE, RN, LFI).
- **Chiffres** : espace insécable comme séparateur de milliers (« 1 247 communes »), virgule décimale (« 32,4 % »), espace insécable avant « % ». Les écarts de pourcentages s'écrivent en points (« +2,1 pts »).
- **Vocabulaire électoral précis** : « participation » ou « mobilisation » pour la part d'inscrits qui votent ; « choix des candidats » ou « vote » pour la répartition des voix. Ne jamais employer « voter comme » quand on ne précise pas lequel des deux on vise.
- **Ton** : écrire comme on l'expliquerait à un voisin curieux, à la deuxième personne quand le lecteur agit (« faites voter davantage une génération »). Pas de jargon sans traduction immédiate (« calage itératif » vient après l'explication, jamais avant).
- **Titres** : affirmatifs ou interrogatifs, jamais descriptifs (« Qui va gagner le second tour ? » plutôt que « Résultats de la simulation »).
- **Neutralité** : même traitement graphique et rédactionnel pour toutes les forces politiques ; les estimations sont présentées avec leurs marges d'erreur.

## Ce qu'on ne fait pas

- **Ne pas utiliser le Système de design de l'État (DSFR)** ni la police Marianne ou le bloc-marque de la République : leur usage est interdit en dehors des sites de l'État en .gouv.fr, y compris pour les collectivités territoriales.
- Ne pas imiter la charte d'un parti, d'un média ou d'une institution existante.

## Stack technique

- **Par défaut** : HTML, CSS et JavaScript sans framework, données dans un fichier séparé (`donnees.js`) chargé avant le script principal. React (UMD depuis cdnjs, version épinglée) seulement si l'interface a beaucoup d'états imbriqués.
- **Dataviz** : SVG pur pour les graphiques courants. Bibliothèque externe seulement pour une complexité forte (d3-sankey pour un Sankey).
- **Polices** : Google Fonts (Playfair Display 700 et 900, DM Sans 400 à 600, JetBrains Mono 500 à 700), avec des polices de repli.
- **Accessibilité** : focus clavier visible, `prefers-reduced-motion` respecté, contrastes suffisants dans les deux thèmes, texte alternatif sur toute image.

## Vérification avant livraison

1. ☐ Le plan de design est écrit en commentaire et ancré dans le sujet.
2. ☐ Chaque automatisme du tableau apparaît au plus une fois, et seulement s'il porte une information.
3. ☐ Toutes les couleurs passent par des variables, définies pour les deux thèmes.
4. ☐ Titres en Playfair Display, chiffres en JetBrains Mono, reste en DM Sans.
5. ☐ Aucune ombre, aucun arrondi supérieur à 2px.
6. ☐ Le filet rouge de 3px est présent sous l'en-tête.
7. ☐ Photos : licence libre, crédit visible, traitement identique, texte alternatif.
8. ☐ Barre de source présente, crédits photo compris.
9. ☐ Espaces insécables, virgules décimales, casse des ministères.
10. ☐ Vocabulaire électoral précis (participation et choix distingués).
11. ☐ Affichage vérifié sur téléphone, sans défilement horizontal.
