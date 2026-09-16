# 01 — Création ou récupération de l'accès FranceConnect

| Organisme(s) | Durée moyenne de traitement par Relais | Difficulté (1 à 3) | Fréquence estimée par client |
|---|---|---|---|
| FranceConnect (DINUM), via un fournisseur d'identité : impots.gouv.fr, Ameli, L'Identité Numérique La Poste, MSA, Yris | 1 h 30 réparties sur 2 à 5 jours (dépend de l'arrivée des codes) | 2 | 1 fois au diagnostic, puis 1 fois par an environ (perte de mot de passe) |

## Objectif

Disposer d'un moyen de connexion FranceConnect fiable au nom du parent, qui ouvre ensuite Ameli, impots.gouv.fr, info-retraite.fr, l'ANTS, la CAF et la plupart des services publics. C'est le socle de toutes les autres procédures : sans FranceConnect stable, chaque démarche redevient un parcours d'identifiants perdus.

## Prérequis

- Mandat signé, annexe 1 : cases « FranceConnect » et au moins un fournisseur d'identité (« impots.gouv.fr » ou « Ameli ») cochées.
- Clause 2FA du mandat signée : la ligne Relais `{{LIGNE_2FA_RELAIS}}` et l'adresse `{{EMAIL_2FA_RELAIS}}` peuvent être déclarées comme moyen de réception des codes.
- Numéro fiscal (13 chiffres, en haut à gauche de la déclaration ou de l'avis d'imposition) et numéro de sécurité sociale (15 chiffres, sur la carte Vitale ou une attestation).
- Pièce d'identité du parent en cours de validité (nécessaire pour L'Identité Numérique La Poste et pour FranceConnect+).

## Pièces à réunir

| Pièce | Détenteur | Format | Remarque |
|---|---|---|---|
| Dernier avis d'imposition ou déclaration de revenus | Parent (courrier) ou Relais (courrier réexpédié) | Scan | Contient le numéro fiscal et, sur l'avis, le revenu fiscal de référence utile ailleurs |
| Carte Vitale ou attestation de droits | Parent | Scan recto | Numéro de sécurité sociale |
| Pièce d'identité en cours de validité | Parent | Scan recto-verso | Indispensable pour L'Identité Numérique La Poste |
| RIB | Parent | Scan | Certains fournisseurs d'identité le demandent pour vérifier l'identité (Ameli) |
| Téléphone du parent | Parent | — | Nécessaire tant que la ligne Relais n'est pas déclarée |

## Étapes

