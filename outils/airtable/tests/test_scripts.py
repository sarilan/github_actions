"""Tests de create_base.py et seed.py contre la simulation de l'API (mock_api.MockAirtable)."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from airtable_client import AirtableClient, AirtableError  # noqa: E402
from mock_api import MockAirtable  # noqa: E402
import create_base  # noqa: E402
import seed  # noqa: E402

SCHEMA = create_base.load_schema()


@pytest.fixture
def mock():
    return MockAirtable()


@pytest.fixture
def client(mock):
    return AirtableClient(transport=mock.transport)


def remote_tables(client, base_id):
    return {t["name"]: t for t in client.get_base_schema(base_id)["tables"]}


def test_create_base_creates_everything(client, mock, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    base_id, summary = create_base.run(client, SCHEMA, mock.workspace_id, None)
    assert base_id.startswith("app")
    assert (tmp_path / ".base_id").read_text().strip() == base_id
    assert not summary.errors and not summary.manual
    remote = remote_tables(client, base_id)
    assert set(remote) == {"Clients", "Organismes", "Démarches", "Courriers"}
    for table in SCHEMA["tables"]:
        names = {f["name"] for f in remote[table["name"]]["fields"]}
        for f in table["fields"]:
            assert f["name"] in names, f"{table['name']}.{f['name']} manquant"
    for link in SCHEMA["links"]:
        src = {f["name"]: f for f in remote[link["from_table"]]["fields"]}
        dst = {f["name"]: f for f in remote[link["to_table"]]["fields"]}
        assert src[link["field"]]["type"] == "multipleRecordLinks"
        assert src[link["field"]]["options"]["linkedTableId"] == remote[link["to_table"]]["id"]
        assert dst[link["inverse_field"]]["type"] == "multipleRecordLinks", f"inverse {link['inverse_field']} absent"
    # Les champs calculés ont bien été ajoutés après coup
    dem = {f["name"]: f for f in remote["Démarches"]["fields"]}
    assert dem["Statut couleur"]["type"] == "formula"


def test_create_base_is_idempotent(client, mock, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    base_id, _ = create_base.run(client, SCHEMA, mock.workspace_id, None)
    calls_before = len(mock.calls)
    fields_before = {t["name"]: len(t["fields"]) for t in client.get_base_schema(base_id)["tables"]}
    base_id2, summary = create_base.run(client, SCHEMA, mock.workspace_id, base_id)
    assert base_id2 == base_id
    assert not summary.created_tables and not summary.created_fields and not summary.errors
    fields_after = {t["name"]: len(t["fields"]) for t in client.get_base_schema(base_id)["tables"]}
    assert fields_after == fields_before
    # Seuls des GET de schéma ont été faits lors de la seconde exécution
    assert all(m == "GET" for m, _ in mock.calls[calls_before:])


def test_create_base_completes_partial_base(client, mock, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    partial = client.create_base(mock.workspace_id, "Relais — Gestion", [
        {"name": "Clients", "fields": [{"name": "Dossier", "type": "singleLineText"}]},
    ])
    base_id, summary = create_base.run(client, SCHEMA, mock.workspace_id, partial["id"])
    assert base_id == partial["id"]
    assert set(summary.created_tables) == {"Organismes", "Démarches", "Courriers"}
    assert "Clients.Statut" in summary.created_fields
    assert "Clients.Dossier" in summary.skipped
    assert not summary.errors


def test_create_base_reports_rejected_computed_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    strict = MockAirtable(reject_field_types={"formula"})
    client = AirtableClient(transport=strict.transport)
    _, summary = create_base.run(client, SCHEMA, strict.workspace_id, None)
    assert not summary.errors
    assert any("Statut couleur" in m for m in summary.manual)


def test_create_base_requires_workspace(client, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    with pytest.raises(AirtableError) as exc:
        create_base.run(client, SCHEMA, None, None)
    assert "AIRTABLE_WORKSPACE_ID" in str(exc.value)


def test_seed_inserts_two_coherent_clients(client, mock, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    base_id, _ = create_base.run(client, SCHEMA, mock.workspace_id, None)
    counts = seed.seed(client, base_id, log=lambda *_: None)
    assert counts == {"Clients": 2, "Organismes": 14, "Démarches": 12, "Courriers": 16, "ignorés": 0}
    clients = client.list_records(base_id, "Clients")
    assert {c["fields"]["Dossier"] for c in clients} == {"Durand — Sarcelles", "Martin — Lyon"}
    organismes = client.list_records(base_id, "Organismes")
    demarches = client.list_records(base_id, "Démarches")
    courriers = client.list_records(base_id, "Courriers")
    client_ids = {c["id"] for c in clients}
    org_ids = {o["id"] for o in organismes}
    dem_ids = {d["id"] for d in demarches}
    assert all(o["fields"]["Client"][0] in client_ids for o in organismes)
    assert all(d["fields"]["Client"][0] in client_ids for d in demarches)
    assert all(d["fields"]["Organisme"][0] in org_ids for d in demarches if "Organisme" in d["fields"])
    assert all(c["fields"]["Client"][0] in client_ids for c in courriers)
    assert all(c["fields"]["Démarche"][0] in dem_ids for c in courriers if "Démarche" in c["fields"])
    # Chaque vue a de la matière : échéances sous 30 jours, en retard, courrier non traité, terminées ce mois
    from datetime import date
    today = date.today()
    echeances = [date.fromisoformat(d["fields"]["Échéance"]) for d in demarches if d["fields"]["Statut"] not in ("Terminée", "Abandonnée")]
    assert any((e - today).days < 0 for e in echeances)
    assert any(0 <= (e - today).days <= 30 for e in echeances)
    assert any(c["fields"]["Statut"] == "Non traité" for c in courriers)
    assert any(d["fields"]["Statut"] == "Terminée" and d["fields"]["Terminée le"][:7] == today.strftime("%Y-%m") for d in demarches)
    assert any(d["fields"].get("Décision enfant requise") for d in demarches)


def test_seed_is_idempotent(client, mock, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    base_id, _ = create_base.run(client, SCHEMA, mock.workspace_id, None)
    seed.seed(client, base_id, log=lambda *_: None)
    counts = seed.seed(client, base_id, log=lambda *_: None)
    assert counts["ignorés"] == 2 and counts["Clients"] == 0
    assert len(client.list_records(base_id, "Clients")) == 2


def test_seed_uses_only_schema_fields():
    """Chaque champ utilisé par seed.py existe dans schema.json (ou est un lien déclaré)."""
    tables = {t["name"]: {f["name"] for f in t["fields"]} for t in SCHEMA["tables"]}
    for l in SCHEMA["links"]:
        tables[l["from_table"]].add(l["field"])
        tables[l["to_table"]].add(l["inverse_field"])
    for dossier in seed.build_seed():
        assert set(k for k in dossier["client"] if not k.startswith("_")) <= tables["Clients"]
        for o in dossier["organismes"]:
            assert set(k for k in o if not k.startswith("_") and o[k] is not None) <= tables["Organismes"], o
        for dm in dossier["demarches"]:
            assert set(k for k in dm if not k.startswith("_")) <= tables["Démarches"], dm["Titre"]
        for c in dossier["courriers"]:
            assert set(k for k in c if not k.startswith("_")) <= tables["Courriers"], c["Titre"]


def test_list_records_paginates(client, mock, tmp_path, monkeypatch):
    monkeypatch.setattr(create_base, "BASE_ID_FILE", tmp_path / ".base_id")
    base_id, _ = create_base.run(client, SCHEMA, mock.workspace_id, None)
    client.create_records(base_id, "Clients", [{"Dossier": f"Test {i}"} for i in range(23)])
    assert len(client.list_records(base_id, "Clients", page_size=10)) == 23
    assert client.find_first(base_id, "Clients", "Dossier", "Test 7")["fields"]["Dossier"] == "Test 7"
    assert client.find_first(base_id, "Clients", "Dossier", "Inconnu") is None
