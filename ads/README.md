# Campagne Google Ads « Relais — Parents France »

Ce dossier contient la structure complète de la campagne de lancement, prête à importer dans Google Ads Editor, ainsi que le plan de test des deux premières semaines.

| Fichier | Rôle |
|---|---|
| `campagne-google-ads.csv` | Campagne, 4 groupes d'annonces, 96 lignes de mots-clés (12 par groupe, en Exact et en Phrase), 4 annonces responsives (15 titres + 4 descriptions chacune), 4 liens annexes, 4 accroches, 1 extrait structuré, 1 extension d'appel. |
| `mots-cles-negatifs.csv` | 94 mots-clés négatifs au niveau de la campagne (expression négative). |
| `build.py` | Reconstruit les deux CSV depuis les données du script (source de vérité des textes). |
| `check.py` | Contrôle les longueurs, le format et les règles éditoriales. Doit passer avant tout import. |

Avant import, remplacer les variables `{{SITE_URL}}` (URL du site, sans barre oblique finale) et `{{TELEPHONE_RELAIS}}` (numéro français au format international, ex. +33612345678) dans les CSV, ou dans `build.py` puis relancer `python3 ads/build.py`.

```bash
python3 ads/build.py     # régénère les CSV
python3 ads/check.py     # doit afficher « Fichiers Google Ads conformes »
```

## Structure de la campagne

- **Campagne** : « Relais — Parents France », type Search, réseau de Recherche uniquement (partenaires du Réseau de Recherche et Réseau Display désactivés), langue française, budget 20 € par jour, stratégie « Maximiser les conversions » sans CPA cible au démarrage, importée **en pause**.
- **Ciblage géographique** : Israël, Suisse, Belgique, Luxembourg, Royaume-Uni, États-Unis, Canada, Émirats arabes unis, Singapour, Hong Kong.
- **Groupes d'annonces** (section 10.1 du document projet, enrichis) :
  1. Intention directe : « aider parents administratif à distance », « service administratif personnes âgées »…
  2. Problème précis : « ma mère n'arrive pas à utiliser ameli », « parent âgé déclaration impôts en ligne »…
  3. Événement de vie : « sortie hospitalisation démarches », « dossier apa comment faire », « entrée ehpad démarches »…
  4. Procuration et mandat : « procuration administrative parent âgé », « mandat administratif personne âgée »…
- **Mots-clés** : chaque expression est déclinée en correspondance exacte et en expression (« phrase match », l'équivalent actuel de l'ancienne expression large modifiée).
- **URL finale** : `{{SITE_URL}}/?utm_source=google&utm_medium=cpc&utm_campaign=relais-parents-france&utm_content=<groupe>&utm_term={keyword}`. `{keyword}` est un paramètre ValueTrack rempli par Google Ads.

## Format du CSV

Le fichier utilise les en-têtes de colonnes en anglais reconnus par Google Ads Editor, quelle que soit la langue de l'interface. Google Ads Editor identifie le type de chaque ligne d'après les colonnes remplies :

| Type de ligne | Colonnes renseignées |
|---|---|
| Campagne | Campaign, Campaign Type, Campaign Status, Budget, Budget type, Networks, Languages, Location, Bid Strategy Type, Ad rotation |
| Groupe d'annonces | Campaign, Ad Group, Ad Group Type, Ad Group Status |
| Mot-clé | Campaign, Ad Group, Keyword, Criterion Type (Exact ou Phrase), Status |
| Annonce responsive | Campaign, Ad Group, Ad type, Headline 1 à 15, Description 1 à 4, Path 1, Path 2, Final URL |
| Lien annexe | Campaign, Sitelink text, Sitelink final URL, Sitelink description 1 et 2 |
| Accroche | Campaign, Callout text |
| Extrait structuré | Campaign, Structured snippet header, Structured snippet values (séparées par « ; ») |
| Extension d'appel | Campaign, Phone number, Country code |

Les pays sont séparés par « ; » dans la colonne Location. Le fichier est encodé en UTF-8 avec BOM pour que les accents s'affichent correctement dans Excel et dans Google Ads Editor.

## Procédure d'import dans Google Ads Editor

