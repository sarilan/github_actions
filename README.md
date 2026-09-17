# Relais — livrables de lancement

Relais est un service de mandataire administratif à distance pour les parents âgés restés en France, vendu à leurs enfants expatriés. Ce dépôt contient tout ce qui a été produit à partir du document de cadrage [`relais-document-projet.md`](relais-document-projet.md) (source de vérité : offre, tarifs, exclusions, ton, promesse) : documents juridiques, page d'atterrissage, campagne Google Ads, procédures, base Airtable, classification du courrier, rapport mensuel, fiche de poste, courriels.

Tout est en français, sans identifiant ni clé dans le dépôt (`.env.example` liste les variables d'environnement). Les seuls champs laissés ouverts sont les mentions juridiquement variables, balisées `{{VARIABLE}}` et listées plus bas.

## Arborescence

```
.
├── README.md                      ← ce fichier
├── relais-document-projet.md      ← document de cadrage
├── requirements.txt / .env.example / tests.sh
├── juridique/
│   ├── mandat-administratif.docx, cgv.docx, politique-confidentialite.docx
│   ├── registre-traitements-rgpd.xlsx
│   ├── generate.py (docx depuis sources/*.md) · registre.py (xlsx)
│   └── sources/*.md
├── site/index.html                ← landing page autonome
├── ads/
│   ├── campagne-google-ads.csv · mots-cles-negatifs.csv
│   ├── build.py (génère les CSV) · check.py (contrôle) · README.md
├── procedures/                    ← 00-modele.md, 01 à 12, index.md
├── outils/
│   ├── airtable/  schema.json · create_base.py · seed.py · airtable_client.py · mock_api.py · tests/
│   ├── courrier/  classify.py · rules.yaml · README.md · tests/ (corpus de 32 courriers)
│   └── rapport/   template-rapport-mensuel.docx · build_template.py · generate_report.py · tests/
├── rh/fiche-poste-operateur.docx  (+ generate.py, sources/)
└── emails/                        ← 01 à 08 + sequence.md
```

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # puis renseigner les valeurs
# OCR et conversion PDF (facultatifs mais recommandés) :
sudo apt install tesseract-ocr tesseract-ocr-fra poppler-utils libreoffice-writer
```

Python 3.11 ou plus récent.

## Lancer chaque chose

| Livrable | Commande | Résultat |
|---|---|---|
| 1. Juridique | `python3 juridique/generate.py` | Régénère et vérifie les 3 docx (articles numérotés, encadré avocat, en-tête, pagination). `--check` vérifie seulement. |
| 1. Registre RGPD | `python3 juridique/registre.py` | Régénère et vérifie `registre-traitements-rgpd.xlsx` (5 traitements, colonnes CNIL). |
| 2. Landing page | ouvrir `site/index.html` | Remplacer les `{{VARIABLES}}` avant mise en ligne ; validation : voir « Scores ». |
| 3. Google Ads | `python3 ads/build.py && python3 ads/check.py` | Régénère et contrôle les CSV d'import ; procédure d'import dans `ads/README.md`. |
| 4. Procédures | lire `procedures/index.md` | 12 fiches Markdown. |
| 5. Airtable | `python3 outils/airtable/create_base.py [--dry-run]` puis `python3 outils/airtable/seed.py` | Crée la base « Relais — Gestion » (idempotent) et insère 2 dossiers fictifs. Les 6 vues sont à créer à la main ou via le connecteur Airtable : le script imprime filtre, tri et regroupement de chacune. |
| 6. Courrier | `python3 outils/courrier/classify.py fichier.pdf --pretty [--airtable --client "Durand — Sarcelles"]` | JSON de classification ; création du courrier et de la démarche dans Airtable en option. Détails : `outils/courrier/README.md`. |
| 7. Rapport | `python3 outils/rapport/generate_report.py --client "Durand — Sarcelles" --mois 2026-09` | `rapport-durand-sarcelles-2026-09.docx` et `.pdf` dans `outils/rapport/sorties/`. `build_template.py` régénère le modèle. |
| 8. Fiche de poste | `python3 rh/generate.py` | Régénère et vérifie `rh/fiche-poste-operateur.docx`. |
| 9. Courriels | lire `emails/sequence.md` | 8 courriels prêts à personnaliser. |
| Tests | `./tests.sh` | Tous les tests, la couverture du classificateur et les contrôles de conformité. |

## Variables à remplir

Les balises `{{VARIABLE}}` sont volontaires : elles correspondent aux mentions qui dépendent de la société, de ses prestataires ou du dossier. Rien d'autre n'est laissé « à compléter ».

### Société et documents juridiques (à remplir une fois, dans les sources Markdown puis régénérer)

| Variable | Où | Contenu |
|---|---|---|
| `MANDATAIRE_RAISON_SOCIALE`, `MANDATAIRE_FORME_JURIDIQUE`, `MANDATAIRE_CAPITAL`, `MANDATAIRE_VILLE_RCS`, `MANDATAIRE_SIREN`, `MANDATAIRE_TVA`, `MANDATAIRE_ADRESSE`, `MANDATAIRE_REPRESENTANT`, `MANDATAIRE_QUALITE_REPRESENTANT` | mandat, CGV, politique, registre, site, fiche de poste | Identité de la société exploitant Relais (SAS existante ou structure dédiée). |
| `MANDATAIRE_EMAIL`, `MANDATAIRE_TELEPHONE` | mandat, CGV, courriels, rapport (`.env`) | Coordonnées de contact du service. |
| `LIGNE_2FA_RELAIS`, `EMAIL_2FA_RELAIS` | mandat, procédure 01 | Ligne téléphonique et adresse dédiées à la réception des codes de vérification. |
| `ASSUREUR_RC_PRO`, `NUMERO_POLICE_RC_PRO` | mandat, CGV | Assurance responsabilité civile professionnelle. |
| `MEDIATEUR_NOM`, `MEDIATEUR_ADRESSE`, `MEDIATEUR_SITE` | CGV | Médiateur de la consommation choisi. |
| `DATE_CGV`, `DATE_POLITIQUE`, `DATE_FICHE_POSTE` | CGV, politique, fiche de poste | Dates de version. |
| `DPO_EMAIL` | politique, registre, courriel 08 | Adresse du référent protection des données. |
| `AIRTABLE_ENTITE`, `AIRTABLE_HEBERGEMENT`, `BITWARDEN_ENTITE`, `BITWARDEN_HEBERGEMENT`, `SERVICE_SCAN_NOM`, `SERVICE_SCAN_HEBERGEMENT`, `TELEPHONIE_NOM`, `TELEPHONIE_HEBERGEMENT`, `MESSAGERIE_NOM`, `MESSAGERIE_HEBERGEMENT`, `PAIEMENT_NOM`, `PAIEMENT_HEBERGEMENT`, `FORMSPREE_ENTITE`, `FORMSPREE_HEBERGEMENT` | politique, registre | Entité juridique et pays d'hébergement de chaque sous-traitant (à confirmer avec les contrats de sous-traitance). |
| `SITE_URL` | site, ads, CGV, politique, mandat, courriels | URL du site sans barre oblique finale. |
| `EMAIL_RECRUTEMENT` | fiche de poste | Adresse de réception des candidatures. |

### Site (`site/index.html`)

`SITE_URL`, `FORMSPREE_ENDPOINT` (URL du formulaire Formspree), `CONTACT_EMAIL`, `TELEPHONE_AFFICHE` (avec espaces insécables), `TELEPHONE_LIEN` (format `+33…`), `URL_CGV`, `URL_CONFIDENTIALITE`, `URL_MANDAT` (PDF publiés), `HEBERGEUR_NOM`, `HEBERGEUR_ADRESSE`, et les mentions `MANDATAIRE_*` ci-dessus. Le Google Tag et la conversion Google Ads restent commentés tant qu'aucun bandeau de consentement n'est en place (identifiants `AW-XXXXXXXXXX` à remplacer à ce moment-là).

### Google Ads (`ads/`)

`SITE_URL`, `TELEPHONE_RELAIS` (extension d'appel, format international). Modifier dans `build.py` puis relancer `build.py` et `check.py`.

### Courriels (`emails/`) : champs remplis à chaque envoi

Prénoms et coordonnées (`PRENOM_ENFANT`, `PRENOM_PARENT`, `NOM_PARENT`, `CIVILITE`, `FILS_OU_FILLE`, `IL_OU_ELLE`, `PRENOM_FONDATEUR`, `PRENOM_OPERATEUR`, `TELEPHONE_ENFANT`, `TELEPHONE_PARENT`, `TELEPHONE_OPERATEUR`, `VILLE_ENFANT`, `VILLE_PARENT`, `FUSEAU_ENFANT`), dates et heures (`DATE_APPEL`, `HEURE_APPEL`, `HEURE_APPEL_PARIS`, `DATE_APPEL_PARENT`, `HEURE_APPEL_PARENT`, `DATE_APPEL_DEMARRAGE`, `DATE_APPEL_TRIMESTRIEL`, `DATE_RAPPORT_DIAGNOSTIC`, `DATE_PREMIER_RAPPORT`, `DATE_RESTITUTION`, `HEURE_RESTITUTION`, `DATE_LIMITE`, `DATE_DOCUMENT`, `DATE_REPONSE_SOUHAITEE`, `DELAI_RELANCE`, `MOIS_LIBELLE`, `CRENEAU`, `HORAIRES_LIGNE`), contenu (`DEMARCHE`, `OFFRE`, `MODE_COURRIER`, `LISTE_PIECES_DEMANDEES`, `RESUME_SITUATION`, `LISTE_OK`, `LISTE_ANOMALIES`, `LISTE_DROITS`, `LISTE_DECISIONS`, `LISTE_ACTIONS_PARENT`, `POINT_URGENT_OU_AUCUN`, `NB_ORGANISMES`, `NB_ANOMALIES`, `MONTANT_DROITS`, `NB_REALISEES`, `NB_EN_COURS`, `RESUME_LIGNE_1` à `3`, `LISTE_REALISEES_COURTE`, `LISTE_EN_COURS_COURTE`, `LISTE_DECISIONS_OU_AUCUNE`, `LISTE_ECHEANCES_COURTE`, `RESUME_CONTACTS_PARENT`, `MONTANT_MOIS`, `MONTANT_CUMUL`, `OBJET_URGENCE`, `DESCRIPTION_COURRIER`, `ORGANISME`, `EXPLICATION_SIMPLE`, `ACTIONS_DEJA_FAITES`, `ACTION_1` à `3`, `QUI_1` à `3`, `SI_PAIEMENT`, `MONTANT`, `BENEFICIAIRE`, `REFERENCE`, `DECISION_OU_DOCUMENT_ATTENDU`, `ETAT_PARENT`, `CONTEXTE_DERNIER_ECHANGE`, `PLACES_RESTANTES`), liens (`LIEN_RESERVATION`, `LIEN_VISIO`, `LIEN_ESPACE_PARTAGE`, `LIGNE_PARENT`, `URL_CONFIDENTIALITE`).

### Variables d'environnement (`.env`)

`AIRTABLE_API_KEY`, `AIRTABLE_WORKSPACE_ID`, `AIRTABLE_BASE_ID` (ou fichier `outils/airtable/.base_id` écrit par `create_base.py`), `FORMSPREE_ENDPOINT`, `SITE_URL`, `MANDATAIRE_EMAIL`, `MANDATAIRE_TELEPHONE`.

## Actions qui restent humaines

1. **Relecture par un avocat** du mandat, des CGV, de la politique de confidentialité et du registre (chaque document porte l'encadré « Document à faire valider par un avocat avant utilisation ») ; analyse d'impact RGPD à réaliser avant le premier client (données de santé de personnes vulnérables) ; contrats de sous-traitance (article 28) à signer avec Airtable, Bitwarden, le service de scan, la téléphonie, la messagerie, le paiement, Formspree.
2. **Assurance responsabilité civile professionnelle** : devis, souscription, report du nom de l'assureur et du numéro de police dans les documents.
3. **Boîte postale de traitement du courrier** (service de domiciliation avec scan quotidien, hébergement UE) et mise en place des sous-adresses par client.
4. **Numéro de téléphone français** (ligne dédiée parents et ligne 2FA) et adresse électronique dédiée aux codes de vérification.
5. **Compte Formspree** : créer le formulaire, reporter l'URL dans `site/index.html`, activer la réponse automatique (courriel 01).
6. **Hébergement du site**, nom de domaine (relais-admin.fr, monrelais.fr, relais-parents.fr à vérifier), publication des PDF juridiques et image Open Graph (`og-image.png`).
7. **Compte Airtable** : jeton d'accès personnel avec les portées `schema.bases:read`, `schema.bases:write`, `data.records:read`, `data.records:write`, identifiant de l'espace de travail ; exécution de `create_base.py` puis création des 6 vues (l'API ne permet pas de créer des vues) ; suppression des 2 dossiers fictifs avant la production.
8. **Compte Google Ads** : import des CSV dans Google Ads Editor, action de conversion, réglages manuels et lancement (`ads/README.md`) ; l'activation de la mesure suppose un bandeau de consentement sur le site.
9. **Coffre Bitwarden Teams** : création des collections, invitation des opérateurs, journal d'accès.
10. **Choix du médiateur de la consommation** et adhésion ; **choix du référent protection des données**.
11. **Vérification annuelle des barèmes** cités dans les procédures (CSS, réversion, taxe foncière, APA, capital décès, tarifs La Poste), chaque 1er janvier et 1er avril.
12. **Contrôle des sources officielles** : les fiches de procédure citent les pages de service-public.fr, ameli.fr, info-retraite.fr, impots.gouv.fr, ants.gouv.fr, caf.fr et pour-les-personnes-agees.gouv.fr avec une date de consultation ; depuis l'environnement de génération, ces sites n'étaient pas accessibles directement (accès réseau restreint) et les contenus ont été vérifiés par recherche documentaire. Une relecture de chaque fiche face à la page officielle est à faire avant la formation des opérateurs.

## Scores et résultats des tests (16 septembre 2026)

| Contrôle | Résultat |
|---|---|
| `juridique/generate.py` | 3 docx conformes : 14, 18 et 12 articles, encadré, en-tête, pagination |
| `juridique/registre.py` | xlsx conforme : 5 traitements, 20 colonnes |
| `site/index.html` — Nu HTML Checker (vnu 24) | 0 erreur (variables substituées par des valeurs d'exemple) |
| `site/index.html` — html-validate | 0 erreur |
| `site/index.html` — Lighthouse 12, mobile | Performance 99, Accessibilité 100, Bonnes pratiques 96, SEO 100 |
| `site/index.html` — Lighthouse 12, ordinateur | Performance 100, Accessibilité 100, Bonnes pratiques 96, SEO 100 |
| `site/index.html` — largeur | Aucun débordement horizontal à 320 px et 390 px ; poids 47 Ko |
| `ads/check.py` | Conforme : 1 campagne, 4 groupes, 96 lignes de mots-clés, 60 titres, 16 descriptions, 4 liens annexes, 4 accroches, 1 extrait structuré, 1 extension d'appel, 94 négatifs |
| `outils/airtable/tests` | 23 tests, tous passés |
| `outils/courrier/tests` | 95 tests, tous passés ; couverture de `classify.py` : 98 % |
| `outils/rapport/tests` | 11 tests, tous passés (PDF via LibreOffice) |
| `rh/generate.py` | docx conforme : 8 sections, 2 annexes, 3 courriers |
| Placeholders | Aucun `TODO` ni « à compléter » ; seules les `{{VARIABLES}}` listées ci-dessus |

Le seul point « Bonnes pratiques » perdu par Lighthouse vient d'une erreur de certificat sur la police Google Fonts, propre au réseau de l'environnement de test. Les scores s'entendent sur la page servie localement ; les revérifier une fois le site hébergé.

Pour tout relancer : `./tests.sh`.
