#!/usr/bin/env python3
"""Regenerate brand-sheet.html at the repo root.

    python3 tools/gen_brand_sheet.py

Run after adding or changing any logo so the sheet stays honest.
"""
import base64
import html
import os

from assetlib import ICONS, LOGIN, REPO

OUT = os.path.join(REPO, "brand-sheet.html")

ART = ('<rect x="6" y="10" width="26" height="22" rx="5" fill="#2563eb"/>'
       '<rect x="40" y="14" width="96" height="7" rx="3.5" fill="#0f172a"/>'
       '<rect x="40" y="26" width="62" height="6" rx="3" fill="#94a3b8"/>')


def uri(s):
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode()).decode()


BROKEN = uri(f'<svg xmlns="http://www.w3.org/2000/svg" width="220" height="42">{ART}</svg>')
FIXED = uri(f'<svg xmlns="http://www.w3.org/2000/svg" width="220" height="42" viewBox="0 0 220 42">{ART}</svg>')


def scan(d):
    base = {f[:-4] for f in os.listdir(d) if f.endswith(".svg") and not f.endswith("-dark.svg")}
    dark = {f[:-9] for f in os.listdir(d) if f.endswith("-dark.svg")}
    return base, dark


def pair_cells(dirname, slug, has_base, has_dark, kind):
    if not has_base:
        return ('<div class="swatch light"><span class="none">&mdash;</span></div>'
                '<div class="swatch dark"><span class="none">&mdash;</span></div>')
    src = f"{dirname}/{slug}-dark.svg" if has_dark else f"{dirname}/{slug}.svg"
    cls = "" if has_dark else " untreated"
    return (f'<div class="swatch light"><img class="{kind}" src="{dirname}/{slug}.svg" alt="{slug} {kind} light"></div>'
            f'<div class="swatch dark{cls}"><img class="{kind}" src="{src}" alt="{slug} {kind} dark"></div>')


def main():
    login_b, login_d = scan(LOGIN)
    icon_b, icon_d = scan(ICONS)
    slugs = sorted(login_b | icon_b)

    cards = []
    for s in slugs:
        lb, ld, ib, idk = s in login_b, s in login_d, s in icon_b, s in icon_d
        stub = os.path.exists(f"{LOGIN}/{s}.svg") and os.path.getsize(f"{LOGIN}/{s}.svg") < 200
        badges = []
        if stub:
            badges.append('<span class="badge stub">placeholder</span>')
        elif lb and not ld:
            badges.append('<span class="badge warn">no login dark</span>')
        if ib and not idk:
            badges.append('<span class="badge note">icon untreated</span>')
        cards.append(f'''    <article class="card">
      <header><h2>{html.escape(s)}</h2>{"".join(badges)}</header>
      <div class="row">
        <div class="cell"><div class="lbl">login</div><div class="pair">{pair_cells("login", s, lb, ld, "wide")}</div></div>
        <div class="cell"><div class="lbl">icon</div><div class="pair">{pair_cells("square-icons", s, ib, idk, "sq")}</div></div>
      </div>
    </article>''')

    missing = sorted((login_b - login_d) | {s for s in icon_b - icon_d})
    page = TEMPLATE.format(
        n=len(slugs), nl=len(login_d), ni=len(icon_d), nmiss=len(missing),
        broken=BROKEN, fixed=FIXED, cards=chr(10).join(cards))
    open(OUT, "w").write(page)
    print(f"{OUT}\n{len(slugs)} tenants | login dark: {len(login_d)} | icon dark: {len(icon_d)}")


TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Moderne customer brand sheet</title>
<style>
  :root {{
    --bg:#f4f5f7; --fg:#14181f; --muted:#616a7a; --line:#dfe3ea; --card:#fff;
    --sw-light:#fff; --sw-dark:#111827; --warn:#b4530a; --warn-bg:#fdf0e3;
    --note:#3b5bb5; --note-bg:#e8eefb; --bad:#b42318; --good:#087443;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#0d1017; --fg:#e8ecf3; --muted:#8d97a8; --line:#242b38; --card:#151a23;
      --warn:#f0a459; --warn-bg:#33240f; --note:#8fb0ef; --note-bg:#1b2740;
      --bad:#f27166; --good:#4ec98a;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:#0d1017; --fg:#e8ecf3; --muted:#8d97a8; --line:#242b38; --card:#151a23;
    --warn:#f0a459; --warn-bg:#33240f; --note:#8fb0ef; --note-bg:#1b2740;
    --bad:#f27166; --good:#4ec98a;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:2rem 1.5rem 4rem; background:var(--bg); color:var(--fg);
         font:15px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  .wrap {{ max-width:1280px; margin:0 auto; }}
  h1 {{ font-size:1.5rem; margin:0 0 .35rem; letter-spacing:-.01em; }}
  .sub {{ color:var(--muted); margin:0 0 1.5rem; font-size:.9rem; max-width:82ch; }}
  code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.85em; }}
  .grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fill,minmax(420px,1fr)); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
  .card header {{ display:flex; align-items:center; gap:.4rem; padding:.6rem .8rem;
                  border-bottom:1px solid var(--line); flex-wrap:wrap; }}
  .card h2 {{ font:500 .82rem/1 ui-monospace,SFMono-Regular,Menlo,monospace; margin:0;
              color:var(--muted); letter-spacing:.02em; margin-right:auto; }}
  .badge {{ font-size:.66rem; padding:.15rem .45rem; border-radius:4px; font-weight:600;
            text-transform:uppercase; letter-spacing:.04em; background:var(--warn-bg); color:var(--warn); }}
  .badge.note {{ background:var(--note-bg); color:var(--note); }}
  .badge.stub {{ background:transparent; color:var(--muted); border:1px solid var(--line); }}
  .row {{ display:grid; grid-template-columns:1fr auto; }}
  .cell + .cell {{ border-left:1px solid var(--line); }}
  .lbl {{ font:600 .62rem/1 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--muted);
          text-transform:uppercase; letter-spacing:.08em; padding:.45rem .7rem .3rem; }}
  .pair {{ display:grid; grid-template-columns:1fr 1fr; }}
  .swatch {{ display:grid; place-items:center; min-height:84px; padding:.9rem; }}
  .swatch.light {{ background:var(--sw-light); }}
  .swatch.dark {{ background:var(--sw-dark); }}
  .swatch.dark.untreated {{ background:repeating-linear-gradient(45deg,#111827,#111827 9px,#171f31 9px,#171f31 18px); }}
  img.wide {{ max-width:100%; max-height:40px; width:auto; height:auto; display:block; }}
  img.sq {{ width:52px; height:52px; display:block; }}
  .cell:last-child .pair {{ min-width:200px; }}
  .none {{ color:#6b7280; font-size:1.1rem; }}

  body[data-view="light"] .swatch.dark, body[data-view="dark"] .swatch.light {{ display:none; }}
  body[data-view="light"] .pair, body[data-view="dark"] .pair {{ grid-template-columns:1fr; }}

  /* Scale stress: force art to fill a box wider than its authored size. An SVG with
     width/height but no viewBox has no user-coordinate mapping and cannot scale. */
  body[data-view="stress"] .swatch {{ place-items:start; min-height:120px; }}
  body[data-view="stress"] img.wide {{ width:100%; height:auto; max-height:none; }}
  body[data-view="stress"] img.sq {{ width:100%; height:auto; }}
  body[data-view="stress"] .explainer {{ display:block; }}
  .explainer {{ display:none; margin-bottom:1.5rem; }}
  .demo {{ display:grid; grid-template-columns:1fr 1fr; }}
  .demo > div {{ padding:1rem; background:#fff; }}
  .demo > div + div {{ border-left:1px solid var(--line); }}
  .demo img {{ width:100%; height:auto; display:block; }}
  .cap {{ font:600 .7rem/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; margin-bottom:.6rem;
          text-transform:uppercase; letter-spacing:.04em; }}
  .cap.bad {{ color:var(--bad); }} .cap.good {{ color:var(--good); }}

  .bar {{ display:flex; gap:.4rem; margin-bottom:1.25rem; flex-wrap:wrap; }}
  .bar button {{ font:inherit; font-size:.82rem; padding:.35rem .8rem; cursor:pointer;
                 background:var(--card); color:var(--fg); border:1px solid var(--line); border-radius:6px; }}
  .bar button[aria-pressed="true"] {{ background:var(--fg); color:var(--bg); border-color:var(--fg); }}
  .key {{ display:flex; gap:1.1rem; flex-wrap:wrap; font-size:.78rem; color:var(--muted); margin-bottom:1.5rem; }}
  .key i {{ display:inline-block; width:11px; height:11px; border-radius:3px; vertical-align:-1px; margin-right:.3rem; }}
</style>
</head>
<body data-view="both">
<div class="wrap">
  <h1>Moderne customer brand sheet</h1>
  <p class="sub">
    {n} tenants &middot; <code>login/</code> wordmarks and <code>square-icons/</code> symbols,
    each on white and on <code>#111827</code>.
    {nl} login logos and {ni} icons ship a <code>-dark.svg</code>; {nmiss} still do not.
    Anything without a dark variant is shown over a hatched swatch &mdash; if it reads cleanly
    there it needs no dark treatment. Regenerate with <code>tools/gen_brand_sheet.py</code>.
  </p>

  <div class="bar">
    <button data-v="both" aria-pressed="true">Side by side</button>
    <button data-v="light" aria-pressed="false">Light only</button>
    <button data-v="dark" aria-pressed="false">Dark only</button>
    <button data-v="stress" aria-pressed="false">Scale stress</button>
  </div>

  <div class="key">
    <span><i style="background:repeating-linear-gradient(45deg,#111827,#111827 5px,#171f31 5px,#171f31 10px)"></i>hatched = no dark variant</span>
    <span><i style="background:var(--warn-bg);border:1px solid var(--warn)"></i>needs a dark login file</span>
    <span><i style="background:var(--note-bg);border:1px solid var(--note)"></i>icon has no dark variant</span>
  </div>

  <section class="explainer">
    <p class="sub">
      Every asset is forced to <code>width: 100%</code> in a box wider than its authored size.
      An SVG that declares <code>width</code>/<code>height</code> but no <code>viewBox</code> has no
      user-coordinate mapping, so it cannot scale &mdash; it paints at intrinsic size anchored top-left.
      Both controls are identical artwork; only the <code>viewBox</code> differs. Any logo that renders
      small and corner-pinned here is missing its <code>viewBox</code>.
    </p>
    <div class="card"><div class="demo">
      <div><div class="cap bad">control &mdash; no viewBox &mdash; cannot scale</div><img src="{broken}" alt="no viewBox"></div>
      <div><div class="cap good">control &mdash; viewBox set &mdash; scales</div><img src="{fixed}" alt="viewBox set"></div>
    </div></div>
  </section>

  <div class="grid">
{cards}
  </div>
</div>
<script>
  const bar = document.querySelector('.bar');
  bar.addEventListener('click', e => {{
    const b = e.target.closest('button');
    if (!b) return;
    document.body.dataset.view = b.dataset.v;
    bar.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b));
  }});
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