1. Ouvrir Google Ads Editor, sélectionner le compte, cliquer sur **Télécharger les modifications récentes** pour partir d'un état à jour.
2. Menu **Compte → Importer → À partir d'un fichier…** et choisir `campagne-google-ads.csv`.
3. Dans la fenêtre de correspondance des colonnes, vérifier que chaque en-tête est associé au bon champ. Si une colonne apparaît comme « Ignorer », la sélectionner manuellement dans la liste déroulante (par exemple « Sitelink text » → *Texte du lien annexe*, « Callout text » → *Texte de l'accroche*, « Structured snippet values » → *Valeurs de l'extrait structuré*).
4. Cliquer sur **Terminer et vérifier les modifications**. Google Ads Editor affiche le nombre de campagnes, groupes, mots-clés, annonces et éléments créés ; corriger les éventuelles erreurs signalées (les erreurs de longueur sont exclues par `check.py`).
5. Répéter l'import avec `mots-cles-negatifs.csv` (type « Negative Phrase » reconnu comme mot-clé négatif au niveau campagne).
6. Vérifier dans l'arborescence : campagne **en pause**, budget 20 €/jour, 4 groupes, 4 annonces responsives avec la mention « Efficacité de l'annonce » au moins « Bonne ».
7. Cliquer sur **Publier** pour envoyer la structure vers le compte. La campagne reste en pause tant qu'elle n'est pas activée dans l'interface Google Ads.

Alternative : le connecteur Ryze AI (Google Ads) peut créer la même structure directement dans le compte, en état pausé, à partir de ces CSV (voir la partie B du brief).

## Réglages à faire à la main dans l'interface Google Ads

Ces réglages ne s'importent pas par CSV.

1. **Action de conversion** : *Objectifs → Conversions → Nouvelle action de conversion → Site web*, nom « Demande d'appel », catégorie « Envoyer un formulaire pour prospect », valeur 100 € (valeur indicative d'un prospect), comptabilisation « Une », fenêtre de conversion 30 jours. Installer le Google Tag et l'événement de conversion dans `site/index.html` aux emplacements commentés, après mise en place d'un bandeau de consentement (aucun cookie n'est déposé au lancement). Sans conversion enregistrée, passer temporairement la stratégie en « Maximiser les clics » avec un CPC max de 3 €.
2. **Exclusions d'emplacements et de réseaux** : dans les paramètres de la campagne, désactiver « Inclure les partenaires du Réseau de Recherche de Google » et « Inclure le Réseau Display ».
3. **Emplacements géographiques** : vérifier que l'option de ciblage est « Présence : personnes situées dans les zones ciblées ou qui s'y rendent régulièrement » et non « Présence ou intérêt ».
4. **Extension d'appel** : vérifier le numéro `{{TELEPHONE_RELAIS}}`, activer le suivi des appels et régler un calendrier d'affichage aux heures ouvrées françaises.
5. **Calendrier de diffusion** : tous les jours, 7 h à 23 h heure de Paris (les clients appellent le soir).
6. **Paramètres de suivi** : vérifier que l'URL finale résout bien vers la page d'atterrissage avec les UTM.
7. **Zones exclues** : exclure la France si des clics locaux non pertinents apparaissent dans les termes de recherche.
8. **Audience** : ajouter en observation (sans ciblage) les segments « Expatriés », « Parents de personnes âgées » et un segment personnalisé sur les requêtes des groupes, pour analyse.

## Plan de test sur deux semaines

Budget : 20 €/jour, soit environ 280 € sur 14 jours, pour 100 à 180 clics attendus (CPC estimé 1,50 à 3 €).

| Jour | Action |
|---|---|
| J0 | Activer la campagne. Vérifier le lendemain que les annonces sont approuvées (statut « Éligible ») et que les impressions démarrent. |
| J1 à J3 | Relire chaque jour le rapport **Termes de recherche**. Ajouter en négatif toute requête hors cible (emploi, formation, tutelle judiciaire, requêtes en anglais, requêtes locales françaises). |
| J4 | Vérifier que la conversion se déclenche (test de formulaire) et que les UTM remontent dans les statistiques. |
| J7 | Premier bilan : CTR par groupe, CPC moyen, taux de conversion. Couper les mots-clés à plus de 30 impressions et CTR < 1 %. |
| J10 | Ajouter les titres et descriptions notés « Faible » dans l'efficacité des annonces. Tester une variante de page si le taux de conversion est < 2 %. |
| J14 | Bilan final selon les règles de décision ci-dessous. Décider du budget du mois suivant. |

## Règles de décision

- **Couper un groupe d'annonces** si son CPA dépasse 200 € après 30 clics, ou s'il n'a produit aucune conversion après 60 clics.
- **Couper un mot-clé** après 30 impressions sans clic, ou 15 clics sans conversion avec un CPC supérieur à 3 €.
- **Augmenter le budget** de 50 % (30 €/jour) si le CPA est inférieur à 120 € sur 10 conversions et que la part d'impressions perdue pour cause de budget dépasse 30 %.
- **Passer en « Maximiser les conversions avec CPA cible »** à 130 € une fois 15 conversions enregistrées sur 30 jours.
- **Mettre la campagne en pause** si le taux de conversion reste inférieur à 1 % après 200 clics : le problème est alors la page ou l'offre, pas les annonces.
- **Ajouter un groupe** à partir des termes de recherche convertissant sans correspondre à un groupe existant, avec ses propres annonces.
