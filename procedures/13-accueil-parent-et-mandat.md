# 13 — Accueil du parent et signature du mandat

| Organisme(s) | Durée moyenne de traitement par Relais | Difficulté (1 à 3) | Fréquence estimée par client |
|---|---|---|---|
| Aucun (relation Relais, enfant, parent) | 1 h 30 sur 3 à 10 jours (appel à trois 30 min, préparation et envoi du mandat 30 min, suivi 30 min) | 2 | 1 fois, à l'entrée du client |

## Objectif

Obtenir le mandat signé par le parent et les deux pièces d'identité, sans que le parent ait à imprimer, compléter ni scanner quoi que ce soit, et sans qu'il ait à aucun moment l'impression d'être démarché par un inconnu. À la fin, le dossier passe au statut « Mandat signé » et le diagnostic peut commencer.

## Prérequis

- Prospect au statut « Payé » dans la table Prospects (paiement reçu par le lien du courriel 03, case « J'accepte les CGV et demande que le service commence tout de suite » renseignée).
- Informations recueillies lors de l'appel de présentation avec l'enfant : identité, date de naissance et adresse du parent, organismes connus, téléphone du parent, créneau où le parent est disponible, préférence de signature (électronique par SMS ou papier).
- Vérifié pendant l'appel de présentation : pas de mesure de protection juridique (tutelle, curatelle, habilitation familiale) ni d'instruction en cours. En cas de doute, arrêter la procédure et passer le prospect en « Non éligible » avec le motif « Mesure de protection ».
- Lien de dépôt sécurisé du dossier créé (espace partagé du client).

## Pièces à réunir

- Mandat prérempli (PDF) : identité du Mandant et de la Personne de confiance, organismes cochés dans l'annexe 1 selon l'appel de présentation.
- Copie recto verso de la pièce d'identité du parent (en cours de validité ou périmée depuis moins de 5 ans).
- Copie de la pièce d'identité de l'enfant.
- Attestation d'assurance responsabilité civile professionnelle de Relais (à joindre à l'envoi du mandat).

## Étapes

1. **Préremplir le mandat.** Ouvrir `juridique/mandat-administratif.docx`, compléter les identités et cocher dans l'annexe 1 les organismes cités par l'enfant. Laisser vides uniquement la date et la signature. Exporter en PDF.
2. **Fixer l'appel à trois avec l'enfant.** Proposer deux créneaux où le parent est chez lui et reposé (en général en fin de matinée). L'enfant prévient son parent à l'avance : « Quelqu'un de Relais va nous appeler ensemble mardi à 11 h. »
3. **Mener l'appel à trois** (30 minutes, script ci-dessous). L'enfant présente Relais en premier. Convenir d'un **mot de code** que Relais donnera à chaque appel sortant. Faire enregistrer le numéro de Relais dans le téléphone du parent pendant l'appel.
4. **Envoyer le mandat le jour même**, selon la préférence retenue :
   - *Signature électronique* : envoyer le mandat par le service de signature électronique, avec code reçu par SMS sur le téléphone du parent. Rappeler le parent à l'heure convenue et le guider pas à pas, sans jamais lui demander le code reçu : c'est lui qui le saisit.
   - *Papier* : envoyer par lettre suivie le mandat prérempli, la notice « Comment signer » (un seul endroit à signer) et une enveloppe retour affranchie à l'adresse de traitement du courrier.
5. **Recevoir les pièces d'identité** uniquement par le lien de dépôt sécurisé. Si une pièce arrive par courriel ou messagerie, la déposer dans l'espace du dossier, supprimer le message des deux côtés si possible, et le dire à l'expéditeur.
6. **Relancer à J+3** si rien n'est revenu (le champ « Action du jour » de la table Prospects l'affiche) : appel au parent, puis message à l'enfant. Deux relances au maximum.
7. **À réception du mandat signé** : vérifier la signature, la date, les organismes cochés et la lisibilité des pièces d'identité. Créer le dossier dans la table Clients (date de signature, organismes cochés, consentement données de santé), relier la ligne Prospects au dossier et passer le statut à « Mandat signé ».
8. **Envoyer le courriel 04** (bienvenue et démarrage du diagnostic) le jour même, avec la copie du mandat signé en lien dans l'espace partagé.
9. **Si le mandat n'est pas signé à J+30 après le paiement** : proposer un dernier appel à trois ; sans signature, rembourser intégralement dans Stripe (Paiements → Rembourser), passer le prospect en « Perdu » avec le motif, et en informer l'enfant par écrit (CGV, article « Souscription »).

