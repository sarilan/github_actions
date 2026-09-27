# Site public de Relais

Le site est construit par `site/build.py` dans le dossier `dist/`, puis publié sur **Cloudflare** (Workers avec ressources statiques, offre gratuite, usage commercial autorisé).

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
| `SITE_URL` | `https://relais-parents.ilansarfati-paris.workers.dev`, puis le domaine propre une fois acheté |
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
| `STRIPE_LIEN_ABONNEMENT`, `STRIPE_LIEN_FONDATEUR` | bouton « Réserver un appel » seul | boutons « S'abonner » vers les liens de paiement Stripe (le lien fondateur suppose le lien normal) |
| `STRIPE_LIEN_DIAGNOSTIC`, `_HOSPITALISATION`, `_EHPAD`, `_SUCCESSION`, `_DEMARCHE` | forfaits affichés sans bouton | bouton « Commander » sur chaque forfait (les 5 ensemble) |
| `STRIPE_PORTAIL_CLIENT` | lien absent | lien « Gérer mon abonnement » dans le pied de page |

## Publier sur Cloudflare (Workers, ressources statiques)

Le projet Cloudflare `relais-parents` est un Worker sans code serveur qui sert le dossier `dist/`. Sa configuration est versionnée dans `wrangler.jsonc` à la racine du dépôt (nom, dossier `dist`, page 404, barres obliques finales). Les en-têtes de `dist/_headers` s'appliquent comme sur Pages.

Réglages du projet (Workers & Pages → `relais-parents` → Paramètres → Build) :

| Champ | Valeur |
|---|---|
| Dépôt Git | `sarilan/github_actions` |
| Branche de production | `claude/gallant-wozniak-a7exic` |
| Commande de build | `python3 site/build.py` |
| Commande de déploiement | `npx wrangler deploy` (déploie le Worker `worker/index.js` et le dossier `dist/`) |
| Répertoire racine | vide (racine du dépôt) |
| Variable de build | `SKIP_DEPENDENCY_INSTALL` = `1` (le build n'a besoin d'aucune dépendance) |

Chaque commit sur la branche de production reconstruit et republie le site. L'adresse publique est `https://relais-parents.<sous-domaine du compte>.workers.dev` (affichée dans l'onglet **Domaines** du projet) : la reporter dans `SITE_URL`.

Vérification locale de la configuration : `python3 site/build.py && npx wrangler deploy --dry-run`.

### Domaine propre (plus tard)

Acheter le domaine dans Cloudflare (**Domain Registration**), l'ajouter au projet (**Domaines → Ajouter un domaine personnalisé**), puis remplacer `SITE_URL` par `https://www.le-domaine.fr`. Le build ajoute alors automatiquement un en-tête `noindex` sur les adresses techniques `*.workers.dev` et `*.pages.dev` pour éviter le contenu en double.

## Stripe

À l'activation du compte, indiquer l'adresse du site (`SITE_URL`). Stripe y vérifie la description du service, les prix, un moyen de contact et les conditions de vente, de résiliation et de rétractation : tout est présent sur la page d'accueil et dans `/cgv/`.

### Liens de paiement à créer (Stripe → Catalogue de produits, puis Liens de paiement)

| Produit | Prix | Type | Réglages du lien | Clé de `config.json` |
|---|---|---|---|---|
| Abonnement Relais | 89 € | récurrent, mensuel | — | `STRIPE_LIEN_ABONNEMENT` |
| Abonnement Relais — tarif fondateur | 59 € | récurrent, mensuel (second prix du même produit) | limiter à 10 paiements | `STRIPE_LIEN_FONDATEUR` |
| Diagnostic initial | 149 € | paiement unique | — | `STRIPE_LIEN_DIAGNOSTIC` |
| Forfait Hospitalisation | 490 € | paiement unique | — | `STRIPE_LIEN_HOSPITALISATION` |
| Forfait Entrée en EHPAD ou résidence | 690 € | paiement unique | — | `STRIPE_LIEN_EHPAD` |
| Forfait Succession (volet administratif) | 890 € | paiement unique | — | `STRIPE_LIEN_SUCCESSION` |
| Démarche isolée | 79 € | paiement unique | — | `STRIPE_LIEN_DEMARCHE` |

Réglages communs à chaque lien : collecter l'adresse de facturation et le numéro de téléphone ; après le paiement, rediriger vers `SITE_URL/merci/` ; exiger l'acceptation des conditions (renseigner d'abord l'adresse `SITE_URL/cgv/` dans Paramètres → Détails publics). Portail client (Paramètres → Portail client) : activer la résiliation et la mise à jour du moyen de paiement, puis copier le lien de connexion dans `STRIPE_PORTAIL_CLIENT`.

### Liens créés (27 septembre 2026, compte Stripe en mode réel)

Le paiement se fait **après l'appel de présentation** : les liens ci-dessous sont envoyés dans le courriel 03 (`{{LIEN_PAIEMENT}}`), et les clés `STRIPE_LIEN_*` de `config.json` restent vides pour que la page d'accueil ne propose que « Réserver un appel ». Seul le portail client est publié (pied de page).

