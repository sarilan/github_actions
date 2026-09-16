#!/usr/bin/env python3
"""Crée (ou complète) la base Airtable « Relais — Gestion » à partir de schema.json.

Usage :
    python3 outils/airtable/create_base.py               # crée la base, ou complète une base existante
    python3 outils/airtable/create_base.py --dry-run     # affiche le plan sans appeler l'API
    python3 outils/airtable/create_base.py --base appXXX # complète une base existante

Variables (.env) : AIRTABLE_API_KEY (obligatoire), AIRTABLE_WORKSPACE_ID (obligatoire pour
créer), AIRTABLE_BASE_ID (facultatif ; sinon lu/écrit dans outils/airtable/.base_id).

Idempotence : si une base est connue (argument, variable ou fichier .base_id), le script lit
son schéma et ne crée que les tables et champs manquants ; il ne supprime ni ne modifie rien.

Déroulement :
1. création de la base avec les 4 tables et leurs champs simples (l'API exige au moins un
   champ par table et un champ principal de type texte) ;
2. ajout des champs de liaison (multipleRecordLinks) une fois les tables créées, puis
   renommage du champ inverse créé automatiquement ;
3. ajout des champs calculés (formula, createdTime, lastModifiedTime) ; si l'API refuse un
   type, le champ est listé dans le résumé « à créer à la main » avec sa formule ;
4. les vues ne peuvent pas être créées par l'API : le résumé imprime, pour chacune des 6
   vues, le filtre, le tri et le regroupement à saisir dans Airtable (ou via le connecteur
   Airtable de Claude Cowork, partie B du brief).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from airtable_client import AirtableClient, AirtableError, BASE_ID_FILE, load_env, resolve_base_id  # noqa: E402

SCHEMA_PATH = HERE / "schema.json"
COMPUTED_TYPES = {"formula", "createdTime", "lastModifiedTime", "count", "rollup", "multipleLookupValues", "autoNumber"}


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _clean_field(field: dict) -> dict:
    """Ne conserve que les clés acceptées par l'API (name, type, options, description)."""
    out = {"name": field["name"], "type": field["type"]}
    if field.get("options"):
        out["options"] = field["options"]
    if field.get("description"):
        out["description"] = field["description"]
    return out


def simple_fields(table: dict) -> list[dict]:
    return [_clean_field(f) for f in table["fields"] if f["type"] not in COMPUTED_TYPES]


def computed_fields(table: dict) -> list[dict]:
    return [_clean_field(f) for f in table["fields"] if f["type"] in COMPUTED_TYPES]


class Summary:
    def __init__(self) -> None:
        self.created_tables: list[str] = []
        self.created_fields: list[str] = []
        self.skipped: list[str] = []
        self.manual: list[str] = []
        self.errors: list[str] = []

    def print(self, schema: dict, base_id: str | None) -> None:
        print("\n===== Résumé =====")
        print(f"Base : {base_id or '(non créée)'}")
        print(f"Tables créées ({len(self.created_tables)}) : {', '.join(self.created_tables) or '—'}")
        print(f"Champs créés ({len(self.created_fields)}) : {', '.join(self.created_fields) or '—'}")
        print(f"Éléments déjà présents, ignorés ({len(self.skipped)}) : {', '.join(self.skipped) or '—'}")
        if self.errors:
            print(f"Erreurs ({len(self.errors)}) :")
            for e in self.errors:
                print(f"  ✘ {e}")
        if self.manual:
            print("À créer à la main dans Airtable (refusé par l'API) :")
            for m in self.manual:
                print(f"  • {m}")
        print(f"\nVues à créer à la main ({len(schema['views'])}) — l'API Airtable ne permet pas de créer des vues :")
        for v in schema["views"]:
            print(f"  • [{v['table']}] « {v['name']} » ({v['type']})")
            print(f"      filtre       : {v['filter'] or 'aucun'}")
            tri = ", ".join(f"{s['field']} {s['direction']}" for s in v["sort"]) or "aucun"
            print(f"      tri          : {tri}")
            print(f"      regroupement : {v['group_by'] or 'aucun'}")
            print(f"      champs       : {', '.join(v['fields_visible'])}")


def ensure_base(client: AirtableClient, schema: dict, workspace_id: str | None, base_id: str | None, summary: Summary) -> str:
    if base_id:
        try:
            client.get_base_schema(base_id)
            summary.skipped.append(f"base {base_id}")
            return base_id
        except AirtableError as exc:
            if exc.status != 404:
                raise
            summary.errors.append(f"base {base_id} introuvable, création d'une nouvelle base")
    if not workspace_id:
        raise AirtableError(400, "AIRTABLE_WORKSPACE_ID absent : nécessaire pour créer la base (identifiant « wsp… » visible dans l'URL de l'espace de travail)")
    payload_tables = [{"name": t["name"], "description": t.get("description", ""), "fields": simple_fields(t)} for t in schema["tables"]]
    created = client.create_base(workspace_id, schema["base"]["name"], payload_tables)
    summary.created_tables.extend(t["name"] for t in created["tables"])
    BASE_ID_FILE.write_text(created["id"] + "\n", encoding="utf-8")
    return created["id"]


