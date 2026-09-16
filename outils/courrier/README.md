# Classification automatique du courrier

`classify.py` lit un courrier scanné (PDF ou image) ou son texte, reconnaît l'organisme expéditeur et le type de document, extrait les dates limites, les montants et les références, calcule un niveau d'urgence de 1 à 4 et renvoie un JSON. Avec `--airtable`, il crée directement le courrier et la démarche dans la base « Relais — Gestion ».

C'est une aide au tri : chaque résultat est vérifié par un opérateur avant action (voir la politique de confidentialité, aucune décision automatisée).

## Installation

```bash
pip install -r requirements.txt            # pytesseract, Pillow, pypdf, pdf2image, PyYAML…
# Moteur OCR et langue française :
sudo apt install tesseract-ocr tesseract-ocr-fra poppler-utils   # Debian / Ubuntu
brew install tesseract tesseract-lang poppler                     # macOS
```

Sous Windows, installer Tesseract depuis https://github.com/UB-Mannheim/tesseract/wiki (cocher la langue « French ») et poppler (https://github.com/oschwartz10612/poppler-windows), puis les ajouter au PATH.

Si Tesseract est absent, le script s'arrête avec un message explicite (code de retour 2) ; les fichiers `.txt` restent utilisables.

## Usage

```bash
python3 outils/courrier/classify.py courrier.pdf --pretty
python3 outils/courrier/classify.py photo-whatsapp.jpg --reference-date 2026-09-16
python3 outils/courrier/classify.py lettre.txt
python3 outils/courrier/classify.py courrier.pdf --airtable --client "Durand — Sarcelles"
```