## Script de l'appel à trois

À adapter au ton de la famille. Toujours vouvoyer le parent, parler lentement, laisser les silences.

> **Enfant** : « Maman, je t'ai parlé de Relais. Je te présente Ilan, qui va s'occuper de tes papiers avec nous. »
>
> **Relais** : « Bonjour Madame Durand. Je m'appelle Ilan, je travaille pour Relais. Votre fille m'a demandé de vous aider pour le courrier, la Sécurité sociale, la retraite, les impôts. Je vais vous expliquer en quelques minutes ce que nous ferions, et surtout ce que nous ne ferons jamais. Vous pourrez me poser toutes les questions que vous voulez. Rien n'est décidé aujourd'hui. »
>
> « Ce que nous ferions : nous recevons votre courrier administratif et nous y répondons. Nous nous occupons des sites internet comme Ameli ou les impôts, pour que vous n'ayez plus à chercher des codes. Nous faisons les demandes d'aides auxquelles vous avez droit. Et vous pouvez nous appeler quand vous voulez, aux heures de bureau. »
>
> « Ce que nous ne ferons jamais : nous ne touchons pas à votre argent. Aucun virement, aucun paiement, aucun retrait. Nous ne signons rien qui vous engage à payer. Nous ne décidons rien à votre place : nous préparons, nous vous expliquons, c'est vous qui décidez. »
>
> « Pour que les organismes acceptent de nous parler, il faut un document signé par vous, qu'on appelle un mandat. Il est valable un an et vous pouvez l'arrêter quand vous voulez, par une simple lettre. Votre fille en reçoit une copie. »
>
> « Une chose importante contre les arnaques : convenons ensemble d'un mot de code. Chaque fois que Relais vous appellera, nous vous le dirons. Si quelqu'un vous appelle en disant venir de Relais sans connaître ce mot, raccrochez et appelez votre fille. Quel mot voulez-vous choisir ? »
>
> « Je vous propose d'enregistrer notre numéro dans votre téléphone sous le nom "Relais". »
>
> « Pour signer, vous préférez que je vous guide par téléphone avec un code reçu par SMS, ou recevoir le document par la poste avec une enveloppe retour ? Il sera déjà rempli, vous n'aurez qu'à signer à un seul endroit. »
>
> « Avez-vous des questions ? »

Consigner dans le champ Notes de la ligne Prospects : date de l'appel, accord ou hésitation du parent, mode de signature choisi, questions posées. **Le mot de code est noté dans le coffre Bitwarden du client, jamais dans Airtable.**

## Délais

- Envoi du mandat : le jour même de l'appel à trois.
- Relance : J+3, puis J+7 ; appel à trois de rattrapage à J+20.
- Limite : J+30 après le paiement ; au-delà, remboursement intégral (CGV).

## Pièges connus

- **Parent qui hésite** : ne jamais insister. Proposer un second appel une semaine plus tard, ou que l'enfant en parle lors de sa prochaine visite. Une signature obtenue sous pression est un risque d'abus de faiblesse.
- **Parent qui semble ne pas comprendre ce qu'il signe** (confusion, questions répétées sans mémorisation) : ne pas envoyer le mandat. En parler seul à seul avec l'enfant et l'orienter vers le médecin traitant ; le mandat suppose la pleine capacité.
- **Signature d'un tiers à la place du parent** (conjoint, enfant) : refusée. Seul le parent signe.
- **Pièce d'identité illisible ou photo de travers** : redemander une copie par le lien de dépôt, en expliquant comment la prendre (à plat, à la lumière du jour, les quatre coins visibles).
- **Code SMS demandé par un tiers** : Relais ne demande jamais le code au parent. Le parent le saisit lui-même.

## Modèles de courrier

- Courriel 03, versions A (enfant) et B (parent) : `emails/03-envoi-mandat.md`.
- Courriel 04, bienvenue et démarrage du diagnostic : `emails/04-bienvenue-diagnostic.md`.
- Notice « Comment signer » : une page, capture du mandat avec une flèche vers l'unique zone de signature, et le numéro de Relais en gros caractères.

## Sources

- Code civil, articles 1984 et suivants (mandat) et 1366 et 1367 (écrit et signature électroniques), Légifrance, consulté le 27 septembre 2026.
- Code de la consommation, articles L. 221-18, L. 221-25 et L. 221-28 (rétractation et exécution anticipée), Légifrance, consulté le 27 septembre 2026.
- Code pénal, article 223-15-2 (abus de faiblesse), Légifrance, consulté le 27 septembre 2026.
