#!/usr/bin/env python3
"""Audit logo assets for dark-mode readiness, missing viewBoxes, plates and bloat.

    python3 tools/audit_assets.py                 # both directories
    python3 tools/audit_assets.py login           # one directory
    python3 tools/audit_assets.py --size 60       # change the bloat threshold (KB)
"""
import argparse
import os
import sys

from assetlib import (DARK_BG, ICONS, LIGHT_BG, LOGIN, REPO, VIEWBOX_RE, corners_opaque,
                      coverage, ink_lost, pairs, render, svg_head)

LOST_LIMIT = 8.0     # % of ink that may vanish before we call it a failure


def audit(directory, size_kb):
    name = os.path.basename(directory)
    print(f"\n{'=' * 92}\n{name}\n{'=' * 92}")
    print(f"{'asset':<24} {'ink%':<6} {'lost/light':<11} {'lost/dark':<10} {'plate':<6} {'viewBox':<8} {'KB':<6} flags")
    print("-" * 92)

    problems = {"no_viewbox": [], "dark_fail": [], "light_fail": [], "bloat": [], "no_dark": []}
    for slug, light, dark in pairs(directory):
        text = open(light, errors="replace").read()
        has_vb = bool(VIEWBOX_RE.search(svg_head(text)))
        kb = os.path.getsize(light) / 1024

        try:
            lim = render(light, 220)
        except Exception as e:
            print(f"{slug:<24} RENDER FAIL: {e}")
            continue
        cov = coverage(lim)
        if cov == 0:
            print(f"{slug:<24} (empty placeholder)")
            continue

        ll = ink_lost(lim, LIGHT_BG)
        plate = corners_opaque(lim) >= 3
        if dark:
            dl = ink_lost(render(dark, 220), DARK_BG)
        else:
            dl = ink_lost(lim, DARK_BG)

        flags = []
        if not has_vb:
            flags.append("NO-viewBox")
            problems["no_viewbox"].append(slug)
        if not dark:
            flags.append("no-dark")
            problems["no_dark"].append(slug)
        if dl is not None and dl > LOST_LIMIT:
            flags.append("DARK-FAIL")
            problems["dark_fail"].append(slug)
        if ll is not None and ll > LOST_LIMIT:
            flags.append("light-check")
            problems["light_fail"].append(slug)
        if kb > size_kb:
            flags.append(f"{kb:.0f}KB")
            problems["bloat"].append(slug)

        print(f"{slug:<24} {cov:<6.0f} {ll:<11.1f} {dl if dl is not None else -1:<10.1f} "
              f"{'yes' if plate else '-':<6} {'yes' if has_vb else 'NO':<8} {kb:<6.0f} {' '.join(flags)}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*", default=None)
    ap.add_argument("--size", type=float, default=60, help="bloat threshold in KB")
    args = ap.parse_args()

    targets = [os.path.join(REPO, d) for d in args.dirs] if args.dirs else [LOGIN, ICONS]
    summary = {}
    for d in targets:
        if not os.path.isdir(d):
            sys.exit(f"not a directory: {d}")
        summary[os.path.basename(d)] = audit(d, args.size)

    print(f"\n{'=' * 92}\nSUMMARY\n{'=' * 92}")
    for name, p in summary.items():
        for key, label in [("no_viewbox", "missing viewBox"), ("no_dark", "no -dark.svg"),
                           ("dark_fail", "unreadable on dark"), ("light_fail", "check on light"),
                           ("bloat", "oversized")]:
            if p[key]:
                print(f"  {name}/{label:<20} {', '.join(p[key])}")
    print("\nNote: 'check on light' over-reports marks that enclose white inside a coloured\n"
          "shape (e.g. white letters in a blue tile). Look at those before acting.")


if __name__ == "__main__":
    main()
