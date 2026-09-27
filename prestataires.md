# Prestataires à choisir avant le premier client

Relevé du 27 septembre 2026. Prix publics constatés à cette date, à reconfirmer au moment de souscrire. Chaque prestataire retenu doit ensuite être nommé dans `site/config.json` (clés `*_NOM` et `*_HEBERGEMENT`), dans la politique de confidentialité et le registre (régénérer avec `juridique/generate.py` et `juridique/registre.py`), et son contrat de sous-traitance accepté.

| Besoin | Piste retenue | Prix constaté | Point à vérifier avant de signer |
|---|---|---|---|
| Médiateur de la consommation (obligatoire avant la première vente) | CM2C, Centre de la Médiation de la Consommation de Conciliateurs de Justice | Adhésion 48 € pour 3 ans (jusqu'à 10 personnes), puis 36 € par médiation à distance | Aucun. Reporter `MEDIATEUR_NOM`, `MEDIATEUR_ADRESSE`, `MEDIATEUR_SITE` dans `site/config.json`. |
| Signature électronique du mandat | Yousign (société française) | Starter 9 €/mois, 10 signatures par mois ; Business 25 €/mois, signatures illimitées ; essai gratuit 14 jours | Vérifier que la signature simple par code SMS convient (question 4 de la consultation de l'avocat). |
| Réception et numérisation du courrier | Kandbaz (numérisation quotidienne, espace en ligne, application) | À partir de 13 € HT/mois pour la numérisation | **Bloquant possible** : la réception de courrier adressé au nom des clients (réexpédié par La Poste) n'est pas mentionnée. Question posée dans le brouillon Gmail « Domiciliation et numérisation du courrier ». À envoyer à deux ou trois domiciliataires. |
| Ligne de réception des codes SMS (2FA) | Vraie carte SIM d'un opérateur mobile français dans un téléphone dédié | Forfait 2 € par mois chez Free ; à l'étranger, l'option Voyage doit être activée (avance de 10 €), coût de réception des SMS hors Europe non affiché | **Ne pas utiliser de numéro virtuel (VoIP)** : les banques et certains services bloquent l'envoi de SMS vers ces numéros (confirmé par le support d'Onoff). Tester la réception depuis Israël avec ton propre compte Ameli et impots.gouv avant le premier client. |
| Ligne vocale du parent | Numéro fixe français avec messagerie vocale transcrite par courriel | Selon opérateur | Peut être distincte de la ligne 2FA ; un numéro virtuel convient ici. |
| Espace partagé et lien de dépôt des pièces | Leviia Next (Nextcloud hébergé en France, certifié ISO 27001 et HDS, liens publics avec mot de passe et date d'expiration) | Sur la page tarifs de l'éditeur | Confirmer le besoin HDS avec l'avocat (question 3). Un dossier par client, lien de dépôt pour les pièces d'identité. |
| Assurance responsabilité civile professionnelle | Hiscox (devis en ligne) ou un courtier ; comparer avec les comparateurs RC Pro | Sur devis | Brouillon Gmail « Demande de devis RC professionnelle » prêt : demander aussi une garantie cyber (violation de données). |
| Avocat | Consultation au forfait | Budget visé 500 à 1 000 € HT | Brouillon Gmail prêt ; joindre les 6 documents listés en bas du message. |
| Expert-comptable | Mission tenue, bilan et déclarations ; avis TVA | Sur devis | Brouillon Gmail prêt (TVA, régularisation IS et CVAE 2025, dirigeant résidant en Israël, rapprochement Stripe). |

## Sources

- CM2C, tarifs : https://www.cm2c.net/tarifs.php
- Yousign, grille tarifaire : https://stackindep.fr/signature-electronique/yousign-prix
- Kandbaz, numérisation du courrier : https://www.kandbaz.com/services/courrier/numerisation/
- Free Mobile, communications à l'étranger : https://mobile.free.fr/communications-a-l-etranger
- Onoff Business, SMS non reçus : https://support.onoffbusiness.com/hc/fr/articles/34909989725213-Je-ne-re%C3%A7ois-pas-certains-SMS-Comment-y-rem%C3%A9dier
- Leviia Next : https://www.leviia.com/en/leviia-next/
- Hiscox, assurance professionnelle en ligne : https://www.hiscox.fr/assurance-professionnelle-en-ligne
