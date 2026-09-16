#!/usr/bin/env python3
"""Génère le rapport mensuel d'un client (docx + PDF) à partir de la base Airtable.

Usage :
    python3 outils/rapport/generate_report.py --client "Durand — Sarcelles" --mois 2026-09
    python3 outils/rapport/generate_report.py --client "Martin — Lyon" --mois 2026-09 --out rapports/
    python3 outils/rapport/generate_report.py --client "Durand — Sarcelles"        # mois en cours

Lit les tables Clients, Organismes, Démarches et Courriers (client Airtable de
outils/airtable/airtable_client.py, jeton dans .env), applique la logique de la vue
« Rapport du mois » (démarches terminées dans le mois + démarches en cours signalées
« À inclure au rapport »), remplit template-rapport-mensuel.docx (docxtpl) et convertit
en PDF (LibreOffice si disponible, sinon rendu de secours avec reportlab).

Sortie : <out>/rapport-<dossier>-<AAAA-MM>.docx et .pdf. Code de retour 0 si les deux
fichiers sont produits, 1 sinon.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

from docxtpl import DocxTemplate

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "outils" / "airtable"))

from airtable_client import AirtableClient, AirtableError, load_env, resolve_base_id  # noqa: E402

TEMPLATE = HERE / "template-rapport-mensuel.docx"
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
STATUTS_CLOS = {"Terminée", "Abandonnée"}


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def fmt_date(iso: str | None) -> str:
    if not iso:
        return "—"
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {MOIS_FR[d.month - 1]} {d.year}"


def fmt_montant(value: float | None) -> str:
    if value is None:
        return "—"
    entier, dec = f"{abs(value):,.2f}".split(".")
    entier = entier.replace(",", " ")
    signe = "-" if value < 0 else ""
    return f"{signe}{entier},{dec} €"


def periode_from(mois: str) -> tuple[date, date]:
    y, m = int(mois[:4]), int(mois[5:7])
    debut = date(y, m, 1)
    fin = (date(y + (m // 12), m % 12 + 1, 1) - timedelta(days=1))
    return debut, fin


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c").replace("ô", "o").replace("î", "i").replace("û", "u"))
    return s.strip("-")


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------
def fetch_data(api: AirtableClient, base_id: str, dossier: str) -> dict:
    client = api.find_first(base_id, "Clients", "Dossier", dossier)
    if not client:
        raise AirtableError(404, f"dossier « {dossier} » introuvable dans la table Clients")
    cid = client["id"]
    organismes = {o["id"]: o["fields"] for o in api.list_records(base_id, "Organismes") if cid in o["fields"].get("Client", [])}
    demarches = [d["fields"] | {"_id": d["id"]} for d in api.list_records(base_id, "Démarches") if cid in d["fields"].get("Client", [])]
    courriers = [c["fields"] | {"_id": c["id"]} for c in api.list_records(base_id, "Courriers") if cid in c["fields"].get("Client", [])]
    return {"client": client["fields"], "organismes": organismes, "demarches": demarches, "courriers": courriers}


def _org_name(fields: dict, organismes: dict) -> str:
    ids = fields.get("Organisme") or []
    if ids and ids[0] in organismes:
        nom = organismes[ids[0]].get("Nom", "")
        return nom.split(" — ")[0]
    return "—"


def build_context(data: dict, mois: str, edite_le: date | None = None, email_relais: str = "{{MANDATAIRE_EMAIL}}", telephone_relais: str = "{{MANDATAIRE_TELEPHONE}}") -> dict:
    """Transforme les enregistrements en contexte pour le modèle (structure de l'annexe C)."""
    debut, fin = periode_from(mois)
    edite_le = edite_le or date.today()
    c = data["client"]
    orgs = data["organismes"]

    def in_period(iso: str | None) -> bool:
        return bool(iso) and debut <= date.fromisoformat(iso[:10]) <= fin

    inclus = [d for d in data["demarches"] if d.get("À inclure au rapport", True)]
    realisees = sorted([d for d in inclus if d.get("Statut") == "Terminée" and in_period(d.get("Terminée le"))], key=lambda d: d.get("Terminée le", ""))
    en_cours = sorted([d for d in inclus if d.get("Statut") not in STATUTS_CLOS], key=lambda d: (d.get("Échéance") or "9999", d.get("Titre", "")))

    horizon = fin + timedelta(days=60)
    echeances = []
    for d in en_cours:
        e = d.get("Échéance")
        if e and date.fromisoformat(e) <= horizon:
            qui = "Vous" if d.get("Décision enfant requise") else ("Votre parent" if d.get("Statut") == "En attente parent" else "Relais")
            echeances.append({"date": fmt_date(e), "_d": e, "organisme": _org_name(d, orgs), "objet": d.get("Titre", ""), "qui": qui})
    for oid, o in orgs.items():
        dk = o.get("Date clé")
        if dk and debut <= date.fromisoformat(dk) <= horizon:
            echeances.append({"date": fmt_date(dk), "_d": dk, "organisme": o.get("Nom", "").split(" — ")[0], "objet": "Date clé du contrat ou du titre (échéance, expiration)", "qui": "Relais"})
    echeances.sort(key=lambda e: e["_d"])

    montants = [{"organisme": _org_name(d, orgs), "titre": d.get("Titre", ""), "montant": fmt_montant(d["Montant obtenu"]), "_v": d["Montant obtenu"]}
                for d in realisees if d.get("Montant obtenu")]
    total_mois = sum(m["_v"] for m in montants)
    cumul = sum(d.get("Montant obtenu") or 0 for d in data["demarches"] if d.get("Statut") == "Terminée")

    attention = []
    for d in en_cours:
        if d.get("Décision enfant requise"):
            attention.append({"texte": f"Décision attendue de votre part — {d.get('Titre', '')} ({_org_name(d, orgs)}) : {d.get('Prochaine étape', 'voir la démarche')}. Échéance : {fmt_date(d.get('Échéance'))}."})
        elif d.get("Statut") == "En attente enfant":
            attention.append({"texte": f"Document ou réponse attendu de votre part — {d.get('Titre', '')} ({_org_name(d, orgs)}). Échéance : {fmt_date(d.get('Échéance'))}."})
    for e in echeances:
        if e["qui"] == "Votre parent":
            attention.append({"texte": f"Action de votre parent — {e['objet']} ({e['organisme']}), avant le {e['date']} ; nous l'accompagnons par téléphone."})
    urgents = [d for d in en_cours if d.get("Urgence", "").startswith("4")]
    for d in urgents:
        attention.append({"texte": f"Situation critique suivie de près — {d.get('Titre', '')} ({_org_name(d, orgs)}) : {d.get('Prochaine étape', '')}."})

    courriers_mois = sorted([x for x in data["courriers"] if in_period(x.get("Reçu le"))], key=lambda x: x.get("Reçu le", ""))
    courriers_ctx = []
    for x in courriers_mois:
        statut = x.get("Statut", "")
        if statut == "Traité":
            traitement = f"Traité le {fmt_date(x.get('Traité le'))}"
        elif statut == "Classé sans suite":
            traitement = "Classé, sans action nécessaire"
        else:
            traitement = f"En cours ({statut.lower()})"
        courriers_ctx.append({"recu_le": fmt_date(x.get("Reçu le")), "organisme": _org_name(x, orgs), "titre": x.get("Résumé") or x.get("Type", ""), "traitement": traitement})
    non_traites = sum(1 for x in courriers_mois if x.get("Statut") in ("Non traité", "En cours"))

    nb_real, nb_cours = len(realisees), len(en_cours)
    ligne1 = f"{nb_real} démarche{'s' if nb_real != 1 else ''} clôturée{'s' if nb_real != 1 else ''} ce mois, {nb_cours} en cours, {len(courriers_mois)} courrier{'s' if len(courriers_mois) != 1 else ''} reçu{'s' if len(courriers_mois) != 1 else ''}."
    ligne2 = (f"Montants obtenus ce mois : {fmt_montant(total_mois)}." if total_mois else "Aucun montant obtenu ce mois ; les dossiers en cours portent sur "
              + fmt_montant(sum(d.get('Montant en jeu') or 0 for d in en_cours)) + ".")
    if attention:
        ligne3 = f"{len(attention)} point{'s' if len(attention) != 1 else ''} d'attention pour vous, détaillé{'s' if len(attention) != 1 else ''} en section 6."
    elif non_traites:
        ligne3 = f"{non_traites} courrier{'s' if non_traites != 1 else ''} en cours de traitement, sans action attendue de votre part."
    else:
        ligne3 = "Rien n'est attendu de votre part ce mois-ci."

    parent = c.get("Parent — Prénom Nom", "")
    situation = c.get("Parent — Situation", "")
    mode = c.get("Mode de réception du courrier", "")
    contacts_texte = (f"Ligne dédiée ouverte à {parent.split(' ')[0] if parent else 'votre parent'} aux heures ouvrées françaises. "
                      f"Situation : {situation.lower() if situation else 'non renseignée'}. Réception du courrier : {mode.lower() if mode else 'non renseignée'}. "
                      f"Prochain appel trimestriel avec vous : {fmt_date(c.get('Prochain appel trimestriel'))}.")

    return {
        "client": {"dossier": c.get("Dossier", ""), "parent": parent, "ville": c.get("Parent — Ville", ""), "enfant": c.get("Enfant — Prénom Nom", ""), "operateur": c.get("Opérateur", "Relais")},
        "periode": {"libelle": f"{MOIS_FR[debut.month - 1].capitalize()} {debut.year}", "debut": debut.isoformat(), "fin": fin.isoformat(), "edite_le": fmt_date(edite_le.isoformat())},
        "resume": {"ligne1": ligne1, "ligne2": ligne2, "ligne3": ligne3},
        "realisees": [{"organisme": _org_name(d, orgs), "titre": d.get("Titre", ""), "resultat": d.get("Résultat", ""), "terminee_le": fmt_date(d.get("Terminée le"))} for d in realisees],
        "en_cours": [{"organisme": _org_name(d, orgs), "titre": d.get("Titre", ""), "statut": d.get("Statut", ""), "prochaine_etape": d.get("Prochaine étape", ""), "echeance": fmt_date(d.get("Échéance"))} for d in en_cours],
        "echeances": [{k: v for k, v in e.items() if not k.startswith("_")} for e in echeances],
        "montants": [{k: v for k, v in m.items() if not k.startswith("_")} for m in montants],
        "montants_total": fmt_montant(total_mois),
        "montants_cumul": fmt_montant(cumul),
        "attention": attention,
        "courriers": courriers_ctx,
        "contacts": {"texte": contacts_texte, "email_relais": email_relais, "telephone_relais": telephone_relais},
    }


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------
def render_docx(context: dict, out_docx: Path, template: Path = TEMPLATE) -> Path:
    tpl = DocxTemplate(str(template))
    tpl.render(context)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    tpl.save(str(out_docx))
    return out_docx


def _soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    return None


def docx_to_pdf(docx_path: Path, pdf_path: Path, context: dict | None = None, timeout: int = 180) -> tuple[Path, str]:
    """Convertit en PDF avec LibreOffice ; à défaut, rendu de secours reportlab depuis le contexte."""
    exe = _soffice()
    if exe:
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOME=tmp)
            try:
                subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx_path)],
                               check=True, capture_output=True, timeout=timeout, env=env)
                produced = Path(tmp) / (docx_path.stem + ".pdf")
                if produced.exists() and produced.stat().st_size > 0:
                    shutil.copyfile(produced, pdf_path)
                    return pdf_path, "libreoffice"
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
                pass
    if context is None:
        raise RuntimeError("LibreOffice indisponible et aucun contexte fourni pour le rendu de secours")
    return render_pdf_fallback(context, pdf_path), "reportlab"


