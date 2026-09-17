# 06 — Rapport mensuel (courriel d'accompagnement)

**Déclencheur** : rapport mensuel généré (outils/rapport/generate_report.py) et relu par le responsable.
**Délai** : le 1er de chaque mois avant 12 h (heure de Paris) ; le 1er jour ouvré si le 1er tombe un week-end.
**Destinataires** : l'enfant ; le parent s'il a demandé à le recevoir (par courriel ou par courrier).
**Pièces jointes** : rapport mensuel (PDF).

---

**Objet :** {{PRENOM_PARENT}} — rapport de {{MOIS_LIBELLE}} : {{NB_REALISEES}} démarches réglées, {{NB_EN_COURS}} en cours

Bonjour {{PRENOM_ENFANT}},

Voici le rapport de {{MOIS_LIBELLE}} pour {{PRENOM_PARENT}}, en pièce jointe. En trois lignes :

- {{RESUME_LIGNE_1}}
- {{RESUME_LIGNE_2}}
- {{RESUME_LIGNE_3}}

**Ce mois-ci, nous avons réglé :** {{LISTE_REALISEES_COURTE}}

**En cours :** {{LISTE_EN_COURS_COURTE}}

**Vos décisions :** {{LISTE_DECISIONS_OU_AUCUNE}}

**À venir dans les 60 jours :** {{LISTE_ECHEANCES_COURTE}}

**Du côté de {{PRENOM_PARENT}} :** {{RESUME_CONTACTS_PARENT}}

Montant obtenu ce mois : {{MONTANT_MOIS}} €. Depuis le début : {{MONTANT_CUMUL}} €.

Tout est détaillé dans le rapport, et chaque démarche est consultable dans l'espace partagé : {{LIEN_ESPACE_PARTAGE}}. Si un point vous interroge, répondez à ce message ou appelez {{PRENOM_OPERATEUR}} ; notre prochain appel trimestriel est prévu le {{DATE_APPEL_TRIMESTRIEL}}.

Bien à vous,

{{PRENOM_OPERATEUR}}
Relais — dossier de {{PRENOM_PARENT}}
{{MANDATAIRE_TELEPHONE}} · {{SITE_URL}}

Vous pouvez à tout moment demander un rapport intermédiaire, ajouter un organisme au mandat, ou résilier l'abonnement (effet à la fin du mois, sans frais).
