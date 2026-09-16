# 02 — Ameli : carte Vitale, attestation, remboursements, Complémentaire santé solidaire

| Organisme(s) | Durée moyenne de traitement par Relais | Difficulté (1 à 3) | Fréquence estimée par client |
|---|---|---|---|
| Assurance Maladie (CPAM du département du parent), via ameli.fr et le 3646 | 45 min pour une attestation ou une mise à jour ; 2 h pour une demande de Complémentaire santé solidaire | 1 à 2 | 3 à 4 fois par an (attestations, remboursements bloqués, carte Vitale) ; CSS : 1 fois par an si éligible |

## Objectif

Rétablir et maintenir les droits du parent à l'Assurance Maladie : carte Vitale à jour, attestation de droits disponible, remboursements versés sur le bon compte, et, si les ressources le permettent, Complémentaire santé solidaire (CSS) qui remplace ou complète la mutuelle à coût nul ou réduit.

## Prérequis

- Accès au compte ameli (procédure 01) ; case « Ameli » cochée dans l'annexe 1 du mandat ; consentement au traitement des données de santé coché dans le mandat.
- Numéro de sécurité sociale, date de naissance, code postal.
- Pour les remboursements : RIB du parent.
- Pour la CSS : avis d'imposition et justificatifs de ressources des douze derniers mois ; composition du foyer.

## Pièces à réunir

| Pièce | Détenteur | Format | Remarque |
|---|---|---|---|
| Carte Vitale (recto) | Parent | Photo | Vérifier qu'elle est bien au nom du parent |
| RIB | Parent | Scan | Pour la mise à jour des coordonnées bancaires |
| Avis d'imposition N-1 | Parent ou Relais | Scan | Pour la CSS |
| Justificatifs de ressources des 12 derniers mois (pensions, revenus fonciers, aides) | Parent, caisses de retraite | Scans | Pour la CSS ; les pensions figurent sur info-retraite.fr |
| Pièce d'identité | Parent | Scan | En cas de mise à jour d'état civil |
| Formulaire de demande de CSS (cerfa n° 12504) | Relais | PDF rempli | Si la demande ne peut pas être faite en ligne |
| Attestation de la mutuelle en cours | Parent | Scan | Pour la date d'effet de la CSS et la résiliation de la mutuelle |

## Étapes

1. Se connecter au compte ameli. Aller dans « Mes informations » : vérifier l'adresse postale, le RIB, le médecin traitant déclaré et l'adresse électronique de contact. Corriger ce qui est faux (le RIB se modifie en ligne avec téléversement du nouveau RIB).
2. **Attestation de droits** : « Mes démarches » → « Attestation de droits » → télécharger le PDF. La classer dans l'espace partagé du client (dossier Santé) ; elle est demandée par les mutuelles, les hôpitaux, les EHPAD.
3. **Carte Vitale** : si la carte est perdue, volée ou illisible, « Mes démarches » → « Déclarer la perte ou le vol » puis « Commander une nouvelle carte ». Le compte demande une photo d'identité et une pièce d'identité téléversées. La carte arrive au domicile du parent sous 2 à 3 semaines. Si la carte est simplement à mettre à jour (changement de caisse, de mutuelle), indiquer au parent de la passer dans une borne de pharmacie ; aucune démarche en ligne n'existe pour cela.
4. **Remboursements** : « Mes paiements » : vérifier les trois derniers mois. Un remboursement manquant vient le plus souvent d'une feuille de soins papier non envoyée, d'un RIB clos ou d'une mutuelle non rattachée. Envoyer les feuilles de soins papier à la CPAM (adresse dans « Adresses et contacts »), avec un courrier de transmission. En cas de RIB clos, mettre à jour et demander la réémission par la messagerie du compte.
5. **Rattachement de la mutuelle (télétransmission)** : vérifier dans « Mes informations » → « Ma complémentaire santé ». Si aucune complémentaire n'apparaît alors que le parent en paie une, demander à la mutuelle d'activer la télétransmission NOÉMIE (procédure 08).
6. **Complémentaire santé solidaire** : calculer l'éligibilité avec le simulateur de mesdroitssociaux.gouv.fr. Plafonds pour une personne seule (barème du 1er avril 2026, à revérifier chaque 1er avril) : 868 € par mois de ressources pour la CSS sans participation, 1 172 € par mois pour la CSS avec participation (participation de 8 à 30 € par mois selon l'âge ; 30 € par mois à partir de 70 ans). Les ressources prises en compte sont celles des douze derniers mois, y compris les pensions et l'ASPA n'est pas comptée. Si le parent est éligible, faire la demande en ligne depuis le compte ameli (« Mes démarches » → « Faire une demande de Complémentaire santé solidaire »), choisir l'organisme gestionnaire (la CPAM elle-même ou une mutuelle de la liste), téléverser les justificatifs. Sinon, remplir le cerfa n° 12504 et l'envoyer à la CPAM avec les pièces.
7. En cas d'attribution de la CSS, résilier la mutuelle actuelle à la date d'effet (la loi permet la résiliation sans préavis à la date d'attribution de la CSS) : voir procédure 08. Adresser l'attestation de CSS à la mutuelle et au médecin traitant.
8. Enregistrer les résultats dans la base et dans le rapport mensuel (montant des remboursements récupérés, économie annuelle de mutuelle grâce à la CSS).

## Délais

- Objectif Relais : attestation et corrections d'informations sous 48 h ouvrées ; dossier CSS complet déposé sous 10 jours ouvrés après réception des justificatifs.
- Nouvelle carte Vitale : 2 à 3 semaines.
- Décision sur une demande de CSS : 2 mois maximum à compter de la réception du dossier complet ; le silence de la caisse au-delà de 2 mois vaut rejet. Les droits sont ouverts au 1er jour du mois suivant la décision. Renouvellement à demander chaque année, entre 4 et 2 mois avant l'échéance (renouvellement automatique pour les bénéficiaires de l'ASPA).
- Remboursement d'une feuille de soins papier : 2 à 4 semaines.

