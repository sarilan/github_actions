# Analyse d'impact relative à la protection des données (AIPD) — service Relais

> Document à faire valider par un avocat avant utilisation. Version du 27 septembre 2026, établie selon la méthode de la CNIL (guide « PIA », 2018) et les lignes directrices du CEPD (WP 248). À revoir à chaque changement de prestataire, d'outil ou de périmètre, et au moins une fois par an.

Responsable de traitement : NESS ACADEMIE, SAS au capital de 1 000 €, RCS Paris 978 575 397, exploitant le service « Relais ».
Rédacteur : le président de NESS ACADEMIE. Contact protection des données : ilansarfati.paris@gmail.com (adresse provisoire, à remplacer par l'adresse dédiée du domaine).

## 1. Pourquoi une AIPD est obligatoire

Le CEPD et la CNIL imposent une AIPD lorsqu'un traitement remplit au moins deux des neuf critères de risque. Relais en remplit quatre :

| Critère (WP 248) | Situation Relais |
|---|---|
| Données sensibles ou hautement personnelles | Données de santé (comptes rendus d'hospitalisation, APA, CSS, remboursements), données financières (pensions, relevés, avis d'imposition), identifiants de connexion. |
| Personnes vulnérables | Personnes âgées de 70 à 90 ans, parfois en perte d'autonomie. |
| Traitement à grande échelle ou croisement de données | Centralisation de l'ensemble de la vie administrative d'une personne (santé, retraite, fiscalité, banque, logement). |
| Usage innovant ou nouvelle solution | Classification automatique du courrier par reconnaissance de texte et règles (outil `classify.py`). |

La liste CNIL des traitements soumis à AIPD vise en outre la « gestion des dossiers de personnes vulnérables ». L'AIPD doit être terminée **avant le premier client**.

## 2. Description du traitement

### 2.1 Finalités

1. Gérer les demandes de contact et la relation commerciale avec l'enfant (prospects).
2. Exécuter le mandat de représentation administrative du parent : réception et traitement du courrier, gestion des comptes en ligne, dépôt de demandes et de réclamations, rendez-vous.
3. Rendre compte à l'enfant (rapport mensuel, alertes).
4. Facturer et encaisser.
5. Conserver la preuve des actions réalisées et des consentements.

### 2.2 Personnes concernées et données

| Personnes | Données | Sensibilité |
|---|---|---|
| Enfant (client, prospect) | Identité, courriel, téléphone, pays et fuseau, pièce d'identité, données de paiement (traitées par Stripe, jamais par Relais), historique des échanges | Standard ; pièce d'identité à protéger |
| Parent (bénéficiaire, mandant) | Identité, date de naissance, adresse, téléphone, pièce d'identité, numéros d'organismes (sécurité sociale, fiscal, allocataire), identifiants de connexion, courrier reçu, montants (pensions, factures, aides) | **Élevée** : santé, finances, identifiants, NIR |
| Tiers cités dans le courrier (conjoint, médecin, syndic) | Nom, qualité, coordonnées professionnelles | Faible |
| Opérateurs Relais | Identité, journal d'accès au coffre | Standard |

Le numéro de sécurité sociale (NIR) n'est conservé que lorsqu'il figure sur un document nécessaire à une démarche ; il n'est jamais utilisé comme identifiant dans la base.

### 2.3 Flux et outils

| Étape | Outil | Hébergement | Base de l'encadrement |
|---|---|---|---|
| Formulaire du site | Cloudflare Workers (`/api/demande`) | Réseau mondial Cloudflare | Contrat de sous-traitance Cloudflare, clauses contractuelles types |
| Base de gestion (Prospects, Clients, Organismes, Démarches, Courriers) | Airtable (Formagrid Inc.) | États-Unis | Contrat de sous-traitance Airtable ; vérifier la certification au cadre de protection des données UE–États-Unis (DPF), à défaut clauses contractuelles types |
| Identifiants de connexion | Bitwarden Teams, région UE | Union européenne | Contrat de sous-traitance Bitwarden |
| Courrier papier | Service de domiciliation avec numérisation (à choisir) | Union européenne (condition de sélection) | Contrat de sous-traitance à signer |
| Codes de vérification (2FA) | Ligne téléphonique Relais dédiée (à choisir) | Union européenne (condition de sélection) | Accord écrit du parent dans le mandat |
| Documents partagés avec l'enfant | Espace partagé (à choisir) | Union européenne ; HDS si documents médicaux (question posée à l'avocat) | Contrat de sous-traitance |
| Paiement | Stripe Payments Europe | Union européenne et États-Unis | Contrat Stripe, clauses contractuelles types |
| Courriels | Messagerie professionnelle du domaine (à choisir) ; Airtable pour les accusés de réception automatiques | Union européenne (condition de sélection) ; États-Unis pour Airtable | Contrats de sous-traitance |

