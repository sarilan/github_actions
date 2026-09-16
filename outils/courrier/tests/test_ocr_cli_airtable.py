"""OCR (image et PDF), messages d'erreur, ligne de commande et option --airtable (contre le mock)."""
import json
import shutil
import sys
from datetime import date

import pytest
from PIL import Image, ImageDraw, ImageFont

import classify
from conftest import CORPUS, REFERENCE

TESSERACT = shutil.which("tesseract") is not None


def _render(text: str, path, size=(1400, 900)):
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    y = 40
    for line in text.splitlines():
        draw.text((40, y), line, fill="black", font=font)
        y += 44
    img.save(path)


LETTRE = "Assurance Maladie\nCaisse primaire d'assurance maladie\nCergy, le 3 septembre 2026\nObjet : demande de pieces justificatives\nMerci de nous retourner votre RIB\navant le 15 octobre 2026.\nMontant a payer : 120,50 EUR"


@pytest.mark.skipif(not TESSERACT, reason="Tesseract absent")
def test_ocr_image(tmp_path, rules):
    png = tmp_path / "lettre.png"
    _render(LETTRE, png)
    result = classify.classify_file(png, reference=REFERENCE, rules=rules)
    assert result.ocr["moteur"] == "tesseract"
    assert result.organisme["id"] == "cpam"
    assert result.type["nom"] == "Demande de pièces"
    assert result.date_limite_principale == "2026-10-15"
    assert result.montant_principal == 120.50


def test_pdf_texte_natif(tmp_path, rules):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    pdf = tmp_path / "facture.pdf"
    c = canvas.Canvas(str(pdf), pagesize=A4)
    y = 800
    for line in (CORPUS / "02-edf-facture.txt").read_text(encoding="utf-8").splitlines():
        c.drawString(40, y, line)
        y -= 18
    c.save()
    result = classify.classify_file(pdf, reference=REFERENCE, rules=rules)
    assert result.ocr["moteur"] == "pdf-texte-natif"
    assert result.organisme["id"] == "edf"
    assert result.type["nom"] == "Facture"
    assert result.montant_principal == 486.30


@pytest.mark.skipif(not TESSERACT or shutil.which("pdftoppm") is None, reason="Tesseract ou poppler absent")
def test_pdf_scanne(tmp_path, rules):
    png = tmp_path / "scan.png"
    _render(LETTRE, png)
    pdf = tmp_path / "scan.pdf"
    Image.open(png).convert("RGB").save(pdf, "PDF", resolution=150)
    result = classify.classify_file(pdf, reference=REFERENCE, rules=rules)
    assert result.ocr["moteur"] == "tesseract" and result.ocr["pages"] == 1
    assert result.organisme["id"] == "cpam"


def test_format_non_pris_en_charge(tmp_path):
    f = tmp_path / "lettre.docx"
    f.write_bytes(b"x")
    with pytest.raises(ValueError):
        classify.extract_text(f)


def test_tesseract_absent_message_clair(tmp_path, monkeypatch):
    import pytesseract
    def boom(*args, **kwargs):
        raise pytesseract.TesseractNotFoundError()
    monkeypatch.setattr(pytesseract, "image_to_string", boom)
    png = tmp_path / "x.png"
    Image.new("RGB", (50, 50), "white").save(png)
    with pytest.raises(classify.OcrUnavailable) as exc:
        classify.extract_text(png)
    assert "tesseract-ocr-fra" in str(exc.value)


def test_langue_absente_message_clair(tmp_path, monkeypatch):
    import pytesseract
    def boom(*args, **kwargs):
        raise pytesseract.TesseractError(1, "Error opening data file fra.traineddata")
    monkeypatch.setattr(pytesseract, "image_to_string", boom)
    png = tmp_path / "x.png"
    Image.new("RGB", (50, 50), "white").save(png)
    with pytest.raises(classify.OcrUnavailable) as exc:
        classify.extract_text(png)
    assert "française" in str(exc.value)


def test_autre_erreur_tesseract_propagee(tmp_path, monkeypatch):
    import pytesseract
    def boom(*args, **kwargs):
        raise pytesseract.TesseractError(1, "autre problème")
    monkeypatch.setattr(pytesseract, "image_to_string", boom)
    png = tmp_path / "x.png"
    Image.new("RGB", (50, 50), "white").save(png)
    with pytest.raises(pytesseract.TesseractError):
        classify.extract_text(png)


def test_pdf_scanne_sans_poppler(tmp_path, monkeypatch):
    import pdf2image
    def boom(*args, **kwargs):
        raise RuntimeError("poppler introuvable")
    monkeypatch.setattr(pdf2image, "convert_from_path", boom)
    pdf = tmp_path / "scan.pdf"
    Image.new("RGB", (50, 50), "white").save(pdf, "PDF")
    with pytest.raises(classify.OcrUnavailable) as exc:
        classify.extract_text(pdf)
    assert "poppler" in str(exc.value)


