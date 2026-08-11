"""Shared helpers for the logo asset tools."""
import base64
import io
import os
import re

import cairosvg
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIN = os.path.join(REPO, "login")
ICONS = os.path.join(REPO, "square-icons")

DARK_BG = (17, 24, 39)      # tailwind gray-900, the dark login surface
LIGHT_BG = (255, 255, 255)

VIEWBOX_RE = re.compile(r'viewBox="\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)\s*"')


def render(path, width=400):
    """Rasterize an SVG (or open a bitmap) as RGBA."""
    if path.lower().endswith(".svg"):
        return Image.open(io.BytesIO(cairosvg.svg2png(url=path, output_width=width))).convert("RGBA")
    im = Image.open(path)
    if getattr(im, "n_frames", 1) > 1:
        im.seek(im.n_frames - 1)   # .ico: last frame is the largest
    return im.convert("RGBA")


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    return 0.2126 * _lin(rgb[0]) + 0.7152 * _lin(rgb[1]) + 0.0722 * _lin(rgb[2])


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ink_lost(im, bg, threshold=1.6):
    """Share of opaque pixels that vanish against bg.

    Over-reports for marks that enclose white inside a coloured shape (a white
    letter inside a blue tile counts as lost); always eyeball a flagged asset.
    """
    ink = [p for p in im.getdata() if p[3] > 128]
    if not ink:
        return None
    lost = sum(1 for p in ink if contrast(p[:3], bg) < threshold)
    return 100.0 * lost / len(ink)


def coverage(im):
    ink = sum(1 for p in im.getdata() if p[3] > 128)
    return 100.0 * ink / (im.size[0] * im.size[1])


def corners_opaque(im):
    """4 means a full-bleed background plate; 0 means a bare transparent mark."""
    w, h = im.size
    pts = [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]
    return sum(1 for p in pts if im.getpixel(p)[3] > 128)


def svg_head(text):
    m = re.search(r"<svg\b[^>]*>", text)
    return m.group(0) if m else ""


def wrap_raster(path, max_width=512):
    """Embed a bitmap in an SVG shell, downscaled. Matches the repo's existing convention."""
    im = Image.open(path)
    if getattr(im, "n_frames", 1) > 1:
        im.seek(im.n_frames - 1)
    im = im.convert("RGBA")
    if max(im.size) > max_width:
        r = max_width / max(im.size)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    w, h = im.size
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" fill="none">'
            f'<image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64}"/></svg>\n')


def svg_files(directory, include_dark=True):
    out = []
    for f in sorted(os.listdir(directory)):
        if not f.endswith(".svg"):
            continue
        if not include_dark and f.endswith(".dark.svg"):
            continue
        out.append(f)
    return out


def pairs(directory):
    """(slug, light_path, dark_path_or_None) for every base asset in a directory."""
    for f in svg_files(directory, include_dark=False):
        slug = f[:-4]
        dark = os.path.join(directory, f"{slug}.dark.svg")
        yield slug, os.path.join(directory, f), (dark if os.path.exists(dark) else None)
