"""Simulation en mémoire de l'API Airtable, pour les tests (aucun appel réseau).

Reproduit le comportement des points de terminaison utilisés par airtable_client.py :
création de base, de table, de champ (avec création automatique du champ inverse d'un
lien), lecture du schéma, création, mise à jour et lecture d'enregistrements avec
pagination et un sous-ensemble de filterByFormula ({Champ} = 'valeur').

Usage :
    from mock_api import MockAirtable
    mock = MockAirtable()
    client = AirtableClient(transport=mock.transport)
"""
from __future__ import annotations

import copy
import itertools
import re
from typing import Any

from airtable_client import API_URL, AirtableError

_EQ_FORMULA = re.compile(r"^\{(?P<field>[^}]+)\}\s*=\s*'(?P<value>(?:\\'|[^'])*)'$")


class MockAirtable:
    def __init__(self, workspace_id: str = "wspMOCK00000000000", reject_field_types: set[str] | None = None):
        self.workspace_id = workspace_id
        self.bases: dict[str, dict] = {}
        self.records: dict[tuple[str, str], list[dict]] = {}
        self.calls: list[tuple[str, str]] = []
        self.reject_field_types = reject_field_types or set()
        self._ids = itertools.count(1)

    # -- utilitaires --------------------------------------------------------
    def _new_id(self, prefix: str) -> str:
        return f"{prefix}{next(self._ids):014d}"

    def _table(self, base_id: str, table_ref: str) -> dict:
        base = self.bases.get(base_id)
        if base is None:
            raise AirtableError(404, "NOT_FOUND base inconnue")
        for t in base["tables"]:
            if t["id"] == table_ref or t["name"] == table_ref:
                return t
        raise AirtableError(404, f"TABLE_NOT_FOUND {table_ref}")

    def _make_field(self, base: dict, table: dict, spec: dict) -> dict:
        if spec["type"] in self.reject_field_types:
            raise AirtableError(422, f"INVALID_REQUEST_UNKNOWN champ de type {spec['type']} non pris en charge")
        if any(f["name"].lower() == spec["name"].lower() for f in table["fields"]):
            raise AirtableError(422, f"DUPLICATE_OR_EMPTY_FIELD_NAME {spec['name']}")
        field = {"id": self._new_id("fld"), "name": spec["name"], "type": spec["type"]}
        if "description" in spec:
            field["description"] = spec["description"]
        options = copy.deepcopy(spec.get("options", {}))
        if spec["type"] in ("singleSelect", "multipleSelects"):
            for choice in options.get("choices", []):
                choice.setdefault("id", self._new_id("sel"))
        if spec["type"] == "multipleRecordLinks":
            target = next((t for t in base["tables"] if t["id"] == options.get("linkedTableId")), None)
            if target is None:
                raise AirtableError(422, "INVALID_REQUEST_UNKNOWN linkedTableId inconnu")
            inverse = {"id": self._new_id("fld"), "name": table["name"], "type": "multipleRecordLinks",
                       "options": {"linkedTableId": table["id"], "isReversed": False, "prefersSingleRecordLink": False}}
            base_name = inverse["name"]
            n = 2
            while any(f["name"] == inverse["name"] for f in target["fields"]):
                inverse["name"] = f"{base_name} {n}"
                n += 1
            options["inverseLinkFieldId"] = inverse["id"]
            inverse["options"]["inverseLinkFieldId"] = field["id"]
            target["fields"].append(inverse)
        if options:
            field["options"] = options
        table["fields"].append(field)
        return field

    def _make_table(self, base: dict, spec: dict) -> dict:
        if not spec.get("fields"):
            raise AirtableError(422, "INVALID_REQUEST_UNKNOWN une table doit avoir au moins un champ")
        table = {"id": self._new_id("tbl"), "name": spec["name"], "description": spec.get("description", ""), "fields": [], "views": []}
        base["tables"].append(table)
        for fspec in spec["fields"]:
            self._make_field(base, table, fspec)
        table["primaryFieldId"] = table["fields"][0]["id"]
        self.records[(base["id"], table["id"])] = []
        return table

    # -- transport ----------------------------------------------------------
    def transport(self, method: str, url: str, json: dict | None, params: dict | None) -> dict:
        self.calls.append((method, url))
        path = url[len(API_URL):].strip("/")
        parts = path.split("/")
        if parts[0] == "meta":
            return self._meta(method, parts[1:], json or {})
        return self._data(method, parts, json or {}, params or {})

    def _meta(self, method: str, parts: list[str], body: dict) -> dict:
        if parts == ["bases"] and method == "POST":
            if body.get("workspaceId") != self.workspace_id:
                raise AirtableError(403, "INVALID_PERMISSION_OR_REQUEST_ERROR espace de travail inconnu")
            base = {"id": self._new_id("app"), "name": body["name"], "tables": []}
            self.bases[base["id"]] = base
            for tspec in body.get("tables", []):
                self._make_table(base, tspec)
            return copy.deepcopy(base)
        if len(parts) >= 3 and parts[0] == "bases":
            base = self.bases.get(parts[1])
            if base is None:
                raise AirtableError(404, "NOT_FOUND base inconnue")
            if parts[2] == "tables" and len(parts) == 3:
                if method == "GET":
                    return {"tables": copy.deepcopy(base["tables"])}
                if method == "POST":
                    return copy.deepcopy(self._make_table(base, body))
            if parts[2] == "tables" and len(parts) == 5 and parts[4] == "fields" and method == "POST":
                table = self._table(base["id"], parts[3])
                return copy.deepcopy(self._make_field(base, table, body))
            if parts[2] == "tables" and len(parts) == 6 and parts[4] == "fields" and method == "PATCH":
                table = self._table(base["id"], parts[3])
                for f in table["fields"]:
                    if f["id"] == parts[5]:
                        if "name" in body:
                            f["name"] = body["name"]
                        if "description" in body:
                            f["description"] = body["description"]
                        return copy.deepcopy(f)
                raise AirtableError(404, "FIELD_NOT_FOUND")
        raise AirtableError(404, f"NOT_FOUND {method} meta/{'/'.join(parts)}")

    def _data(self, method: str, parts: list[str], body: dict, params: dict) -> dict:
        base_id, table_ref = parts[0], parts[1]
        table = self._table(base_id, table_ref)
        store = self.records[(base_id, table["id"])]
        if method == "GET":
            rows = store
            formula = params.get("filterByFormula")
            if formula:
                m = _EQ_FORMULA.match(formula.strip())
                if not m:
                    raise AirtableError(422, f"INVALID_FILTER_BY_FORMULA non pris en charge par le mock : {formula}")
                field, value = m.group("field"), m.group("value").replace("\\'", "'")
                rows = [r for r in store if str(r["fields"].get(field, "")) == value]
            wanted = params.get("fields[]")
            page_size = int(params.get("pageSize", 100))
            start = int(params.get("offset", 0) or 0)
            page = rows[start:start + page_size]
            out = []
            for r in page:
                rec = copy.deepcopy(r)
                if wanted:
                    rec["fields"] = {k: v for k, v in rec["fields"].items() if k in wanted}
                out.append(rec)
            result: dict[str, Any] = {"records": out}
            if start + page_size < len(rows):
                result["offset"] = str(start + page_size)
            return result
        if method == "POST":
            if len(body.get("records", [])) > 10:
                raise AirtableError(422, "INVALID_REQUEST_UNKNOWN 10 enregistrements maximum par appel")
            created = []
            names = {f["name"] for f in table["fields"]}
            for entry in body["records"]:
                unknown = set(entry["fields"]) - names
                if unknown:
                    raise AirtableError(422, f"UNKNOWN_FIELD_NAME {sorted(unknown)}")
                rec = {"id": self._new_id("rec"), "createdTime": "2026-09-16T00:00:00.000Z", "fields": copy.deepcopy(entry["fields"])}
                store.append(rec)
                created.append(copy.deepcopy(rec))
            return {"records": created}
        if method == "PATCH":
            updated = []
            for entry in body["records"]:
                for rec in store:
                    if rec["id"] == entry["id"]:
                        rec["fields"].update(copy.deepcopy(entry["fields"]))
                        updated.append(copy.deepcopy(rec))
            return {"records": updated}
        raise AirtableError(405, "méthode non prise en charge")
