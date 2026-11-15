"""Genera el set de favicons e iconos de FOBANDOR desde instructions/logo-fobandor.jpg."""
import json
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "instructions" / "logo-fobandor.jpg"
OUT_DIR = BASE_DIR / "static" / "images" / "favicons"


def fit_logo(size: int, background: str | None = None) -> Image.Image:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo.thumbnail((size, size), Image.LANCZOS)
    if background:
        canvas = Image.new("RGBA", (size, size), background)
    else:
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - logo.width) // 2
    y = (size - logo.height) // 2
    canvas.paste(logo, (x, y), logo)
    return canvas


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sizes = [16, 32, 48]
    ico_images = [fit_logo(s).convert("RGB") for s in sizes]
    ico_images[0].save(
        OUT_DIR / "favicon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
    )

    fit_logo(16).save(OUT_DIR / "favicon-16x16.png", format="PNG")
    fit_logo(32).save(OUT_DIR / "favicon-32x32.png", format="PNG")

    apple = fit_logo(180, background="#0D1117")
    apple.save(OUT_DIR / "apple-touch-icon.png", format="PNG")

    manifest = {
        "name": "FOBANDOR",
        "short_name": "FOBANDOR",
        "description": "BUILD. ADVERTISE. ENTERTAIN. WITH AI.",
        "icons": [
            {"src": "/static/images/favicons/favicon-16x16.png", "sizes": "16x16", "type": "image/png"},
            {"src": "/static/images/favicons/favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/static/images/favicons/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
        ],
        "theme_color": "#0D1117",
        "background_color": "#0D1117",
        "display": "standalone",
    }
    (OUT_DIR / "site.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Favicons generados en", OUT_DIR)


if __name__ == "__main__":
    main()
