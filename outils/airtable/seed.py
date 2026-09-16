#!/usr/bin/env python3
"""Insère deux dossiers clients fictifs et cohérents dans la base Airtable pour tester les
vues et le générateur de rapport.

Usage :
    python3 outils/airtable/seed.py             # insère (idempotent : un dossier déjà présent est ignoré)
    python3 outils/airtable/seed.py --dry-run   # affiche les enregistrements sans appeler l'API

Chaque client comporte : le parent, ses organismes, 6 démarches et 8 courriers, avec des
dates relatives à aujourd'hui (échéances passées, sous 7 jours, sous 30 jours, futures ;
démarches terminées ce mois et le mois précédent) pour alimenter toutes les vues.
Les données sont inventées : aucun numéro réel.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from airtable_client import AirtableClient, AirtableError, load_env, resolve_base_id  # noqa: E402


def d(days: int) -> str:
    """Date ISO relative à aujourd'hui (jours positifs = futur)."""
    return (date.today() + timedelta(days=days)).isoformat()


def first_of_this_month() -> date:
    return date.today().replace(day=1)


def build_seed() -> list[dict]:
    """Renvoie la liste des dossiers, chacun avec ses organismes, démarches et courriers."""
    ce_mois = first_of_this_month()
    mois_prec = (ce_mois - timedelta(days=1)).replace(day=1)
    return [
        {
            "client": {
                "Dossier": "Durand — Sarcelles",
                "Statut": "Actif",
                "Enfant — Prénom Nom": "Sarah Durand",
                "Enfant — Courriel": "sarah.durand@exemple.org",
                "Enfant — Téléphone": "+972 50 000 00 01",
                "Enfant — Pays": "Israël",
                "Enfant — Fuseau horaire": "UTC+3 (Israël)",
                "Parent — Prénom Nom": "Monique Durand",
                "Parent — Date de naissance": "1949-03-12",
                "Parent — Adresse": "14 rue des Lilas\n95200 Sarcelles",
                "Parent — Ville": "Sarcelles",
                "Parent — Département": "95",
                "Parent — Téléphone": "+33 1 00 00 00 01",
                "Parent — Situation": "Seul(e) à domicile",
                "Mandat signé le": d(-75),
                "Mandat — Organismes cochés": ["FranceConnect", "Ameli", "L'Assurance retraite", "Agirc-Arrco", "impots.gouv.fr", "Conseil départemental", "Mutuelle", "Électricité", "Banque (consultation)", "La Poste"],
                "Consentement données de santé": True,
                "Offre": "Tarif fondateur 59 €/mois",
                "Forfaits souscrits": ["Diagnostic 149 €"],
                "Mode de réception du courrier": "Réexpédition La Poste",
                "Opérateur": "Fondateur",
                "Coffre Bitwarden": "Relais — Durand",
                "Prochain appel trimestriel": d(40),
                "Notes": "Veuve, autonome, très à l'aise au téléphone, ne touche pas à l'ordinateur. Sarah joignable le soir heure d'Israël.",
            },
            "organismes": [
                {"Nom": "CPAM 95 — Durand", "Catégorie": "Santé", "Organisme": "CPAM", "Référence": "Dossier 95-DUR-001", "Espace en ligne": "https://assure.ameli.fr", "Accès dans le coffre": True, "2FA vers ligne Relais": True, "Mandat accepté": "Oui", "Téléphone": "3646"},
                {"Nom": "L'Assurance retraite IDF — Durand", "Catégorie": "Retraite", "Organisme": "L'Assurance retraite (CARSAT / CNAV)", "Référence": "Pension 1 234 567 A", "Espace en ligne": "https://www.lassuranceretraite.fr", "Accès dans le coffre": True, "Mandat accepté": "Oui", "Montant mensuel": 1180.00},
                {"Nom": "Agirc-Arrco — Durand", "Catégorie": "Retraite", "Organisme": "Agirc-Arrco", "Référence": "Allocation 98 765", "Espace en ligne": "https://espace-personnel.agirc-arrco.fr", "Accès dans le coffre": True, "Mandat accepté": "Inconnu", "Montant mensuel": 410.00},
                {"Nom": "SIP Sarcelles — Durand", "Catégorie": "Impôts", "Organisme": "DGFiP", "Référence": "Numéro fiscal dans le coffre", "Espace en ligne": "https://www.impots.gouv.fr", "Accès dans le coffre": True, "2FA vers ligne Relais": True, "Mandat accepté": "Oui"},
                {"Nom": "Conseil départemental 95 — Durand", "Catégorie": "Aides sociales", "Organisme": "Conseil départemental", "Référence": "APA 2026-0412", "Mandat accepté": "Appel à trois nécessaire", "Téléphone": "+33 1 00 00 00 95"},
                {"Nom": "Mutuelle Harmonie — Durand", "Catégorie": "Complémentaire santé", "Organisme": "Mutuelle", "Référence": "Adhérent 77 001", "Accès dans le coffre": True, "Mandat accepté": "Oui", "Montant mensuel": -94.00, "Date clé": d(20)},
                {"Nom": "EDF — Durand", "Catégorie": "Énergie", "Organisme": "EDF", "Référence": "Client 3 456 789 012", "Espace en ligne": "https://particulier.edf.fr", "Accès dans le coffre": True, "Mandat accepté": "Inconnu", "Montant mensuel": -78.00},
                {"Nom": "Crédit Agricole IDF — Durand", "Catégorie": "Banque", "Organisme": "Banque", "Référence": "Compte courant (consultation seule)", "Accès dans le coffre": True, "Mandat accepté": "Oui", "Notes": "Consultation uniquement. Aucune opération."},
            ],
            "demarches": [
                {"Titre": "Récupération accès FranceConnect et Ameli", "Type": "Récupération d'accès", "Procédure": "01 FranceConnect", "Statut": "Terminée", "Urgence": "2 - Normale", "Échéance": (mois_prec + timedelta(days=12)).isoformat(), "Terminée le": (mois_prec + timedelta(days=10)).isoformat(), "Résultat": "Accès rétablis, code Ameli reçu par courrier, ligne Relais déclarée pour les codes.", "Opérateur": "Fondateur", "À inclure au rapport": True, "_organisme": "CPAM 95 — Durand"},
                {"Titre": "Régularisation remboursements Ameli bloqués", "Type": "Réclamation", "Procédure": "02 Ameli", "Statut": "Terminée", "Urgence": "3 - Élevée", "Échéance": (ce_mois + timedelta(days=5)).isoformat(), "Terminée le": (ce_mois + timedelta(days=3)).isoformat(), "Montant en jeu": 312.40, "Montant obtenu": 312.40, "Résultat": "RIB clos remplacé, trois feuilles de soins renvoyées, 312,40 € versés.", "Opérateur": "Fondateur", "À inclure au rapport": True, "_organisme": "CPAM 95 — Durand"},
                {"Titre": "Déclaration de revenus 2025 et demande d'exonération taxe foncière", "Type": "Déclaration", "Procédure": "04 Impôts", "Statut": "Terminée", "Urgence": "2 - Normale", "Échéance": (ce_mois + timedelta(days=8)).isoformat(), "Terminée le": (ce_mois + timedelta(days=6)).isoformat(), "Montant obtenu": 640.00, "Résultat": "Déclaration déposée ; réclamation taxe foncière acceptée, dégrèvement de 640 €.", "Opérateur": "Fondateur", "À inclure au rapport": True, "_organisme": "SIP Sarcelles — Durand"},
                {"Titre": "Demande APA à domicile", "Type": "Demande de droits", "Procédure": "05 APA", "Statut": "En attente organisme", "Urgence": "3 - Élevée", "Échéance": d(25), "Prochaine étape": "Visite de l'équipe médico-sociale prévue, relancer si pas de date sous 10 jours", "Référence dossier": "APA 2026-0412", "Montant en jeu": 650.00, "Opérateur": "Fondateur", "À inclure au rapport": True, "_organisme": "Conseil départemental 95 — Durand"},
                {"Titre": "Comparatif mutuelle avant échéance", "Type": "Changement de contrat", "Procédure": "08 Mutuelle", "Statut": "En attente enfant", "Urgence": "2 - Normale", "Échéance": d(5), "Prochaine étape": "Sarah doit choisir entre les deux devis envoyés", "Montant en jeu": 420.00, "Opérateur": "Fondateur", "Décision enfant requise": True, "À inclure au rapport": True, "_organisme": "Mutuelle Harmonie — Durand"},
                {"Titre": "Contestation facture EDF estimée", "Type": "Réclamation", "Procédure": "09 Énergie / télécom", "Statut": "En cours", "Urgence": "2 - Normale", "Échéance": d(-3), "Prochaine étape": "Relance écrite J+30 puis médiateur si silence", "Référence dossier": "Réclamation R-55 321", "Montant en jeu": 186.00, "Opérateur": "Fondateur", "À inclure au rapport": True, "_organisme": "EDF — Durand"},
            ],
            "courriers": [
                {"Titre": d(-40) + " — CPAM — Demande de pièces", "Reçu le": d(-40), "Date du document": d(-44), "Type": "Demande de pièces", "Urgence": "3 - Élevée", "Date limite": d(-10), "Référence": "95-DUR-001", "Statut": "Traité", "Résumé": "Demande de RIB et de feuilles de soins originales.", "Confiance classification": 0.92, "Traité le": d(-39), "Opérateur": "Fondateur", "_organisme": "CPAM 95 — Durand", "_demarche": "Régularisation remboursements Ameli bloqués"},
                {"Titre": d(-32) + " — DGFiP — Avis de taxe foncière", "Reçu le": d(-32), "Date du document": d(-35), "Type": "Facture", "Urgence": "2 - Normale", "Date limite": d(12), "Montant": 640.00, "Statut": "Traité", "Résumé": "Avis 2026 sans exonération ; réclamation déposée.", "Confiance classification": 0.88, "Traité le": d(-31), "Opérateur": "Fondateur", "_organisme": "SIP Sarcelles — Durand", "_demarche": "Déclaration de revenus 2025 et demande d'exonération taxe foncière"},
                {"Titre": d(-28) + " — EDF — Facture", "Reçu le": d(-28), "Date du document": d(-30), "Type": "Facture", "Urgence": "2 - Normale", "Date limite": d(-8), "Montant": 486.30, "Référence": "Facture F-2026-8891", "Statut": "Traité", "Résumé": "Facture sur consommation estimée, très supérieure à l'habitude.", "Confiance classification": 0.95, "Traité le": d(-27), "Opérateur": "Fondateur", "_organisme": "EDF — Durand", "_demarche": "Contestation facture EDF estimée"},
                {"Titre": d(-20) + " — Conseil départemental — Accusé de réception", "Reçu le": d(-20), "Date du document": d(-22), "Type": "Information", "Urgence": "1 - Faible", "Référence": "APA 2026-0412", "Statut": "Traité", "Résumé": "Dossier APA complet reçu, visite à programmer.", "Confiance classification": 0.9, "Traité le": d(-20), "Opérateur": "Fondateur", "_organisme": "Conseil départemental 95 — Durand", "_demarche": "Demande APA à domicile"},
                {"Titre": d(-12) + " — Mutuelle — Avis d'échéance", "Reçu le": d(-12), "Date du document": d(-15), "Type": "Information", "Urgence": "2 - Normale", "Date limite": d(20), "Montant": 1128.00, "Statut": "Traité", "Résumé": "Cotisation annuelle en hausse de 9 %.", "Confiance classification": 0.86, "Traité le": d(-11), "Opérateur": "Fondateur", "_organisme": "Mutuelle Harmonie — Durand", "_demarche": "Comparatif mutuelle avant échéance"},
                {"Titre": d(-6) + " — EDF — Relance", "Reçu le": d(-6), "Date du document": d(-8), "Type": "Relance", "Urgence": "3 - Élevée", "Date limite": d(4), "Montant": 486.30, "Référence": "Facture F-2026-8891", "Statut": "En cours", "Résumé": "Relance malgré réclamation en cours ; rappeler la suspension du recouvrement.", "Confiance classification": 0.93, "Opérateur": "Fondateur", "_organisme": "EDF — Durand", "_demarche": "Contestation facture EDF estimée"},
                {"Titre": d(-4) + " — Agirc-Arrco — Attestation fiscale", "Reçu le": d(-4), "Date du document": d(-7), "Type": "Information", "Urgence": "1 - Faible", "Statut": "Non traité", "Résumé": "Attestation annuelle à classer.", "Confiance classification": 0.97, "Opérateur": "Fondateur", "_organisme": "Agirc-Arrco — Durand"},
                {"Titre": d(-1) + " — CPAM — Convocation", "Reçu le": d(-1), "Date du document": d(-3), "Type": "Convocation", "Urgence": "3 - Élevée", "Date limite": d(9), "Statut": "Non traité", "Résumé": "Convocation au service médical, rendez-vous à confirmer.", "Confiance classification": 0.81, "Opérateur": "Fondateur", "_organisme": "CPAM 95 — Durand"},
            ],
        },
        {
            "client": {
                "Dossier": "Martin — Lyon",
                "Statut": "Actif",
                "Enfant — Prénom Nom": "Julien Martin",
                "Enfant — Courriel": "julien.martin@exemple.org",
                "Enfant — Téléphone": "+1 514 000 0002",
                "Enfant — Pays": "Canada",
                "Enfant — Fuseau horaire": "UTC-4 (Montréal)",
                "Parent — Prénom Nom": "Robert Martin",
                "Parent — Date de naissance": "1944-11-02",
                "Parent — Adresse": "3 place Bellecour\n69002 Lyon",
                "Parent — Ville": "Lyon",
                "Parent — Département": "69",
                "Parent — Téléphone": "+33 4 00 00 00 02",
                "Parent — Situation": "En couple à domicile",
                "Mandat signé le": d(-20),
                "Mandat — Organismes cochés": ["FranceConnect", "Ameli", "L'Assurance retraite", "impots.gouv.fr", "ANTS", "CAF", "Syndic", "Téléphonie", "Internet", "Banque (consultation)"],
                "Consentement données de santé": True,
                "Offre": "Abonnement 89 €/mois",
                "Forfaits souscrits": ["Diagnostic 149 €", "Hospitalisation 490 €"],
                "Mode de réception du courrier": "Scan par un proche",
                "Opérateur": "Opérateur 1",
                "Coffre Bitwarden": "Relais — Martin",
                "Prochain appel trimestriel": d(70),
                "Notes": "Sortie d'hospitalisation il y a 3 semaines (fracture du col du fémur). Épouse présente mais fatiguée. La voisine scanne le courrier avec WhatsApp.",
            },
            "organismes": [
                {"Nom": "CPAM 69 — Martin", "Catégorie": "Santé", "Organisme": "CPAM", "Référence": "Dossier 69-MAR-002", "Espace en ligne": "https://assure.ameli.fr", "Accès dans le coffre": True, "Mandat accepté": "Oui"},
                {"Nom": "CARSAT Rhône-Alpes — Martin", "Catégorie": "Retraite", "Organisme": "L'Assurance retraite (CARSAT / CNAV)", "Référence": "Pension 7 654 321 B", "Accès dans le coffre": False, "Mandat accepté": "Inconnu", "Montant mensuel": 1540.00},
                {"Nom": "SIP Lyon 2e — Martin", "Catégorie": "Impôts", "Organisme": "DGFiP", "Espace en ligne": "https://www.impots.gouv.fr", "Accès dans le coffre": True, "Mandat accepté": "Oui"},
                {"Nom": "ANTS — Martin", "Catégorie": "Titres d'identité", "Organisme": "ANTS", "Référence": "CNI expirée", "Accès dans le coffre": True, "Mandat accepté": "Non", "Date clé": d(-15), "Notes": "CNI expirée depuis 15 jours ; la banque la réclame."},
                {"Nom": "Syndic Foncia Bellecour — Martin", "Catégorie": "Copropriété", "Organisme": "Syndic", "Référence": "Lot 12", "Espace en ligne": "https://myfoncia.fr", "Accès dans le coffre": True, "Mandat accepté": "Oui", "Montant mensuel": -210.00, "Date clé": d(18)},
                {"Nom": "Orange — Martin", "Catégorie": "Télécom", "Organisme": "Orange", "Référence": "Contrat fixe + box", "Accès dans le coffre": True, "Mandat accepté": "Appel à trois nécessaire", "Montant mensuel": -44.99},
            ],
            "demarches": [
                {"Titre": "Diagnostic initial et inventaire des organismes", "Type": "Information", "Procédure": "Hors procédure", "Statut": "Terminée", "Urgence": "2 - Normale", "Échéance": (ce_mois + timedelta(days=2)).isoformat(), "Terminée le": (ce_mois + timedelta(days=1)).isoformat(), "Résultat": "Rapport de diagnostic envoyé : 6 organismes, 2 anomalies (CNI expirée, box internet inutilisée).", "Opérateur": "Opérateur 1", "À inclure au rapport": True},
                {"Titre": "Coordination sortie d'hospitalisation : aide à domicile et APA en urgence", "Type": "Demande de droits", "Procédure": "05 APA", "Statut": "En cours", "Urgence": "4 - Critique", "Échéance": d(2), "Prochaine étape": "Certificat médical à récupérer chez le médecin traitant, dépôt en procédure d'urgence", "Montant en jeu": 900.00, "Opérateur": "Opérateur 1", "À inclure au rapport": True, "_organisme": "CPAM 69 — Martin"},
                {"Titre": "Renouvellement carte d'identité expirée", "Type": "Rendez-vous", "Procédure": "07 ANTS", "Statut": "En attente parent", "Urgence": "3 - Élevée", "Échéance": d(12), "Prochaine étape": "Rendez-vous mairie du 2e pris ; photo à faire par la voisine chez le photographe", "Référence dossier": "Pré-demande en cours", "Opérateur": "Opérateur 1", "À inclure au rapport": True, "_organisme": "ANTS — Martin"},
                {"Titre": "Assemblée générale de copropriété : pouvoir et consignes de vote", "Type": "Information", "Procédure": "11 Copropriété", "Statut": "En attente enfant", "Urgence": "2 - Normale", "Échéance": d(11), "Prochaine étape": "Julien doit donner ses consignes de vote sur les travaux d'ascenseur (quote-part 3 400 €)", "Montant en jeu": 3400.00, "Opérateur": "Opérateur 1", "Décision enfant requise": True, "À inclure au rapport": True, "_organisme": "Syndic Foncia Bellecour — Martin"},
                {"Titre": "Résiliation box internet inutilisée", "Type": "Résiliation", "Procédure": "09 Énergie / télécom", "Statut": "À faire", "Urgence": "1 - Faible", "Échéance": d(45), "Prochaine étape": "Appel à trois avec Robert pour obtenir le RIO et confirmer", "Montant obtenu": 0, "Montant en jeu": 360.00, "Opérateur": "Opérateur 1", "À inclure au rapport": True, "_organisme": "Orange — Martin"},
                {"Titre": "Attestation fiscale de pension pour le dossier APA", "Type": "Attestation", "Procédure": "03 Retraite", "Statut": "Terminée", "Urgence": "2 - Normale", "Échéance": (ce_mois + timedelta(days=4)).isoformat(), "Terminée le": (ce_mois + timedelta(days=4)).isoformat(), "Résultat": "Attestation téléchargée et jointe au dossier APA.", "Opérateur": "Opérateur 1", "À inclure au rapport": True, "_organisme": "CARSAT Rhône-Alpes — Martin"},
            ],
            "courriers": [
                {"Titre": d(-18) + " — Hôpital — Compte rendu de sortie", "Reçu le": d(-18), "Date du document": d(-21), "Type": "Information", "Urgence": "3 - Élevée", "Statut": "Traité", "Résumé": "Sortie le " + d(-21) + ", aide à domicile recommandée, kinésithérapie.", "Confiance classification": 0.7, "Traité le": d(-18), "Opérateur": "Opérateur 1", "_organisme": "CPAM 69 — Martin", "_demarche": "Coordination sortie d'hospitalisation : aide à domicile et APA en urgence"},
                {"Titre": d(-16) + " — Banque — Demande de pièce d'identité", "Reçu le": d(-16), "Date du document": d(-19), "Type": "Demande de pièces", "Urgence": "3 - Élevée", "Date limite": d(14), "Statut": "Traité", "Résumé": "La banque exige une CNI valide sous 30 jours.", "Confiance classification": 0.84, "Traité le": d(-15), "Opérateur": "Opérateur 1", "_organisme": "ANTS — Martin", "_demarche": "Renouvellement carte d'identité expirée"},
                {"Titre": d(-14) + " — Syndic — Convocation AG", "Reçu le": d(-14), "Date du document": d(-16), "Type": "Convocation", "Urgence": "2 - Normale", "Date limite": d(11), "Montant": 3400.00, "Référence": "AG " + str(date.today().year), "Statut": "Traité", "Résumé": "Ordre du jour : travaux d'ascenseur, budget, élection du conseil syndical.", "Confiance classification": 0.91, "Traité le": d(-13), "Opérateur": "Opérateur 1", "_organisme": "Syndic Foncia Bellecour — Martin", "_demarche": "Assemblée générale de copropriété : pouvoir et consignes de vote"},
                {"Titre": d(-10) + " — Orange — Facture", "Reçu le": d(-10), "Date du document": d(-12), "Type": "Facture", "Urgence": "1 - Faible", "Date limite": d(5), "Montant": 44.99, "Statut": "Traité", "Résumé": "Facture mensuelle box + fixe ; box jamais branchée.", "Confiance classification": 0.96, "Traité le": d(-9), "Opérateur": "Opérateur 1", "_organisme": "Orange — Martin", "_demarche": "Résiliation box internet inutilisée"},
                {"Titre": d(-7) + " — CARSAT — Attestation de paiement", "Reçu le": d(-7), "Date du document": d(-9), "Type": "Information", "Urgence": "1 - Faible", "Statut": "Traité", "Résumé": "Attestation classée.", "Confiance classification": 0.95, "Traité le": d(-7), "Opérateur": "Opérateur 1", "_organisme": "CARSAT Rhône-Alpes — Martin", "_demarche": "Attestation fiscale de pension pour le dossier APA"},
                {"Titre": d(-5) + " — Syndic — Appel de fonds", "Reçu le": d(-5), "Date du document": d(-7), "Type": "Facture", "Urgence": "2 - Normale", "Date limite": d(18), "Montant": 630.00, "Référence": "Appel T4", "Statut": "En cours", "Résumé": "Appel trimestriel, à faire payer par Julien avant le " + d(18) + ".", "Confiance classification": 0.9, "Opérateur": "Opérateur 1", "_organisme": "Syndic Foncia Bellecour — Martin"},
                {"Titre": d(-3) + " — CPAM — Décision", "Reçu le": d(-3), "Date du document": d(-6), "Type": "Décision", "Urgence": "2 - Normale", "Statut": "Non traité", "Résumé": "Prise en charge des séances de kinésithérapie accordée.", "Confiance classification": 0.89, "Opérateur": "Opérateur 1", "_organisme": "CPAM 69 — Martin"},
                {"Titre": d(0) + " — Orange — Mise en demeure", "Reçu le": d(0), "Date du document": d(-2), "Type": "Mise en demeure", "Urgence": "4 - Critique", "Date limite": d(8), "Montant": 134.97, "Statut": "Non traité", "Résumé": "Trois factures impayées suite au rejet de prélèvement pendant l'hospitalisation.", "Confiance classification": 0.94, "Opérateur": "Opérateur 1", "_organisme": "Orange — Martin"},
            ],
        },
    ]


