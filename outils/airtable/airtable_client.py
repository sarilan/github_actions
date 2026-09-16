"""Client minimal pour l'API web Airtable (REST), sans dépendance autre que `requests`.

Utilisé par create_base.py, seed.py, outils/courrier/classify.py (--airtable) et
outils/rapport/generate_report.py.

Authentification : jeton d'accès personnel lu dans la variable AIRTABLE_API_KEY
(fichier .env à la racine du dépôt, chargé avec python-dotenv). Portées nécessaires :
schema.bases:read, schema.bases:write, data.records:read, data.records:write.

Points de terminaison utilisés (https://airtable.com/developers/web/api) :
- POST  /v0/meta/bases                                  créer une base (workspaceId, name, tables)
- GET   /v0/meta/bases/{baseId}/tables                  schéma d'une base
- POST  /v0/meta/bases/{baseId}/tables                  créer une table
- POST  /v0/meta/bases/{baseId}/tables/{tableId}/fields créer un champ
- PATCH /v0/meta/bases/{baseId}/tables/{tableId}/fields/{fieldId} renommer un champ
- GET   /v0/{baseId}/{tableIdOrName}                    lister des enregistrements (pagination par offset)
- POST  /v0/{baseId}/{tableIdOrName}                    créer des enregistrements (10 max par appel)
- PATCH /v0/{baseId}/{tableIdOrName}                    mettre à jour des enregistrements

Le transport est injectable (paramètre `transport`) pour les tests : voir mock_api.py.
"""
from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import requests

API_URL = "https://api.airtable.com/v0"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
BASE_ID_FILE = HERE / ".base_id"

Transport = Callable[[str, str, dict | None, dict | None], dict]


class AirtableError(RuntimeError):
    """Erreur renvoyée par l'API Airtable (statut HTTP et message)."""

    def __init__(self, status: int, message: str, method: str = "", url: str = ""):
        where = f" sur {method} {url}" if method or url else ""
        super().__init__(f"Airtable {status}{where} : {message}")
        self.status = status
        self.message = message


def load_env() -> None:
    """Charge le fichier .env de la racine du dépôt s'il existe (sans écraser l'environnement)."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dépendance déclarée dans requirements.txt
        return
    load_dotenv(REPO_ROOT / ".env", override=False)


def resolve_base_id(explicit: str | None = None) -> str | None:
    """Identifiant de base : argument, puis AIRTABLE_BASE_ID, puis fichier .base_id."""
    if explicit:
        return explicit
    env = os.environ.get("AIRTABLE_BASE_ID", "").strip()
    if env:
        return env
    if BASE_ID_FILE.exists():
        value = BASE_ID_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    return None


def _http_transport_factory(token: str, max_retries: int = 5) -> Transport:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})

    def transport(method: str, url: str, json: dict | None, params: dict | None) -> dict:
        delay = 1.0
        for attempt in range(max_retries):
            resp = session.request(method, url, json=json, params=params, timeout=60)
            if resp.status_code == 429 and attempt < max_retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            if resp.status_code >= 400:
                try:
                    payload = resp.json()
                    msg = payload.get("error", payload)
                    if isinstance(msg, dict):
                        msg = f"{msg.get('type', '')} {msg.get('message', '')}".strip()
                except ValueError:
                    msg = resp.text[:500]
                raise AirtableError(resp.status_code, str(msg), method, url)
            if not resp.content:
                return {}
            return resp.json()
        raise AirtableError(429, "trop de tentatives", method, url)

    return transport


class AirtableClient:
    """Enveloppe fine autour de l'API. Toutes les méthodes renvoient les dictionnaires JSON de l'API."""

    def __init__(self, token: str | None = None, transport: Transport | None = None):
        if transport is None:
            load_env()
            token = token or os.environ.get("AIRTABLE_API_KEY", "").strip()
            if not token:
                raise AirtableError(401, "AIRTABLE_API_KEY absent : copier .env.example en .env et renseigner le jeton")
            transport = _http_transport_factory(token)
        self._transport = transport

    # -- schéma -------------------------------------------------------------
    def create_base(self, workspace_id: str, name: str, tables: list[dict]) -> dict:
        return self._transport("POST", f"{API_URL}/meta/bases", {"name": name, "workspaceId": workspace_id, "tables": tables}, None)

    def get_base_schema(self, base_id: str) -> dict:
        return self._transport("GET", f"{API_URL}/meta/bases/{base_id}/tables", None, None)

    def create_table(self, base_id: str, table: dict) -> dict:
        return self._transport("POST", f"{API_URL}/meta/bases/{base_id}/tables", table, None)

    def create_field(self, base_id: str, table_id: str, field: dict) -> dict:
        return self._transport("POST", f"{API_URL}/meta/bases/{base_id}/tables/{table_id}/fields", field, None)

    def update_field(self, base_id: str, table_id: str, field_id: str, changes: dict) -> dict:
        return self._transport("PATCH", f"{API_URL}/meta/bases/{base_id}/tables/{table_id}/fields/{field_id}", changes, None)

    # -- enregistrements ----------------------------------------------------
    def list_records(self, base_id: str, table: str, filter_by_formula: str | None = None,
                     fields: Iterable[str] | None = None, view: str | None = None, page_size: int = 100) -> list[dict]:
        records: list[dict] = []
        params: dict[str, Any] = {"pageSize": page_size}
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if fields:
            params["fields[]"] = list(fields)
        if view:
            params["view"] = view
        offset: str | None = None
        while True:
            if offset:
                params["offset"] = offset
            payload = self._transport("GET", f"{API_URL}/{base_id}/{table}", None, dict(params))
            records.extend(payload.get("records", []))
            offset = payload.get("offset")
            if not offset:
                return records

    def create_records(self, base_id: str, table: str, records: list[dict], typecast: bool = True) -> list[dict]:
        created: list[dict] = []
        for i in range(0, len(records), 10):
            chunk = [{"fields": r} for r in records[i:i + 10]]
            payload = self._transport("POST", f"{API_URL}/{base_id}/{table}", {"records": chunk, "typecast": typecast}, None)
            created.extend(payload.get("records", []))
        return created

    def update_records(self, base_id: str, table: str, records: list[dict], typecast: bool = True) -> list[dict]:
        updated: list[dict] = []
        for i in range(0, len(records), 10):
            payload = self._transport("PATCH", f"{API_URL}/{base_id}/{table}", {"records": records[i:i + 10], "typecast": typecast}, None)
            updated.extend(payload.get("records", []))
        return updated

    def find_first(self, base_id: str, table: str, field: str, value: str) -> dict | None:
        escaped = value.replace("'", "\\'")
        found = self.list_records(base_id, table, filter_by_formula=f"{{{field}}} = '{escaped}'", page_size=1)
        return found[0] if found else None
