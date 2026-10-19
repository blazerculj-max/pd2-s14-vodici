"""Prenese Hiim PD2 S14 tier liste, katalog plannerja in vse povezane planerje.

Uporablja curl, ker sistemski Python nima SSL certifikatov.
Rezultat: data/hiim/tiers_*.json, data/hiim/catalog/*.json, data/hiim/builds/<id>.json
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "hiim")
BASE = "https://hiimpd2.com"
LISTS = ["solo", "starter", "boss", "group-generalist", "group-physical", "group-elemental"]
CATALOG = ["manifest", "classes", "items", "runewords", "socketables", "corruptions", "presets",
           "charms", "mercs", "crafts", "effects"] + [
    f"skills.{c}" for c in ["amazon", "assassin", "barbarian", "druid", "necromancer", "paladin", "sorceress"]]


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


if __name__ == "__main__":
    main()
