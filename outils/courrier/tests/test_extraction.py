"""Tests unitaires : dates (formats français absolus et relatifs), montants, références, urgence."""
from datetime import date

import pytest

import classify
from classify import extract_amounts, extract_deadlines, extract_references, find_document_date, normalize, principal_amount

REF = date(2026, 9, 16)
DOC = date(2026, 9, 10)


def deadlines(text, doc=DOC, ref=REF):
    return extract_deadlines(normalize(text), doc, ref)


# --- dates absolues -----------------------------------------------------------
@pytest.mark.parametrize("texte, attendu", [
    ("Merci de répondre avant le 15 octobre 2026.", "2026-10-15"),
    ("Réponse attendue au plus tard le 03/10/2026.", "2026-10-03"),
    ("Vous pouvez payer jusqu'au 30.09.2026 sans majoration.", "2026-09-30"),
    ("À retourner d'ici le 1er novembre 2026.", "2026-11-01"),
    ("Date limite de paiement : 02/10/2026", "2026-10-02"),
    ("Date limite de paiement : le 2 oct. 2026", "2026-10-02"),
    ("Échéance : le 01/11/2026", "2026-11-01"),
    ("Votre rendez-vous est fixé le 29/09/2026 à 10 h 15.", "2026-09-29"),
    ("Vous êtes convoqué à l'audience du 5 novembre 2026.", "2026-11-05"),
    ("Le titre sera détruit au-delà du 14/12/2026.", "2026-12-14"),
    ("Le contrat expire le 15/03/2027.", "2027-03-15"),
    ("règlement attendu pour le 20/10/26", "2026-10-20"),
])
def test_dates_absolues(texte, attendu):
    result = deadlines(texte)
    assert result, texte
    assert result[0]["date"] == attendu
    assert result[0]["type"] == "absolue"
    assert result[0]["jours_restants"] == (date.fromisoformat(attendu) - REF).days


def test_date_passee_sans_introduction_forte_ignoree():
    # « le 3 septembre 2026 » sans mot-clé d'échéance et antérieur au courrier : ce n'est pas une échéance
    assert deadlines("Suite à votre courrier du 3 septembre 2026, nous vous informons que votre dossier est complet.") == []


def test_date_future_faible_avec_contexte():
    assert deadlines("Merci de nous renvoyer le formulaire signé, le 30 septembre 2026 au plus tard.")[0]["date"] == "2026-09-30"


# --- dates relatives ----------------------------------------------------------
@pytest.mark.parametrize("texte, attendu", [
    ("Merci de régulariser sous 30 jours.", "2026-10-10"),
    ("dans un délai de deux mois à compter de la présente", "2026-11-10"),
    ("Vous disposez d'un délai de huit jours pour régler.", "2026-09-18"),
    ("Réponse souhaitée dans les 15 jours.", "2026-09-25"),
    ("sous 10 jours ouvrés", "2026-09-24"),
    ("dans un délai maximum de trois semaines", "2026-10-01"),
    ("d'ici 1 mois", "2026-10-10"),
    ("dans un délai d'un an", "2027-09-10"),
])
def test_dates_relatives(texte, attendu):
    result = deadlines(texte)
    assert result, texte
    assert result[0]["date"] == attendu
    assert result[0]["type"] == "relative"


def test_relatif_calcule_depuis_la_date_de_reference_sans_date_de_courrier():
    result = extract_deadlines(normalize("à régler sous 30 jours"), None, REF)
    assert result[0]["date"] == "2026-10-16"


def test_fin_de_mois_et_annee_bissextile():
    assert classify._add_relative(date(2026, 1, 31), 1, "mois") == date(2026, 2, 28)
    assert classify._add_relative(date(2028, 1, 31), 1, "mois") == date(2028, 2, 29)
    assert classify._add_relative(date(2026, 12, 15), 2, "mois") == date(2027, 2, 15)
    assert classify._add_relative(date(2026, 9, 18), 2, "jours ouvres") == date(2026, 9, 22)  # vendredi -> mardi


def test_categorie_recours_et_information():
    r = deadlines("Vous pouvez contester cette décision dans un délai de deux mois. Le remboursement interviendra sous 30 jours. Merci de répondre avant le 15 octobre 2026.")
    cats = {x["texte"][:20]: x["categorie"] for x in r}
    assert any(c == "recours" for c in cats.values())
    assert any(c == "information" for c in cats.values())
    assert any(c == "action" for c in cats.values())


def test_doublons_de_dates_fusionnes():
    r = deadlines("Avant le 15/10/2026. Nous répétons : avant le 15 octobre 2026.")
    assert len(r) == 1


