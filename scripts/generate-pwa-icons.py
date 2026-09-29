"""Create launcher icons with the complete DHL name inside the maskable safe area."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
YELLOW = "#ffcc00"
RED = "#d40511"
DESIGN_SIZE = 512
PANEL = (88, 161, 424, 351)
BARS = (177, 335)
FONT_PATHS = (
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ROOT / "BarlowCondensed-ExtraBold.ttf",
)


def font_path():
    for path in FONT_PATHS:
        if path.is_file():
            return path
    raise FileNotFoundError("No se encontró una fuente para generar los íconos de DHL")


def make_png(size, path):
    # Render above the requested size so the 192 px icon remains legible.
    render_size = size * 4
    scale = render_size / DESIGN_SIZE
    image = Image.new("RGB", (render_size, render_size), YELLOW)
    draw = ImageDraw.Draw(image)
    draw.rectangle(tuple(round(value * scale) for value in PANEL), fill=RED)
    for y in BARS:
        draw.line(
            (round(100 * scale), round(y * scale), round(412 * scale), round(y * scale)),
            fill=YELLOW,
            width=round(10 * scale),
        )

    font = ImageFont.truetype(str(font_path()), round(112 * scale))
    box = draw.textbbox((0, 0), "DHL", font=font)
    x = (render_size - (box[2] - box[0])) / 2 - box[0]
    y = (render_size - (box[3] - box[1])) / 2 - box[1]
    draw.text((round(x), round(y)), "DHL", font=font, fill="white")
    image.resize((size, size), Image.Resampling.LANCZOS).save(path, optimize=True)


def make_svg(path):
    # The complete artwork fits in the central 80% circle used for maskable icons.
    path.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="{YELLOW}"/>
  <rect x="88" y="161" width="336" height="190" fill="{RED}"/>
  <path d="M100 177h312M100 335h312" stroke="{YELLOW}" stroke-width="10"/>
  <text x="256" y="292" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700" font-size="112" fill="white">DHL</text>
</svg>
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    for icon_size in (192, 512):
        make_png(icon_size, ROOT / f"icon-{icon_size}.png")
    make_svg(ROOT / "icon.svg")
