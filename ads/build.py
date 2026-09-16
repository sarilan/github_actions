#!/usr/bin/env python3
"""Construit les fichiers d'import Google Ads Editor de la campagne Relais.

Usage :
    python3 ads/build.py          # écrit campagne-google-ads.csv et mots-cles-negatifs.csv
    python3 ads/check.py          # contrôle les fichiers produits

Le CSV utilise les en-têtes de colonnes anglais reconnus par Google Ads Editor
(« Campaign », « Ad Group », « Keyword », « Criterion Type », « Headline 1 »…). Google
Ads Editor identifie le type de chaque ligne (campagne, groupe, mot-clé, annonce,
extension) d'après les colonnes renseignées. Si une colonne n'est pas reconnue
automatiquement à l'import, l'assistant d'import permet de la faire correspondre.
"""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAGNE_CSV = HERE / "campagne-google-ads.csv"
NEGATIFS_CSV = HERE / "mots-cles-negatifs.csv"

CAMPAGNE = "Relais — Parents France"
SITE = "{{SITE_URL}}"
UTM = "utm_source=google&utm_medium=cpc&utm_campaign=relais-parents-france"
BUDGET_JOUR = "20"
PAYS = [
    "Israel",
    "Switzerland",
    "Belgium",
    "Luxembourg",
    "United Kingdom",
    "United States",
    "Canada",
    "United Arab Emirates",
    "Singapore",
    "Hong Kong",
]

COLONNES = [
    "Campaign", "Campaign Type", "Campaign Status", "Budget", "Budget type", "Networks",
    "Languages", "Location", "Bid Strategy Type", "Ad rotation",
    "Ad Group", "Ad Group Type", "Ad Group Status",
    "Keyword", "Criterion Type", "Status",
    "Ad type", "Ad Status",
    *[f"Headline {i}" for i in range(1, 16)],
    *[f"Description {i}" for i in range(1, 5)],
    "Path 1", "Path 2", "Final URL",
    "Sitelink text", "Sitelink final URL", "Sitelink description 1", "Sitelink description 2",
    "Callout text",
    "Structured snippet header", "Structured snippet values",
    "Phone number", "Country code",
]


def url(content: str) -> str:
    return f"{SITE}/?{UTM}&utm_content={content}&utm_term={{keyword}}"


