#!/usr/bin/env python3
"""Classification automatique d'un courrier administratif (service Relais).

Usage :
    python3 outils/courrier/classify.py courrier.pdf
    python3 outils/courrier/classify.py photo.jpg --reference-date 2026-09-16
    python3 outils/courrier/classify.py lettre.txt --pretty
    python3 outils/courrier/classify.py courrier.pdf --airtable --client "Durand — Sarcelles"

Entrée : un fichier PDF, une image (JPG, PNG, TIFF, WEBP) ou un fichier texte (.txt, pour les
tests et le débogage). Sortie : un objet JSON sur la sortie standard.

Étapes :
1. OCR — Tesseract (langue française) via pytesseract ; pour un PDF, le texte natif est
   utilisé s'il existe, sinon chaque page est rendue en image puis reconnue. Si Tesseract
   n'est pas installé, le script s'arrête avec un message clair (code de retour 2) ;
   un fichier .txt reste utilisable sans OCR.
2. Identification de l'organisme et du type de document par motifs pondérés (rules.yaml).
3. Extraction des dates limites (formats français absolus et relatifs), des montants et des
   références de dossier.
4. Calcul d'un niveau d'urgence de 1 à 4 selon les règles explicites de rules.yaml.
5. Option --airtable : création de l'enregistrement Courrier et de la Démarche associée
   dans la base (client identifié par --client, nom du dossier).

Codes de retour : 0 succès, 1 erreur d'entrée, 2 OCR indisponible, 3 erreur Airtable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RULES_PATH = HERE / "rules.yaml"
REPO_ROOT = HERE.parent.parent

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
HEADER_LINES = 15

MOIS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
    "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
    "janv": 1, "fev": 2, "avr": 4, "juil": 7, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
NOMBRES = {
    "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8,
    "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quinze": 15, "vingt": 20, "trente": 30,
    "quarante": 40, "quarante-cinq": 45, "soixante": 60, "quatre-vingt-dix": 90,
}


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    """Minuscules, accents supprimés, apostrophes typographiques unifiées, espaces réduits par ligne."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("œ", "oe")
    text = text.lower()
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------
class OcrUnavailable(RuntimeError):
    pass


def _ocr_image(image, lang: str) -> str:
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - dépendance déclarée
        raise OcrUnavailable("pytesseract n'est pas installé : pip install pytesseract") from exc
    try:
        return pytesseract.image_to_string(image, lang=lang)
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrUnavailable(
            "Tesseract OCR est introuvable. Installer le moteur et la langue française :\n"
            "  Debian/Ubuntu : sudo apt install tesseract-ocr tesseract-ocr-fra\n"
            "  macOS         : brew install tesseract tesseract-lang\n"
            "  Windows       : https://github.com/UB-Mannheim/tesseract/wiki (cocher « French »)\n"
            "En attendant, le script accepte un fichier .txt contenant le texte du courrier."
        ) from exc
    except pytesseract.TesseractError as exc:
        if "fra" in str(exc) or "language" in str(exc).lower():
            raise OcrUnavailable(
                "La langue française de Tesseract est absente : installer le paquet tesseract-ocr-fra "
                "(ou copier fra.traineddata dans le dossier tessdata)."
            ) from exc
        raise


