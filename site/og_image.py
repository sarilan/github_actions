#!/usr/bin/env python3
"""Génère l'image de partage (Open Graph) du site : site/static/og-image.png, 1200 × 630.

Usage : python3 site/og_image.py   (nécessite Pillow ; l'image produite est versionnée,
le build du site n'a donc pas besoin de Pillow).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SORTIE = Path(__file__).resolve().parent / "static" / "og-image.png"
POLICES = Path("/usr/share/fonts/truetype/dejavu")
BLEU, BLEU_FONCE, OCRE, BLANC, DOUX = "#1f3a5f", "#142640", "#d98a2b", "#ffffff", "#c9d5e4"


def police(nom: str, taille: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(POLICES / nom), taille)


def main() -> None:
    img = Image.new("RGB", (1200, 630), BLEU)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 560, 1200, 630], fill=BLEU_FONCE)
    # Logo : carré arrondi avec un R
    d.rounded_rectangle([80, 80, 176, 176], radius=22, fill=BLANC)
    d.text((128, 128), "R", font=police("DejaVuSerif-Bold.ttf", 64), fill=BLEU, anchor="mm")
    d.text((200, 128), "Relais", font=police("DejaVuSerif-Bold.ttf", 60), fill=BLANC, anchor="lm")
    titre = police("DejaVuSerif-Bold.ttf", 54)
    d.text((80, 250), "Vos parents en France,", font=titre, fill=BLANC)
    d.text((80, 318), "leur administratif entre", font=titre, fill=BLANC)
    d.text((80, 386), "de bonnes mains.", font=titre, fill=BLANC)
    d.rectangle([80, 474, 200, 480], fill=OCRE)
    d.text((80, 500), "Mandat écrit · traitement sous 48 h · rapport mensuel",
           font=police("DejaVuSans.ttf", 30), fill=DOUX)
    d.text((80, 595), "Pour les enfants expatriés de parents restés en France",
           font=police("DejaVuSans.ttf", 26), fill=DOUX, anchor="lm")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    img.save(SORTIE, optimize=True)
    print(f"✔ {SORTIE.relative_to(Path.cwd()) if SORTIE.is_relative_to(Path.cwd()) else SORTIE}")


if __name__ == "__main__":
    main()
