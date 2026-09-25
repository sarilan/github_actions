#!/usr/bin/env python3
"""Construit le site public de Relais dans dist/, prêt à publier sur Cloudflare Pages.

Usage :
    python3 site/build.py                 # build de publication (échoue si une valeur manque)
    python3 site/build.py --apercu        # aperçu local : valeurs manquantes surlignées, non publiable
    python3 site/build.py --config autre.json --sortie dossier/

Pages produites :
    /                      page d'accueil (site/src/index.html)
    /cgv/                  conditions générales de vente     (juridique/sources/cgv.md)
    /confidentialite/      politique de confidentialité       (juridique/sources/politique-confidentialite.md)
    /mandat/               modèle de mandat                   (juridique/sources/mandat-administratif.md)
    /mentions-legales/     mentions légales
    /404.html, /robots.txt, /sitemap.xml, /_headers, /og-image.png

Les documents juridiques du site sont générés depuis les mêmes sources Markdown que les
documents Word : une modification des sources se répercute partout. L'encadré interne
« Document à faire valider par un avocat » n'est pas publié.

Aucune dépendance hors bibliothèque standard (le build tourne tel quel sur Cloudflare).
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE / "juridique"))

from organismes import ORGANISMES_CHECKLIST  # noqa: E402
from variables import VariablesManquantes, render  # noqa: E402

SOURCES_JURIDIQUES = RACINE / "juridique" / "sources"
AVERTISSEMENT = "Document à faire valider par un avocat avant utilisation."

# (chemin publié, source Markdown, titre court pour la navigation)
DOCUMENTS = [
    ("cgv", "cgv.md", "Conditions générales de vente"),
    ("confidentialite", "politique-confidentialite.md", "Politique de confidentialité"),
    ("mandat", "mandat-administratif.md", "Modèle de mandat"),
]


class ErreurBuild(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def charger_config(chemin: Path) -> dict[str, str]:
    brut = json.loads(chemin.read_text(encoding="utf-8"))
    valeurs = {k: ("" if v is None else str(v)) for k, v in brut.items() if not k.startswith("_")}
    # Les variables d'environnement du même nom priment (réglages Cloudflare).
    for cle in list(valeurs):
        if os.environ.get(cle, "").strip():
            valeurs[cle] = os.environ[cle].strip()
    valeurs["SITE_URL"] = valeurs.get("SITE_URL", "").rstrip("/")
    # Adresses de contact : une seule suffit au lancement, les autres la reprennent si elles sont vides.
    for cle in ("MANDATAIRE_EMAIL", "DPO_EMAIL"):
        if not valeurs.get(cle):
            valeurs[cle] = valeurs.get("CONTACT_EMAIL", "")
    return valeurs


def controler_config(v: dict[str, str]) -> list[str]:
    """Règles de cohérence entre valeurs, au-delà du simple « renseigné / vide »."""
    erreurs = []
    if v.get("SITE_URL") and not re.fullmatch(r"https://[a-z0-9.-]+\.[a-z]{2,}", v["SITE_URL"]):
        erreurs.append("SITE_URL doit être de la forme https://domaine.tld (sans chemin ni barre finale)")
    for cle in ("CONTACT_EMAIL", "MANDATAIRE_EMAIL", "DPO_EMAIL", "EMAIL_2FA_RELAIS"):
        if v.get(cle) and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]{2,}", v[cle]):
            erreurs.append(f"{cle} n'est pas une adresse de courriel valide")
    if bool(v.get("TELEPHONE_AFFICHE")) != bool(v.get("TELEPHONE_LIEN")):
        erreurs.append("TELEPHONE_AFFICHE et TELEPHONE_LIEN vont ensemble : renseigner les deux ou aucun")
    if v.get("TELEPHONE_LIEN") and not re.fullmatch(r"\+\d{8,15}", v["TELEPHONE_LIEN"]):
        erreurs.append("TELEPHONE_LIEN doit être au format international, ex. +33180000000")
    if v.get("FORMSPREE_ENDPOINT"):
        if not re.fullmatch(r"https://formspree\.io/f/[A-Za-z0-9]+", v["FORMSPREE_ENDPOINT"]):
            erreurs.append("FORMSPREE_ENDPOINT doit être de la forme https://formspree.io/f/xxxxxxxx")
        if not v.get("FORMSPREE_ENTITE"):
            erreurs.append("FORMSPREE_ENTITE est obligatoire dès que FORMSPREE_ENDPOINT est renseigné "
                           "(sous-traitant cité dans la politique de confidentialité)")
    if bool(v.get("ASSUREUR_RC_PRO")) != bool(v.get("NUMERO_POLICE_RC_PRO")):
        erreurs.append("ASSUREUR_RC_PRO et NUMERO_POLICE_RC_PRO vont ensemble")
    mediateur = [v.get(k) for k in ("MEDIATEUR_NOM", "MEDIATEUR_ADRESSE", "MEDIATEUR_SITE")]
    if any(mediateur) and not all(mediateur):
        erreurs.append("MEDIATEUR_NOM, MEDIATEUR_ADRESSE et MEDIATEUR_SITE vont ensemble")
    return erreurs


# ---------------------------------------------------------------------------
# Markdown -> HTML (sous-ensemble utilisé par juridique/sources, voir juridique/generate.py)
# ---------------------------------------------------------------------------
_GRAS = re.compile(r"\*\*(.+?)\*\*")
_MANQUANT = re.compile(r"\[\[MANQUANT:([A-Z0-9_]+)\]\]")


def inline(texte: str) -> str:
    t = html.escape(texte, quote=False)
    t = _GRAS.sub(r"<strong>\1</strong>", t)
    t = _MANQUANT.sub(r'<mark class="manquant">\1</mark>', t)
    return t


def ancre(texte: str) -> str:
    t = texte.lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"), ("ùûü", "u"), ("ç", "c"), ("œ", "oe")):
        for c in a:
            t = t.replace(c, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def signatures_html(v: dict[str, str]) -> str:
    raison = inline(v.get("MANDATAIRE_RAISON_SOCIALE", ""))
    representant = inline(v.get("MANDATAIRE_REPRESENTANT", ""))
    return f"""<p>Fait à ……………………………………, le ……… / ……… / ………………, en deux exemplaires originaux.</p>