def extract_text(path: Path, lang: str = "fra", dpi: int = 300) -> tuple[str, dict]:
    """Renvoie (texte, informations sur le moteur utilisé)."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8"), {"moteur": "texte", "langue": lang, "pages": 1}
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        native = "\n".join((page.extract_text() or "") for page in reader.pages)
        if len(native.strip()) >= 80:
            return native, {"moteur": "pdf-texte-natif", "langue": lang, "pages": len(reader.pages)}
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(str(path), dpi=dpi)
        except Exception as exc:  # pdf2image absent ou poppler manquant
            raise OcrUnavailable(
                "Le PDF est un scan sans texte et sa conversion en images a échoué : installer poppler "
                "(apt install poppler-utils) et pdf2image. Détail : " + str(exc)
            ) from exc
        text = "\n\f\n".join(_ocr_image(img, lang) for img in images)
        return text, {"moteur": "tesseract", "langue": lang, "pages": len(images)}
    if suffix in IMAGE_SUFFIXES:
        from PIL import Image
        with Image.open(path) as img:
            return _ocr_image(img.convert("RGB"), lang), {"moteur": "tesseract", "langue": lang, "pages": 1}
    raise ValueError(f"Format non pris en charge : {suffix or path.name} (PDF, image ou .txt attendus)")


# ---------------------------------------------------------------------------
# Règles
# ---------------------------------------------------------------------------
def load_rules(path: Path = RULES_PATH) -> dict:
    with path.open(encoding="utf-8") as f:
        rules = yaml.safe_load(f)
    for org in rules["organismes"]:
        for m in org["motifs"]:
            m["_re"] = re.compile(m["regex"])
    for t in rules["types"]:
        for m in t["marqueurs"]:
            m["_re"] = re.compile(m["regex"])
    rules["urgence"]["modificateurs"]["mots_cles_sanction"]["_re"] = [
        re.compile(r) for r in rules["urgence"]["modificateurs"]["mots_cles_sanction"]["regex"]
    ]
    return rules


def _score(motifs: list[dict], text: str, header: str) -> tuple[float, float, list[str]]:
    score, maximum, found = 0.0, 0.0, []
    for m in motifs:
        maximum += m["poids"] * 2
        if m["_re"].search(header):
            score += m["poids"] * 2
            found.append(m["regex"])
        elif m["_re"].search(text):
            score += m["poids"]
            found.append(m["regex"])
    return score, maximum, found


def identify_organisme(norm: str, rules: dict) -> dict:
    header = "\n".join(norm.splitlines()[:HEADER_LINES])
    best = {"id": None, "nom": "Organisme non identifié", "categorie": "Autre", "confiance": 0.0, "motifs": [], "critique": False}
    best_score = 0.0
    for org in rules["organismes"]:
        score, maximum, found = _score(org["motifs"], norm, header)
        # Un organisme générique (« autre ») ne l'emporte sur un organisme nommé qu'à score strictement supérieur
        adjusted = score * 0.6 if org["id"].endswith("-generique") else score
        if adjusted > best_score:
            best_score = adjusted
            best = {
                "id": org["id"], "nom": org["nom"], "categorie": org["categorie"],
                "confiance": round(min(1.0, score / max(maximum * 0.5, 1)), 2),
                "motifs": found, "critique": bool(org.get("critique", False)),
            }
    return best


def identify_type(norm: str, rules: dict) -> dict:
    header = "\n".join(norm.splitlines()[:HEADER_LINES])
    ranked = []
    for priority, t in enumerate(rules["types"]):
        score, maximum, found = _score(t["marqueurs"], norm, header)
        ranked.append((score, -priority, t["nom"], maximum, found))
    ranked.sort(reverse=True)
    score, _, nom, maximum, found = ranked[0]
    if score == 0:
        return {"nom": "Autre", "confiance": 0.0, "motifs": []}
    second = ranked[1][0] if len(ranked) > 1 else 0.0
    confiance = min(1.0, (score / max(maximum * 0.4, 1)) * (0.6 + 0.4 * (1 - second / score if score else 0)))
    return {"nom": nom, "confiance": round(confiance, 2), "motifs": found}


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------
_DATE_NUM = r"(?P<j>[0-3]?\d)[/.\-](?P<m>[01]?\d)[/.\-](?P<a>20\d{2}|\d{2})"
_DATE_TXT = r"(?P<jt>1er|[0-3]?\d)(?:er)?\s+(?P<mt>janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre|janv|fev|avr|juil|sept|oct|nov|dec)\.?\s+(?P<at>20\d{2})"
DATE_RE = re.compile(rf"(?:{_DATE_NUM}|{_DATE_TXT})")

DEADLINE_INTRO = (
    r"(?:avant le|au plus tard le|jusqu'au|jusqu'a la date du|d'ici le|a compter du|"
    r"date limite(?: de paiement| de reponse)?\s*:?\s*(?:le\s+)?|a payer avant le|a regler avant le|"
    r"echeance\s*:?\s*(?:le\s+)?|a retourner avant le|delai de reponse\s*:?\s*(?:le\s+)?|"
    r"(?:reglement|paiement|reponse) attendu[e]? (?:avant|pour) le|expire le|fin de validite\s*:?\s*(?:le\s+)?|"
    r"vous presenter le|rendez-vous (?:est )?fixe (?:au|le)|au-dela du|audience du|rendez-vous du|le|au)"
)
DEADLINE_ABS_RE = re.compile(rf"(?P<intro>{DEADLINE_INTRO})\s*(?P<date>{DATE_RE.pattern})")
DEADLINE_STRONG_INTROS = ("avant", "plus tard", "jusqu", "d'ici", "limite", "echeance", "retourner", "attendu", "expire", "validite", "presenter", "rendez-vous", "delai", "au-dela", "audience")

RECOURS_CONTEXT_RE = re.compile(r"(recours|contest|reclamation aupres|saisir (la|le) (commission|mediateur|tribunal)|voies et delais)")
INFO_CONTEXT_RE = re.compile(r"(remboursement|versement|virement|interviendra|sera (verse|rembourse|adresse|envoye)|vous recevrez)")


def deadline_category(norm: str, start: int) -> str:
    """Un délai précédé d'une mention de recours ou d'un versement à venir n'appelle pas d'action."""
    context = norm[max(0, start - 160):start].replace("\n", " ")
    context = re.split(r"[.;!?]", context)[-1]  # seule la phrase en cours compte
    if RECOURS_CONTEXT_RE.search(context):
        return "recours"
    if INFO_CONTEXT_RE.search(context):
        return "information"
    return "action"


RELATIVE_RE = re.compile(
    r"(?:sous|dans (?:un delai d[e']\s*|les\s+|un delai maximum d[e']\s*)?|d'ici|au plus tard dans|delai de|avant)\s*"
    r"(?P<n>\d{1,3}|un|une|deux|trois|quatre|cinq|six|sept|huit|dix|quinze|vingt|trente|quarante-cinq|quarante|soixante|quatre-vingt-dix)\s*"
    r"(?P<u>jours? (?:ouvres?|ouvrables?|francs?|calendaires?)?|jours?|semaines?|mois|ans?)"
)
DOC_DATE_RE = re.compile(rf"(?:^|\n)[^\n]{{0,60}}?(?:,\s*le|\ble|date\s*:|fait a [^\n,]{{1,40}},?\s*le)\s+(?P<date>{DATE_RE.pattern})")


def parse_date(m: re.Match) -> date | None:
    try:
        if m.group("j"):
            year = int(m.group("a"))
            if year < 100:
                year += 2000
            return date(year, int(m.group("m")), int(m.group("j")))
        day = 1 if m.group("jt") == "1er" else int(m.group("jt"))
        return date(int(m.group("at")), MOIS[m.group("mt")], day)
    except (ValueError, KeyError):
        return None


def find_document_date(norm: str, reference: date) -> date | None:
    """Date du courrier : première date précédée de « le », « date : » ou « Ville, le » dans l'en-tête."""
    header = "\n".join(norm.splitlines()[:HEADER_LINES + 10])
    candidates: list[date] = []
    for m in DOC_DATE_RE.finditer(header):
        d = parse_date(DATE_RE.match(m.group("date")))
        if d and abs((d - reference).days) <= 400:
            candidates.append(d)
    if candidates:
        return candidates[0]
    for m in DATE_RE.finditer(header):
        d = parse_date(m)
        if d and d <= reference and (reference - d).days <= 120:
            return d
    return None


