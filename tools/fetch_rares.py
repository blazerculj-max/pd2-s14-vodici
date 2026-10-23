"""Rari, magic predmeti in korupcije pri S13 likih 90+ (pd2.tools) za vsak build.

Za vsak (razred, glavni skill) iz data/pd2tools/stats.json prebere do 80 likov in po slotih
zbere: kakšne kakovosti so predmeti, katere affixe imajo rari, crafti in magic predmeti,
katere korupcije so na predmetih in najboljši primer rara.

Rezultat: data/pd2tools/rares.json
"""
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_pd2tools import OUT, query  # noqa: E402

PAGES, PAGE_SIZE, MIN_N = 2, 40, 8
SLOT = {"Helm": "helm", "Amulet": "amulet", "Armor": "armor", "Right Hand": "weapon", "Left Hand": "offhand",
        "Right Ring": "ring", "Left Ring": "ring", "Belt": "belt", "Boots": "boots", "Gloves": "gloves"}
SKIP = re.compile(r"^(Corrupt|Desecrat|Socketed|Ethereal|Indestructible|Level \d+ .*\(\d+/\d+ Charges\)|Requirements|Repairs)")


def norm(label):
    """»+2 to Sorceress Skill Levels« → »+# to Sorceress Skill Levels«; vrne (oznaka, prva vrednost)."""
    m = re.search(r"\d+", label)
    return re.sub(r"\d+", "#", label), (int(m.group(0)) if m else None)


def collect(chars):
    slots = {}
    for ch in chars:
        for it in ch.get("items", []):
            loc = it.get("location") or {}
            slot = SLOT.get(loc.get("equipment")) if loc.get("zone") == "Equipped" else None
            if not slot:
                continue
            s = slots.setdefault(slot, {"n": 0, "q": {}, "mods": {}, "corr": {}, "corr_items": {}, "cands": []})
            s["n"] += 1
            q = "Runeword" if it.get("is_runeword") else (it.get("quality") or {}).get("name", "?")
            s["q"][q] = s["q"].get(q, 0) + 1
            mods = it.get("modifiers") or []
            if q in ("Rare", "Crafted", "Magic"):
                labels = []
                for md in mods:
                    if md.get("corrupted") or SKIP.match(md.get("label") or ""):
                        continue
                    lab, val = norm(md["label"])
                    s["mods"].setdefault(lab, []).append(val)
                    labels.append(lab)
                s["cands"].append({"labels": labels, "props": [p for p in it.get("properties") or [] if p],
                                   "base": (it.get("base") or {}).get("name"), "q": q, "lvl": ch["character"]["level"]})
            if it.get("corrupted"):
                cn = it.get("corruptions") or []
                if "all_resist" in cn:
                    cl = ["All Resistances +#%"]
                elif "item_numsockets" in cn:
                    cl = ["Sockets"]
                else:
                    cl = sorted({norm(md["label"])[0] for md in mods if md.get("corrupted") and not SKIP.match(md.get("label") or "")})
                for lab in cl or ["(brez učinka)"]:
                    s["corr"][lab] = s["corr"].get(lab, 0) + 1
                    who = it["name"] if q in ("Unique", "Set", "Runeword") else f"{q} {(it.get('base') or {}).get('type') or ''}".strip()
                    k = f"{who}|{lab}"
                    s["corr_items"][k] = s["corr_items"].get(k, 0) + 1
    out = {}
    for slot, s in slots.items():
        mods = sorted(((lab, len(v), statistics.median([x for x in v if x is not None] or [0]), max([x for x in v if x is not None] or [0]))
                       for lab, v in s["mods"].items()), key=lambda x: -x[1])
        top = {m[0] for m in mods[:8]}
        best = max(s["cands"], key=lambda c: (len(top & set(c["labels"])), c["q"] != "Magic", c["lvl"]), default=None)
        out[slot] = {"n": s["n"], "q": s["q"], "rares": len(s["cands"]),
                     "mods": [list(m) for m in mods[:14]],
                     "corr": sorted(s["corr"].items(), key=lambda x: -x[1])[:10],
                     "corr_items": sorted(([*k.split("|"), v] for k, v in s["corr_items"].items()), key=lambda x: -x[2])[:12],
                     "best": {k: best[k] for k in ("props", "base", "q")} if best else None}
    return out


def main(force=False):
    path = os.path.join(OUT, "rares.json")
    cache = json.load(open(path)) if os.path.exists(path) and not force else {}
    stats = json.load(open(os.path.join(OUT, "stats.json")))
    for key, rec in stats.items():
        if key in cache or not rec.get("skill") or (rec.get("n90") or 0) < MIN_N:
            continue
        cls = key.split("|")[0]
        chars = []
        for page in range(1, PAGES + 1):
            d = query("/characters", cls, rec["skill"], 90, 99, {"page": page, "pageSize": PAGE_SIZE}) or {}
            chars += d.get("characters", [])
            if len(d.get("characters", [])) < PAGE_SIZE:
                break
            time.sleep(0.3)
        cache[key] = {"skill": rec["skill"], "chars": len(chars), "slots": collect(chars)}
        json.dump(cache, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
        print(key, len(chars), flush=True)


if __name__ == "__main__":
    main("--force" in sys.argv)
