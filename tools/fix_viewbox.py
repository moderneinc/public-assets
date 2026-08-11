#!/usr/bin/env python3
"""viewBox repairs.

An SVG with width/height but no viewBox has no user-coordinate mapping, so it
cannot scale: it paints at intrinsic size anchored top-left inside whatever box
it is given. Every asset here needs one.

    python3 tools/fix_viewbox.py add                      # report what is missing
    python3 tools/fix_viewbox.py add --write              # add viewBox="0 0 w h"
    python3 tools/fix_viewbox.py tighten a.svg b.svg      # shrink viewBox to the ink
"""
import argparse
import os
import re
import sys

from assetlib import ICONS, LIGHT_BG, LOGIN, REPO, VIEWBOX_RE, render, svg_head

NUM = r'([\d.]+)\s*(?:px)?'


def add(directories, write):
    fixed = 0
    for d in directories:
        print(f"=== {os.path.basename(d)} ===")
        for f in sorted(os.listdir(d)):
            if not f.endswith(".svg"):
                continue
            p = os.path.join(d, f)
            text = open(p, errors="replace").read()
            head = svg_head(text)
            if not head or "viewBox" in head:
                continue
            w = re.search(r'\swidth="' + NUM + '"', head)
            h = re.search(r'\sheight="' + NUM + '"', head)
            if not (w and h):
                print(f"  !! no usable width/height: {f}")
                continue
            vb = f'viewBox="0 0 {w.group(1)} {h.group(1)}"'
            new = head[:-1].rstrip() + f" {vb}>"
            print(f"  {f:<28} + {vb}")
            fixed += 1
            if write:
                open(p, "w").write(text.replace(head, new, 1))
    print(f"\n{fixed} file(s) {'updated' if write else 'would change (pass --write)'}")


def tighten(src, dst, pad_frac=0.04, render_w=1400):
    """Shrink the viewBox to the rendered ink bbox. Geometry is untouched.

    Use when a mark was extracted from a lockup and sits in a mostly empty canvas.
    """
    text = open(src, errors="replace").read()
    m = VIEWBOX_RE.search(text)
    if not m:
        sys.exit(f"no viewBox in {src} - run `add` first")
    vx, vy, vw, vh = (float(g) for g in m.groups())

    im = render(src, render_w)
    bb = im.getchannel("A").getbbox()
    if not bb:
        sys.exit(f"no ink in {src}")
    pw, ph = im.size
    nx = vx + (bb[0] / pw) * vw
    ny = vy + (bb[1] / ph) * vh
    nw = ((bb[2] - bb[0]) / pw) * vw
    nh = ((bb[3] - bb[1]) / ph) * vh
    pad = max(nw, nh) * pad_frac
    nx, ny, nw, nh = nx - pad, ny - pad, nw + 2 * pad, nh + 2 * pad

    out = text[:m.start()] + f'viewBox="{nx:.2f} {ny:.2f} {nw:.2f} {nh:.2f}"' + text[m.end():]
    # fixed width/height would fight the new box
    out = re.sub(r'(<svg\b[^>]*?)\s+width="[^"]*"', r"\1", out, count=1)
    out = re.sub(r'(<svg\b[^>]*?)\s+height="[^"]*"', r"\1", out, count=1)
    open(dst, "w").write(out)
    print(f"{os.path.basename(src)}: {vw:.0f}x{vh:.0f} -> {nw:.1f}x{nh:.1f} "
          f"(aspect {nw / nh:.2f}) -> {os.path.basename(dst)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("dirs", nargs="*")
    a.add_argument("--write", action="store_true")
    t = sub.add_parser("tighten")
    t.add_argument("src")
    t.add_argument("dst")
    t.add_argument("--pad", type=float, default=0.04)
    args = ap.parse_args()

    if args.cmd == "add":
        dirs = [os.path.join(REPO, d) for d in args.dirs] if args.dirs else [LOGIN, ICONS]
        add(dirs, args.write)
    else:
        tighten(args.src, args.dst, args.pad)


if __name__ == "__main__":
    main()
