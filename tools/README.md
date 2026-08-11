# Logo asset tools

Utilities for keeping tenant logos correct in both light and dark mode.

## Setup

```sh
python3 -m venv tools/venv
tools/venv/bin/pip install -r tools/requirements.txt
```

Run everything from the repo root with `tools/venv/bin/python`.

## Layout

Each tenant has up to four files:

```
login/<slug>.svg              wordmark, dark ink   -> light UI
login/<slug>.dark.svg         wordmark, light ink  -> dark UI
square-icons/<slug>.svg       symbol,   dark ink   -> light UI
square-icons/<slug>.dark.svg  symbol,   light ink  -> dark UI
```

Icons are bare transparent symbols. A few brands legitimately keep a coloured
container because their mark is defined that way — Amex (white type knocked out
of a blue box), Grubhub (the guide requires the GH monogram be framed), bol
(their own app icon is a circle). Don't "fix" those.

Do **not** put `@media (prefers-color-scheme: dark)` inside an SVG. It follows
the OS setting, not the app's theme toggle, so it fights the `.dark.svg` files
and can render a logo invisible. `strip` below removes them.

## Commands

```sh
# health check: contrast on both themes, missing viewBox, plates, bloat
tools/venv/bin/python tools/audit_assets.py
tools/venv/bin/python tools/audit_assets.py square-icons --size 40

# add a missing viewBox (an SVG without one cannot scale)
tools/venv/bin/python tools/fix_viewbox.py add
tools/venv/bin/python tools/fix_viewbox.py add --write

# shrink a viewBox to the artwork, for a mark extracted from a lockup
tools/venv/bin/python tools/fix_viewbox.py tighten in.svg out.svg

# PNG of every asset on white and on gray-900
tools/venv/bin/python tools/contact_sheet.py

# rebuild brand-sheet.html
tools/venv/bin/python tools/gen_brand_sheet.py
```

## Adding a tenant

1. Get the official reversed/white mark from the brand's own site — their dark
   footer or favicon is usually a better source than a press kit.
2. Drop in `<slug>.svg` and `<slug>.dark.svg`; wrap rasters with
   `assetlib.wrap_raster()`, which downscales to 512px.
3. `audit_assets.py`, then `contact_sheet.py` and actually look at it.
4. `gen_brand_sheet.py`.

## Caveat on the contrast metric

`audit_assets.py` reports the share of opaque pixels with contrast < 1.6:1
against each surface. It over-reports marks that enclose white inside a coloured
shape — white letters in a blue tile count as "lost" even though they read fine.
Treat `light-check` as *look at this*, not as a failure. `DARK-FAIL` is reliable.
