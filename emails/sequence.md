# Séquence des courriels Relais

Huit courriels couvrent le parcours client (document projet, section 6) : contact, appel, mandat, diagnostic, régime de croisière, urgence, relance des prospects. Le ton est celui du produit : rassurant, concret, jamais infantilisant envers le parent. Chaque fichier contient l'objet, le corps, et en tête le déclencheur, le délai et le destinataire. Les champs entre `{{…}}` sont remplis à l'envoi (prénoms, dates, montants) ou une fois pour toutes (coordonnées Relais, voir README).

| N° | Courriel | Déclencheur | Délai | Destinataire | Envoi |
|---|---|---|---|---|---|
| 01 | [Accusé de réception du formulaire](01-accuse-reception.md) | Formulaire du site envoyé | Immédiat (réponse automatique Formspree) ou sous 1 h ouvrée | Enfant (prospect) | Automatique |
| 02 | [Confirmation de l'appel](02-confirmation-appel.md) | Créneau d'appel fixé | Immédiat, rappel 2 h avant | Enfant (prospect) | Manuel ou outil de réservation |
| 03 | [Envoi du mandat](03-envoi-mandat.md) — version A enfant, version B parent | Accord de principe à la fin de l'appel | Jour même (J1) ; appel au parent sous 3 jours | Enfant, puis parent (courriel ou courrier + appel) | Manuel, pièces jointes |
| 04 | [Bienvenue et démarrage du diagnostic](04-bienvenue-diagnostic.md) | Mandat signé et pièces reçues | Jour de réception (J7 au plus tard) | Enfant ; parent par téléphone | Manuel |
| 05 | [Rapport de diagnostic](05-rapport-diagnostic.md) | Diagnostic terminé | J21 au plus tard ; appel de restitution dans la semaine | Enfant ; parent à l'oral | Manuel, PDF joint |
| 06 | [Rapport mensuel](06-rapport-mensuel.md) | Rapport généré et relu | Le 1er du mois avant 12 h (Paris) | Enfant ; parent sur demande | Semi-automatique (generate_report.py + envoi) |
| 07 | [Alerte urgence](07-alerte-urgence.md) | Urgence de niveau 4 ou décision urgente | Dans l'heure ouvrée, courriel + message ou appel | Enfant ; parent par téléphone | Manuel, scan joint |
| 08 | [Relance d'un prospect](08-relance-inactif.md) — J+3 puis J+10 | Prospect sans réponse | 3 jours puis 10 jours après le dernier échange ; jamais au-delà | Enfant (prospect) | Manuel ou automatisation simple |

## Règles d'envoi

- **Un seul expéditeur visible** : l'adresse `{{MANDATAIRE_EMAIL}}` (nom d'affichage « Prénom — Relais »). Les réponses arrivent dans la boîte partagée, triées par dossier.
- **Jamais d'identifiant, de mot de passe ni de code** dans un courriel, dans les deux sens. Si un client en envoie un, le supprimer du fil, le déposer dans le coffre et le lui dire.
- **Pièces jointes** : PDF uniquement ; les documents contenant des données de santé sont déposés dans l'espace partagé plutôt qu'attachés, avec un lien.
- **Urgence** : le courriel 07 ne remplace jamais l'appel ou le message instantané ; l'opérateur consigne l'heure de chaque tentative dans la démarche.
- **Fuseaux horaires** : indiquer toujours l'heure locale de l'enfant et l'heure de Paris.
- **Relances** : deux au maximum (J+3, J+10) ; toute demande d'arrêt est respectée immédiatement et notée dans le dossier.
- **Traçabilité** : chaque courriel envoyé est enregistré dans la démarche correspondante (table Démarches, champ Résultat ou pièce jointe), sauf les relances commerciales qui restent dans le suivi des prospects.
- **Langue** : français ; un courriel en anglais peut être proposé à l'enfant s'il le demande, le parent est toujours écrit en français.
