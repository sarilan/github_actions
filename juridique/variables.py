"""Substitution des variables {{VARIABLE}} dans les sources Markdown et HTML.

Syntaxe (inspirée de Mustache, sans imbrication d'un même nom) :

    {{VARIABLE}}                     remplacé par la valeur
    {{#VARIABLE}} … {{/VARIABLE}}    conservé seulement si la valeur est renseignée
    {{^VARIABLE}} … {{/VARIABLE}}    conservé seulement si la valeur est vide

Deux modes :

- ``values=None`` (mode modèle, utilisé pour les documents Word à faire relire) :
  les blocs {{#…}} sont conservés, les blocs {{^…}} supprimés et les {{VARIABLE}}
  restent visibles, ce qui produit le modèle complet avec ses champs à remplir ;
- ``values`` fourni (mode publication, utilisé pour le site) : tout est résolu ;
  une variable absente ou vide hors bloc conditionnel lève ``VariablesManquantes``.
"""
from __future__ import annotations

import re
from typing import Callable, Mapping, Optional

_BLOC = re.compile(r"\{\{([#^])([A-Z0-9_]+)\}\}(.*?)\{\{/\2\}\}", re.DOTALL)
_VAR = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


class VariablesManquantes(ValueError):
    """Levée quand des variables obligatoires ne sont pas renseignées."""

    def __init__(self, noms: list[str]):
        self.noms = sorted(set(noms))
        super().__init__("variables non renseignées : " + ", ".join(self.noms))


def _renseignee(values: Mapping[str, object], nom: str) -> bool:
    valeur = values.get(nom)
    return valeur is not None and str(valeur).strip() != ""


def render(
    texte: str,
    values: Optional[Mapping[str, object]] = None,
    echapper: Optional[Callable[[str], str]] = None,
) -> str:
    """Résout les blocs conditionnels puis les variables (voir le docstring du module)."""

    def bloc(m: re.Match) -> str:
        signe, nom, contenu = m.group(1), m.group(2), m.group(3)
        if values is None:
            present = True
        else:
            present = _renseignee(values, nom)
        garder = present if signe == "#" else not present
        return contenu if garder else ""

    # Les blocs peuvent contenir d'autres blocs portant un nom différent :
    # on répète jusqu'à stabilité.
    precedent = None
    while precedent != texte:
        precedent = texte
        texte = _BLOC.sub(bloc, texte)

    if values is None:
        return texte

    manquantes: list[str] = []

    def variable(m: re.Match) -> str:
        nom = m.group(1)
        if not _renseignee(values, nom):
            manquantes.append(nom)
            return m.group(0)
        valeur = str(values[nom]).strip()
        return echapper(valeur) if echapper else valeur

    texte = _VAR.sub(variable, texte)
    if manquantes:
        raise VariablesManquantes(manquantes)
    return texte


def variables_utilisees(texte: str) -> set[str]:
    """Noms de toutes les variables et de tous les blocs présents dans un texte."""
    noms = set(_VAR.findall(texte))
    noms.update(m.group(2) for m in _BLOC.finditer(texte))
    return noms