def _add_relative(start: date, n: int, unit: str) -> date:
    if unit.startswith("jour"):
        if "ouvr" in unit:
            d, added = start, 0
            while added < n:
                d += timedelta(days=1)
                if d.weekday() < 5:
                    added += 1
            return d
        return start + timedelta(days=n)
    if unit.startswith("semaine"):
        return start + timedelta(weeks=n)
    if unit.startswith("mois"):
        month = start.month - 1 + n
        year = start.year + month // 12
        month = month % 12 + 1
        day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    return date(start.year + n, start.month, start.day)


def extract_deadlines(norm: str, document_date: date | None, reference: date) -> list[dict]:
    """Dates limites absolues (« avant le 15 octobre 2026 ») et relatives (« sous 30 jours »)."""
    base = document_date or reference
    results: list[dict] = []
    seen: set[str] = set()

    for m in DEADLINE_ABS_RE.finditer(norm):
        intro = m.group("intro").strip()
        strong = any(k in intro for k in DEADLINE_STRONG_INTROS)
        d = parse_date(DATE_RE.match(m.group("date")))
        if not d:
            continue
        if not strong:
            # « le 3 septembre 2026 » seul : n'est une échéance que si c'est une date future par rapport au courrier
            if document_date and d <= document_date:
                continue
            if not document_date and d < reference:
                continue
            context = norm[max(0, m.start() - 40):m.start()]
            if not re.search(r"(avant|jusqu|limite|echeance|delai|reponse|paiement|regler|payer|retourner|renvoyer|rendez-vous|convoqu|presenter|expire)", context):
                continue
        key = d.isoformat()
        if key in seen:
            continue
        seen.add(key)
        results.append({"texte": m.group(0).strip(), "date": key, "jours_restants": (d - reference).days, "type": "absolue", "categorie": deadline_category(norm, m.start())})

    for m in RELATIVE_RE.finditer(norm):
        raw = m.group("n")
        n = int(raw) if raw.isdigit() else NOMBRES.get(raw)
        if not n:
            continue
        d = _add_relative(base, n, m.group("u"))
        key = d.isoformat()
        if key in seen:
            continue
        seen.add(key)
        results.append({"texte": m.group(0).strip(), "date": key, "jours_restants": (d - reference).days, "type": "relative", "categorie": deadline_category(norm, m.start())})

    results.sort(key=lambda r: r["date"])
    return results


