import re
from pathlib import Path

import pytest

import build

SITE = Path(__file__).resolve().parents[1]


def construire(config, tmp_path, **kw):
    sortie = tmp_path / "dist"
    manquantes = build.construire(config, sortie, **kw)
    return sortie, manquantes


def lire(sortie, nom):
    return (sortie / nom).read_text(encoding="utf-8")


def test_config_du_depot_bloque_la_publication_tant_que_l_identite_manque(tmp_path):
    sortie, manquantes = construire(SITE / "config.json", tmp_path)
    toutes = set().union(*manquantes.values())
    assert {"CONTACT_EMAIL", "MANDATAIRE_ADRESSE", "MANDATAIRE_CAPITAL",
            "MANDATAIRE_VILLE_RCS", "MANDATAIRE_REPRESENTANT"} <= toutes
    assert not sortie.exists(), "rien ne doit être écrit quand une valeur obligatoire manque"


def test_apercu_construit_malgre_les_manques_et_n_est_pas_indexable(tmp_path):
    sortie, manquantes = construire(SITE / "config.json", tmp_path, apercu=True)
    assert manquantes
    accueil = lire(sortie, "index.html")
    assert 'class="manquant"' in accueil and "noindex" in accueil
    assert "Disallow: /" in lire(sortie, "robots.txt")


def test_build_complet(config_complete, tmp_path):
    sortie, manquantes = construire(config_complete(), tmp_path)
    assert manquantes == {}
    for nom in ("index.html", "cgv/index.html", "confidentialite/index.html", "mandat/index.html",
                "mentions-legales/index.html", "404.html", "robots.txt", "sitemap.xml", "_headers", "og-image.png"):
        assert (sortie / nom).exists(), nom
    for page in sortie.rglob("*.html"):
        contenu = page.read_text(encoding="utf-8")
        assert "{{" not in contenu, page
        assert "valider par un avocat" not in contenu, page
    assert "Sitemap: https://relais-parents.pages.dev/sitemap.xml" in lire(sortie, "robots.txt")
    assert lire(sortie, "sitemap.xml").count("<loc>") == 5


@pytest.mark.parametrize("page,attendus", [("cgv", 18), ("confidentialite", 12), ("mandat", 14)])
def test_numerotation_des_articles_identique_aux_documents_word(config_complete, tmp_path, page, attendus):
    sortie, _ = construire(config_complete(), tmp_path)
    numeros = [int(n) for n in re.findall(r'<h2 id="article-(\d+)">', lire(sortie, f"{page}/index.html"))]
    assert numeros == list(range(1, attendus + 1))


def test_mandat_contient_signatures_et_liste_des_organismes(config_complete, tmp_path):
    sortie, _ = construire(config_complete(), tmp_path)
    mandat = lire(sortie, "mandat/index.html")
    assert "Bon pour mandat" in mandat and "Représenté par : Camille Exemple" in mandat
    assert mandat.count('<td class="case"') == len(build.ORGANISMES_CHECKLIST)
    assert "☐ Je consens au traitement de mes données de santé" in mandat


def test_sans_formspree_le_formulaire_passe_par_la_messagerie(config_complete, tmp_path):
    sortie, _ = construire(config_complete(), tmp_path)
    accueil = lire(sortie, "index.html")
    assert 'action="mailto:contact@exemple.fr"' in accueil and 'data-envoi="courriel"' in accueil
    assert "Formspree" not in lire(sortie, "confidentialite/index.html")
    assert "formspree.io" not in lire(sortie, "_headers")
    assert "tel:" not in accueil and '"telephone"' not in accueil


def test_avec_formspree_et_telephone(config_complete, tmp_path):
    cfg = config_complete(FORMSPREE_ENDPOINT="https://formspree.io/f/abcd1234", FORMSPREE_ENTITE="Formspree, Inc.",
                          TELEPHONE_AFFICHE="01 80 00 00 00", TELEPHONE_LIEN="+33180000000")
    sortie, _ = construire(cfg, tmp_path)
    accueil = lire(sortie, "index.html")
    assert 'action="https://formspree.io/f/abcd1234"' in accueil and 'data-envoi="formulaire"' in accueil
    assert 'href="tel:+33180000000"' in accueil and '"telephone": "+33180000000"' in accueil
    assert "Formspree (Formspree, Inc.)" in lire(sortie, "confidentialite/index.html")
    assert "https://formspree.io" in lire(sortie, "_headers")
    assert "01 80 00 00 00" in lire(sortie, "mentions-legales/index.html")


def test_formulations_avant_et_apres_assurance_et_mediateur(config_complete, tmp_path):
    sortie, _ = construire(config_complete(), tmp_path)
    cgv = lire(sortie, "cgv/index.html")
    assert "souscrit, préalablement à l'exécution de toute prestation" in cgv
    assert "Les coordonnées du médiateur auquel le Prestataire adhère" in cgv

    cfg = config_complete(ASSUREUR_RC_PRO="Assureur Exemple", NUMERO_POLICE_RC_PRO="P-123",
                          MEDIATEUR_NOM="Médiateur Exemple", MEDIATEUR_ADRESSE="1 place X, Paris",
                          MEDIATEUR_SITE="https://mediateur.exemple.fr")
    sortie, _ = construire(cfg, tmp_path / "b")
    cgv = lire(sortie, "cgv/index.html")
    assert "auprès de Assureur Exemple, police n° P-123" in cgv
    assert "médiateur de la consommation suivant : Médiateur Exemple" in cgv
    assert "Assureur Exemple" in lire(sortie, "mandat/index.html")


@pytest.mark.parametrize("surcharges,message", [
    ({"SITE_URL": "http://site.fr"}, "SITE_URL"),
    ({"CONTACT_EMAIL": "pas-un-courriel"}, "CONTACT_EMAIL"),
    ({"TELEPHONE_AFFICHE": "01 80 00 00 00"}, "TELEPHONE_LIEN"),
    ({"FORMSPREE_ENDPOINT": "https://formspree.io/f/abcd1234"}, "FORMSPREE_ENTITE"),
    ({"ASSUREUR_RC_PRO": "X"}, "NUMERO_POLICE_RC_PRO"),
    ({"MEDIATEUR_NOM": "X"}, "MEDIATEUR_ADRESSE"),
])
def test_configuration_incoherente_refusee(config_complete, tmp_path, surcharges, message):
    with pytest.raises(build.ErreurBuild, match=message):
        construire(config_complete(**surcharges), tmp_path)


def test_variable_d_environnement_prioritaire(config_complete, tmp_path, monkeypatch):
    monkeypatch.setenv("CONTACT_EMAIL", "autre@exemple.fr")
    sortie, _ = construire(config_complete(), tmp_path)
    assert "autre@exemple.fr" in lire(sortie, "mentions-legales/index.html")


def test_noindex_de_l_adresse_technique_seulement_avec_un_domaine_propre(config_complete, tmp_path):
    sortie, _ = construire(config_complete(), tmp_path)
    assert "X-Robots-Tag" not in lire(sortie, "_headers")
    sortie, _ = construire(config_complete(SITE_URL="https://www.relais-parents.fr"), tmp_path / "b")
    assert "https://:project.pages.dev/*" in lire(sortie, "_headers")


def test_echappement_html_des_valeurs(config_complete, tmp_path):
    sortie, _ = construire(config_complete(MANDATAIRE_ADRESSE="1 rue <X> & Y"), tmp_path)
    mentions = lire(sortie, "mentions-legales/index.html")
    assert "1 rue &lt;X&gt; &amp; Y" in mentions and "<X>" not in mentions
