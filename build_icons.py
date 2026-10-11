#!/usr/bin/env python3
"""build_icons.py -- Offline UI Icons v0.1 generator.

Zero dependencies (Python 3 stdlib only), zero network, deterministic and
path-independent: everything is written relative to this script's own
directory, so the same bytes are produced no matter the current working
directory.

Outputs (all under this directory):

    dist/svg/<name>.svg            32 standalone SVG files
    dist/offline-ui-icons.js       merged data: name -> inner SVG markup
    dist/index.html                self-contained icon gallery
    dist/offline-ui-icons-v0.1.zip release archive
    README.md                      documentation
    LICENSE                        MIT license text

The icon geometry is stored as data in the ICONS table below (each icon is a
list of primitives: 'p <d>' path, 'c <cx> <cy> <r>' circle,
'r <x> <y> <w> <h> <rx>' rect). The renderer only turns that data into SVG
text; there is no hidden state and no clock/time input anywhere, which is what
makes repeated builds byte-identical.
"""

import json
import os
import zipfile

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
SVG_DIR = os.path.join(DIST_DIR, "svg")

VERSION = "0.1"
ICON_COUNT = 32
STROKE_WIDTH = "2"          # uniform, one of {1.75, 2}
VIEWBOX = "0 0 24 24"
SIZE = "24"
SVG_NS = "http://www.w3.org/2000/svg"
DONATION_URL = "https://ko-fi.com/colome"
LICENSE_HOLDER = "Offline UI Icons contributors"

ZIP_NAME = "offline-ui-icons-v%s.zip" % VERSION
ZIP_PATH = os.path.join(DIST_DIR, ZIP_NAME)

# deterministic zip timestamp (year, month, day, hour, min, sec)
ZIP_DATE = (2026, 1, 1, 0, 0, 0)

# --------------------------------------------------------------------------
# Precomputed geometry (literal path data, generated once, inlined as data)
# --------------------------------------------------------------------------

GEAR_D = (
    "M20.28 10.09 L20.28 13.91 L17.67 13.95 L17.39 14.63 L19.21 16.5 "
    "L16.5 19.21 L14.63 17.39 L13.95 17.67 L13.91 20.28 L10.09 20.28 "
    "L10.05 17.67 L9.37 17.39 L7.5 19.21 L4.79 16.5 L6.61 14.63 L6.33 13.95 "
    "L3.72 13.91 L3.72 10.09 L6.33 10.05 L6.61 9.37 L4.79 7.5 L7.5 4.79 "
    "L9.37 6.61 L10.05 6.33 L10.09 3.72 L13.91 3.72 L13.95 6.33 L14.63 6.61 "
    "L16.5 4.79 L19.21 7.5 L17.39 9.37 L17.67 10.05 Z"
)
STAR_D = (
    "M12 3.3 L14.26 9.19 L20.56 9.52 L15.66 13.49 L17.29 19.58 L12 16.15 "
    "L6.71 19.58 L8.34 13.49 L3.44 9.52 L9.74 9.19 Z"
)

# --------------------------------------------------------------------------
# The icon set: name -> list of primitives
# --------------------------------------------------------------------------