# ---------------------------------------------------------------------------
# Montants et références
# ---------------------------------------------------------------------------
AMOUNT_RE = re.compile(
    r"(?<![\d,.])(?P<int>\d{1,3}(?:[   .]\d{3})+|\d+)(?:[,.](?P<dec>\d{1,2}))?\s?(?:€|euros?|eur\b)",
    re.IGNORECASE,
)
AMOUNT_CONTEXT_RE = re.compile(r"(quote-part|a payer|montant|total|solde|somme|reste|regler|payer|net|ttc|cotisation|loyer|charges|prime|indu|penalite|majoration|remboursement|verse|attribue|degrevement)")


def extract_amounts(norm: str) -> list[dict]:
    amounts: list[dict] = []
    for m in AMOUNT_RE.finditer(norm):
        integer = re.sub(r"[   .]", "", m.group("int"))
        dec = m.group("dec") or "0"
        try:
            value = float(f"{integer}.{dec}")
        except ValueError:
            continue
        context = norm[max(0, m.start() - 60):m.start()].replace("\n", " ")
        label = AMOUNT_CONTEXT_RE.findall(context)
        amounts.append({"texte": m.group(0).strip(), "valeur": round(value, 2), "contexte": label[-1] if label else ""})
    return amounts


def principal_amount(amounts: list[dict]) -> float | None:
    if not amounts:
        return None
    priority = ("a payer", "total", "regler", "payer", "verse", "attribue", "degrevement", "quote-part", "montant", "solde", "somme", "reste", "ttc", "net")
    for key in priority:
        for a in amounts:
            if a["contexte"] == key:
                return a["valeur"]
    return max(a["valeur"] for a in amounts)