1. Vérifier dans la table Organismes si un compte impots.gouv.fr ou Ameli existe déjà (le parent a reçu des courriels de ces services, ou une déclaration en ligne a déjà été faite). Choisir le fournisseur d'identité dans cet ordre de préférence : impots.gouv.fr (le plus stable, pas de dépendance au téléphone), puis Ameli, puis L'Identité Numérique La Poste (indispensable pour FranceConnect+ exigé par certains services, par exemple l'ANTS pour le permis ou certaines démarches de la CAF).
2. **Cas impots.gouv.fr existant** : aller sur impots.gouv.fr → « Votre espace particulier » → « Mot de passe oublié ». Saisir le numéro fiscal. Un courriel de réinitialisation part à l'adresse enregistrée. Si l'adresse est celle du parent, l'appeler et lui faire lire le courriel, ou lui faire transférer le courriel à `{{EMAIL_2FA_RELAIS}}`. Définir un nouveau mot de passe respectant les règles affichées et l'enregistrer immédiatement dans le coffre Bitwarden du client.
3. **Cas impots.gouv.fr sans accès courriel** : sur la page de connexion, choisir « Aide » → « Vous n'avez pas accès à votre messagerie ». Le formulaire demande le numéro fiscal, le numéro d'accès en ligne (sur la déclaration papier) et le revenu fiscal de référence (sur l'avis). Une nouvelle adresse électronique peut alors être déclarée : indiquer `{{EMAIL_2FA_RELAIS}}` avec l'accord écrit du parent. À défaut de ces trois numéros, faire une demande via la messagerie sécurisée, ou déposer un courrier au service des impôts des particuliers du parent avec copie du mandat et de sa pièce d'identité.
4. **Cas Ameli** : sur ameli.fr → « Compte ameli » → « Code personnel oublié ». Saisir le numéro de sécurité sociale, la date de naissance, le code postal. Choisir la réception du code provisoire par courriel ou SMS si une adresse ou un numéro est déjà enregistré ; sinon, le code provisoire est envoyé par courrier postal sous 5 à 10 jours (délai à intégrer dans l'échéance). Une fois connecté, aller dans « Mes informations » et déclarer la ligne Relais et l'adresse Relais comme coordonnées de contact, en conservant l'adresse postale du parent.
5. **Cas L'Identité Numérique La Poste** (pour FranceConnect+) : la création exige un smartphone, une pièce d'identité valide et une vérification de l'identité, soit en ligne par vidéo, soit en bureau de poste, soit par visite d'un facteur au domicile. Pour un parent sans smartphone, choisir la vérification par le facteur ou en bureau de poste ; le parent doit être présent. Relais prépare la demande en ligne, prend le rendez-vous et explique la procédure au parent par téléphone. L'application reste installée sur le téléphone du parent ; les codes passent par lui : prévoir un appel à trois pour chaque connexion FranceConnect+.
6. Tester la connexion FranceConnect depuis un service tiers (par exemple info-retraite.fr → « Se connecter avec FranceConnect ») et vérifier que le nom et le prénom retournés sont ceux du parent.
7. Enregistrer dans Bitwarden : identifiant, mot de passe, fournisseur d'identité utilisé, adresse courriel et numéro déclarés, questions de sécurité éventuelles. Vérifier que le journal d'accès enregistre la création de l'entrée.
8. Envoyer au parent, par courrier ou par téléphone, un message simple : « Votre accès en ligne est rétabli. Vous n'avez rien à faire. Si vous recevez un code par SMS ou par courrier, appelez-nous. »

## Délais

- Objectif Relais : accès opérationnel sous 5 jours ouvrés après réception du mandat signé.
- Courrier de code provisoire Ameli : 5 à 10 jours.
- Vérification d'identité La Poste par le facteur : rendez-vous sous 1 à 2 semaines selon la zone.
- Réinitialisation impots.gouv.fr par courriel : immédiate.

## Pièges connus

- Un compte FranceConnect n'existe pas en tant que tel : c'est le compte du fournisseur d'identité (impôts, Ameli…) qui sert. Si le parent « a perdu son FranceConnect », chercher quel fournisseur il utilisait (regarder ses courriels et ses courriers).
- Ameli bloque le compte après trois codes erronés et impose un nouvel envoi postal : ne jamais tenter un code au hasard.
- Les codes SMS envoyés au numéro du parent expirent en quelques minutes : convenir d'un créneau où le parent a son téléphone en main et lit le code en direct.
- Certains services (ANTS pour le permis, certains téléservices de la CAF) exigent FranceConnect+ (niveau substantiel), donc L'Identité Numérique La Poste ; anticiper cette création dès le diagnostic si le parent a un smartphone ou un proche disponible.
- Ne jamais créer un compte au nom du parent avec une adresse courriel personnelle d'un opérateur : toujours l'adresse dédiée Relais, tracée et transférable.
- Si un organisme refuse la modification des coordonnées sans le parent en ligne, organiser un appel à trois : Relais appelle l'organisme avec le parent en conférence, le parent confirme oralement son accord.

## Modèle de courrier ou de message

Courrier au service des impôts des particuliers (SIP), en cas d'impossibilité totale de réinitialisation en ligne :

> Objet : demande de réinitialisation de l'accès à l'espace particulier — numéro fiscal [numéro]
>
> Madame, Monsieur,
>
> Agissant pour le compte de [Prénom Nom du parent], né(e) le [date], demeurant [adresse], en vertu du mandat de représentation administrative ci-joint, je vous demande de bien vouloir réinitialiser l'accès à son espace particulier sur impots.gouv.fr et d'enregistrer l'adresse électronique suivante comme adresse de contact : [adresse Relais].
>
> Vous trouverez ci-joint le mandat signé, la copie de la pièce d'identité de [Prénom Nom] et la copie de son dernier avis d'imposition.
>
> Je vous remercie de votre aide et vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.
>
> Pour [Prénom Nom du parent], en vertu du mandat de représentation administrative du [date], [Prénom Nom de l'opérateur], service Relais.

## Comment vérifier que c'est fait

- Une connexion réussie à info-retraite.fr ou à ameli.fr via FranceConnect, avec capture d'écran de la page d'accueil de l'espace personnel (sans donnée sensible) jointe à la démarche.
- L'entrée Bitwarden existe et a été testée par un second opérateur ou par le responsable (double contrôle le premier mois).
- Contrôle à J+7 : si le code postal Ameli n'est pas arrivé, relancer par le téléphone 3646 avec le parent en ligne.

## Quoi noter dans la base

- Table Organismes : ligne « FranceConnect » avec le fournisseur d'identité retenu, la date de dernière connexion réussie, l'adresse et le numéro déclarés.
- Table Démarches : « Récupération accès FranceConnect », statut « Terminée », date, pièce jointe = capture d'écran.
- Rapport mensuel : mentionner « Accès en ligne rétablis » dans le résumé du mois du diagnostic ; aucun montant.

## Sources

- FranceConnect — Comprendre FranceConnect, création de compte — https://aide.franceconnect.gouv.fr/faq/comprendre-franceconnect/creation-compte/ — consultée le 16/09/2026.
- FranceConnect+ — https://www.franceconnect.gouv.fr/franceconnect-plus/ — consultée le 16/09/2026.
- L'Identité Numérique La Poste — Comment l'obtenir — https://lidentitenumerique.laposte.fr/comment-lobtenir — consultée le 16/09/2026.
- ameli.fr — Compte ameli, code personnel oublié — https://www.ameli.fr/assure/adresses-et-contacts/votre-compte-ameli — consultée le 16/09/2026.
- impots.gouv.fr — Aide à la connexion à l'espace particulier — https://www.impots.gouv.fr/particulier/questions/comment-recuperer-mon-mot-de-passe — consultée le 16/09/2026.
