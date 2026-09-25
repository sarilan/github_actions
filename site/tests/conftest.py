import json
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE))
sys.path.insert(0, str(SITE.parent / "juridique"))

# Valeurs fictives, uniquement pour les tests.
VALEURS_TEST = {
    "CONTACT_EMAIL": "contact@exemple.fr",
    "MANDATAIRE_CAPITAL": "1 000",
    "MANDATAIRE_VILLE_RCS": "Paris",
    "MANDATAIRE_ADRESSE": "10 rue de l'Exemple, 75001 Paris",
    "MANDATAIRE_REPRESENTANT": "Camille Exemple",
}


@pytest.fixture
def config_complete(tmp_path):
    """Copie de site/config.json complétée avec des valeurs fictives."""
    def fabrique(**surcharges):
        donnees = json.loads((SITE / "config.json").read_text(encoding="utf-8"))
        donnees.update(VALEURS_TEST)
        donnees.update(surcharges)
        chemin = tmp_path / "config.json"
        chemin.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
        return chemin
    return fabrique