REFERENCE_RE = re.compile(
    r"(?:(?:votre|notre|nos|vos)\s+)?(?:n(?:o|°|um(?:ero)?)?\.?\s*(?:de\s+|d')?(?:dossier|contrat|client|adherent|allocataire|pension|facture|reference|securite sociale|police|lot|compte|assure|reclamation|sinistre)|"
    r"reference(?:s)?(?: (?:dossier|client|contrat|de dossier))?|dossier n(?:o|°)?\.?|contrat n(?:o|°)?\.?|facture n(?:o|°)?\.?|"
    r"identifiant|code (?:client|adherent)|n(?:o|°) ?(?:sec(?:urite)?\.? ?soc(?:iale)?)|nir)\s*:?\s*(?P<ref>[a-z0-9][a-z0-9 /\-\.]{3,30}[a-z0-9])",
)


def extract_references(norm: str) -> list[dict]:
    refs: list[dict] = []
    seen: set[str] = set()
    for m in REFERENCE_RE.finditer(norm):
        label = m.group(0)[: m.start("ref") - m.start()].strip(" :")
        value = m.group("ref").strip()
        value = re.split(r"\s{2,}|\s(?:du|le|au|de|en|pour|a)\s", value)[0].strip()
        if len(value) < 4 or value in seen or not re.search(r"\d", value):
            continue
        seen.add(value)
        refs.append({"libelle": label, "valeur": value.upper()})
    return refs


# ---------------------------------------------------------------------------
# Urgence
# ---------------------------------------------------------------------------
def compute_urgency(doc_type: str, organisme: dict, deadlines: list[dict], amount: float | None, norm: str, rules: dict) -> dict:
    cfg = rules["urgence"]
    mods = cfg["modificateurs"]
    level = cfg["base_par_type"].get(doc_type, cfg["base_par_type"]["Autre"])
    reasons = [f"type « {doc_type} » : niveau de base {level}"]
    minimum, maximum = 1, 4

    if deadlines:
        soonest = min(d["jours_restants"] for d in deadlines)
        if soonest < 0:
            minimum = max(minimum, mods["delai_depasse"]["niveau_minimum"])
            reasons.append(mods["delai_depasse"]["motif"])
        elif soonest <= 7:
            level += mods["delai_7_jours"]["ajout"]
            reasons.append(mods["delai_7_jours"]["motif"])
        elif soonest <= 15:
            level += mods["delai_15_jours"]["ajout"]
            reasons.append(mods["delai_15_jours"]["motif"])
    if amount is not None and amount > mods["montant_eleve"]["seuil"] and doc_type in mods["montant_eleve"]["types_concernes"]:
        level += mods["montant_eleve"]["ajout"]
        reasons.append(mods["montant_eleve"]["motif"])
    enjeu = 0
    if organisme.get("critique"):
        enjeu = max(enjeu, mods["organisme_critique"]["ajout"])
        reasons.append(mods["organisme_critique"]["motif"])
    sanction = mods["mots_cles_sanction"]
    hits = [r.pattern for r in sanction["_re"] if r.search(norm)]
    if hits:
        enjeu = max(enjeu, sanction["ajout"])
        reasons.append(f"{sanction['motif']} ({', '.join(hits[:3])})")
    level += enjeu  # organisme à enjeu et mention de sanction : +1 au plus, pas de cumul
    if doc_type == "Information" and not deadlines:
        maximum = mods["information_sans_delai"]["niveau_maximum"]
        reasons.append(mods["information_sans_delai"]["motif"])

    level = max(minimum, min(maximum, level))
    return {"niveau": level, "motifs": reasons}


# ---------------------------------------------------------------------------
# Classification complète
# ---------------------------------------------------------------------------
@dataclass
class Classification:
    fichier: str
    organisme: dict
    type: dict
    date_document: str | None
    dates_limites: list[dict]
    date_limite_principale: str | None
    montants: list[dict]
    montant_principal: float | None
    references: list[dict]
    urgence: dict
    resume: str
    ocr: dict
    texte_longueur: int
    avertissements: list[str] = field(default_factory=list)

    def to_json(self, pretty: bool = False) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2 if pretty else None)


def summarize(text: str, max_len: int = 240) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    objet = next((ln for ln in lines if re.match(r"(?i)^(objet|sujet)\s*:", ln)), None)
    if objet:
        return objet[:max_len]
    body = " ".join(lines)
    return body[:max_len]