# ---------------------------------------------------------------------------
# Groupes d'annonces : mots-clés (section 10.1 du document projet, enrichis),
# 15 titres (≤ 30 caractères) et 4 descriptions (≤ 90 caractères)
# ---------------------------------------------------------------------------
GROUPES = [
    {
        "nom": "Intention directe",
        "slug": "intention-directe",
        "path": ("parents", "administratif"),
        "mots_cles": [
            "aider parents administratif à distance",
            "gérer démarches parents âgés expatrié",
            "service administratif personnes âgées",
            "aide administrative parents âgés",
            "aide administrative personne âgée",
            "assistant administratif parent âgé",
            "gestion administrative personne âgée",
            "aide démarches administratives seniors",
            "démarches administratives parents âgés",
            "s'occuper des papiers de ses parents",
            "gérer les papiers de ses parents à distance",
            "mandataire administratif personne âgée",
        ],
        "titres": [
            "L'administratif de vos parents",
            "Vos parents en France, gérés",
            "Relais, mandataire à distance",
            "Courrier, Ameli, impôts, aides",
            "Traitement sous 48 h ouvrées",
            "Un rapport mensuel, c'est tout",
            "Mandat écrit et révocable",
            "Aucune opération financière",
            "Abonnement 89 € par mois",
            "Sans engagement, résiliable",
            "Pour les enfants expatriés",
            "Un interlocuteur unique",
            "Appel de 20 minutes offert",
            "Vos parents restent décideurs",
            "Diagnostic complet offert",
        ],
        "descriptions": [
            "Relais reçoit le courrier de votre parent, gère ses comptes en ligne, fait les démarches.",
            "Mandat écrit, rapport mensuel, alerte en cas d'urgence. Aucune opération financière.",
            "Vous vivez à l'étranger, votre parent est en France. Nous prenons le relais sous 48 h.",
            "89 € par mois, sans engagement. Diagnostic offert. Réservez un appel de 20 minutes.",
        ],
    },
    {
        "nom": "Problème précis",
        "slug": "probleme-precis",
        "path": ("ameli", "impots"),
        "mots_cles": [
            "ma mère n'arrive pas à utiliser ameli",
            "parent âgé compte ameli bloqué",
            "parent âgé déclaration impôts en ligne",
            "aide déclaration impôts personne âgée",
            "aide franceconnect personne âgée",
            "parent âgé identifiants impots gouv perdus",
            "aide carte vitale personne âgée",
            "aide ants personne âgée",
            "renouvellement carte identité personne âgée",
            "aide info retraite personne âgée",
            "pension de réversion démarches",
            "courrier administratif parents âgés",
        ],
        "titres": [
            "Compte Ameli bloqué ?",
            "Déclaration d'impôts du parent",
            "FranceConnect, on s'en occupe",
            "Carte Vitale, attestations",
            "Identifiants perdus ? Réglé",
            "Retraite, pension de réversion",
            "Relais, mandataire à distance",
            "Traité sous 48 h ouvrées",
            "Mandat écrit, signé du parent",
            "Un rapport mensuel pour vous",
            "Aucune opération financière",
            "89 € par mois, sans engagement",
            "Pour les enfants expatriés",
            "Appel de 20 minutes offert",
            "Fini les soirées au téléphone",
        ],
        "descriptions": [
            "Ameli bloqué, impôts en ligne, FranceConnect : nous récupérons les accès, puis le reste.",
            "Sous mandat écrit, sans jamais toucher à l'argent. Chaque action est tracée et rapportée.",
            "Traitement sous 48 h ouvrées, ligne dédiée pour votre parent, alerte immédiate si urgence.",
            "Abonnement 89 € par mois, sans engagement. Réservez un appel de 20 minutes, sans frais.",
        ],
    },
    {
        "nom": "Événement de vie",
        "slug": "evenement-de-vie",
        "path": ("apa", "hospitalisation"),
        "mots_cles": [
            "sortie hospitalisation démarches",
            "démarches après hospitalisation personne âgée",
            "dossier apa comment faire",
            "demande apa à domicile",
            "aide pour dossier apa",
            "entrée ehpad démarches",
            "dossier admission ehpad",
            "aide sociale hébergement démarches",
            "démarches après décès parent",
            "déclaration décès organismes",
            "aide à domicile personne âgée démarches",
            "dossier viatrajectoire aide",
        ],
        "titres": [
            "Sortie d'hospitalisation",
            "Dossier APA pris en charge",
            "Entrée en EHPAD, démarches",
            "Démarches après un décès",
            "Aide à domicile, dossier fait",
            "Relais coordonne à distance",
            "Vous êtes loin, nous sommes là",
            "Forfaits à partir de 490 €",
            "Mandat écrit, tout est tracé",
            "Aucune opération financière",
            "Un interlocuteur unique",
            "Traité sous 48 h ouvrées",
            "Appel de 20 minutes offert",
            "Pour les enfants expatriés",
            "Coordination avec le notaire",
        ],
        "descriptions": [
            "Hospitalisation, APA, EHPAD, décès : nous montons les dossiers et suivons les organismes.",
            "Forfaits Hospitalisation 490 €, EHPAD 690 €, Succession 890 €. Ou abonnement 89 €/mois.",
            "Mandat écrit, aucune opération financière, rapport détaillé. Vous validez, nous faisons.",
            "Vous ne pouvez pas être en France ? Réservez un appel de 20 min. Nous prenons le relais.",
        ],
    },
    {
        "nom": "Procuration et mandat",
        "slug": "procuration-mandat",
        "path": ("mandat", "parents"),
        "mots_cles": [
            "procuration administrative parent âgé",
            "procuration démarches administratives",
            "mandat administratif personne âgée",
            "mandat pour gérer les affaires de ses parents",
            "procuration parent âgé administratif",
            "représenter ses parents administration",
            "procuration ameli",
            "procuration impôts parent",
            "alternative tutelle parent âgé",
            "procuration courrier personne âgée",
            "mandat de gestion administrative",
            "procuration pour gérer les papiers de ma mère",
        ],
        "titres": [
            "Mandat administratif complet",
            "Procuration simple, sans juge",
            "Votre parent reste décideur",
            "Révocable à tout moment",
            "Aucune opération financière",
            "Relais, mandataire à distance",
            "Courrier, Ameli, impôts, aides",
            "Mandat écrit, relu par avocat",
            "Copie du mandat pour vous",
            "Coffre chiffré, accès tracés",
            "Assurance RC professionnelle",
            "Traitement sous 48 h ouvrées",
            "89 € par mois, sans engagement",
            "Appel de 20 minutes offert",
            "Pour les enfants expatriés",
        ],
        "descriptions": [
            "Un mandat de représentation administrative écrit, limité, révocable. Le parent décide.",
            "Sous mandat pour le courrier, les comptes en ligne et les demandes. Jamais pour l'argent.",
            "Coffre chiffré, journal d'accès, assurance responsabilité civile pro, rapport mensuel.",
            "Une alternative simple à la tutelle pour un parent autonome. Réservez un appel de 20 min.",
        ],
    },
]

