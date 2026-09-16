"""Validation structurelle de schema.json (types Airtable, liens, vues, champs calculés)."""
import json
import re
from pathlib import Path

import jsonschema
import pytest

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE.parent / "schema.json").read_text(encoding="utf-8"))

FIELD_TYPES = {
    "singleLineText", "multilineText", "richText", "email", "url", "phoneNumber", "number", "percent", "currency",
    "singleSelect", "multipleSelects", "date", "dateTime", "checkbox", "multipleAttachments", "formula", "createdTime",
    "lastModifiedTime", "multipleRecordLinks", "rating", "duration", "count", "rollup", "multipleLookupValues", "autoNumber",
}
PRIMARY_TYPES = {"singleLineText", "email", "url", "phoneNumber", "number", "date", "dateTime", "formula", "autoNumber", "barcode"}

META_SCHEMA = {
    "type": "object",
    "required": ["base", "tables", "links", "views"],
    "properties": {
        "base": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string", "minLength": 1}}},
        "tables": {
            "type": "array", "minItems": 4, "maxItems": 4,
            "items": {
                "type": "object", "required": ["name", "fields"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "fields": {
                        "type": "array", "minItems": 1,
                        "items": {
                            "type": "object", "required": ["name", "type"],
                            "properties": {
                                "name": {"type": "string", "minLength": 1},
                                "type": {"type": "string", "enum": sorted(FIELD_TYPES)},
                                "options": {"type": "object"},
                                "description": {"type": "string"},
                            },
                            "additionalProperties": False,
                        },
                    },
                },
            },
        },
        "links": {"type": "array", "items": {"type": "object", "required": ["from_table", "field", "to_table", "inverse_field"]}},
        "views": {
            "type": "array", "minItems": 6, "maxItems": 6,
            "items": {"type": "object", "required": ["table", "name", "type", "filter", "sort", "group_by", "fields_visible"]},
        },
    },
}


def tables_by_name():
    return {t["name"]: t for t in SCHEMA["tables"]}


def test_schema_matches_meta_schema():
    jsonschema.validate(SCHEMA, META_SCHEMA)


def test_four_expected_tables():
    assert [t["name"] for t in SCHEMA["tables"]] == ["Clients", "Organismes", "Démarches", "Courriers"]


@pytest.mark.parametrize("table", SCHEMA["tables"], ids=lambda t: t["name"])
def test_field_names_unique_and_primary_valid(table):
    names = [f["name"].lower() for f in table["fields"]]
    assert len(names) == len(set(names)), f"doublons dans {table['name']}"
    assert table["fields"][0]["type"] in PRIMARY_TYPES, "le premier champ est le champ principal : type texte attendu"
    assert all(f["type"] != "multipleRecordLinks" for f in table["fields"]), "les liens sont déclarés dans « links »"


@pytest.mark.parametrize("table", SCHEMA["tables"], ids=lambda t: t["name"])
def test_select_fields_have_choices(table):
    for f in table["fields"]:
        if f["type"] in ("singleSelect", "multipleSelects"):
            choices = f.get("options", {}).get("choices", [])
            assert choices, f"{table['name']}.{f['name']} sans choix"
            names = [c["name"] for c in choices]
            assert len(names) == len(set(names)), f"choix en double dans {f['name']}"
        if f["type"] == "currency":
            assert f["options"] == {"precision": 2, "symbol": "€"}
        if f["type"] == "date":
            assert f["options"]["dateFormat"]["name"] == "european"


def test_formulas_reference_existing_fields():
    for table in SCHEMA["tables"]:
        names = {f["name"] for f in table["fields"]}
        for f in table["fields"]:
            if f["type"] == "formula":
                formula = f["options"]["formula"]
                for ref in re.findall(r"\{([^}]+)\}", formula):
                    assert ref in names, f"{table['name']}.{f['name']} référence un champ inconnu : {ref}"
                assert formula.count("(") == formula.count(")"), f"parenthèses déséquilibrées dans {f['name']}"


def test_links_reference_existing_tables_and_do_not_collide():
    tables = tables_by_name()
    for link in SCHEMA["links"]:
        assert link["from_table"] in tables and link["to_table"] in tables
        src_names = {f["name"].lower() for f in tables[link["from_table"]]["fields"]}
        dst_names = {f["name"].lower() for f in tables[link["to_table"]]["fields"]}
        assert link["field"].lower() not in src_names, f"{link['field']} existe déjà dans {link['from_table']}"
        assert link["inverse_field"].lower() not in dst_names, f"{link['inverse_field']} existe déjà dans {link['to_table']}"
    pairs = [(l["from_table"], l["field"]) for l in SCHEMA["links"]]
    assert len(pairs) == len(set(pairs))
    assert {(l["from_table"], l["to_table"]) for l in SCHEMA["links"]} >= {
        ("Organismes", "Clients"), ("Démarches", "Clients"), ("Démarches", "Organismes"),
        ("Courriers", "Clients"), ("Courriers", "Organismes"), ("Courriers", "Démarches"),
    }


def test_computed_fields_present():
    tables = tables_by_name()
    dem = {f["name"]: f for f in tables["Démarches"]["fields"]}
    assert dem["Jours avant échéance"]["type"] == "formula"
    assert dem["Statut couleur"]["type"] == "formula"
    assert dem["Mois de clôture"]["type"] == "formula"
    cour = {f["name"]: f for f in tables["Courriers"]["fields"]}
    assert cour["Alerte 48 h"]["type"] == "formula"
    assert cour["Délai de traitement (jours)"]["type"] == "formula"


def test_views_reference_existing_tables_and_fields():
    tables = tables_by_name()
    link_fields = {}
    for l in SCHEMA["links"]:
        link_fields.setdefault(l["from_table"], set()).add(l["field"])
        link_fields.setdefault(l["to_table"], set()).add(l["inverse_field"])
    expected = {"Échéances 30 jours", "Démarches en cours", "Courrier non traité", "Par client", "Par opérateur", "Rapport du mois"}
    assert {v["name"] for v in SCHEMA["views"]} == expected
    for v in SCHEMA["views"]:
        assert v["table"] in tables
        available = {f["name"] for f in tables[v["table"]]["fields"]} | link_fields.get(v["table"], set())
        for name in v["fields_visible"]:
            assert name in available, f"vue {v['name']} : champ inconnu {name}"
        for s in v["sort"]:
            assert s["field"] in available and s["direction"] in ("asc", "desc")
        if v["group_by"]:
            assert v["group_by"] in available
        if v["filter"]:
            for ref in re.findall(r"\{([^}]+)\}", v["filter"]):
                assert ref in available, f"vue {v['name']} : filtre sur champ inconnu {ref}"