## Pièges connus

- Le compte ameli impose un code personnel de 4 à 13 caractères et bloque après plusieurs erreurs ; toujours utiliser Bitwarden pour le saisir.
- La CPAM envoie certains documents uniquement par courrier postal (nouvelle carte Vitale, code provisoire) : la réexpédition du courrier vers Relais fait alors gagner du temps, mais la carte Vitale doit ensuite être remise au parent.
- Une carte Vitale reste valable tant que les droits sont ouverts ; les organismes qui « exigent une carte Vitale mise à jour » acceptent l'attestation de droits.
- Pour la CSS, les ressources du conjoint comptent ; un parent en couple a un plafond différent (1 302 € par mois pour deux personnes sans participation, barème 2026).
- L'ASPA (minimum vieillesse) n'est pas comptée dans les ressources, et ses bénéficiaires ont un renouvellement automatique de la CSS.
- Le choix de l'organisme gestionnaire de la CSS est libre mais engage pour un an ; la CPAM en gestion directe est le choix le plus simple à distance.
- Un changement de département du parent (déménagement, EHPAD) impose une mutation de caisse (procédure : déclarer la nouvelle adresse dans le compte ameli ; la mutation est automatique mais peut prendre un mois, pendant lequel les remboursements sont suspendus).

## Modèle de courrier ou de message

Courrier de transmission de feuilles de soins à la CPAM :

> Objet : transmission de feuilles de soins — assuré(e) [Prénom Nom], n° de sécurité sociale [numéro]
>
> Madame, Monsieur,
>
> Vous trouverez ci-joint [nombre] feuilles de soins originales au nom de [Prénom Nom], pour des soins des [dates], ainsi que les prescriptions correspondantes. Je vous remercie de bien vouloir procéder au remboursement sur le compte dont le RIB est enregistré sur le compte ameli de l'assuré(e).
>
> J'agis en vertu du mandat de représentation administrative ci-joint. Toute correspondance peut être adressée à [adresse Relais].
>
> Veuillez agréer, Madame, Monsieur, mes salutations distinguées.
>
> Pour [Prénom Nom du parent], en vertu du mandat de représentation administrative du [date], [Prénom Nom de l'opérateur], service Relais.

## Comment vérifier que c'est fait

- Attestation : PDF classé dans l'espace partagé, daté du jour.
- Carte Vitale : le parent confirme la réception par téléphone ; noter la date. Contrôle à J+21 si rien n'est reçu : messagerie du compte ameli.
- Remboursements : la ligne apparaît dans « Mes paiements » ; contrôle à J+30.
- CSS : notification de décision reçue (courrier ou messagerie ameli) et mention de la complémentaire « CSS » dans « Ma complémentaire santé » ; contrôle à J+60 par la messagerie si aucune décision.

## Quoi noter dans la base

- Table Organismes : ligne « CPAM [département] », numéro de sécurité sociale (dans le coffre, pas dans la base), date de la dernière attestation, mutuelle rattachée, date d'échéance de la CSS le cas échéant.
- Table Démarches : une démarche par action (« Attestation de droits », « Nouvelle carte Vitale », « Feuilles de soins », « Demande CSS »), avec échéance de contrôle.
- Rapport mensuel : montants remboursés récupérés ; économie annuelle estimée si CSS accordée (cotisation de mutuelle supprimée moins participation) ; décision à prendre par l'enfant : choix de l'organisme gestionnaire si plusieurs options.

## Sources

- ameli.fr — Complémentaire santé solidaire : qui peut en bénéficier — https://www.ameli.fr/assure/droits-demarches/difficultes-acces-droits-soins/complementaire-sante/complementaire-sante-beneficiaires — consultée le 16/09/2026.
- service-public.fr — Complémentaire santé solidaire : plafonds de ressources 2026 — https://www.service-public.gouv.fr/particuliers/actualites/A17326 — consultée le 16/09/2026.
- ameli.fr — Carte Vitale : perte, vol, renouvellement — https://www.ameli.fr/assure/remboursements/etre-bien-rembourse/carte-vitale — consultée le 16/09/2026.
- ameli.fr — Compte ameli : services et démarches — https://www.ameli.fr/assure/adresses-et-contacts/votre-compte-ameli — consultée le 16/09/2026.
- mesdroitssociaux.gouv.fr — Simulateur de droits — https://www.mesdroitssociaux.gouv.fr/ — consultée le 16/09/2026.
