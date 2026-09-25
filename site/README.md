# Site public de Relais

Le site est construit par `site/build.py` dans le dossier `dist/`, puis publié sur **Cloudflare Pages** (offre gratuite, usage commercial autorisé).

| Adresse | Contenu | Source |
|---|---|---|
| `/` | Page d'accueil : offre, tarifs, sécurité, FAQ, formulaire de premier contact | `site/src/index.html` |
| `/cgv/` | Conditions générales de vente | `juridique/sources/cgv.md` |
| `/confidentialite/` | Politique de confidentialité | `juridique/sources/politique-confidentialite.md` |
| `/mandat/` | Modèle de mandat (imprimable en PDF depuis le navigateur) | `juridique/sources/mandat-administratif.md` |
| `/mentions-legales/` | Éditeur, directeur de la publication, hébergeur | `site/build.py` |
| `/404.html`, `/robots.txt`, `/sitemap.xml`, `/_headers`, `/og-image.png` | Page d'erreur, référencement, en-têtes de sécurité, image de partage | `site/build.py`, `site/static/` |

Les pages juridiques sont produites depuis les mêmes sources Markdown que les documents Word : une correction faite dans `juridique/sources/` (par exemple après la relecture de l'avocat) se retrouve dans les deux après `python3 juridique/generate.py` et `python3 site/build.py`. L'encadré interne « Document à faire valider par un avocat » figure dans les Word mais n'est pas publié sur le site.

## Construire

```bash
python3 site/build.py            # build de publication, dans dist/
python3 site/build.py --apercu   # aperçu local dans dist-apercu/, valeurs manquantes surlignées (non publiable)
python3 -m http.server -d dist 8000   # puis ouvrir http://localhost:8000
```

Le build n'utilise que la bibliothèque standard de Python (3.9 ou plus récent). Il **refuse de publier** tant qu'une valeur obligatoire manque : il affiche la liste et n'écrit rien. Il vérifie ensuite la sortie (aucune variable non résolue, un seul titre par page, aucun lien interne cassé, fichiers techniques présents).

## Renseigner les valeurs : `site/config.json`

Une valeur vide `""` signifie « non renseignée ». Toute clé peut aussi être fournie par une variable d'environnement du même nom (réglage du projet Cloudflare), qui prime sur le fichier.

**Obligatoires** (le build s'arrête sans elles) :

| Clé | Exemple |
|---|---|
| `SITE_URL` | `https://relais-parents.pages.dev`, puis le domaine propre une fois acheté |
| `CONTACT_EMAIL` | adresse affichée sur le site et destinataire des demandes d'appel |
| `MANDATAIRE_RAISON_SOCIALE`, `MANDATAIRE_FORME_JURIDIQUE`, `MANDATAIRE_SIREN` | `NESS ACADEMIE`, `SAS`, `978 575 397` (déjà remplis) |
| `MANDATAIRE_CAPITAL` | `1 000` (sans le symbole €) |
| `MANDATAIRE_VILLE_RCS` | ville du greffe, ex. `Paris` |
| `MANDATAIRE_ADRESSE` | adresse du siège social |
| `MANDATAIRE_REPRESENTANT`, `MANDATAIRE_QUALITE_REPRESENTANT` | nom du dirigeant, `Président` |
| `DATE_CGV`, `DATE_POLITIQUE` | date de version publiée |
| `HEBERGEUR_*`, sous-traitants (`AIRTABLE_*`, `BITWARDEN_*`, `SERVICE_SCAN_*`, `TELEPHONIE_*`, `MESSAGERIE_*`, `PAIEMENT_*`) | déjà remplis ; les prestataires non encore choisis sont indiqués « en cours de sélection », à remplacer par leur nom réel dès le choix fait |

**Facultatives** (le texte s'adapte quand elles sont vides) :

| Clé | Vide | Renseignée |
|---|---|---|
| `MANDATAIRE_EMAIL`, `DPO_EMAIL` | reprennent `CONTACT_EMAIL` | adresses distinctes |
| `MANDATAIRE_TVA` | mention absente | numéro affiché dans les CGV et les mentions légales |
| `TELEPHONE_AFFICHE` + `TELEPHONE_LIEN` | aucun numéro affiché | numéro cliquable (format `+33…` pour le lien) |
| `FORMSPREE_ENDPOINT` + `FORMSPREE_ENTITE` | le formulaire ouvre la messagerie du visiteur avec sa demande déjà rédigée, adressée à `CONTACT_EMAIL` | le formulaire est envoyé sans quitter la page ; Formspree apparaît dans la politique de confidentialité |
| `ASSUREUR_RC_PRO` + `NUMERO_POLICE_RC_PRO` | CGV et mandat : l'attestation est remise avant la signature du mandat | assureur et numéro de police cités |
| `MEDIATEUR_NOM` + `MEDIATEUR_ADRESSE` + `MEDIATEUR_SITE` | CGV : coordonnées du médiateur communiquées avant la conclusion du contrat | médiateur cité ; **obligatoire avant la première vente** (articles L. 612-1 et L. 616-1 du Code de la consommation) |
| `LIGNE_2FA_RELAIS`, `EMAIL_2FA_RELAIS` | mandat : indiqués au parent lors de la signature | cités dans le mandat |

## Publier sur Cloudflare Pages

### Première mise en ligne, sans rien installer (recommandé)

1. Sur dash.cloudflare.com : **Workers & Pages → Créer → Pages → Se connecter à Git**, autoriser GitHub et choisir le dépôt `sarilan/github_actions`.
2. Réglages du build :

   | Champ | Valeur |
   |---|---|
   | Nom du projet | `relais-parents` (donne l'adresse `https://relais-parents.pages.dev`) |
   | Branche de production | `claude/gallant-wozniak-a7exic` |
   | Préréglage du framework | Aucun |
   | Commande de build | `python3 site/build.py` |
   | Répertoire de sortie | `dist` |
   | Variable d'environnement | `SKIP_DEPENDENCY_INSTALL` = `1` (le build n'a besoin d'aucune dépendance) |

3. **Enregistrer et déployer.** Chaque nouveau commit sur la branche republie le site automatiquement.

Si le nom `relais-parents` est déjà pris, Cloudflare en propose un autre : reporter l'adresse obtenue dans `SITE_URL` (fichier ou variable d'environnement du projet), puis relancer un déploiement.

### Alternative : téléversement manuel

Lancer `python3 site/build.py`, puis **Workers & Pages → Créer → Pages → Téléverser des ressources** et déposer le dossier `dist/`. À refaire à chaque modification.

### Domaine propre (plus tard)

Acheter le domaine dans Cloudflare (**Domain Registration**), l'ajouter au projet (**Domaines personnalisés**), puis remplacer `SITE_URL` par `https://www.le-domaine.fr`. Le build ajoute alors automatiquement un en-tête `noindex` sur l'adresse technique `*.pages.dev` pour éviter le contenu en double.

## Stripe

À l'activation du compte, indiquer l'adresse du site (`SITE_URL`). Stripe y vérifie la description du service, les prix, un moyen de contact et les conditions de vente, de résiliation et de rétractation : tout est présent sur la page d'accueil et dans `/cgv/`.

## Image de partage

`site/static/og-image.png` (1200 × 630) est versionnée. Pour la régénérer après un changement de promesse : `python3 site/og_image.py` (nécessite Pillow).

## Tests

```bash
python3 -m pytest site/tests -q
```

Couvrent : substitution des variables et blocs conditionnels, refus de publier quand une valeur manque, aperçu non indexable, numérotation des articles identique aux documents Word (18, 12 et 14 articles), formulaire en mode messagerie ou Formspree, formulations avant et après assurance et médiateur, contrôles de cohérence de la configuration, priorité des variables d'environnement, en-têtes, échappement HTML.
