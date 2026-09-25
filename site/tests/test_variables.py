import pytest

from variables import VariablesManquantes, render, variables_utilisees


def test_substitution_simple():
    assert render("Bonjour {{NOM}}.", {"NOM": "Relais"}) == "Bonjour Relais."


def test_variable_manquante_leve_une_erreur_avec_tous_les_noms():
    with pytest.raises(VariablesManquantes) as e:
        render("{{A}} {{B}} {{A}}", {"A": " "})
    assert e.value.noms == ["A", "B"]


def test_blocs_conditionnels():
    gabarit = "x{{#T}} tél. {{T}}{{/T}}{{^T}} sans tél.{{/T}}"
    assert render(gabarit, {"T": "01"}) == "x tél. 01"
    assert render(gabarit, {"T": ""}) == "x sans tél."
    assert render(gabarit, {}) == "x sans tél."


def test_bloc_vide_n_exige_pas_ses_variables_internes():
    assert render("a{{#X}}{{Y}}{{/X}}b", {"X": ""}) == "ab"


def test_blocs_multilignes_et_imbriques_de_noms_differents():
    gabarit = "{{#A}}\nligne {{#B}}{{B}}{{/B}}\n{{/A}}fin"
    assert render(gabarit, {"A": "1", "B": "2"}) == "\nligne 2\nfin"
    assert render(gabarit, {"A": "1"}) == "\nligne \nfin"


def test_mode_modele_garde_les_champs_et_la_branche_positive():
    gabarit = "{{#T}}Tél. {{T}}{{/T}}{{^T}}Sans{{/T}} — {{NOM}}"
    assert render(gabarit) == "Tél. {{T}} — {{NOM}}"


def test_echappement():
    assert render("{{X}}", {"X": "<b>"}, echapper=lambda s: s.replace("<", "&lt;")) == "&lt;b>"


def test_variables_utilisees():
    assert variables_utilisees("{{A}} {{#B}}{{C}}{{/B}} {{^D}}x{{/D}}") == {"A", "B", "C", "D"}