def classify_text(text: str, source: str = "texte", reference: date | None = None, rules: dict | None = None, ocr_info: dict | None = None) -> Classification:
    rules = rules or load_rules()
    reference = reference or date.today()
    norm = normalize(text)
    warnings: list[str] = []
    if len(norm.strip()) < 40:
        warnings.append("texte très court : OCR probablement incomplet, vérifier le scan")

    organisme = identify_organisme(norm, rules)
    doc_type = identify_type(norm, rules)
    doc_date = find_document_date(norm, reference)
    deadlines = extract_deadlines(norm, doc_date, reference)
    amounts = extract_amounts(norm)
    amount = principal_amount(amounts)
    references = extract_references(norm)
    urgency = compute_urgency(doc_type["nom"], organisme, [d for d in deadlines if d["categorie"] == "action"], amount, norm, rules)

    if organisme["confiance"] < 0.3:
        warnings.append("organisme incertain : vérifier l'expéditeur")
    if doc_type["confiance"] < 0.3:
        warnings.append("type de document incertain")
    actionable = [d for d in deadlines if d["categorie"] == "action" and d["jours_restants"] >= -365]
    principal_deadline = actionable[0]["date"] if actionable else None

    return Classification(
        fichier=source,
        organisme=organisme,
        type=doc_type,
        date_document=doc_date.isoformat() if doc_date else None,
        dates_limites=deadlines,
        date_limite_principale=principal_deadline,
        montants=amounts,
        montant_principal=amount,
        references=references,
        urgence=urgency,
        resume=summarize(text),
        ocr=ocr_info or {"moteur": "texte", "langue": "fra", "pages": 1},
        texte_longueur=len(norm),
        avertissements=warnings,
    )


def classify_file(path: Path, reference: date | None = None, lang: str = "fra", rules: dict | None = None) -> Classification:
    text, ocr_info = extract_text(path, lang=lang)
    return classify_text(text, source=path.name, reference=reference, rules=rules, ocr_info=ocr_info)


# ---------------------------------------------------------------------------
# Airtable
# ---------------------------------------------------------------------------
URGENCE_LABELS = {1: "1 - Faible", 2: "2 - Normale", 3: "3 - Élevée", 4: "4 - Critique"}
TYPE_LABELS = {"Facture", "Relance", "Mise en demeure", "Demande de pièces", "Information", "Décision", "Convocation"}