def _strip_private(record: dict) -> dict:
    return {k: v for k, v in record.items() if not k.startswith("_") and v is not None}


def seed(client: AirtableClient, base_id: str, dossiers: list[dict] | None = None, log=print) -> dict[str, int]:
    """Insère les dossiers ; renvoie le nombre d'enregistrements créés par table."""
    dossiers = dossiers or build_seed()
    counts = {"Clients": 0, "Organismes": 0, "Démarches": 0, "Courriers": 0, "ignorés": 0}
    for dossier in dossiers:
        nom = dossier["client"]["Dossier"]
        if client.find_first(base_id, "Clients", "Dossier", nom):
            log(f"• dossier « {nom} » déjà présent, ignoré")
            counts["ignorés"] += 1
            continue
        client_rec = client.create_records(base_id, "Clients", [_strip_private(dossier["client"])])[0]
        client_id = client_rec["id"]
        counts["Clients"] += 1

        org_ids: dict[str, str] = {}
        org_records = [dict(_strip_private(o), **{"Client": [client_id]}) for o in dossier["organismes"]]
        for spec, rec in zip(dossier["organismes"], client.create_records(base_id, "Organismes", org_records)):
            org_ids[spec["Nom"]] = rec["id"]
        counts["Organismes"] += len(org_records)

        dem_ids: dict[str, str] = {}
        dem_records = []
        for dm in dossier["demarches"]:
            rec = dict(_strip_private(dm), **{"Client": [client_id]})
            if dm.get("_organisme"):
                rec["Organisme"] = [org_ids[dm["_organisme"]]]
            dem_records.append(rec)
        for spec, rec in zip(dossier["demarches"], client.create_records(base_id, "Démarches", dem_records)):
            dem_ids[spec["Titre"]] = rec["id"]
        counts["Démarches"] += len(dem_records)

        courrier_records = []
        for c in dossier["courriers"]:
            rec = dict(_strip_private(c), **{"Client": [client_id]})
            if c.get("_organisme"):
                rec["Organisme"] = [org_ids[c["_organisme"]]]
            if c.get("_demarche"):
                rec["Démarche"] = [dem_ids[c["_demarche"]]]
            courrier_records.append(rec)
        client.create_records(base_id, "Courriers", courrier_records)
        counts["Courriers"] += len(courrier_records)
        log(f"✔ dossier « {nom} » : {len(org_records)} organismes, {len(dem_records)} démarches, {len(courrier_records)} courriers")
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--base", help="identifiant de la base (sinon AIRTABLE_BASE_ID ou .base_id)")
    args = parser.parse_args(argv)
    dossiers = build_seed()
    if args.dry_run:
        print(json.dumps(dossiers, ensure_ascii=False, indent=2))
        return 0
    load_env()
    base_id = resolve_base_id(args.base)
    if not base_id:
        print("✘ base inconnue : lancer create_base.py d'abord ou renseigner AIRTABLE_BASE_ID")
        return 1
    try:
        counts = seed(AirtableClient(), base_id, dossiers)
    except AirtableError as exc:
        print(f"✘ {exc}")
        return 1
    print("Résumé :", ", ".join(f"{k} {v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