# --- ligne de commande --------------------------------------------------------
def test_cli_txt(capsys):
    code = classify.main([str(CORPUS / "03-orange-mise-en-demeure.txt"), "--reference-date", "2026-09-16", "--pretty"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["organisme"]["id"] == "orange"
    assert payload["urgence"]["niveau"] == 4


def test_cli_fichier_absent(capsys):
    assert classify.main(["/nulle/part/lettre.txt"]) == 1
    assert "introuvable" in capsys.readouterr().err


def test_cli_format_invalide(tmp_path, capsys):
    f = tmp_path / "x.docx"
    f.write_bytes(b"x")
    assert classify.main([str(f)]) == 1


def test_cli_ocr_indisponible(tmp_path, monkeypatch, capsys):
    import pytesseract
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: (_ for _ in ()).throw(pytesseract.TesseractNotFoundError()))
    png = tmp_path / "x.png"
    Image.new("RGB", (50, 50), "white").save(png)
    assert classify.main([str(png)]) == 2
    assert "OCR indisponible" in capsys.readouterr().err


def test_cli_airtable_sans_client(capsys):
    assert classify.main([str(CORPUS / "02-edf-facture.txt"), "--airtable"]) == 1
    assert "--client" in capsys.readouterr().err


def test_cli_airtable_erreur(monkeypatch, capsys):
    monkeypatch.setattr(classify, "push_to_airtable", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("panne")))
    assert classify.main([str(CORPUS / "02-edf-facture.txt"), "--airtable", "--client", "Durand — Sarcelles"]) == 3
    assert "panne" in capsys.readouterr().err


# --- Airtable (mock) ----------------------------------------------------------
@pytest.fixture
def base_avec_seed():
    from airtable_client import AirtableClient
    from mock_api import MockAirtable
    import create_base
    import seed
    mock = MockAirtable()
    api = AirtableClient(transport=mock.transport)
    base_id, _ = create_base.run(api, create_base.load_schema(), mock.workspace_id, None)
    seed.seed(api, base_id, log=lambda *_: None)
    return api, base_id


def test_push_to_airtable(base_avec_seed, rules, monkeypatch):
    api, base_id = base_avec_seed
    result = classify.classify_file(CORPUS / "02-edf-facture.txt", reference=REFERENCE, rules=rules)
    ids = classify.push_to_airtable(result, "Durand — Sarcelles", api=api, base_id=base_id, reference=REFERENCE)
    assert ids["courrier_id"].startswith("rec") and ids["demarche_id"].startswith("rec")
    assert ids["organisme_id"], "l'organisme EDF du dossier Durand doit être rattaché"
    courriers = [c for c in api.list_records(base_id, "Courriers") if c["id"] == ids["courrier_id"]]
    f = courriers[0]["fields"]
    assert f["Type"] == "Facture" and f["Urgence"] == "2 - Normale" and f["Statut"] == "Non traité"
    assert f["Montant"] == 486.30 and f["Date limite"] == "2026-10-02" and f["Reçu le"] == "2026-09-16"
    assert f["Démarche"] == [ids["demarche_id"]] and f["Client"] == [ids["client_id"]]
    assert json.loads(f["Classification automatique"])["organisme"]["id"] == "edf"
    demarche = [d for d in api.list_records(base_id, "Démarches") if d["id"] == ids["demarche_id"]][0]["fields"]
    assert demarche["Type"] == "Courrier à traiter" and demarche["Échéance"] == "2026-10-02"
    assert demarche["Montant en jeu"] == 486.30 and demarche["Statut"] == "À faire"


def test_push_to_airtable_sans_organisme_ni_echeance(base_avec_seed, rules):
    api, base_id = base_avec_seed
    result = classify.classify_file(CORPUS / "30-inconnu-publicite.txt", reference=REFERENCE, rules=rules)
    ids = classify.push_to_airtable(result, "Martin — Lyon", api=api, base_id=base_id, reference=REFERENCE)
    assert ids["organisme_id"] is None
    demarche = [d for d in api.list_records(base_id, "Démarches") if d["id"] == ids["demarche_id"]][0]["fields"]
    assert demarche["Échéance"] == "2026-09-18"  # objectif 48 h par défaut


def test_push_to_airtable_client_inconnu(base_avec_seed, rules):
    from airtable_client import AirtableError
    api, base_id = base_avec_seed
    result = classify.classify_file(CORPUS / "02-edf-facture.txt", reference=REFERENCE, rules=rules)
    with pytest.raises(AirtableError):
        classify.push_to_airtable(result, "Inconnu — Nulle part", api=api, base_id=base_id)


def test_push_to_airtable_base_inconnue(rules, monkeypatch):
    from airtable_client import AirtableClient, AirtableError
    from mock_api import MockAirtable
    monkeypatch.delenv("AIRTABLE_BASE_ID", raising=False)
    import airtable_client
    monkeypatch.setattr(airtable_client, "BASE_ID_FILE", classify.REPO_ROOT / "nope" / ".base_id")
    api = AirtableClient(transport=MockAirtable().transport)
    result = classify.classify_file(CORPUS / "02-edf-facture.txt", reference=REFERENCE, rules=rules)
    with pytest.raises(AirtableError):
        classify.push_to_airtable(result, "Durand — Sarcelles", api=api, base_id=None)
