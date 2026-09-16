"""Chaque courrier synthétique du corpus doit être classé comme attendu (attendus.yaml)."""
import yaml
import pytest

import classify
from conftest import CORPUS, REFERENCE

ATTENDUS = yaml.safe_load((CORPUS / "attendus.yaml").read_text(encoding="utf-8"))


def test_corpus_size_and_coverage(rules):
    assert len(ATTENDUS) >= 25
    types_attendus = {v["type"] for v in ATTENDUS.values()}
    assert types_attendus >= {"Facture", "Relance", "Mise en demeure", "Demande de pièces", "Information", "Décision", "Convocation"}
    organismes = {v["organisme"] for v in ATTENDUS.values()} - {None}
    majeurs = {"cpam", "assurance-retraite", "agirc-arrco", "dgfip", "caf", "conseil-departemental", "ants", "mairie-ccas", "edf", "orange", "la-poste"}
    assert majeurs <= organismes
    assert len(rules["organismes"]) >= 40
    for f in CORPUS.glob("*.txt"):
        assert f.stem in ATTENDUS, f"{f.name} sans valeurs attendues"


@pytest.mark.parametrize("nom", sorted(ATTENDUS), ids=sorted(ATTENDUS))
def test_courrier(nom, rules):
    attendu = ATTENDUS[nom]
    result = classify.classify_file(CORPUS / f"{nom}.txt", reference=REFERENCE, rules=rules)
    assert result.organisme["id"] == attendu["organisme"]
    assert result.type["nom"] == attendu["type"]
    assert result.date_limite_principale == attendu["date_limite_principale"]
    assert result.montant_principal == attendu["montant_principal"]
    assert result.urgence["niveau"] == attendu["urgence"]
    assert 1 <= result.urgence["niveau"] <= 4
    if attendu["organisme"]:
        assert result.organisme["confiance"] >= 0.3
        assert result.organisme["nom"]
    else:
        assert "organisme incertain : vérifier l'expéditeur" in result.avertissements
    payload = result.to_json()
    assert '"urgence"' in payload and '"organisme"' in payload