SITELINKS = [
    ("Comment ça marche", "#fonctionnement", "Mandat, diagnostic, 48 h", "puis rapport mensuel"),
    ("Tarifs", "#tarifs", "89 € par mois", "sans engagement"),
    ("Sécurité et mandat", "#confiance", "Mandat écrit, coffre chiffré", "journal d'accès, RC pro"),
    ("Questions fréquentes", "#faq", "Légalité, tutelle, TVA", "résiliation, données"),
]

ACCROCHES = [
    "Traitement sous 48 h",
    "Zéro opération financière",
    "Rapport mensuel",
    "Sans engagement",
]

EXTRAITS = ("Services", ["Courrier", "Ameli", "Retraite", "Impôts", "APA", "Mutuelle", "Énergie"])

TELEPHONE = ("{{TELEPHONE_RELAIS}}", "FR")

# ---------------------------------------------------------------------------
# Mots-clés négatifs (niveau campagne) — expression négative
# ---------------------------------------------------------------------------
NEGATIFS = [
    # emploi et formation
    "emploi", "offre d'emploi", "recrutement", "job", "salaire", "cdi", "cdd", "intérim", "stage",
    "alternance", "formation", "diplôme", "concours", "école", "cours", "bts", "licence", "master",
    "fiche métier", "devenir", "reconversion",
    # gratuit et institutionnel
    "gratuit", "gratuite", "gratuitement", "bénévole", "bénévolat", "association", "ccas", "mairie",
    "assistante sociale", "maison france services", "france services", "point info",
    # juridique et protection judiciaire
    "tutelle judiciaire", "curatelle", "juge des tutelles", "juge des contentieux", "avocat", "notaire",
    "huissier", "tribunal", "jurisprudence", "procès", "plainte", "abus de faiblesse", "mandataire judiciaire",
    "mjpm", "habilitation familiale", "mandat de protection future", "mandat de protection",
    # logiciels et modèles
    "logiciel", "application", "appli", "télécharger", "pdf", "modèle", "modele", "exemple",
    "lettre type", "formulaire", "cerfa", "définition", "wikipedia", "forum", "avis",
    # hors cible géographique ou métier
    "belgique administratif", "suisse administratif", "québec", "auto-entrepreneur", "entreprise",
    "société", "comptable", "secrétaire", "assistante de direction", "domiciliation entreprise",
    # santé, soins, immobilier
    "infirmier", "infirmière", "médecin", "soins", "toilette", "ménage", "courses", "portage repas",
    "téléassistance", "maison de retraite prix", "vente", "achat", "immobilier", "viager",
    # divers
    "livre", "film", "série", "définition", "traduction", "anglais",
]


