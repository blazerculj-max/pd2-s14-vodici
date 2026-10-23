"""JuxtAPoserjeva S14 tier lista (pd2guides.pages.dev) → data/juxt/tierlist.json.

Stran podatke bere iz Google Sheeta prek svojega API-ja /api/build-data?class=<Razred>; za vsak razred
so tam odseki Leveling, Early Farming, Early Bossing, CMapper (cenen mapper), EMapper (endgame mapper)
in T2Bosser z oceno, opremo, merci, mesti za farmanje in opombami."""
import datetime
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "juxt")
SITE = "https://pd2guides.pages.dev"
CLASSES = ["Amazon", "Assassin", "Barbarian", "Druid", "Necromancer", "Paladin", "Sorceress"]


def fetch(cls):
    r = subprocess.run(["curl", "-s", "-f", "-L", "-A", "Mozilla/5.0", f"{SITE}/api/build-data?class={cls}"],
                       capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    sections = []
    for s in d.get("sections", []):
        builds = [{k: b.get(k) for k in ("name", "rank", "ratings", "details", "mercs", "gear", "notes", "links", "season")}
                  for b in s.get("builds", [])]
        sections.append({"type": s.get("type"), "title": s.get("title"), "description": s.get("description"), "builds": builds})
    return {"updated": d.get("updatedAt"), "sections": sections}


def main():
    os.makedirs(OUT, exist_ok=True)
    data = {"url": SITE, "fetched": datetime.date.today().isoformat(),
            "classes": {c.lower(): fetch(c) for c in CLASSES}}
    json.dump(data, open(os.path.join(OUT, "tierlist.json"), "w"), indent=1, ensure_ascii=False)
    n = sum(len(s["builds"]) for c in data["classes"].values() for s in c["sections"])
    print(f"JuxtAPoser: {n} vnosov v {len(CLASSES)} razredih")


if __name__ == "__main__":
    main()
