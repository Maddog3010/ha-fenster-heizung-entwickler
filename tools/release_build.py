#!/usr/bin/env python3
"""Baut aus der Entwickler-Version die Version für das Hauptprojekt (ohne Entwickler-Modus).

  python3 tools/release_build.py --out OUT --version 3.0.5.6 --changelog-file aenderungen.md [--date 2026-10-28]

Was passiert:
  1. Der Ordner custom_components/fenster_heizung_dev wird nach OUT/custom_components/fenster_heizung kopiert.
  2. Entwickler-Dateien (devgate.py, devapi.py, frontend-src/parts/*entwicklung*) werden weggelassen.
  3. Blöcke zwischen  <DEV> ... <RELEASE> ... </DEV>  werden ersetzt: die Entwickler-Zeilen fallen weg,
     die Zeilen hinter <RELEASE> (mit führendem  #>  bzw.  //>  ) werden zu normalem Code.
  4. Namen werden zurückgesetzt (fenster_heizung_dev -> fenster_heizung, Panel-Name, Titel).
  5. Manifest, README-Badge und CHANGELOG bekommen die neue Version, panel.js wird neu gebaut.
  6. Prüfungen: keine Reste des Entwickler-Modus, kein privater Schlüssel, Python- und JS-Syntax.
"""
import argparse, json, pathlib, re, shutil, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = "fenster_heizung_dev"
REL = "fenster_heizung"
SKIP_FILES = {"devgate.py", "devapi.py"}
SKIP_PARTS = ("entwicklung",)
REPLACE = [
    (DEV, REL),
    ("fenster-heizung-dev-panel", "fenster-heizung-panel"),
    ('PANEL_URL = "fenster-heizung-dev"', 'PANEL_URL = "fenster-heizung"'),
    ('sidebar_title="Strom & Wärme Entwickler"', 'sidebar_title="Strom & Wärme"'),
    ('sidebar_icon="mdi:code-braces"', 'sidebar_icon="mdi:window-open-variant"'),
    ('PRODUCT = "Strom & Wärme · Entwickler"', 'PRODUCT = "Strom & Wärme"'),
]
FORBIDDEN = ["FHDEV", "FHDEVPRIV", "devgate", "devapi", "fenster_heizung_dev", "fenster-heizung-dev", "<DEV>", "</DEV>", "<RELEASE>", "dvx", "MOD_DV"]


def strip_blocks(text: str, c: str) -> str:
    out, state = [], None
    for line in text.split("\n"):
        t = line.strip().replace(c + " ", c, 1) if line.strip().startswith(c + " <") or line.strip().startswith(c + " </") else line.strip()
        if t == f"{c}<DEV>":
            state = "dev"; continue
        if t == f"{c}<RELEASE>":
            state = "rel"; continue
        if t == f"{c}</DEV>":
            state = None; continue
        if state == "dev":
            continue
        if state == "rel":
            if not line.startswith(f"{c}>"):
                sys.exit(f"Release-Zeile ohne '{c}>' : {line[:80]}")
            out.append(line[len(c) + 1:]); continue
        out.append(line)
    if state is not None:
        sys.exit("Block <DEV> nicht geschlossen")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--changelog-file", required=True)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    if not re.match(r"^\d+(\.\d+){2,3}$", a.version):
        sys.exit("Version ungültig")
    out = pathlib.Path(a.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    cc_out = out / "custom_components" / REL
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", "panel.js")
    shutil.copytree(ROOT / "custom_components" / DEV, cc_out, ignore=ign)
    shutil.copytree(ROOT / "frontend-src", out / "frontend-src", ignore=shutil.ignore_patterns("__pycache__"))
    for f in SKIP_FILES:
        (cc_out / f).unlink(missing_ok=True)
    for p in list((out / "frontend-src" / "parts").glob("*.js")):
        if any(s in p.name for s in SKIP_PARTS):
            p.unlink()
    for f in (ROOT / "release").iterdir():
        shutil.copy2(f, out / f.name)
    # Text umbauen
    for p in list(out.rglob("*")):
        if not p.is_file() or p.suffix not in (".py", ".js", ".json"):
            continue
        s = p.read_text(encoding="utf-8")
        s = strip_blocks(s, "#" if p.suffix == ".py" else "//") if p.suffix in (".py", ".js") else s
        for o, n in REPLACE:
            s = s.replace(o, n)
        p.write_text(s, encoding="utf-8")
    # Manifest
    m = cc_out / "manifest.json"
    d = json.loads(m.read_text(encoding="utf-8"))
    d.update(domain=REL, name="Strom & Wärme", version=a.version,
             documentation="https://github.com/Maddog3010/ha-fenster-heizung",
             issue_tracker="https://github.com/Maddog3010/ha-fenster-heizung/issues")
    m.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # README-Badge und CHANGELOG
    rd = out / "README.md"
    rd.write_text(re.sub(r"Version-[0-9.]+-", f"Version-{a.version}-", rd.read_text(encoding="utf-8"), count=1), encoding="utf-8")
    cl = out / "CHANGELOG.md"
    text = cl.read_text(encoding="utf-8")
    body = pathlib.Path(a.changelog_file).read_text(encoding="utf-8").strip()
    i = text.find("## [")
    entry = f"## [{a.version}] - {a.date}\n\n{body}\n\n"
    cl.write_text(text[:i] + entry + text[i:] if i >= 0 else text + "\n" + entry, encoding="utf-8")
    # panel.js neu bauen
    r = subprocess.run([sys.executable, str(out / "frontend-src" / "build.py")], capture_output=True, text=True)
    if r.returncode:
        sys.exit("Bauen fehlgeschlagen:\n" + r.stdout + r.stderr)
    # Prüfungen
    bad = []
    for p in out.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".js", ".json", ".md", ".yaml"):
            s = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"FHPRIV1-[A-Za-z0-9_-]{20,}", s):
                bad.append(f"{p.relative_to(out)}: privater Schlüssel")
            for w in FORBIDDEN:
                if w in s:
                    bad.append(f"{p.relative_to(out)}: {w}")
    if bad:
        sys.exit("Reste des Entwickler-Modus gefunden:\n  " + "\n  ".join(bad[:20]))
    r = subprocess.run([sys.executable, "-m", "compileall", "-q", str(cc_out)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("Python-Syntaxfehler:\n" + r.stdout + r.stderr)
    for p in cc_out.rglob("__pycache__"):
        shutil.rmtree(p)
    print(f"OK: Version {a.version} gebaut in {out}")


if __name__ == "__main__":
    main()
