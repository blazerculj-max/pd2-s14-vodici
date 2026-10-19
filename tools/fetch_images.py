"""Prenese slike iz hiimpd2.com/planner-art v docs/img in poišče slike baznih predmetov.

1. data/images.json (poti, ki jih je zbral build_data.py) → docs/img/<pot>
2. za bazne kode (runewordi, custom predmeti, wiki baz) poskusi mape istega tipa → data/base_images.json
"""
import json
import os
import subprocess
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = "https://hiimpd2.com/planner-art/"
SITE_IMG = os.path.join(ROOT, "docs", "img")
CAT = os.path.join(ROOT, "data", "hiim", "catalog")


def download(path):
    dest = os.path.join(SITE_IMG, path)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = ART + urllib.parse.quote(path)
    code = subprocess.run(["curl", "-sL", "-m", "30", "-o", dest, "-w", "%{http_code}", url],
                          capture_output=True, text=True).stdout.strip()
    if code != "200":
        if os.path.exists(dest):
            os.remove(dest)
        return False
    return True


def base_dirs(bases):
    """Mape, v katerih Hiim hrani slike predmetov (brez /special), skupaj in po tipu baze."""
    dirs, by_type = set(), {}
    items = json.load(open(os.path.join(CAT, "items.json")))["items"]
    presets = json.load(open(os.path.join(CAT, "presets.json")))
    for it in items + presets:
        p = it.get("image") or ""
        d = os.path.dirname(p).replace("/special", "")
        if d:
            dirs.add(d)
            b = bases.get(it.get("base"))
            if b:
                by_type.setdefault(b["type"], {}).setdefault(d, 0)
                by_type[b["type"]][d] += 1
    by_type = {t: sorted(c, key=lambda d: -c[d]) for t, c in by_type.items()}
    return sorted(dirs), by_type


def main():
    paths = json.load(open(os.path.join(ROOT, "data", "images.json")))
    ok = sum(download(p) for p in paths)
    print(f"slike: {ok}/{len(paths)}")

    bases = {b["code"]: b for b in json.load(open(os.path.join(CAT, "bases.json")))}
    need = json.load(open(os.path.join(ROOT, "data", "base_codes.json"))) if os.path.exists(
        os.path.join(ROOT, "data", "base_codes.json")) else []
    out_path = os.path.join(ROOT, "data", "base_images.json")
    found = json.load(open(out_path)) if os.path.exists(out_path) else {}
    dirs, by_type = base_dirs(bases)
    for code in need:
        if code in found:
            continue
        b = bases.get(code)
        if not b:
            continue
        names = []
        for c in (b.get("normCode"), code):
            if c and bases.get(c):
                names.append(bases[c]["name"].replace(" ", "_").replace("'", "%27"))
        kind = b.get("kind")
        cands = by_type.get(b.get("type")) or [d for d in dirs if (kind == "weapon" and d.startswith("items/weapon")) or
                                                (kind != "weapon" and not d.startswith("items/weapon"))]
        hit = None
        for n in dict.fromkeys(x for x in names if "/" not in x):
            for d in cands:
                path = f"{d}/{urllib.parse.unquote(n)}.png"
                if download(path):
                    hit = path
                    break
            if hit:
                break
        found[code] = hit
        print(code, b.get("name"), "->", hit)
    json.dump(found, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