ICONS = [
    ("menu", ["p M4 7h16M4 12h16M4 17h16"]),
    ("close", ["p M6 6l12 12M18 6L6 18"]),
    ("search", ["c 11 11 7", "p M16 16l4.5 4.5"]),
    ("settings", ["p " + GEAR_D, "c 12 12 3"]),
    ("user", ["c 12 7 4", "p M20 20v-1a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v1"]),
    ("home", ["p M3 12 12 3l9 9", "p M5 10v10h14V10", "p M9 20v-6h6v6"]),
    ("star", ["p " + STAR_D]),
    ("heart", ["p M19.5 5.5a4.5 4.5 0 0 0-6.36 0L12 6.64l-1.14-1.14a4.5 4.5 0 1 0-6.36 6.36L12 20l7.5-8.14a4.5 4.5 0 0 0 0-6.36z"]),
    ("bell", ["p M18 8a6 6 0 0 0-12 0c0 7-2.5 9-2.5 9h17s-2.5-2-2.5-9", "p M10.3 21a2 2 0 0 0 3.4 0"]),
    ("calendar", ["r 3 4.5 18 16 2", "p M8 2.5v4M16 2.5v4M3 10h18"]),
    ("clock", ["c 12 12 8.5", "p M12 6.5V12l3.5 2.5"]),
    ("mail", ["r 3 5 18 14 2", "p M4 7l8 6 8-6"]),
    ("download", ["p M12 3v11", "p M7 9l5 5 5-5", "p M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"]),
    ("upload", ["p M12 14V3", "p M7 8l5-5 5 5", "p M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"]),
    ("cloud", ["p M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"]),
    ("folder", ["p M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"]),
    ("file", ["p M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z", "p M13 2v7h7"]),
    ("edit", ["p M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7", "p M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"]),
    ("trash", ["p M3 6h18", "p M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2", "p M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6", "p M10 11v6M14 11v6"]),
    ("plus", ["p M12 5v14M5 12h14"]),
    ("minus", ["p M5 12h14"]),
    ("check", ["p M4 12.5l5 5L20 6.5"]),
    ("arrow-right", ["p M4 12h15", "p M14 6l6 6-6 6"]),
    ("arrow-left", ["p M20 12H5", "p M10 6l-6 6 6 6"]),
    ("chevron-down", ["p M6 9l6 6 6-6"]),
    ("chevron-up", ["p M6 15l6-6 6 6"]),
    ("lock", ["r 4 10.5 16 10 2", "p M8 10.5V7a4 4 0 0 1 8 0v3.5"]),
    ("eye", ["p M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z", "c 12 12 3"]),
    ("refresh", ["p M21 4v5h-5", "p M3 20v-5h5", "p M3.7 9a8.6 8.6 0 0 1 14.2-3.3L21 9", "p M20.3 15a8.6 8.6 0 0 1-14.2 3.3L3 15"]),
    ("external-link", ["p M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6", "p M15 3h6v6", "p M10 14 21 3"]),
    ("copy", ["r 9 9 13 13 2", "p M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"]),
    ("info", ["c 12 12 9", "p M12 16.5V11.5M12 8h.01"]),
]

EXPECTED_NAMES = [name for name, _ in ICONS]

# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _num(value):
    """Render a number with the fewest characters, deterministically."""
    if isinstance(value, str):
        value = float(value)
    if float(value).is_integer():
        return str(int(value))
    return ("%.3f" % value).rstrip("0").rstrip(".")


def _primitive_markup(prim):
    parts = prim.split()
    kind = parts[0]
    if kind == "p":
        d = prim[2:]
        return '<path d="%s"/>' % d
    if kind == "c":
        cx, cy, r = parts[1], parts[2], parts[3]
        return '<circle cx="%s" cy="%s" r="%s"/>' % (_num(cx), _num(cy), _num(r))
    if kind == "r":
        x, y, w, h = parts[1], parts[2], parts[3], parts[4]
        rx = parts[5] if len(parts) > 5 else None
        attr = ''
        if rx is not None:
            attr = ' rx="%s"' % _num(rx)
        return '<rect x="%s" y="%s" width="%s" height="%s"%s/>' % (
            _num(x), _num(y), _num(w), _num(h), attr)
    raise ValueError("unknown primitive: %r" % prim)


def icon_markup(name, primitives):
    """Full standalone SVG document text for one icon."""
    children = "".join(_primitive_markup(p) for p in primitives)
    open_tag = (
        '<svg xmlns="%s" width="%s" height="%s" viewBox="%s" fill="none" '
        'stroke="currentColor" stroke-width="%s" stroke-linecap="round" '
        'stroke-linejoin="round" role="img" aria-label="%s">'
        % (SVG_NS, SIZE, SIZE, VIEWBOX, STROKE_WIDTH, name)
    )
    return "%s\n  <title>%s</title>\n  %s\n</svg>\n" % (open_tag, name, children)


