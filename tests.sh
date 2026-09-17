#!/usr/bin/env bash
# Lance l'ensemble des contrôles du dépôt Relais.
set -euo pipefail
cd "$(dirname "$0")"

echo "== Juridique =="
python3 juridique/generate.py --check
python3 juridique/registre.py

echo "== Google Ads =="
python3 ads/check.py

echo "== Fiche de poste =="
python3 rh/generate.py

echo "== Tests Python =="
python3 -m pytest outils/airtable/tests outils/rapport/tests -q
(cd outils/courrier && python3 -m pytest tests -q --cov=classify --cov-report=term --cov-fail-under=85)

echo "== Placeholders =="
if grep -rnE "TODO|FIXME|lorem ipsum|à compléter\b" --include="*.md" --include="*.html" --include="*.csv" --include="*.json" --include="*.yaml" . | grep -v "^./README.md" ; then
  echo "✘ placeholders non balisés trouvés" ; exit 1
fi
echo "✔ aucun placeholder non balisé"