## 3. Principes fondamentaux

### 3.1 Bases légales

| Finalité | Base légale (RGPD) |
|---|---|
| Prospects | Mesures précontractuelles à la demande de l'enfant (art. 6.1.b) |
| Exécution du mandat | Exécution du contrat (art. 6.1.b) ; pour les données de santé, **consentement explicite du parent** recueilli dans le mandat (art. 9.2.a), case distincte, retirable à tout moment |
| Rapport à l'enfant | Exécution du contrat ; le parent désigne l'enfant comme Personne de confiance dans le mandat et accepte qu'il reçoive les rapports |
| Facturation | Obligation légale (art. 6.1.c, conservation comptable) |
| Preuves | Intérêt légitime (art. 6.1.f) : se défendre en cas de litige ou de suspicion d'abus de faiblesse |

### 3.2 Minimisation

- Les rapports mensuels à l'enfant mentionnent l'existence et l'issue des démarches de santé, jamais le contenu médical.
- La classification automatique ne conserve que l'organisme, le type, les dates et le montant ; le texte intégral reste dans le scan.
- Aucune donnée bancaire du parent n'est saisie dans la base : seul un montant mensuel indicatif par organisme.
- Les identifiants ne sont jamais dans Airtable, les courriels ou les messageries : uniquement dans le coffre Bitwarden du client.
- Les pièces d'identité sont reçues uniquement par le lien de dépôt sécurisé.

### 3.3 Durées de conservation

| Données | Durée |
|---|---|
| Prospect non converti | 3 ans à compter du dernier contact |
| Dossier client (base active) | Durée du mandat |
| Identifiants | Durée du mandat ; suppression sous 15 jours après la fin |
| Courrier numérisé | Durée du mandat, puis restitution au parent ou à ses ayants droit et suppression sous 3 mois |
| Preuves (mandat, consentements, journal des actions) | 5 ans après la fin du mandat (prescription civile) |
| Factures | 10 ans (Code de commerce) |
| Journal d'accès au coffre | 1 an |

### 3.4 Droits des personnes

Accès, rectification, effacement, limitation, portabilité et opposition : demande à l'adresse de contact, réponse sous un mois. Le parent peut retirer son consentement au traitement des données de santé : les démarches de santé cessent, le reste du mandat continue. À la fin du mandat, rapport de clôture et restitution de tous les documents.

## 4. Risques

Gravité et vraisemblance cotées de 1 (négligeable) à 4 (maximale), avant et après mesures.