def icon_inner(name, primitives):
    """Children-only markup, used by the merged JS data file."""
    return "".join(_primitive_markup(p) for p in primitives)


# --------------------------------------------------------------------------
# Gallery page
# --------------------------------------------------------------------------

_CSS = """\
:root{
  --bg:#f6f7f9; --fg:#16181d; --muted:#646b78; --card:#ffffff;
  --line:#e2e5ea; --accent:#3b6cf6; --edge:#c9cfda;
}
[data-theme="dark"]{
  --bg:#14161a; --fg:#e8eaee; --muted:#9aa2b1; --card:#1d2026;
  --line:#2b2f38; --accent:#7aa2ff; --edge:#39404c;
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  background:var(--bg); color:var(--fg);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
       "Helvetica Neue",Arial,"Noto Sans",sans-serif;
  padding:24px; transition:background .15s ease,color .15s ease;
}
header{max-width:960px;margin:0 auto 8px}
h1{font-size:22px;margin:0 0 4px;font-weight:650;letter-spacing:.2px}
h1 .ver{color:var(--muted);font-weight:500;font-size:15px}
.sub{color:var(--muted);margin:0 0 16px}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
#q{
  flex:1 1 240px;min-width:200px;padding:9px 12px;font:inherit;
  color:var(--fg);background:var(--card);
  border:1px solid var(--edge);border-radius:9px;outline:none;
}
#q:focus{border-color:var(--accent)}
#theme{
  padding:9px 14px;font:inherit;cursor:pointer;color:var(--fg);
  background:var(--card);border:1px solid var(--edge);border-radius:9px;
}
#theme:hover{border-color:var(--accent)}
main{max-width:960px;margin:18px auto}
.grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));
  gap:10px;
}
.cell{
  display:flex;flex-direction:column;align-items:center;gap:8px;
  padding:14px 8px 10px;cursor:pointer;color:var(--fg);
  background:var(--card);border:1px solid var(--line);border-radius:12px;
  font:inherit;transition:border-color .12s ease,transform .06s ease;
}
.cell:hover{border-color:var(--accent)}
.cell:active{transform:scale(.97)}
.cell svg{width:32px;height:32px;color:var(--fg)}
.cell .label{font-size:12px;color:var(--muted);word-break:break-all;text-align:center}
.empty{color:var(--muted);text-align:center;padding:24px 0}
footer{max-width:960px;margin:26px auto 4px;color:var(--muted);font-size:13px;
       border-top:1px solid var(--line);padding-top:14px}
footer a{color:var(--accent)}
.toast{
  position:fixed;left:50%;bottom:22px;transform:translateX(-50%);
  background:var(--card);border:1px solid var(--edge);border-radius:10px;
  padding:10px 16px;font-size:13px;max-width:min(90vw,420px);text-align:center;
  box-shadow:0 8px 26px rgba(0,0,0,.18);
}
.toast.ok{border-color:var(--accent)}
.toast.err{border-color:#e5484d;color:#e5484d}
"""