def sync_tables_and_fields(client: AirtableClient, schema: dict, base_id: str, summary: Summary) -> dict[str, dict]:
    """Crée les tables et champs manquants ; renvoie {nom de table: schéma distant}."""
    remote = {t["name"]: t for t in client.get_base_schema(base_id)["tables"]}
    for table in schema["tables"]:
        if table["name"] not in remote:
            created = client.create_table(base_id, {"name": table["name"], "description": table.get("description", ""), "fields": simple_fields(table)})
            remote[table["name"]] = created
            summary.created_tables.append(table["name"])
            continue
        existing = {f["name"].lower() for f in remote[table["name"]]["fields"]}
        for field in simple_fields(table):
            if field["name"].lower() in existing:
                summary.skipped.append(f"{table['name']}.{field['name']}")
                continue
            try:
                client.create_field(base_id, remote[table["name"]]["id"], field)
                summary.created_fields.append(f"{table['name']}.{field['name']}")
            except AirtableError as exc:
                summary.errors.append(f"{table['name']}.{field['name']} : {exc.message}")
    return {t["name"]: t for t in client.get_base_schema(base_id)["tables"]}


def sync_links(client: AirtableClient, schema: dict, base_id: str, remote: dict[str, dict], summary: Summary) -> dict[str, dict]:
    for link in schema["links"]:
        src, dst = remote[link["from_table"]], remote[link["to_table"]]
        src_names = {f["name"].lower(): f for f in src["fields"]}
        if link["field"].lower() in src_names:
            summary.skipped.append(f"{link['from_table']}.{link['field']}")
            continue
        try:
            field = client.create_field(base_id, src["id"], {
                "name": link["field"], "type": "multipleRecordLinks",
                "options": {"linkedTableId": dst["id"], "prefersSingleRecordLink": bool(link.get("prefers_single_record_link", False))},
            })
            summary.created_fields.append(f"{link['from_table']}.{link['field']}")
            inverse_id = field.get("options", {}).get("inverseLinkFieldId")
            if inverse_id:
                client.update_field(base_id, dst["id"], inverse_id, {"name": link["inverse_field"]})
                summary.created_fields.append(f"{link['to_table']}.{link['inverse_field']}")
        except AirtableError as exc:
            summary.errors.append(f"lien {link['from_table']}.{link['field']} : {exc.message}")
        remote = {t["name"]: t for t in client.get_base_schema(base_id)["tables"]}
    return remote


def sync_computed(client: AirtableClient, schema: dict, base_id: str, remote: dict[str, dict], summary: Summary) -> None:
    for table in schema["tables"]:
        existing = {f["name"].lower() for f in remote[table["name"]]["fields"]}
        for field in computed_fields(table):
            if field["name"].lower() in existing:
                summary.skipped.append(f"{table['name']}.{field['name']}")
                continue
            try:
                client.create_field(base_id, remote[table["name"]]["id"], field)
                summary.created_fields.append(f"{table['name']}.{field['name']}")
            except AirtableError as exc:
                formula = field.get("options", {}).get("formula", "")
                summary.manual.append(f"{table['name']} → champ « {field['name']} » ({field['type']}) {formula} — refus API : {exc.message}")


def run(client: AirtableClient, schema: dict, workspace_id: str | None, base_id: str | None) -> tuple[str, Summary]:
    summary = Summary()
    base_id = ensure_base(client, schema, workspace_id, base_id, summary)
    remote = sync_tables_and_fields(client, schema, base_id, summary)
    remote = sync_links(client, schema, base_id, remote, summary)
    sync_computed(client, schema, base_id, remote, summary)
    return base_id, summary


def print_plan(schema: dict) -> None:
    print(f"Plan pour la base « {schema['base']['name']} » :")
    for t in schema["tables"]:
        print(f"- table {t['name']} : {len(simple_fields(t))} champs simples, {len(computed_fields(t))} champs calculés")
    print(f"- {len(schema['links'])} liaisons, {len(schema['views'])} vues (à créer à la main)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="n'appelle pas l'API, affiche le plan")
    parser.add_argument("--base", help="identifiant d'une base existante à compléter (appXXXXXXXXXXXXXX)")
    parser.add_argument("--workspace", help="identifiant de l'espace de travail (wspXXXXXXXXXXXXXX)")
    args = parser.parse_args(argv)

    schema = load_schema()
    if args.dry_run:
        print_plan(schema)
        return 0
    load_env()
    import os
    workspace_id = args.workspace or os.environ.get("AIRTABLE_WORKSPACE_ID", "").strip() or None
    base_id = resolve_base_id(args.base)
    try:
        client = AirtableClient()
        base_id, summary = run(client, schema, workspace_id, base_id)
    except AirtableError as exc:
        print(f"✘ {exc}")
        return 1
    summary.print(schema, base_id)
    return 1 if summary.errors else 0


if __name__ == "__main__":
    sys.exit(main())