<div class="signatures">
  <div><p><strong>Le Mandant</strong></p><p>Nom, prénom : ……………………………………</p><p><em>Mention manuscrite obligatoire : « Bon pour mandat »</em></p><p class="zone-signature">Signature :</p></div>
  <div><p><strong>Le Mandataire</strong></p><p>{raison} — service Relais</p><p>Représenté par : {representant}</p><p class="zone-signature">Signature et cachet :</p></div>
  <div class="large"><p><strong>Copie reçue par la Personne de confiance</strong></p><p>Nom, prénom : ……………………………………   Date : ……… / ……… / ………………</p><p>Je reconnais avoir reçu copie du présent mandat et accepte d'être destinataire des rapports et des alertes.</p><p class="zone-signature">Signature :</p></div>
</div>"""


def checklist_html() -> str:
    lignes = "\n".join(
        f'<tr><td class="case" aria-label="Case à cocher">☐</td><td>{inline(org)}</td><td></td></tr>'
        for org in ORGANISMES_CHECKLIST
    )
    return f"""<div class="tableau"><table>
<thead><tr><th scope="col"><span class="visually-hidden">Coché</span></th><th scope="col">Organisme ou compte</th><th scope="col">Identifiant, n° de dossier ou remarque</th></tr></thead>
<tbody>
{lignes}
</tbody></table></div>
<p><em>Paraphe du Mandant : ……………   Paraphe du Mandataire : ……………</em></p>"""


def markdown_en_html(texte: str, v: dict[str, str]) -> tuple[str, str, list[tuple[str, str]]]:
    """Retourne (titre, corps HTML, sommaire [(ancre, libellé)])."""
    lignes = texte.splitlines()
    titre = next((ln[2:].strip() for ln in lignes if ln.startswith("# ")), "")
    corps: list[str] = []
    sommaire: list[tuple[str, str]] = []
    paragraphe: list[str] = []
    tableau: list[list[str]] = []
    liste: list[str] = []
    numero = 0
    avertissement_vu = False

    def vider_paragraphe():
        if paragraphe:
            corps.append(f"<p>{inline(' '.join(s.strip() for s in paragraphe))}</p>")
            paragraphe.clear()

    def vider_liste():
        if liste:
            corps.append("<ul>\n" + "\n".join(f"<li>{inline(e)}</li>" for e in liste) + "\n</ul>")
            liste.clear()

    def vider_tableau():
        if tableau:
            entete, *lignes_t = tableau
            th = "".join(f'<th scope="col">{inline(c)}</th>' for c in entete)
            trs = "\n".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in ligne) + "</tr>" for ligne in lignes_t)
            corps.append(f'<div class="tableau"><table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n{trs}\n</tbody></table></div>')
            tableau.clear()

    def vider_tout():
        vider_paragraphe()
        vider_liste()
        vider_tableau()

    for ligne in lignes:
        s = ligne.strip()
        if s.startswith("|"):
            vider_paragraphe()
            vider_liste()
            cellules = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cellules):
                tableau.append(cellules)
            continue
        vider_tableau()
        if not s:
            vider_paragraphe()
            vider_liste()
        elif s.startswith("# "):
            continue
        elif s.startswith("## "):
            vider_tout()
            intitule = s[3:].strip()
            if intitule.startswith("Article"):
                numero += 1
                libelle = intitule.split("—", 1)[1].strip() if "—" in intitule else intitule
                texte_titre = f"Article {numero} — {libelle}"
                id_ = f"article-{numero}"
            else:
                texte_titre = intitule
                id_ = ancre(intitule)
            sommaire.append((id_, texte_titre))
            corps.append(f'<h2 id="{id_}">{inline(texte_titre)}</h2>')
        elif s.startswith("### "):
            vider_tout()
            corps.append(f"<h3>{inline(s[4:].strip())}</h3>")
        elif s.startswith("> "):
            vider_tout()
            contenu = s[2:].strip()
            if not avertissement_vu and contenu == AVERTISSEMENT:
                avertissement_vu = True  # note interne, non publiée
                continue
            corps.append(f'<blockquote class="modele">{inline(contenu)}</blockquote>')
        elif s.startswith("- "):
            vider_paragraphe()
            liste.append(s[2:].strip())
        elif s == "[[SIGNATURES]]":
            vider_tout()
            corps.append(signatures_html(v))
        elif s == "[[CHECKLIST]]":
            vider_tout()
            corps.append(checklist_html())
        else:
            vider_liste()
            paragraphe.append(s)
    vider_tout()
    return titre, "\n".join(corps), sommaire


# ---------------------------------------------------------------------------
# Gabarit des pages secondaires
# ---------------------------------------------------------------------------
CSS_PAGES = """
:root{--bleu:#1f3a5f;--bleu-fonce:#142640;--bleu-clair:#e8eef5;--ocre:#a3560f;--ocre-fonce:#8a4b00;--texte:#1c2430;--texte-doux:#4a5563;--fond:#fff;--fond-doux:#f6f8fb;--bord:#d5dde7;--rayon:12px;--max:820px;--serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:var(--sans);font-size:1.0625rem;line-height:1.65;color:var(--texte);background:var(--fond)}
a{color:var(--bleu)}
a:focus-visible{outline:3px solid var(--ocre);outline-offset:3px}
.visually-hidden{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.lien-evitement{position:absolute;left:-999px;top:0;background:var(--bleu);color:#fff;padding:.6rem 1rem;z-index:100}
.lien-evitement:focus{left:1rem;top:1rem}
.conteneur{width:min(100% - 2rem,var(--max));margin-inline:auto}
header.site{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.96);border-bottom:1px solid var(--bord)}
.barre{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.75rem 0;width:min(100% - 2rem,1080px);margin-inline:auto}
.logo{display:inline-flex;align-items:center;gap:.55rem;text-decoration:none;font-family:var(--serif);font-weight:700;font-size:1.35rem;color:var(--bleu)}
.logo svg{width:32px;height:32px}
.bouton{display:inline-block;padding:.55rem 1rem;border-radius:999px;font-weight:600;text-decoration:none;background:var(--ocre);color:#fff;font-size:.95rem}
.bouton:hover{background:var(--ocre-fonce)}
main{padding:2.5rem 0 3.5rem}
h1,h2,h3{font-family:var(--serif);line-height:1.25;color:var(--bleu);text-wrap:balance}
h1{font-size:clamp(1.7rem,4.5vw,2.4rem);margin:0 0 .4rem}
h2{font-size:1.3rem;margin:2.2rem 0 .6rem;scroll-margin-top:5rem}
h3{font-size:1.1rem;margin:1.4rem 0 .4rem}
p{margin:0 0 1em}
main p,main li,main td,main blockquote{overflow-wrap:anywhere}
.fil{font-size:.92rem;color:var(--texte-doux);margin-bottom:1.25rem}
.chapeau{color:var(--texte-doux);margin-bottom:1.5rem}
nav.sommaire{background:var(--fond-doux);border:1px solid var(--bord);border-radius:var(--rayon);padding:1rem 1.25rem;margin:1.5rem 0}
nav.sommaire h2{font-family:var(--sans);font-size:.85rem;text-transform:uppercase;letter-spacing:.06em;margin:0 0 .5rem;color:var(--texte-doux)}
nav.sommaire ol{margin:0;padding-left:1.1rem;columns:2 16rem;column-gap:2rem;font-size:.95rem}
nav.sommaire li{break-inside:avoid;margin-bottom:.25rem}
nav.sommaire ol{list-style:none;padding-left:0}
ul{padding-left:1.25rem}
li{margin-bottom:.35rem}
.tableau{overflow-x:auto;margin:1rem 0 1.25rem;border:1px solid var(--bord);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th,td{text-align:left;vertical-align:top;padding:.6rem .7rem;border-bottom:1px solid var(--bord)}
thead th{background:var(--bleu-clair);color:var(--bleu)}
tbody tr:last-child td{border-bottom:0}
td.case{font-size:1.2rem;text-align:center;width:2.5rem}
blockquote.modele{margin:1rem 0;padding:1rem 1.25rem;background:var(--fond-doux);border-left:4px solid var(--bleu);border-radius:0 8px 8px 0}
.signatures{display:grid;gap:1rem;margin:1rem 0 1.5rem}
.signatures>div{border:1px solid var(--bord);border-radius:8px;padding:1rem}
.signatures p{margin:0 0 .4rem}
.zone-signature{padding-top:3rem}
@media (min-width:640px){.signatures{grid-template-columns:1fr 1fr}.signatures .large{grid-column:1/-1}}
.actions-doc{display:flex;flex-wrap:wrap;gap:.75rem;margin:1.5rem 0 0}
.actions-doc button{font:inherit;font-size:.95rem;padding:.5rem 1rem;border-radius:999px;border:2px solid var(--bleu);background:transparent;color:var(--bleu);cursor:pointer}
.bandeau-apercu{background:#fff4d6;border-bottom:2px solid #c77700;color:#5c3500;padding:.6rem 1rem;text-align:center;font-weight:600}
mark.manquant{background:#ffe08a;color:#5c3500;padding:0 .25rem;border-radius:4px;font-family:ui-monospace,monospace;font-size:.85em}
footer.site{background:var(--bleu-fonce);color:#d9e1ec;padding:2rem 0;font-size:.95rem}
footer.site a{color:#fff}
footer .liens{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;list-style:none;margin:0 0 1rem;padding:0}
footer .petit{font-size:.88rem;color:#b6c2d2;margin:0}
@media print{header.site,footer.site,nav.sommaire,.actions-doc,.lien-evitement{display:none}main{padding:0}a{color:inherit;text-decoration:none}}
"""

LOGO_SVG = ('<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><rect width="64" height="64" rx="14" fill="#1f3a5f"/>'
            '<path d="M18 46V18h14a9 9 0 0 1 3.4 17.3L42 46h-8l-5.6-9.6H25V46z M25 24v7h7a3.5 3.5 0 0 0 0-7z" fill="#fff"/></svg>')
FAVICON = ("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'%20height='64'%20rx='14'%20fill='%231f3a5f'/%3E"
           "%3Cpath%20d='M18%2046V18h14a9%209%200%200%201%203.4%2017.3L42%2046h-8l-5.6-9.6H25V46z%20M25%2024v7h7a3.5%203.5%200%200%200%200-7z'%20fill='%23fff'/%3E%3C/svg%3E")


def page(v: dict[str, str], *, chemin: str, titre: str, description: str, contenu: str,
         apercu: bool, indexable: bool = True) -> str:
    url = f"{v['SITE_URL']}{chemin}" if v.get("SITE_URL") else chemin
    robots = "index, follow" if indexable and not apercu else "noindex, follow"
    bandeau = ('<div class="bandeau-apercu" role="note">Aperçu local — les valeurs surlignées ne sont pas encore '
               'renseignées dans site/config.json. Ne pas publier.</div>') if apercu else ""
    liens_pied = "".join(
        f'<li><a href="/{slug}/">{html.escape(nom)}</a></li>' for slug, _, nom in DOCUMENTS
    ) + '<li><a href="/mentions-legales/">Mentions légales</a></li>'
    contact = html.escape(v.get("CONTACT_EMAIL", ""))
    contact_html = f'<a href="mailto:{contact}">{contact}</a>' if contact else '<mark class="manquant">CONTACT_EMAIL</mark>'
    document = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(titre)} — Relais</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{html.escape(url)}">
  <meta name="robots" content="{robots}">
  <meta name="theme-color" content="#1f3a5f">
  <link rel="icon" href="{FAVICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=Inter:wght@400;500;600&display=swap">
  <style>{CSS_PAGES}</style>
</head>
<body>
  {bandeau}
  <a class="lien-evitement" href="#contenu">Aller au contenu</a>
  <header class="site">
    <div class="barre">
      <a class="logo" href="/" aria-label="Relais, accueil">{LOGO_SVG}Relais</a>
      <a class="bouton" href="/#contact">Réserver un appel</a>
    </div>
  </header>
  <main id="contenu">
    <div class="conteneur">
{contenu}
    </div>
  </main>
  <footer class="site">
    <div class="conteneur">
      <ul class="liens">
        <li><a href="/">Accueil</a></li>
        {liens_pied}
      </ul>
      <p class="petit">Contact : {contact_html}. Ce site ne dépose aucun cookie et n'utilise aucun outil de mesure d'audience.</p>
    </div>
  </footer>
</body>
</html>
"""
    # Lignes vides des blocs optionnels (bandeau d'aperçu, bouton d'impression) : pas d'espaces en fin de ligne.
    return "\n".join(ligne.rstrip() for ligne in document.splitlines()) + "\n"


def page_document(v: dict[str, str], slug: str, source: str, nom: str, apercu: bool) -> str:
    texte = (SOURCES_JURIDIQUES / source).read_text(encoding="utf-8")
    texte = resoudre(texte, v, apercu, contexte=f"juridique/sources/{source}")
    titre, corps, sommaire = markdown_en_html(texte, v)
    items = "\n".join(f'<li><a href="#{a}">{inline(t)}</a></li>' for a, t in sommaire)
    imprimer = ('<div class="actions-doc"><button type="button" onclick="window.print()">Imprimer ou enregistrer en PDF</button></div>'
                if slug == "mandat" else "")
    chapeau = {
        "cgv": "Conditions applicables à la souscription de l'abonnement et des forfaits Relais.",
        "confidentialite": "Comment Relais traite les données personnelles de ses clients, de leurs parents et des visiteurs du site.",
        "mandat": "Modèle du mandat de représentation administrative signé par le parent. Il est envoyé pré-rempli au parent et à l'enfant après l'appel de présentation.",
    }[slug]
    contenu = f"""      <p class="fil"><a href="/">Accueil</a> › {html.escape(nom)}</p>
      <h1>{inline(titre)}</h1>
      <p class="chapeau">{html.escape(chapeau)}</p>
      <nav class="sommaire" aria-label="Sommaire"><h2>Sommaire</h2><ol>
{items}
      </ol></nav>
{corps}
      {imprimer}"""
    return page(v, chemin=f"/{slug}/", titre=nom, description=chapeau, contenu=contenu, apercu=apercu)


GABARIT_MENTIONS = """## Éditeur du site

Le site {{SITE_URL}} est édité par {{MANDATAIRE_RAISON_SOCIALE}}, {{MANDATAIRE_FORME_JURIDIQUE}} au capital de {{MANDATAIRE_CAPITAL}} €, immatriculée au registre du commerce et des sociétés de {{MANDATAIRE_VILLE_RCS}} sous le numéro {{MANDATAIRE_SIREN}}{{#MANDATAIRE_TVA}}, numéro de TVA intracommunautaire {{MANDATAIRE_TVA}}{{/MANDATAIRE_TVA}}, dont le siège social est situé {{MANDATAIRE_ADRESSE}}. La société exploite le service Relais.

Courriel : {{CONTACT_EMAIL}}{{#TELEPHONE_AFFICHE}} — Téléphone : {{TELEPHONE_AFFICHE}}{{/TELEPHONE_AFFICHE}}

## Directeur de la publication

{{MANDATAIRE_REPRESENTANT}}, {{MANDATAIRE_QUALITE_REPRESENTANT}} de {{MANDATAIRE_RAISON_SOCIALE}}.

## Hébergeur

{{HEBERGEUR_NOM}}, {{HEBERGEUR_ADRESSE}}.

## Propriété intellectuelle

Les textes, la marque « Relais », le logo et la mise en page de ce site sont la propriété de {{MANDATAIRE_RAISON_SOCIALE}}. Toute reproduction, même partielle, sans autorisation écrite préalable est interdite. Les polices de caractères Source Serif 4 et Inter sont diffusées sous licence SIL Open Font License.

## Données personnelles et cookies

Les données transmises par le formulaire de contact ou par courriel sont traitées conformément à la politique de confidentialité. Ce site ne dépose aucun cookie et n'utilise aucun outil de mesure d'audience ni de publicité.
"""


def page_mentions(v: dict[str, str], apercu: bool) -> str:
    texte = resoudre(GABARIT_MENTIONS, v, apercu, contexte="mentions légales (site/build.py)")
    _, corps, _ = markdown_en_html(texte, v)
    corps = corps.replace("politique de confidentialité.", '<a href="/confidentialite/">politique de confidentialité</a>.', 1)
    contenu = f"""      <p class="fil"><a href="/">Accueil</a> › Mentions légales</p>
      <h1>Mentions légales</h1>
      <p class="chapeau">Informations prévues par l'article 6 de la loi n° 2004-575 du 21 juin 2004 pour la confiance dans l'économie numérique.</p>
{corps}"""
    return page(v, chemin="/mentions-legales/", titre="Mentions légales",
                description="Éditeur, directeur de la publication et hébergeur du site Relais.", contenu=contenu, apercu=apercu)


def page_404(v: dict[str, str], apercu: bool) -> str:
    contenu = """      <h1>Page introuvable</h1>
      <p class="chapeau">Cette adresse ne correspond à aucune page du site.</p>
      <p><a href="/">Revenir à l'accueil</a> ou <a href="/#contact">réserver un appel de 20 minutes</a>.</p>"""
    return page(v, chemin="/404.html", titre="Page introuvable", description="Page introuvable.",
                contenu=contenu, apercu=apercu, indexable=False)


# ---------------------------------------------------------------------------
# Résolution des variables
# ---------------------------------------------------------------------------
_MANQUANTES: dict[str, set[str]] = {}


def resoudre(texte: str, v: dict[str, str], apercu: bool, contexte: str, echapper=None) -> str:
    try:
        return render(texte, v, echapper=echapper)
    except VariablesManquantes as e:
        _MANQUANTES.setdefault(contexte, set()).update(e.noms)
        if not apercu:
            return ""
        complete = dict(v)
        for nom in e.noms:
            complete[nom] = f"[[MANQUANT:{nom}]]"
        return render(texte, complete, echapper=echapper)


def page_accueil(v: dict[str, str], apercu: bool) -> str:
    texte = (ICI / "src" / "index.html").read_text(encoding="utf-8")
    sortie = resoudre(texte, v, apercu, contexte="site/src/index.html",
                      echapper=lambda s: html.escape(s, quote=True))
    sortie = _MANQUANT.sub(r'<mark class="manquant">\1</mark>', sortie)
    if apercu:
        sortie = sortie.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, follow">', 1)
        sortie = sortie.replace("<body>", '<body>\n  <div style="background:#fff4d6;border-bottom:2px solid #c77700;color:#5c3500;padding:.6rem 1rem;text-align:center;font-weight:600" role="note">Aperçu local — valeurs manquantes surlignées. Ne pas publier.</div>', 1)
        sortie = sortie.replace("</style>", "mark.manquant{background:#ffe08a;color:#5c3500;padding:0 .25rem;border-radius:4px;font-family:ui-monospace,monospace;font-size:.85em}\n  </style>", 1)
    return sortie


# ---------------------------------------------------------------------------
# Fichiers techniques
# ---------------------------------------------------------------------------
def entetes(v: dict[str, str]) -> str:
    connect = "'self' https://formspree.io" if v.get("FORMSPREE_ENDPOINT") else "'self'"
    action = "'self' https://formspree.io mailto:" if v.get("FORMSPREE_ENDPOINT") else "'self' mailto:"
    csp = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           f"font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src {connect}; form-action {action}; "
           "base-uri 'self'; frame-ancestors 'none'; object-src 'none'; upgrade-insecure-requests")
    regles = f"""/*
  Content-Security-Policy: {csp}
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Strict-Transport-Security: max-age=31536000

/og-image.png
  Cache-Control: public, max-age=604800
"""
    if not v.get("SITE_URL", "").endswith(".pages.dev"):
        # Domaine propre en place : l'adresse technique .pages.dev ne doit pas être indexée en doublon.
        regles += "\nhttps://:project.pages.dev/*\n  X-Robots-Tag: noindex\n"
    return regles


def robots(v: dict[str, str], apercu: bool) -> str:
    if apercu:
        return "User-agent: *\nDisallow: /\n"
    return f"User-agent: *\nAllow: /\n\nSitemap: {v['SITE_URL']}/sitemap.xml\n"


def sitemap(v: dict[str, str]) -> str:
    aujourd_hui = date.today().isoformat()
    chemins = ["/"] + [f"/{slug}/" for slug, _, _ in DOCUMENTS] + ["/mentions-legales/"]
    urls = "\n".join(
        f"  <url><loc>{html.escape(v['SITE_URL'] + c)}</loc><lastmod>{aujourd_hui}</lastmod></url>" for c in chemins
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'


# ---------------------------------------------------------------------------
# Vérifications de la sortie
# ---------------------------------------------------------------------------
def verifier_sortie(sortie: Path, apercu: bool) -> list[str]:
    problemes: list[str] = []
    pages = sorted(sortie.rglob("*.html"))
    ids_par_page: dict[Path, set[str]] = {}
    for p in pages:
        contenu = p.read_text(encoding="utf-8")
        ids_par_page[p] = set(re.findall(r'\sid="([^"]+)"', contenu))
        if not apercu and ("{{" in contenu or "[[MANQUANT" in contenu or 'class="manquant"' in contenu):
            problemes.append(f"{p.relative_to(sortie)} : variable non résolue")
        if AVERTISSEMENT in contenu:
            problemes.append(f"{p.relative_to(sortie)} : encadré interne « avocat » publié")
        if not re.search(r"<title>[^<]+</title>", contenu):
            problemes.append(f"{p.relative_to(sortie)} : balise <title> absente")
        if contenu.count("<h1") != 1:
            problemes.append(f"{p.relative_to(sortie)} : {contenu.count('<h1')} titres h1 (1 attendu)")
    for p in pages:
        contenu = p.read_text(encoding="utf-8")
        for lien in re.findall(r'href="(/[^"]*|#[^"]*)"', contenu):
            chemin, _, fragment = lien.partition("#")
            if not chemin:
                cible = p
            else:
                cible = sortie / chemin.lstrip("/")
                if chemin.endswith("/") or cible.is_dir():
                    cible = cible / "index.html"
            if not cible.exists():
                problemes.append(f"{p.relative_to(sortie)} : lien cassé {lien}")
            elif fragment and fragment not in ids_par_page.get(cible, set()):
                problemes.append(f"{p.relative_to(sortie)} : ancre introuvable {lien}")
    for requis in ("index.html", "cgv/index.html", "confidentialite/index.html", "mandat/index.html",
                   "mentions-legales/index.html", "404.html", "robots.txt", "sitemap.xml", "_headers", "og-image.png"):
        if not (sortie / requis).exists():
            problemes.append(f"fichier attendu absent : {requis}")
    return problemes


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------
def construire(config: Path, sortie: Path, apercu: bool = False) -> dict[str, set[str]]:
    """Construit le site. Retourne les variables manquantes par fichier (vide si tout est renseigné)."""
    _MANQUANTES.clear()
    v = charger_config(config)
    erreurs = controler_config(v)
    if erreurs:
        raise ErreurBuild("configuration incohérente :\n  - " + "\n  - ".join(erreurs))

    fichiers: dict[str, str] = {"index.html": page_accueil(v, apercu)}
    for slug, source, nom in DOCUMENTS:
        fichiers[f"{slug}/index.html"] = page_document(v, slug, source, nom, apercu)
    fichiers["mentions-legales/index.html"] = page_mentions(v, apercu)
    fichiers["404.html"] = page_404(v, apercu)

    if _MANQUANTES and not apercu:
        return dict(_MANQUANTES)
    if not v.get("SITE_URL"):
        _MANQUANTES.setdefault("site/config.json", set()).add("SITE_URL")
        if not apercu:
            return dict(_MANQUANTES)

    fichiers["robots.txt"] = robots(v, apercu)
    fichiers["sitemap.xml"] = sitemap(v) if v.get("SITE_URL") else ""
    fichiers["_headers"] = entetes(v)

    if sortie.exists():
        shutil.rmtree(sortie)
    for nom, contenu in fichiers.items():
        cible = sortie / nom
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")
    for statique in (ICI / "static").iterdir():
        shutil.copy2(statique, sortie / statique.name)

    problemes = verifier_sortie(sortie, apercu)
    if problemes:
        raise ErreurBuild("contrôles de sortie en échec :\n  - " + "\n  - ".join(problemes))
    return dict(_MANQUANTES)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=ICI / "config.json")
    parser.add_argument("--sortie", type=Path, default=None, help="dossier de sortie (défaut : dist/, ou dist-apercu/ avec --apercu)")
    parser.add_argument("--apercu", action="store_true", help="aperçu local non publiable, valeurs manquantes surlignées")
    args = parser.parse_args(list(argv) if argv is not None else None)
    sortie = args.sortie or (RACINE / ("dist-apercu" if args.apercu else "dist"))

    try:
        manquantes = construire(args.config, sortie, apercu=args.apercu)
    except ErreurBuild as e:
        print(f"✘ {e}", file=sys.stderr)
        return 1

    toutes = sorted(set().union(*manquantes.values())) if manquantes else []
    if manquantes and not args.apercu:
        print("✘ Valeurs obligatoires non renseignées dans site/config.json :", file=sys.stderr)
        for nom in toutes:
            print(f"  - {nom}", file=sys.stderr)
        print("Rien n'a été écrit. Renseigner ces valeurs puis relancer (ou --apercu pour prévisualiser).", file=sys.stderr)
        return 1

    nb = len(list(sortie.rglob("*.html")))
    if args.apercu:
        print(f"✔ Aperçu construit dans {sortie} ({nb} pages)" + (f" — {len(toutes)} valeur(s) manquante(s) : {', '.join(toutes)}" if toutes else ""))
    else:
        print(f"✔ Site construit dans {sortie} ({nb} pages), contrôles de sortie conformes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