_JS = """\
(function () {
  var cells = Array.prototype.slice.call(document.querySelectorAll('.cell'));
  var q = document.getElementById('q');
  var empty = document.getElementById('empty');
  var toast = document.getElementById('toast');
  var themeBtn = document.getElementById('theme');
  var root = document.documentElement;
  var timer = null;

  function applyFilter() {
    var v = (q.value || '').trim().toLowerCase();
    var shown = 0;
    cells.forEach(function (c) {
      var m = c.getAttribute('data-name').toLowerCase().indexOf(v) >= 0;
      c.hidden = !m;
      if (m) { shown++; }
    });
    empty.hidden = shown !== 0;
  }
  q.addEventListener('input', applyFilter);

  function showToast(msg, ok) {
    toast.textContent = msg;
    toast.className = 'toast ' + (ok ? 'ok' : 'err');
    toast.hidden = false;
    if (timer) { clearTimeout(timer); }
    timer = setTimeout(function () { toast.hidden = true; }, 2400);
  }

  function legacyCopy(text) {
    try {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (e) { return false; }
  }

  function copyText(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { done(true); },
        function () { done(legacyCopy(text)); }
      );
    } else {
      done(legacyCopy(text));
    }
  }

  cells.forEach(function (c) {
    c.addEventListener('click', function () {
      var svg = c.querySelector('svg');
      if (!svg) { showToast('Copy failed: SVG not found.', false); return; }
      copyText(svg.outerHTML, function (ok) {
        if (ok) {
          showToast('Copied SVG source of "' + c.getAttribute('data-name') + '"', true);
        } else {
          showToast('Copy failed: clipboard blocked. Select and copy the SVG manually.', false);
        }
      });
    });
  });

  function setTheme(t, persist) {
    root.setAttribute('data-theme', t);
    themeBtn.textContent = (t === 'dark') ? 'Light' : 'Dark';
    if (persist) { try { localStorage.setItem('oui-theme', t); } catch (e) {} }
  }
  var saved = null;
  try { saved = localStorage.getItem('oui-theme'); } catch (e) {}
  setTheme(saved === 'dark' ? 'dark' : 'light', false);
  themeBtn.addEventListener('click', function () {
    setTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark', true);
  });

  applyFilter();
})();
"""


def build_html():
    cells = []
    for name, primitives in ICONS:
        svg = icon_markup(name, primitives).rstrip("\n")
        cells.append(
            '    <button class="cell" type="button" data-name="%s" '
            'title="Copy SVG source: %s">\n      %s\n      '
            '<span class="label">%s</span>\n    </button>'
            % (name, name, svg, name)
        )
    grid = "\n".join(cells)
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en" data-theme="light">\n'
        '<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>Offline UI Icons v%s</title>\n'
        '<style>\n%s</style>\n'
        '</head>\n'
        '<body>\n'
        '<header>\n'
        '  <h1>Offline UI Icons <span class="ver">v%s</span></h1>\n'
        '  <p class="sub">%d line icons &middot; 24x24 &middot; offline, '
        'dependency-free &middot; click any icon to copy its SVG source</p>\n'
        '  <div class="controls">\n'
        '    <input id="q" type="search" autocomplete="off" '
        'placeholder="Filter by name..." aria-label="Filter icons by name">\n'
        '    <button id="theme" type="button" '
        'aria-label="Toggle colour theme">Dark</button>\n'
        '  </div>\n'
        '</header>\n'
        '<main>\n'
        '  <div id="grid" class="grid">\n%s\n  </div>\n'
        '  <p id="empty" class="empty" hidden>No icons match that filter.</p>\n'
        '</main>\n'
        '<footer>\n'
        '  <p>MIT licensed. No trackers, no network requests. '
        'If these icons help you, you can '
        '<a href="%s" rel="noopener noreferrer">support this work on Ko-fi</a>.</p>\n'
        '</footer>\n'
        '<div id="toast" class="toast" role="status" aria-live="polite" hidden></div>\n'
        '<script>\n%s</script>\n'
        '</body>\n'
        '</html>\n'
        % (VERSION, _CSS, VERSION, ICON_COUNT, grid, DONATION_URL, _JS)
    )


def build_js():
    data = {}
    for name, primitives in ICONS:
        data[name] = icon_inner(name, primitives)
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"))
    header = (
        "/* Offline UI Icons v%s -- merged icon data.\n"
        " * Map: icon name -> inner SVG markup (children of a 24x24 "
        "stroke-based <svg>).\n"
        " * MIT licensed. Generated by build_icons.py; do not edit by hand. */\n"
        % VERSION
    )
    return header + "window.OFFLINE_UI_ICONS = " + payload + ";\n"