def render_pdf_fallback(context: dict, pdf_path: Path) -> Path:
    """Rendu PDF simplifié (mêmes sections) sans LibreOffice."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading2"], textColor=colors.HexColor("#1F3A5F"), spaceBefore=10)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=12)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=10.5)

    def table(headers, rows, widths):
        data = [[Paragraph(f"<b>{h}</b>", small) for h in headers]] + [[Paragraph(str(v), small) for v in r] for r in rows]
        if not rows:
            data.append([Paragraph("<i>Néant</i>", small)] + [""] * (len(headers) - 1))
        t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C4D3")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    c, p, r = context["client"], context["periode"], context["resume"]
    story = [Paragraph(f"RELAIS — Rapport mensuel — {p['libelle']}", styles["Title"]),
             Paragraph(f"Dossier {c['dossier']} · Bénéficiaire : {c['parent']}, {c['ville']} · Destinataire : {c['enfant']} · Interlocuteur : {c['operateur']} · Édité le {p['edite_le']}", body),
             Paragraph("1. Résumé", h1), Paragraph(r["ligne1"], body), Paragraph(r["ligne2"], body), Paragraph(r["ligne3"], body),
             Paragraph("2. Démarches réalisées ce mois", h1), table(["Organisme", "Action", "Résultat", "Terminée le"], [[d["organisme"], d["titre"], d["resultat"], d["terminee_le"]] for d in context["realisees"]], [3.4, 4.4, 6.4, 2.6]),
             Paragraph("3. Démarches en cours et prochaine étape", h1), table(["Organisme", "Démarche", "Statut", "Prochaine étape", "Échéance"], [[d["organisme"], d["titre"], d["statut"], d["prochaine_etape"], d["echeance"]] for d in context["en_cours"]], [3.0, 4.0, 2.6, 4.6, 2.6]),
             Paragraph("4. Échéances des 60 prochains jours", h1), table(["Date", "Organisme", "Objet", "Qui agit"], [[e["date"], e["organisme"], e["objet"], e["qui"]] for e in context["echeances"]], [2.6, 3.6, 7.4, 3.2]),
             Paragraph("5. Montants obtenus ou économisés", h1), table(["Organisme", "Démarche", "Montant"], [[m["organisme"], m["titre"], m["montant"]] for m in context["montants"]], [4.4, 9.0, 3.4]),
             Paragraph(f"<b>Total du mois : {context['montants_total']} · Total depuis le début du mandat : {context['montants_cumul']}</b>", body),
             Paragraph("6. Points d'attention pour vous", h1)]
    story += [Paragraph("• " + a["texte"], body) for a in context["attention"]] or [Paragraph("Aucune décision ni document ne sont attendus de votre part ce mois-ci.", body)]
    story += [Paragraph("7. Contacts et échanges avec votre parent", h1), Paragraph(context["contacts"]["texte"], body),
              table(["Reçu le", "Organisme", "Document", "Traitement"], [[x["recu_le"], x["organisme"], x["titre"], x["traitement"]] for x in context["courriers"]], [2.4, 3.4, 6.2, 4.8]),
              Spacer(1, 8), Paragraph(f"<i>Prochain rapport le 1er du mois prochain. {context['contacts']['email_relais']} — {context['contacts']['telephone_relais']}</i>", small)]
    SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm, title=f"Rapport mensuel {c['dossier']} {p['libelle']}").build(story)
    return pdf_path


def generate(api: AirtableClient, base_id: str, dossier: str, mois: str, out_dir: Path, edite_le: date | None = None, template: Path = TEMPLATE) -> dict:
    data = fetch_data(api, base_id, dossier)
    context = build_context(data, mois, edite_le=edite_le,
                            email_relais=os.environ.get("MANDATAIRE_EMAIL") or "{{MANDATAIRE_EMAIL}}",
                            telephone_relais=os.environ.get("MANDATAIRE_TELEPHONE") or "{{MANDATAIRE_TELEPHONE}}")
    base_name = f"rapport-{slug(dossier)}-{mois}"
    docx_path = render_docx(context, out_dir / f"{base_name}.docx", template)
    pdf_path, engine = docx_to_pdf(docx_path, out_dir / f"{base_name}.pdf", context)
    return {"docx": docx_path, "pdf": pdf_path, "pdf_engine": engine, "context": context}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client", required=True, help="valeur du champ « Dossier » de la table Clients")
    parser.add_argument("--mois", default=date.today().strftime("%Y-%m"), help="mois du rapport AAAA-MM (défaut : mois en cours)")
    parser.add_argument("--out", type=Path, default=HERE / "sorties", help="dossier de sortie")
    parser.add_argument("--base", help="identifiant de la base (sinon AIRTABLE_BASE_ID ou .base_id)")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.mois):
        print("✘ --mois doit être au format AAAA-MM", file=sys.stderr)
        return 1
    if not TEMPLATE.exists():
        print(f"✘ modèle absent : {TEMPLATE} (lancer build_template.py)", file=sys.stderr)
        return 1
    load_env()
    base_id = resolve_base_id(args.base)
    if not base_id:
        print("✘ base inconnue : renseigner AIRTABLE_BASE_ID ou lancer create_base.py", file=sys.stderr)
        return 1
    try:
        result = generate(AirtableClient(), base_id, args.client, args.mois, args.out)
    except AirtableError as exc:
        print(f"✘ {exc}", file=sys.stderr)
        return 1
    print(f"✔ {result['docx']}\n✔ {result['pdf']} (moteur : {result['pdf_engine']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
