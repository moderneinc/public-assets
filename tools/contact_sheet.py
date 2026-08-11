#!/usr/bin/env python3
"""Render a light/dark contact sheet as PNG for visual review.

Browsers and Finder preview SVGs on white, which hides exactly the problems
dark-mode work creates. This paints each asset on both surfaces.

    python3 tools/contact_sheet.py                      # both dirs -> /tmp
    python3 tools/contact_sheet.py square-icons -o q.png
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

from assetlib import DARK_BG, ICONS, LIGHT_BG, LOGIN, REPO, pairs, render

PANEL = (40, 44, 52)


def font(size=10):
    try:
        return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", size)
    except Exception:
        return ImageFont.load_default()


def build(directory, out, cell=84, cols=2):
    items = [(s, l, d) for s, l, d in pairs(directory)]
    items = [i for i in items if os.path.getsize(i[1]) > 200]   # skip empty placeholders
    pad, lbl = 11, 120
    colw = lbl + pad * 2 + cell * 2 + pad
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (colw * cols, rows * (cell + pad) + pad + 18), PANEL)
    dr = ImageDraw.Draw(sheet)
    f = font()
    for c in range(cols):
        dr.text((c * colw + lbl + pad, 4), "light        dark", fill=(170, 178, 192), font=f)

    for i, (slug, light, dark) in enumerate(items):
        cx, ry = i % cols, i // cols
        ox = cx * colw
        y = 18 + pad + ry * (cell + pad)
        dr.text((ox + pad, y + cell // 2 - 9), slug[:16], fill=(200, 205, 215), font=f)
        if not dark:
            dr.text((ox + pad, y + cell // 2 + 3), "no dark", fill=(190, 130, 80), font=f)
        for col, (path, bg) in enumerate([(light, LIGHT_BG), (dark or light, DARK_BG)]):
            x = ox + lbl + pad + col * (cell + pad)
            dr.rectangle([x, y, x + cell, y + cell], fill=bg)
            try:
                im = render(path, (cell - 16) * 3)
                im.thumbnail((cell - 16, cell - 16), Image.LANCZOS)
                sheet.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2), im)
            except Exception:
                dr.text((x + 4, y + cell // 2 - 5), "fail", fill=(200, 90, 90), font=f)

    sheet.save(out)
    print(f"{len(items)} pairs -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--cell", type=int, default=84)
    args = ap.parse_args()

    targets = [os.path.join(REPO, d) for d in args.dirs] if args.dirs else [LOGIN, ICONS]
    for d in targets:
        out = args.out or f"/tmp/contact-{os.path.basename(d)}.png"
        build(d, out, args.cell)


if __name__ == "__main__":
    main()