def build_readme():
    names = ", ".join(EXPECTED_NAMES)
    return """\
# Offline UI Icons v%s

A small, hand-tuned set of %d line-style UI icons drawn on a 24x24 grid.
Pure SVG, zero dependencies, zero network, fully offline. The whole pack is
generated by one Python script and verified by another; only the Python
standard library is used.

## Contents

- `svg/<name>.svg` -- %d standalone SVG files (24x24 viewBox, stroke-based,
  `currentColor`, round caps and joins).
- `offline-ui-icons.js` -- all %d icons merged into a single JS object
  (`window.OFFLINE_UI_ICONS`, mapping `name -> inner SVG markup`) for direct
  use in a front end.
- `index.html` -- a self-contained gallery: a grid of all %d icons, a live
  name filter, click-to-copy of the SVG source, and a light/dark toggle.
  No CDN, no external assets, no trackers.
- `README.md`, `LICENSE` -- this file and the MIT license text.

## Icon set (%d)

%s.

## Design rules

- viewBox `0 0 24 24`
- `fill="none"`, `stroke="currentColor"`, `stroke-width="%s"`
- `stroke-linecap="round"`, `stroke-linejoin="round"`
- geometry laid out on a 24-unit grid with roughly 2 units of padding

Because the stroke colour is `currentColor`, every icon inherits the text
colour of whatever contains it. Use the standalone files directly, or inline
the markup from `offline-ui-icons.js`.

## Rebuild and verify

    python3 build_icons.py     # writes svg/, the .js, index.html, README, LICENSE, the zip
    python3 check_icons.py     # structural + offline/identity invariants; last line "N PASS / N FAIL"

The build is deterministic: running it twice yields byte-identical output,
and it is independent of the current working directory.

## License

MIT -- see `LICENSE`. The copyright line is deliberately neutral
("%s"); no personal data is included anywhere in this pack.

## Support

If these icons are useful to you, you can support the work here:
%s
""" % (VERSION, ICON_COUNT, ICON_COUNT, ICON_COUNT, ICON_COUNT, ICON_COUNT,
       names, STROKE_WIDTH, LICENSE_HOLDER, DONATION_URL)


def build_license():
    return """\
MIT License

Copyright (c) 2026 %s

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""" % LICENSE_HOLDER


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build_zip(members):
    """members: list of (arcname, bytes). Deterministic archive."""
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w") as zf:
        for arcname, data in sorted(members, key=lambda kv: kv[0]):
            info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                        compresslevel=9)


def main():
    if len(ICONS) != ICON_COUNT:
        raise SystemExit("icon table has %d entries, expected %d"
                         % (len(ICONS), ICON_COUNT))
    if len(set(EXPECTED_NAMES)) != ICON_COUNT:
        raise SystemExit("duplicate icon names in the table")

    for d in (DIST_DIR, SVG_DIR):
        if not os.path.isdir(d):
            os.makedirs(d)

    members = []

    # 1. standalone SVG files
    for name, primitives in ICONS:
        text = icon_markup(name, primitives)
        path = os.path.join(SVG_DIR, name + ".svg")
        write_text(path, text)
        members.append(("svg/%s.svg" % name, text.encode("utf-8")))

    # 2. merged JS data
    js_text = build_js()
    write_text(os.path.join(DIST_DIR, "offline-ui-icons.js"), js_text)
    members.append(("offline-ui-icons.js", js_text.encode("utf-8")))

    # 3. gallery page
    html_text = build_html()
    write_text(os.path.join(DIST_DIR, "index.html"), html_text)
    members.append(("index.html", html_text.encode("utf-8")))

    # 4. README + LICENSE (also archived)
    readme = build_readme()
    write_text(os.path.join(SCRIPT_DIR, "README.md"), readme)
    members.append(("README.md", readme.encode("utf-8")))

    license_text = build_license()
    write_text(os.path.join(SCRIPT_DIR, "LICENSE"), license_text)
    members.append(("LICENSE", license_text.encode("utf-8")))

    # 5. archive
    build_zip(members)

    print("built %d icons -> %s" % (ICON_COUNT, DIST_DIR))
    print("archive -> %s" % ZIP_PATH)


if __name__ == "__main__":
    main()