| Risque | Sources | Impacts sur le parent | Gravité | Vraisemblance avant | Vraisemblance après |
|---|---|---|---|---|---|
| **Accès illégitime** aux données ou aux comptes | Vol d'identifiants d'un opérateur, hameçonnage, ordinateur perdu, faux appel se présentant comme Relais | Usurpation d'identité, détournement de prestations, divulgation de l'état de santé, arnaque ciblée | 4 | 3 | 1 |
| **Modification non désirée** | Erreur d'opérateur (mauvais dossier), démarche non autorisée, détournement de l'adresse ou du RIB déclarés | Suspension d'une pension ou d'un remboursement, résiliation d'un contrat utile | 3 | 2 | 1 |
| **Disparition** de données ou de courriers | Panne ou fermeture d'un prestataire, perte d'un courrier réexpédié, suppression accidentelle | Délai légal manqué, pénalités, droits perdus | 3 | 2 | 1 |
| **Abus de faiblesse** ou décision prise à la place du parent | Opérateur malveillant, pression d'un membre de la famille | Préjudice financier, perte d'autonomie | 4 | 1 | 1 |

## 5. Mesures

### 5.1 Existantes (outils et documents livrés)

- Mandat excluant toute opération financière et tout acte de disposition, révocable à tout moment, copie à la Personne de confiance.
- Coffre Bitwarden par client, accès nominatifs, double authentification, journal d'accès, révocation immédiate au départ d'un opérateur.
- Traçabilité de chaque action dans la table Démarches, avec preuve jointe.
- Procédure 13 : appel à trois, mot de code contre les faux appels, refus de signature par un tiers, signalement des signes de perte de capacité.
- Site sans cookie ni mesure d'audience ; formulaire protégé par un champ piège ; en-têtes de sécurité (CSP, HSTS) ; notifications Stripe vérifiées par signature.
- Rapport mensuel à l'enfant : double regard familial sur toutes les actions.

### 5.2 À mettre en place avant le premier client

| Mesure | Risque traité | Responsable | Échéance |
|---|---|---|---|
| Signer ou accepter les contrats de sous-traitance (Airtable, Bitwarden, Cloudflare, Stripe, messagerie, domiciliation, téléphonie, espace partagé) | Tous | Ilan | Avant le 1er client |
| Vérifier la certification DPF d'Airtable ou joindre les clauses contractuelles types | Accès illégitime | Ilan | Avant le 1er client |
| Double authentification sur tous les comptes Relais (Airtable, Google, Stripe, Cloudflare, GitHub, Bitwarden) | Accès illégitime | Ilan | Immédiat |
| Chiffrement du disque de chaque poste de travail et verrouillage automatique | Accès illégitime | Ilan, puis opérateurs | Avant le 1er client |
| Trancher la question de l'hébergement HDS pour les documents médicaux ; en attendant, ne pas les conserver dans l'espace partagé | Accès illégitime | Avocat, Ilan | Consultation |
| Trancher l'accès aux espaces bancaires (voir consultation de l'avocat) ; en attendant, aucune redirection des codes bancaires | Accès illégitime, abus | Avocat, Ilan | Consultation |
| Sauvegarde mensuelle chiffrée de la base Airtable (export CSV) et des scans, conservée dans l'UE | Disparition | Ilan | Mensuel |
| Procédure de violation de données : registre des incidents, notification CNIL sous 72 h, information des personnes | Tous | Ilan | Avant le 1er client |
| Clause de confidentialité et formation RGPD de chaque opérateur (fiche de poste) | Accès illégitime, abus | Ilan | À chaque recrutement |
| Double contrôle des démarches du premier mois de chaque opérateur | Modification non désirée | Ilan | À chaque recrutement |

## 6. Avis et validation

- Avis de la personne en charge de la protection des données : à recueillir (pas d'obligation de désigner un DPO à ce stade ; à réexaminer à 50 dossiers).
- Avis des personnes concernées : recueilli lors des 5 entretiens de validation avec des expatriés (plan de lancement, semaine 3).
- Risque résiduel après mesures : **acceptable**, sous réserve des mesures du 5.2. Si l'une n'est pas en place au premier client, le traitement ne démarre pas pour les données concernées.
- Consultation préalable de la CNIL : non requise si le risque résiduel est acceptable.

Validation par le responsable de traitement : nom, date, signature.