def _base_row() -> dict[str, str]:
    return {c: "" for c in COLONNES}


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    camp = _base_row()
    camp.update({
        "Campaign": CAMPAGNE,
        "Campaign Type": "Search",
        "Campaign Status": "Paused",
        "Budget": BUDGET_JOUR,
        "Budget type": "Daily",
        "Networks": "Google search",
        "Languages": "French",
        "Location": ";".join(PAYS),
        "Bid Strategy Type": "Maximize conversions",
        "Ad rotation": "Optimize",
    })
    rows.append(camp)

    for g in GROUPES:
        ag = _base_row()
        ag.update({"Campaign": CAMPAGNE, "Ad Group": g["nom"], "Ad Group Type": "Standard", "Ad Group Status": "Enabled"})
        rows.append(ag)

        for kw in g["mots_cles"]:
            for ctype in ("Exact", "Phrase"):
                r = _base_row()
                r.update({"Campaign": CAMPAGNE, "Ad Group": g["nom"], "Keyword": kw, "Criterion Type": ctype, "Status": "Enabled"})
                rows.append(r)

        ad = _base_row()
        ad.update({"Campaign": CAMPAGNE, "Ad Group": g["nom"], "Ad type": "Responsive search ad", "Ad Status": "Enabled"})
        for i, t in enumerate(g["titres"], start=1):
            ad[f"Headline {i}"] = t
        for i, d in enumerate(g["descriptions"], start=1):
            ad[f"Description {i}"] = d
        ad["Path 1"], ad["Path 2"] = g["path"]
        ad["Final URL"] = url(g["slug"])
        rows.append(ad)

    for texte, ancre, d1, d2 in SITELINKS:
        r = _base_row()
        r.update({
            "Campaign": CAMPAGNE, "Sitelink text": texte,
            "Sitelink final URL": f"{SITE}/?{UTM}&utm_content=sitelink{ancre}",
            "Sitelink description 1": d1, "Sitelink description 2": d2,
        })
        rows.append(r)

    for a in ACCROCHES:
        r = _base_row()
        r.update({"Campaign": CAMPAGNE, "Callout text": a})
        rows.append(r)

    r = _base_row()
    r.update({"Campaign": CAMPAGNE, "Structured snippet header": EXTRAITS[0], "Structured snippet values": ";".join(EXTRAITS[1])})
    rows.append(r)

    r = _base_row()
    r.update({"Campaign": CAMPAGNE, "Phone number": TELEPHONE[0], "Country code": TELEPHONE[1]})
    rows.append(r)

    return rows


def build_negatifs() -> list[dict[str, str]]:
    vus: set[str] = set()
    rows = []
    for kw in NEGATIFS:
        k = kw.strip().lower()
        if k in vus:
            continue
        vus.add(k)
        rows.append({"Campaign": CAMPAGNE, "Keyword": k, "Criterion Type": "Negative Phrase"})
    return rows


def main() -> None:
    rows = build_rows()
    with CAMPAGNE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        w.writerows(rows)
    negs = build_negatifs()
    with NEGATIFS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Campaign", "Keyword", "Criterion Type"])
        w.writeheader()
        w.writerows(negs)
    print(f"✔ {CAMPAGNE_CSV.name} : {len(rows)} lignes")
    print(f"✔ {NEGATIFS_CSV.name} : {len(negs)} mots-clés négatifs")


if __name__ == "__main__":
    main()