# --- date du courrier ---------------------------------------------------------
@pytest.mark.parametrize("texte, attendu", [
    ("Cergy, le 3 septembre 2026\n\nMadame,", date(2026, 9, 3)),
    ("Date : 08/09/2026\nObjet : facture", date(2026, 9, 8)),
    ("Fait à Lyon, le 12/09/2026", date(2026, 9, 12)),
    ("Facture n° 12 du 8 septembre 2026", date(2026, 9, 8)),
    ("Aucune date ici", None),
])
def test_date_du_courrier(texte, attendu):
    assert find_document_date(normalize(texte), REF) == attendu


def test_parse_date_invalide():
    assert classify.parse_date(classify.DATE_RE.match("31/02/2026")) is None


# --- montants -----------------------------------------------------------------
@pytest.mark.parametrize("texte, valeurs", [
    ("Montant à payer : 486,30 €", [486.30]),
    ("soit un montant de 1 234,56 euros", [1234.56]),
    ("Total : 1.234,56 €", [1234.56]),
    ("frais : 12 EUR et 7,5 €", [12.0, 7.5]),
    ("consommation 2 310 kWh, montant 96,00 €", [96.0]),
    ("montant 340 000 € TTC, quote-part 3 400,00 €", [340000.0, 3400.0]),
])
def test_montants(texte, valeurs):
    assert [a["valeur"] for a in extract_amounts(normalize(texte))] == valeurs


def test_montant_principal_priorite():
    amounts = extract_amounts(normalize("Abonnement : 78,45 €. Consommation : 407,85 €. Montant à payer : 486,30 € TTC. Frais 5 €"))
    assert principal_amount(amounts) == 486.30
    assert principal_amount([]) is None
    assert principal_amount(extract_amounts(normalize("prime 312,50 € puis 20 €"))) == 312.50


# --- références ---------------------------------------------------------------
def test_references():
    refs = extract_references(normalize("N° de dossier : APA 2026-0412\nVotre référence : 95-DUR-001\nN° de contrat : LB-77-23456 (Livebox)\nN° de sécurité sociale : 2 49 03 75 116 234 56"))
    valeurs = [r["valeur"] for r in refs]
    assert "APA 2026-0412" in valeurs
    assert "95-DUR-001" in valeurs
    assert "LB-77-23456" in valeurs
    assert any(v.startswith("2 49 03 75") for v in valeurs)
    assert extract_references(normalize("Référence : sans chiffres")) == []


# --- urgence ------------------------------------------------------------------
def test_urgence_regles(rules):
    org_neutre = {"critique": False}
    org_critique = {"critique": True}
    u = classify.compute_urgency("Facture", org_neutre, [], 50.0, "", rules)
    assert u["niveau"] == 2
    u = classify.compute_urgency("Facture", org_neutre, [{"jours_restants": 3}], 50.0, "", rules)
    assert u["niveau"] == 3 and "sous 7 jours" in " ".join(u["motifs"])
    u = classify.compute_urgency("Facture", org_neutre, [{"jours_restants": -2}], 50.0, "", rules)
    assert u["niveau"] == 4
    u = classify.compute_urgency("Facture", org_neutre, [], 900.0, "", rules)
    assert u["niveau"] == 3
    u = classify.compute_urgency("Décision", org_neutre, [], 900.0, "", rules)
    assert u["niveau"] == 2  # montant élevé ignoré hors documents de paiement
    u = classify.compute_urgency("Facture", org_critique, [], 50.0, "majoration et saisie", rules)
    assert u["niveau"] == 3  # critique + sanction : +1 au plus
    u = classify.compute_urgency("Information", org_neutre, [], 4920.0, "", rules)
    assert u["niveau"] == 1
    u = classify.compute_urgency("Mise en demeure", org_critique, [{"jours_restants": 1}], 5000.0, "saisie", rules)
    assert u["niveau"] == 4
    u = classify.compute_urgency("Type inconnu", org_neutre, [], None, "", rules)
    assert u["niveau"] == 2


def test_normalize():
    assert normalize("Échéance  :  D’ICI   le\tLUNDI") == "echeance : d'ici le lundi"
    assert normalize("œuvre") == "oeuvre"


def test_classify_text_avertissements(rules):
    r = classify.classify_text("ok", reference=REF, rules=rules)
    assert "texte très court : OCR probablement incomplet, vérifier le scan" in r.avertissements
    assert r.organisme["id"] is None and r.type["nom"] == "Autre"
    assert r.date_limite_principale is None and r.montant_principal is None


def test_summarize_objet():
    assert classify.summarize("Bonjour\nObjet : demande de pièces\nSuite") == "Objet : demande de pièces"
    assert classify.summarize("Ligne une\nLigne deux") == "Ligne une Ligne deux"
