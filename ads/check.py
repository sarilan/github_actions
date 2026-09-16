#!/usr/bin/env python3
"""Contrôle les fichiers d'import Google Ads Editor de la campagne Relais.

Usage :
    python3 ads/check.py            # code de retour 0 si tout est conforme, 1 sinon

Contrôles :
- format CSV lisible, en-têtes attendus présents, une seule campagne Search en pause,
  budget 20 €/jour, réseau Search uniquement, langue française, 10 pays ciblés,
  stratégie « Maximiser les conversions » ;
- 4 groupes d'annonces, 8 à 15 mots-clés par groupe, chacun en Exact et en Phrase,
  aucun doublon ;
- une annonce responsive par groupe avec 15 titres ≤ 30 caractères et 4 descriptions
  ≤ 90 caractères, chemins ≤ 15 caractères, URL finale avec paramètres UTM ;
- règles éditoriales Google Ads : pas de point d'exclamation dans les titres, au plus
  un point d'exclamation par description, pas de mot entièrement en majuscules hors sigles
  autorisés, pas de promesse interdite (« garanti », « meilleur », « n° 1 »), pas de
  répétition d'un même titre ;
- extensions : 4 liens annexes (texte ≤ 25, descriptions ≤ 35), 4 accroches ≤ 25,
  extraits structurés (valeurs ≤ 25, au moins 3), une extension d'appel ;
- au moins 60 mots-clés négatifs, sans doublon.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAGNE_CSV = HERE / "campagne-google-ads.csv"
NEGATIFS_CSV = HERE / "mots-cles-negatifs.csv"

LIMITES = {"titre": 30, "description": 90, "chemin": 15, "sitelink": 25, "sitelink_desc": 35, "accroche": 25, "extrait": 25}
SIGLES_AUTORISES = {"APA", "EHPAD", "CAF", "ANTS", "MSA", "RC", "TVA", "FR", "€"}
MOTS_INTERDITS = ("garanti", "garantie", "meilleur", "n° 1", "n°1", "numéro 1", "100 %", "gratuit")
PAYS_ATTENDUS = {"Israel", "Switzerland", "Belgium", "Luxembourg", "United Kingdom", "United States", "Canada", "United Arab Emirates", "Singapore", "Hong Kong"}


def lire(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def mots_en_majuscules(texte: str) -> list[str]:
    return [m for m in re.findall(r"\b[A-ZÀ-Ý]{2,}\b", texte) if m not in SIGLES_AUTORISES]


def controler_texte(label: str, texte: str, limite: int, erreurs: list[str], est_titre: bool = False) -> None:
    if not texte:
        erreurs.append(f"{label} : vide")
        return
    if len(texte) > limite:
        erreurs.append(f"{label} : {len(texte)} caractères > {limite} : « {texte} »")
    if est_titre and "!" in texte:
        erreurs.append(f"{label} : point d'exclamation interdit dans un titre : « {texte} »")
    if not est_titre and texte.count("!") > 1:
        erreurs.append(f"{label} : plus d'un point d'exclamation : « {texte} »")
    maj = mots_en_majuscules(texte)
    if maj:
        erreurs.append(f"{label} : majuscules abusives {maj} : « {texte} »")
    for mot in MOTS_INTERDITS:
        if mot in texte.lower():
            erreurs.append(f"{label} : promesse ou terme à éviter « {mot} » : « {texte} »")
    if texte != texte.strip() or "  " in texte:
        erreurs.append(f"{label} : espaces superflus : « {texte} »")


def controler_campagne(erreurs: list[str]) -> dict[str, int]:
    stats: dict[str, int] = defaultdict(int)
    if not CAMPAGNE_CSV.exists():
        erreurs.append(f"{CAMPAGNE_CSV.name} absent")
        return stats
    entetes, rows = lire(CAMPAGNE_CSV)
    attendus = ["Campaign", "Campaign Type", "Campaign Status", "Budget", "Networks", "Languages", "Location", "Bid Strategy Type",
                "Ad Group", "Keyword", "Criterion Type", "Ad type", "Final URL", "Path 1", "Path 2",
                "Sitelink text", "Sitelink final URL", "Callout text", "Structured snippet header", "Structured snippet values", "Phone number", "Country code"]
    attendus += [f"Headline {i}" for i in range(1, 16)] + [f"Description {i}" for i in range(1, 5)]
    for col in attendus:
        if col not in entetes:
            erreurs.append(f"colonne manquante : {col}")
    if erreurs:
        return stats

    campagnes = [r for r in rows if r["Campaign Type"]]
    stats["campagnes"] = len(campagnes)
    if len(campagnes) != 1:
        erreurs.append(f"{len(campagnes)} lignes de campagne, 1 attendue")
    else:
        c = campagnes[0]
        if c["Campaign Type"] != "Search":
            erreurs.append("type de campagne différent de Search")
        if c["Campaign Status"] != "Paused":
            erreurs.append("la campagne doit être importée en pause")
        if c["Budget"] != "20":
            erreurs.append(f"budget {c['Budget']} au lieu de 20")
        if c["Networks"] != "Google search":
            erreurs.append("réseau différent de « Google search » (Search uniquement)")
        if c["Languages"] != "French":
            erreurs.append("langue différente de French")
        pays = set(c["Location"].split(";"))
        if pays != PAYS_ATTENDUS:
            erreurs.append(f"pays ciblés incorrects : {sorted(pays ^ PAYS_ATTENDUS)}")
        if c["Bid Strategy Type"] != "Maximize conversions":
            erreurs.append("stratégie d'enchères différente de « Maximize conversions »")

    groupes = [r["Ad Group"] for r in rows if r["Ad Group Type"]]
    stats["groupes"] = len(groupes)
    if len(groupes) != 4:
        erreurs.append(f"{len(groupes)} groupes d'annonces, 4 attendus")

    mots: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["Keyword"] and r["Ad Group"]:
            if r["Criterion Type"] not in ("Exact", "Phrase"):
                erreurs.append(f"type de mot-clé inattendu « {r['Criterion Type']} » pour « {r['Keyword']} »")
            if r["Keyword"] in mots[r["Ad Group"]][r["Criterion Type"]]:
                erreurs.append(f"mot-clé en double : {r['Ad Group']} / {r['Criterion Type']} / « {r['Keyword']} »")
            mots[r["Ad Group"]][r["Criterion Type"]].add(r["Keyword"])
            stats["mots_cles"] += 1
    tous_mots: dict[str, str] = {}
    for g in groupes:
        ex, ph = mots[g]["Exact"], mots[g]["Phrase"]
        if not 8 <= len(ex) <= 15:
            erreurs.append(f"groupe « {g} » : {len(ex)} mots-clés exacts, entre 8 et 15 attendus")
        if ex != ph:
            erreurs.append(f"groupe « {g} » : les listes Exact et Phrase diffèrent")
        for kw in ex:
            if kw in tous_mots and tous_mots[kw] != g:
                erreurs.append(f"mot-clé « {kw} » présent dans deux groupes ({tous_mots[kw]}, {g})")
            tous_mots[kw] = g

    annonces = [r for r in rows if r["Ad type"]]
    stats["annonces"] = len(annonces)
    if len(annonces) != len(groupes):
        erreurs.append(f"{len(annonces)} annonces pour {len(groupes)} groupes")
    for a in annonces:
        g = a["Ad Group"]
        if a["Ad type"] != "Responsive search ad":
            erreurs.append(f"groupe « {g} » : type d'annonce {a['Ad type']}")
        titres = [a[f"Headline {i}"] for i in range(1, 16)]
        descs = [a[f"Description {i}"] for i in range(1, 5)]
        if len(set(titres)) != 15:
            erreurs.append(f"groupe « {g} » : titres manquants ou en double")
        for i, t in enumerate(titres, start=1):
            controler_texte(f"{g} / titre {i}", t, LIMITES["titre"], erreurs, est_titre=True)
            stats["titres"] += 1
        for i, d in enumerate(descs, start=1):
            controler_texte(f"{g} / description {i}", d, LIMITES["description"], erreurs)
            stats["descriptions"] += 1
        for p in ("Path 1", "Path 2"):
            if len(a[p]) > LIMITES["chemin"]:
                erreurs.append(f"groupe « {g} » : {p} > 15 caractères")
        if "utm_source=google" not in a["Final URL"] or "utm_medium=cpc" not in a["Final URL"] or "utm_campaign=" not in a["Final URL"]:
            erreurs.append(f"groupe « {g} » : paramètres UTM incomplets dans l'URL finale")

    sitelinks = [r for r in rows if r["Sitelink text"]]
    stats["liens_annexes"] = len(sitelinks)
    if len(sitelinks) != 4:
        erreurs.append(f"{len(sitelinks)} liens annexes, 4 attendus")
    for s in sitelinks:
        controler_texte(f"lien annexe « {s['Sitelink text']} »", s["Sitelink text"], LIMITES["sitelink"], erreurs)
        for k in ("Sitelink description 1", "Sitelink description 2"):
            controler_texte(f"lien annexe « {s['Sitelink text']} » / {k}", s[k], LIMITES["sitelink_desc"], erreurs)
        if "utm_" not in s["Sitelink final URL"]:
            erreurs.append(f"lien annexe « {s['Sitelink text']} » : URL sans UTM")

    accroches = [r["Callout text"] for r in rows if r["Callout text"]]
    stats["accroches"] = len(accroches)
    if len(accroches) != 4:
        erreurs.append(f"{len(accroches)} accroches, 4 attendues")
    for a in accroches:
        controler_texte(f"accroche « {a} »", a, LIMITES["accroche"], erreurs)

    extraits = [r for r in rows if r["Structured snippet header"]]
    stats["extraits"] = len(extraits)
    if len(extraits) < 1:
        erreurs.append("aucun extrait structuré")
    for e in extraits:
        valeurs = e["Structured snippet values"].split(";")
        if len(valeurs) < 3:
            erreurs.append("extrait structuré : au moins 3 valeurs attendues")
        for v in valeurs:
            controler_texte(f"extrait « {v} »", v, LIMITES["extrait"], erreurs)

    appels = [r for r in rows if r["Phone number"]]
    stats["appels"] = len(appels)
    if len(appels) != 1 or appels[0]["Country code"] != "FR":
        erreurs.append("extension d'appel absente ou indicatif pays différent de FR")
    return stats


def controler_negatifs(erreurs: list[str]) -> int:
    if not NEGATIFS_CSV.exists():
        erreurs.append(f"{NEGATIFS_CSV.name} absent")
        return 0
    entetes, rows = lire(NEGATIFS_CSV)
    for col in ("Campaign", "Keyword", "Criterion Type"):
        if col not in entetes:
            erreurs.append(f"{NEGATIFS_CSV.name} : colonne manquante {col}")
    mots = [r["Keyword"] for r in rows]
    if len(mots) < 60:
        erreurs.append(f"{len(mots)} mots-clés négatifs, au moins 60 attendus")
    if len(set(mots)) != len(mots):
        doublons = sorted({m for m in mots if mots.count(m) > 1})
        erreurs.append(f"mots-clés négatifs en double : {doublons}")
    for r in rows:
        if r["Criterion Type"] not in ("Negative Phrase", "Negative Exact", "Negative Broad"):
            erreurs.append(f"type négatif inattendu : {r['Criterion Type']}")
        if not r["Keyword"].strip():
            erreurs.append("mot-clé négatif vide")
    return len(mots)


def main() -> int:
    erreurs: list[str] = []
    stats = controler_campagne(erreurs)
    n_neg = controler_negatifs(erreurs)
    for e in erreurs:
        print("✘", e)
    resume = ", ".join(f"{k} : {v}" for k, v in stats.items())
    print(f"Résumé — {resume}, mots-clés négatifs : {n_neg}")
    if erreurs:
        print(f"{len(erreurs)} anomalie(s).")
        return 1
    print("✔ Fichiers Google Ads conformes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