| Offre | Lien | Réglages |
|---|---|---|
| Abonnement 89 €/mois | https://buy.stripe.com/28E6oHavabaIb8r5INc7u00 | produit `relais_abonnement` |
| Tarif fondateur 59 €/mois | https://buy.stripe.com/fZu28r46M2Ec2BV1sxc7u01 | limité à 10 paiements, message de fin d'offre |
| Diagnostic initial 149 € | https://buy.stripe.com/aFa3cv46MdiQccv7QVc7u02 | facture PDF |
| Hospitalisation 490 € | https://buy.stripe.com/28E3cv32Ia6E90jb37c7u03 | facture PDF |
| Entrée en EHPAD ou résidence 690 € | https://buy.stripe.com/eVqeVdgTy6Us7Wf0otc7u04 | facture PDF |
| Succession 890 € | https://buy.stripe.com/eVq6oH1YE1A85O7gnrc7u05 | facture PDF |
| Démarche isolée 79 € | https://buy.stripe.com/7sY4gz7iY5Qo3FZ5INc7u06 | facture PDF |
| Portail client | https://billing.stripe.com/p/login/28E6oHavabaIb8r5INc7u00 | résiliation en fin de période, carte, factures, coordonnées |

Chaque lien : adresse de facturation et téléphone obligatoires, champ « Votre parent : nom et ville », champ obligatoire « J'accepte les CGV et demande que le service commence tout de suite » (preuve de la demande d'exécution anticipée), redirection vers `/merci/`, métadonnée `offre` pour relier le paiement à la table Prospects. Les forfaits portent le suffixe de relevé `RELAIS`.

Réglages restant à faire dans le tableau de bord Stripe (non disponibles par l'API) : **Paramètres → Détails publics** (nom public « Relais », URL des CGV, courriel et téléphone d'assistance) ; **Paramètres → Libellé de relevé** (`RELAIS`) ; **Paramètres → Facturation → Factures** (pied de page avec raison sociale, SIREN, adresse du siège et mention de TVA retenue, numérotation continue). Après un changement de domaine, mettre à jour la redirection de chaque lien.

## Worker : formulaire et paiements reliés à Airtable

Le Worker `worker/index.js` sert les pages de `dist/` et ajoute deux routes (configuration dans `wrangler.jsonc`) :

| Route | Rôle | En cas de problème |
|---|---|---|
| `POST /api/demande` | Le formulaire « Réserver un appel » crée une ligne **Demande reçue** dans la table **Prospects** (pays, ville et âge du parent, démarche, courriel, créneau, source, `gclid` Google Ads). | Sans configuration ou si Airtable ne répond pas, la page ouvre la messagerie du visiteur avec la demande rédigée : aucune demande n'est perdue. |
| `POST /api/stripe` | Chaque paiement Stripe (`checkout.session.completed`) retrouve le prospect par son courriel et le passe au statut **Payé** avec la date, le montant, l'offre, les identifiants Stripe et l'accord d'exécution anticipée. Sans prospect connu, une ligne « à vérifier » est créée. | Signature invalide refusée ; en cas d'erreur Airtable, Stripe renvoie la notification plus tard. |

Le point de terminaison Stripe est déjà créé (Développeurs → Webhooks → `…/api/stripe`, événement `checkout.session.completed`). À un changement de domaine, modifier son URL.

### Deux secrets à déclarer une fois

Cloudflare → Workers & Pages → `relais-parents` → Paramètres → **Variables et secrets** → Ajouter, type **Secret** :

1. `AIRTABLE_TOKEN` : Airtable → Builder hub → **Personal access tokens** → Create token ; portées `data.records:read` et `data.records:write` ; accès limité à la base « Relais — Gestion ».
2. `STRIPE_WEBHOOK_SECRET` : Stripe → Développeurs → Webhooks → point de terminaison `…/api/stripe` → **Secret de signature** → Révéler (commence par `whsec_`).

`AIRTABLE_BASE_ID` et `AIRTABLE_TABLE` sont déjà déclarés dans `wrangler.jsonc`. Le déploiement suivant les prend en compte ; vérifier en envoyant une demande test depuis le site, puis la supprimer dans Airtable.

Tests : `cd worker && node --test tests/*.test.js` (14 tests : validation, champ piège, repli, signature Stripe, mise à jour sans recul de statut).

## Image de partage

`site/static/og-image.png` (1200 × 630) est versionnée. Pour la régénérer après un changement de promesse : `python3 site/og_image.py` (nécessite Pillow).

## Tests

```bash
python3 -m pytest site/tests -q
```

Couvrent : substitution des variables et blocs conditionnels, refus de publier quand une valeur manque, aperçu non indexable, numérotation des articles identique aux documents Word (18, 12 et 14 articles), formulaire en mode messagerie ou Formspree, formulations avant et après assurance et médiateur, contrôles de cohérence de la configuration, priorité des variables d'environnement, en-têtes, échappement HTML.