| Option | Rôle |
|---|---|
| `--reference-date AAAA-MM-JJ` | Date de réception (défaut : aujourd'hui). Sert au calcul des jours restants et des délais relatifs (« sous 30 jours ») quand la date du courrier n'est pas trouvée. |
| `--lang` | Langue Tesseract (défaut `fra`). |
| `--rules` | Autre fichier de règles (défaut `rules.yaml`). |
| `--pretty` | JSON indenté. |
| `--airtable` | Crée le Courrier et la Démarche dans Airtable. Nécessite `--client` et `AIRTABLE_API_KEY` (fichier `.env`). |
| `--client` | Valeur du champ « Dossier » de la table Clients. |
| `--base` | Identifiant de la base (sinon `AIRTABLE_BASE_ID` ou `outils/airtable/.base_id`). |

Codes de retour : 0 succès, 1 erreur d'entrée, 2 OCR indisponible, 3 erreur Airtable.

### Exemple de sortie

```json
{
  "fichier": "02-edf-facture.txt",
  "organisme": {"id": "edf", "nom": "EDF", "categorie": "Énergie", "confiance": 0.89, "critique": false},
  "type": {"nom": "Facture", "confiance": 0.81},
  "date_document": "2026-09-08",
  "dates_limites": [{"texte": "date limite de paiement : le 02/10/2026", "date": "2026-10-02", "jours_restants": 16, "type": "absolue", "categorie": "action"}],
  "date_limite_principale": "2026-10-02",
  "montants": [{"texte": "78,45 €", "valeur": 78.45, "contexte": ""}, {"texte": "486,30 €", "valeur": 486.3, "contexte": "a payer"}],
  "montant_principal": 486.3,
  "references": [{"libelle": "facture n°", "valeur": "2026-8891"}, {"libelle": "n° client", "valeur": "3 456 789 012"}],
  "urgence": {"niveau": 2, "motifs": ["type « Facture » : niveau de base 2"]},
  "resume": "Votre facture d'électricité Facture n° 2026-8891 du 8 septembre 2026 …",
  "ocr": {"moteur": "texte", "langue": "fra", "pages": 1},
  "avertissements": []
}
```

## Fonctionnement

1. **OCR** : PDF avec texte natif → texte extrait par pypdf ; PDF scanné → pages rendues à 300 ppp (pdf2image) puis Tesseract ; image → Tesseract. Le texte est normalisé (minuscules, sans accents).
2. **Organisme** : chaque organisme de `rules.yaml` a des motifs pondérés (nom, adresse, numéro de téléphone, domaine, formulations). Un motif trouvé dans les 15 premières lignes compte double. Les organismes génériques (« Mutuelle (autre) », « Banque (autre) »…) sont pénalisés et ne l'emportent qu'en l'absence d'organisme nommé.
3. **Type** : Mise en demeure, Convocation, Relance, Demande de pièces, Facture, Décision, Information, avec un ordre de priorité en cas d'égalité.
4. **Dates** : absolues (« avant le 15 octobre 2026 », « au plus tard le 03/10/2026 », « jusqu'au 30.09.2026 », « échéance : le 01/11/2026 », « audience du 5 novembre 2026 ») et relatives (« sous 30 jours », « dans un délai de deux mois », « sous 10 jours ouvrés », « dans les 15 jours »), calculées depuis la date du courrier. Chaque délai est classé `action`, `recours` (délai de contestation) ou `information` (remboursement à venir) ; seuls les délais d'action alimentent l'échéance principale et l'urgence.
5. **Montants** : formats français (« 1 234,56 € », « 486.30 EUR », « 96,00 euros ») avec le mot de contexte précédent ; le montant principal privilégie « à payer », « total », « à régler », « versé », « attribué », sinon le plus élevé.
6. **Références** : n° de dossier, de contrat, d'adhérent, d'allocataire, de facture, de sécurité sociale, « votre référence ».
7. **Urgence** (section `urgence` de `rules.yaml`) : niveau de base par type (mise en demeure 4, convocation / relance / demande de pièces 3, facture / décision 2, information 1) ; +1 si une date limite d'action tombe sous 7 jours ; niveau 4 si elle est dépassée ; +1 si le montant dépasse 500 € sur une facture, une relance ou une mise en demeure ; +1 au plus si l'organisme est à enjeu (impôts, recouvrement, justice) ou si le texte mentionne une sanction (suspension, radiation, saisie, coupure, majoration, expulsion) ; une information sans délai reste au niveau 1.

## Ajouter un organisme

1. Dans `rules.yaml`, section `organismes`, copier un bloc existant et renseigner :
   - `id` : identifiant unique en minuscules avec tirets (ex. `credit-cooperatif`) ;
   - `nom`, `categorie` (une des catégories de la table Organismes d'Airtable) ;
   - `critique: true` uniquement pour un organisme dont les courriers appellent une réaction rapide (impôts, recouvrement, justice) ;
   - `motifs` : au moins deux motifs distinctifs, en minuscules sans accents (le texte est normalisé) : nom complet, domaine internet, numéro de téléphone, adresse, formule caractéristique. Poids de 1 (mot courant) à 5 (nom propre sans ambiguïté).
2. Ajouter un courrier d'exemple `tests/corpus/NN-<organisme>-<type>.txt` (texte inventé, aucune donnée réelle) et ses valeurs attendues dans `tests/corpus/attendus.yaml` (organisme, type, date limite principale, montant principal, urgence).
3. Lancer les tests ; ajuster les poids si un organisme générique ou voisin l'emporte.

Pour ajouter un type de document ou un mot-clé de sanction, procéder de même dans les sections `types` et `urgence`.

## Tests

```bash
cd outils/courrier
python3 -m pytest tests -q --cov=classify --cov-report=term-missing
```

Le corpus contient 32 courriers synthétiques couvrant chaque organisme majeur et chaque type ; les tests unitaires couvrent les formats de dates français, les montants, les références, les règles d'urgence, l'OCR (image et PDF rendus à la volée, Tesseract requis, sinon les tests sont ignorés), les messages d'erreur et l'option `--airtable` contre la simulation de l'API (`outils/airtable/mock_api.py`).