def push_to_airtable(result: Classification, client_name: str, api=None, base_id: str | None = None, reference: date | None = None) -> dict:
    """Crée le Courrier et la Démarche dans Airtable ; renvoie les identifiants créés."""
    sys.path.insert(0, str(REPO_ROOT / "outils" / "airtable"))
    from airtable_client import AirtableClient, AirtableError, load_env, resolve_base_id  # noqa: E402

    if api is None:
        load_env()
        api = AirtableClient()
    base_id = resolve_base_id(base_id)
    if not base_id:
        raise AirtableError(400, "base inconnue : renseigner AIRTABLE_BASE_ID ou lancer create_base.py")
    reference = reference or date.today()

    client_rec = api.find_first(base_id, "Clients", "Dossier", client_name)
    if not client_rec:
        raise AirtableError(404, f"dossier client « {client_name} » introuvable dans la table Clients")
    client_id = client_rec["id"]

    organisme_id = None
    organisme_nom = result.organisme["nom"]
    for org in api.list_records(base_id, "Organismes", fields=["Nom", "Client"]):
        if org["fields"].get("Client", [None])[0] != client_id:
            continue
        nom = org["fields"].get("Nom", "")
        if result.organisme["id"] and (organisme_nom.split(" ")[0].lower() in nom.lower() or nom.split(" — ")[0].lower() in organisme_nom.lower()):
            organisme_id = org["id"]
            break

    doc_type = result.type["nom"] if result.type["nom"] in TYPE_LABELS else "Autre"
    urgence = URGENCE_LABELS[result.urgence["niveau"]]
    titre = f"{reference.isoformat()} — {organisme_nom.split(' — ')[0].split(' (')[0]} — {doc_type}"

    demarche_fields = {
        "Titre": f"Courrier à traiter — {organisme_nom.split(' (')[0]} — {doc_type}",
        "Client": [client_id],
        "Type": "Courrier à traiter",
        "Statut": "À faire",
        "Urgence": urgence,
        "Prochaine étape": f"Lire le courrier et engager l'action ({doc_type.lower()})",
        "À inclure au rapport": True,
        "Décision enfant requise": result.urgence["niveau"] >= 3 and (result.montant_principal or 0) > 500,
    }
    if organisme_id:
        demarche_fields["Organisme"] = [organisme_id]
    if result.date_limite_principale:
        demarche_fields["Échéance"] = result.date_limite_principale
    else:
        demarche_fields["Échéance"] = (reference + timedelta(days=2)).isoformat()
    if result.montant_principal is not None:
        demarche_fields["Montant en jeu"] = result.montant_principal
    if result.references:
        demarche_fields["Référence dossier"] = result.references[0]["valeur"]
    demarche = api.create_records(base_id, "Démarches", [demarche_fields])[0]

    courrier_fields = {
        "Titre": titre,
        "Client": [client_id],
        "Démarche": [demarche["id"]],
        "Reçu le": reference.isoformat(),
        "Type": doc_type,
        "Urgence": urgence,
        "Statut": "Non traité",
        "Résumé": result.resume,
        "Classification automatique": result.to_json(pretty=True),
        "Confiance classification": round(min(result.organisme["confiance"], result.type["confiance"]), 2),
    }
    if organisme_id:
        courrier_fields["Organisme"] = [organisme_id]
    if result.date_document:
        courrier_fields["Date du document"] = result.date_document
    if result.date_limite_principale:
        courrier_fields["Date limite"] = result.date_limite_principale
    if result.montant_principal is not None:
        courrier_fields["Montant"] = result.montant_principal
    if result.references:
        courrier_fields["Référence"] = result.references[0]["valeur"]
    courrier = api.create_records(base_id, "Courriers", [courrier_fields])[0]
    return {"courrier_id": courrier["id"], "demarche_id": demarche["id"], "organisme_id": organisme_id, "client_id": client_id}


# ---------------------------------------------------------------------------
# Ligne de commande
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fichier", type=Path, help="PDF, image ou fichier .txt")
    parser.add_argument("--reference-date", type=date.fromisoformat, default=None, help="date de réception (AAAA-MM-JJ), défaut : aujourd'hui")
    parser.add_argument("--lang", default="fra", help="langue Tesseract (défaut : fra)")
    parser.add_argument("--rules", type=Path, default=RULES_PATH, help="fichier de règles (défaut : rules.yaml)")
    parser.add_argument("--pretty", action="store_true", help="JSON indenté")
    parser.add_argument("--airtable", action="store_true", help="créer le courrier et la démarche dans Airtable")
    parser.add_argument("--client", help="nom du dossier client (champ « Dossier » de la table Clients), requis avec --airtable")
    parser.add_argument("--base", help="identifiant de la base Airtable (sinon AIRTABLE_BASE_ID ou .base_id)")
    args = parser.parse_args(argv)

    if not args.fichier.exists():
        print(f"✘ fichier introuvable : {args.fichier}", file=sys.stderr)
        return 1
    try:
        rules = load_rules(args.rules)
        result = classify_file(args.fichier, reference=args.reference_date, lang=args.lang, rules=rules)
    except OcrUnavailable as exc:
        print(f"✘ OCR indisponible : {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"✘ {exc}", file=sys.stderr)
        return 1

    if args.airtable:
        if not args.client:
            print("✘ --client est requis avec --airtable", file=sys.stderr)
            return 1
        try:
            ids = push_to_airtable(result, args.client, base_id=args.base, reference=args.reference_date)
        except Exception as exc:  # AirtableError ou erreur réseau
            print(f"✘ Airtable : {exc}", file=sys.stderr)
            return 3
        result.avertissements.append(f"Airtable : courrier {ids['courrier_id']}, démarche {ids['demarche_id']}")

    print(result.to_json(pretty=args.pretty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
