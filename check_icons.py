#!/usr/bin/env python3
"""check_icons.py -- structural / offline / identity checker for Offline UI Icons v0.1.

Zero dependencies (Python 3 stdlib only), zero network. Path-independent: every
path is resolved relative to this script's own directory, so it can be run from
any working directory.

It validates the built pack under ./dist plus ./README.md and ./LICENSE:
file inventory, XML/SVG structure, the merged JS data file, the gallery page,
the release archive, and a whole-tree scan for network references and identity
leaks (emails, phone numbers, IPs, machine absolute paths, foreign domains).

The last line is "N PASS / M FAIL"; the process exit code is the FAIL count
(0 when everything passes). An intentionally broken input therefore fails with a
non-zero exit code.

Note on the single permitted "http" token: a standalone .svg file that must
render on its own requires the SVG XML namespace declaration
"http://www.w3.org/2000/svg". That token is a namespace identifier, not a
network reference (nothing is ever fetched), so it is allow-listed. The only
real URL that is allow-listed is the donation link. Every other http(s) URL,
bare domain or IP address is a violation.
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
SVG_DIR = os.path.join(DIST_DIR, "svg")
JS_PATH = os.path.join(DIST_DIR, "offline-ui-icons.js")
HTML_PATH = os.path.join(DIST_DIR, "index.html")
ZIP_PATH = os.path.join(DIST_DIR, "offline-ui-icons-v0.1.zip")
README_PATH = os.path.join(SCRIPT_DIR, "README.md")
LICENSE_PATH = os.path.join(SCRIPT_DIR, "LICENSE")

VERSION = "0.1"
SVG_NS = "http://www.w3.org/2000/svg"
DONATION_URL = "https://ko-fi.com/colome"
LICENSE_HOLDER = "Offline UI Icons contributors"

EXPECTED_NAMES = [
    "menu", "close", "search", "settings", "user", "home", "star", "heart",
    "bell", "calendar", "clock", "mail", "download", "upload", "cloud",
    "folder", "file", "edit", "trash", "plus", "minus", "check", "arrow-right",
    "arrow-left", "chevron-down", "chevron-up", "lock", "eye", "refresh",
    "external-link", "copy", "info",
]

ALLOWED_URLS = {SVG_NS, DONATION_URL}
ALLOWED_DOMAIN_SUFFIXES = ("ko-fi.com", "w3.org")

URL_RE = re.compile(r"https?://[^\s\"'<>()\]]+")
DOMAIN_RE = re.compile(
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.(?:com|net|org|io|dev|app|co|xyz|"
    r"info|biz|online|site|store|me|ai|tv|cc|us|uk|ru|cn|tech|cloud)\b"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
PHONE_RES = [
    re.compile(r"\+\d[\d ().\-]{6,}\d"),
    re.compile(r"\b\d{3}[ .\-]\d{3}[ .\-]\d{4}\b"),
    re.compile(r"\b\d{10,}\b"),
]
# Absolute-path markers are assembled from parts on purpose so that THIS file's
# own source does not itself contain the forbidden path literals.
_S = "/"
ABS_PATH_TOKENS = [
    _S + "home" + _S,
    _S + "Users" + _S,
    _S + "root" + _S,
    "C:" + "\\",
    "\\" + "Users" + "\\",
]

results = []


def add(label, ok, detail=""):
    results.append((label, bool(ok), detail))


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def svg_files():
    if not os.path.isdir(SVG_DIR):
        return {}
    out = {}
    for fn in sorted(os.listdir(SVG_DIR)):
        if fn.endswith(".svg"):
            out[fn[:-4]] = os.path.join(SVG_DIR, fn)
    return out


def main():
    # ------------------------------------------------------------- inventory
    add("dist/ exists", os.path.isdir(DIST_DIR), DIST_DIR)
    add("dist/svg/ exists", os.path.isdir(SVG_DIR), SVG_DIR)

    svgs = svg_files()
    add("exactly 32 SVG files", len(svgs) == 32, "found %d" % len(svgs))
    add("SVG name set matches the spec", sorted(svgs) == sorted(EXPECTED_NAMES),
        "diff=%s" % sorted(set(svgs) ^ set(EXPECTED_NAMES)))

    # per-file structural facts, aggregated
    xml_ok = True
    all_paths_ok = True
    viewbox_ok = True
    width_ok = True
    height_ok = True
    ns_ok = True
    fill_ok = True
    stroke_ok = True
    width_uniform = True
    cap_ok = True
    join_ok = True
    empty_files = []
    d_ok = True

    parsed = {}
    seen_stroke_widths = set()

    for name, path in sorted(svgs.items()):
        if os.path.getsize(path) == 0:
            empty_files.append(name)
        raw = read_text(path)
        if ('xmlns="%s"' % SVG_NS) not in raw:
            ns_ok = False
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            xml_ok = False
            continue
        root = tree.getroot()
        parsed[name] = root

        if localname(root.tag) != "svg":
            ns_ok = False  # root not svg
        if root.get("viewBox") != "0 0 24 24":
            viewbox_ok = False
        if root.get("width") != "24":
            width_ok = False
        if root.get("height") != "24":
            height_ok = False
        if root.get("fill") != "none":
            fill_ok = False
        if root.get("stroke") != "currentColor":
            stroke_ok = False
        if root.get("stroke-linecap") != "round":
            cap_ok = False
        if root.get("stroke-linejoin") != "round":
            join_ok = False
        sw = root.get("stroke-width")
        seen_stroke_widths.add(sw)

        paths = [el for el in root.iter() if localname(el.tag) == "path"]
        if len(paths) < 1:
            all_paths_ok = False
        for p in paths:
            d = (p.get("d") or "").strip()
            if not d or d[0] not in "Mm":
                d_ok = False

    add("every SVG parses as XML", xml_ok)
    add("every SVG root element is <svg> with the SVG namespace", ns_ok)
    add("every SVG declares viewBox '0 0 24 24'", viewbox_ok)
    add("every SVG width == 24", width_ok)
    add("every SVG height == 24", height_ok)
    add("every SVG has >= 1 <path>", all_paths_ok)
    add("every <path> has a non-empty d starting with M/m", d_ok)
    add("every SVG fill == 'none'", fill_ok)
    add("every SVG stroke == 'currentColor'", stroke_ok)
    add("stroke-width is uniform and in {1.75, 2}",
        seen_stroke_widths <= {"1.75", "2"} and len(seen_stroke_widths) == 1,
        "widths=%s" % sorted(str(x) for x in seen_stroke_widths))
    add("every SVG stroke-linecap == 'round'", cap_ok)
    add("every SVG stroke-linejoin == 'round'", join_ok)
    add("no zero-byte SVG file", not empty_files, ",".join(empty_files))

    # --------------------------------------------------------------- JS data
    add("dist/offline-ui-icons.js exists", os.path.isfile(JS_PATH))
    js_text = read_text(JS_PATH) if os.path.isfile(JS_PATH) else ""
    js_data = None
    if js_text:
        marker = "OFFLINE_UI_ICONS = "
        try:
            idx = js_text.index(marker) + len(marker)
            chunk = js_text[idx:]
            chunk = chunk[:chunk.index(";")].strip()
            js_data = json.loads(chunk)
        except (ValueError, json.JSONDecodeError):
            js_data = None
    add("JS data parses as JSON", isinstance(js_data, dict))
    if isinstance(js_data, dict):
        add("JS data has exactly 32 keys", len(js_data) == 32,
            "found %d" % len(js_data))
        add("JS keys match the spec", sorted(js_data) == sorted(EXPECTED_NAMES),
            "diff=%s" % sorted(set(js_data) ^ set(EXPECTED_NAMES)))
        add("JS values are non-empty strings",
            all(isinstance(v, str) and v.strip() for v in js_data.values()))
        add("every JS value contains a <path>",
            all("<path" in v for v in js_data.values()))
    else:
        add("JS data has exactly 32 keys", False, "unparseable")
        add("JS keys match the spec", False, "unparseable")
        add("JS values are non-empty strings", False, "unparseable")
        add("every JS value contains a <path>", False, "unparseable")

    # ------------------------------------------------------------- HTML page
    add("dist/index.html exists", os.path.isfile(HTML_PATH))
    html = read_text(HTML_PATH) if os.path.isfile(HTML_PATH) else ""
    add("index.html inlines exactly 32 <svg> elements",
        html.count("<svg") == 32, "found %d" % html.count("<svg"))
    add("index.html links the donation page", DONATION_URL in html)
    add("index.html has a name filter input",
        'type="search"' in html and 'id="q"' in html)
    add("index.html has a light/dark toggle",
        'data-theme' in html and 'id="theme"' in html)
    add("index.html has no external <script src>", "<script src" not in html)
    add("index.html has no <link> element", "<link" not in html.lower())
    add("index.html has no <img> element", "<img" not in html.lower())
    add("index.html has no @import", "@import" not in html)

    # ------------------------------------------------------------- the archive
    add("dist/offline-ui-icons-v0.1.zip exists", os.path.isfile(ZIP_PATH))
    zip_ok = False
    zip_names = set()
    zip_bytes = {}
    if os.path.isfile(ZIP_PATH):
        try:
            with zipfile.ZipFile(ZIP_PATH) as zf:
                zip_ok = zf.testzip() is None
                zip_names = set(zf.namelist())
                for arc in zf.namelist():
                    zip_bytes[arc] = zf.read(arc)
        except zipfile.BadZipFile:
            zip_ok = False
    add("zip passes integrity test (testzip)", zip_ok)

    expected_zip_names = set(
        ["svg/%s.svg" % n for n in EXPECTED_NAMES]
        + ["offline-ui-icons.js", "index.html", "README.md", "LICENSE"]
    )
    add("zip members match the expected set",
        zip_names == expected_zip_names,
        "extra=%s missing=%s" % (sorted(zip_names - expected_zip_names),
                                 sorted(expected_zip_names - zip_names)))
    add("zip contains exactly 32 svg members",
        len([n for n in zip_names if n.startswith("svg/")]) == 32)
    add("zip members are all non-empty",
        all(len(zip_bytes.get(n, b"")) > 0 for n in zip_names))

    # ------------------------------------------------------- README / LICENSE
    add("README.md exists", os.path.isfile(README_PATH))
    readme = read_text(README_PATH) if os.path.isfile(README_PATH) else ""
    add("README.md mentions the donation page", DONATION_URL in readme)
    add("README.md states the MIT license", "MIT" in readme)
    add("LICENSE exists", os.path.isfile(LICENSE_PATH))
    lic = read_text(LICENSE_PATH) if os.path.isfile(LICENSE_PATH) else ""
    add("LICENSE carries the neutral copyright holder",
        LICENSE_HOLDER in lic)
    add("LICENSE is the MIT text",
        "MIT License" in lic and "WITHOUT WARRANTY OF ANY KIND" in lic)

    # ---------------------------------------------- whole-tree offline/leak scan
    all_files = {}
    for name, path in sorted(svgs.items()):
        all_files["svg/%s.svg" % name] = read_text(path)
    all_files["offline-ui-icons.js"] = js_text
    all_files["index.html"] = html
    all_files["README.md"] = readme
    all_files["LICENSE"] = lic
    for arc, blob in sorted(zip_bytes.items()):
        try:
            all_files["zip:" + arc] = blob.decode("utf-8")
        except UnicodeDecodeError:
            pass

    def scan(find):
        hits = []
        for fname, text in sorted(all_files.items()):
            for m in find(text):
                hits.append((fname, m if isinstance(m, str) else m.group(0)))
        return hits

    # all URL, bare-domain and IP references are aggregated into ONE check so
    # that a single injected reference yields exactly one FAIL (keeping the exit
    # code equal to the FAIL count for a single-defect input).
    def find_network(text):
        hits = []
        for m in re.finditer(r"https?://[^\s\"'<>()\]]*", text):
            u = m.group(0)
            if u not in ALLOWED_URLS:
                hits.append(u)
        for d in DOMAIN_RE.findall(text):
            if not d.lower().endswith(ALLOWED_DOMAIN_SUFFIXES):
                hits.append(d)
        for ip in IP_RE.findall(text):
            hits.append(ip)
        return hits

    net_hits = scan(find_network)
    add("no disallowed network reference (URL/domain/IP) anywhere",
        not net_hits, str(net_hits[:5]))

    email_hits = scan(lambda t: EMAIL_RE.findall(t))
    add("no email-like string anywhere", not email_hits, str(email_hits[:5]))

    phone_hits = []
    for fname, text in sorted(all_files.items()):
        for rx in PHONE_RES:
            for m in rx.findall(text):
                phone_hits.append((fname, m))
    add("no phone-number-like string anywhere", not phone_hits,
        str(phone_hits[:5]))

    abs_hits = []
    for fname, text in sorted(all_files.items()):
        for tok in ABS_PATH_TOKENS:
            if tok in text:
                abs_hits.append((fname, tok))
    add("no machine absolute path anywhere", not abs_hits, str(abs_hits[:5]))

    url_open = scan(lambda t: re.findall(r"url\(", t))
    add("no 'url(' reference anywhere", not url_open, str(url_open[:5]))

    img_hits = scan(lambda t: re.findall(r"<image", t))
    add("no <image> element anywhere", not img_hits, str(img_hits[:5]))

    xlink_hits = scan(lambda t: re.findall(r"xlink:href", t))
    add("no xlink:href anywhere", not xlink_hits, str(xlink_hits[:5]))

    # -------------------------------------------------------------- report
    passes = sum(1 for _, ok, _ in results if ok)
    fails = sum(1 for _, ok, _ in results if not ok)
    for label, ok, detail in results:
        line = ("PASS  " if ok else "FAIL  ") + label
        if (not ok) and detail:
            line += "  [" + detail + "]"
        print(line)
    print("-" * 60)
    print("%d PASS / %d FAIL" % (passes, fails))
    return min(fails, 255)


if __name__ == "__main__":
    sys.exit(main())
