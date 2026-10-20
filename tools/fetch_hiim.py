"""Prenese Hiim PD2 S14 tier liste, katalog plannerja, vse povezane planerje, podatke o mapah in galerijo buildov.

Uporablja curl, ker sistemski Python nima SSL certifikatov.
Rezultat: data/hiim/tiers_*.json, data/hiim/catalog/*.json, data/hiim/builds/<id>.json,
data/hiim/maps/*.json (mape, pošasti, odpornosti) in data/hiim/gallery/builds_s14.json (javni buildi skupnosti)
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "hiim")
BASE = "https://hiimpd2.com"
LISTS = ["solo", "starter", "boss", "group-generalist", "group-physical", "group-elemental"]
CATALOG = ["manifest", "classes", "items", "runewords", "socketables", "corruptions", "presets",
           "charms", "mercs", "crafts", "effects"] + [
    f"skills.{c}" for c in ["amazon", "assassin", "barbarian", "druid", "necromancer", "paladin", "sorceress"]]
EXTRA = ["bases", "item-types", "properties", "affixes"]  # /data/s14/<ime>.json
MAPS = ["levels", "monsters", "monlvl", "explorer-tiers"]  # Maps explorer


def get(url, path, force=False):
    if os.path.exists(path) and not force:
        return json.load(open(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = subprocess.run(["curl", "-sL", "-m", "60", url], capture_output=True, text=True).stdout
    data = json.loads(out)
    json.dump(data, open(path, "w"))
    time.sleep(0.1)
    return data


def main():
    force = "--force" in sys.argv
    for name in LISTS:
        get(f"{BASE}/api/tiers?season=14&list={name}", os.path.join(OUT, f"tiers_{name}.json"), force)
    for name in CATALOG:
        get(f"{BASE}/data/s14/planner/{name}.json", os.path.join(OUT, "catalog", f"{name}.json"), force)

    for name in EXTRA:
        get(f"{BASE}/data/s14/{name}.json", os.path.join(OUT, "catalog", f"{name}.json"), force)
    for name in MAPS:
        get(f"{BASE}/data/s14/{name}.json", os.path.join(OUT, "maps", f"{name}.json"), force)
    gallery(force)

    ids = set()
    for name in LISTS:
        for e in json.load(open(os.path.join(OUT, f"tiers_{name}.json")))["entries"]:
            if e.get("buildId"):
                ids.add(e["buildId"])
            for link in e.get("links") or []:
                if link.get("kind") == "planner" and link.get("buildId"):
                    ids.add(link["buildId"])
    ok = 0
    for bid in sorted(ids):
        try:
            get(f"{BASE}/api/builds/{bid}", os.path.join(OUT, "builds", f"{bid}.json"), force)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print("napaka", bid, exc)
    print(f"planerji: {ok}/{len(ids)}")


def gallery(force=False):
    """Vsi javni S14 buildi iz Hiim galerije (po straneh)."""
    path = os.path.join(OUT, "gallery", "builds_s14.json")
    if os.path.exists(path) and not force:
        return
    out, after = [], None
    for _ in range(200):
        q = {"season": 14}
        if after:
            q["after"] = after
        raw = subprocess.run(["curl", "-sL", "-m", "60", f"{BASE}/api/builds?" + urllib.parse.urlencode(q)],
                             capture_output=True, text=True).stdout
        d = json.loads(raw)
        out += d.get("builds") or []
        after = d.get("next")
        if not after:
            break
        time.sleep(0.2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"))
    print(f"galerija: {len(out)} buildov")


if __name__ == "__main__":
    main()
