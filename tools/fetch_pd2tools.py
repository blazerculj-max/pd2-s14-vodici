"""S13 statistika s pd2.tools za vsak build iz Hiim list.

Za vsak (razred, glavni skill) zabeleži število likov z 20 točkami v skillu na levelih
80-89, 90-99 in 95-99, najpogostejše iteme in merce. Z --respec pa še, ali so najhitrejši
igralci imeli build že ob prvem posnetku (level 80-85, prvih 4,5 dneva sezone).

Poleg tega shrani še splošno uporabo predmetov (vsi liki 90-99) za wiki predmetov.

Rezultat: data/pd2tools/stats.json, item_usage.json, skill_usage.json (in respec.json)
"""
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIIM = os.path.join(ROOT, "data", "hiim")
OUT = os.path.join(ROOT, "data", "pd2tools")
API = "https://api.pd2.tools/api/v1"
SEASON = 13
SEASON_START = datetime.datetime(2026, 4, 24, tzinfo=datetime.timezone.utc).timestamp() * 1000
VIABLE = {"Top", "Good", "Decent", "Utility"}
# Hiim (S14) imena, ki jih pd2.tools (S13) piše drugače
ALIASES = {
    "Summon Ravens": ["Raven"],
    "Raise Skeleton Warrior": ["Raise Skeleton"],
    "Claw and Dagger Mastery": ["Claw Mastery"],
    "War Cry": ["Warcry"],
    "Fire Claws": ["Fire Claws", "Fireclaw"],
    "Enchant Fire": ["Enchant", "Fire Enchant"],
}


def curl_json(url):
    for attempt in range(3):
        out = subprocess.run(["curl", "-sL", "-m", "90", url], capture_output=True, text=True).stdout
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            time.sleep(2 + attempt * 3)
    return None


def skill_names():
    names = {}
    for cls in ["amazon", "assassin", "barbarian", "druid", "necromancer", "paladin", "sorceress"]:
        for s in json.load(open(os.path.join(HIIM, "catalog", f"skills.{cls}.json")))["skills"]:
            names[(cls, s["id"])] = s["name"]
    return names


def build_pairs():
    pairs = {}
    for lst in ["solo", "starter"]:
        for e in json.load(open(os.path.join(HIIM, f"tiers_{lst}.json")))["entries"]:
            if not e.get("mainSkill"):
                continue
            if lst == "solo" and e.get("tier") not in VIABLE and e["buildName"] != "Pure Poison Creeper":
                continue
            pairs[(e["className"], e["mainSkill"])] = True
    return list(pairs)


def query(path, cls, skill, lo, hi, extra=None):
    params = {"gameMode": "softcore", "classes": cls, "items": "", "mercTypes": "", "mercItems": "",
              "skills": json.dumps([{"name": skill, "minLevel": 20}]), "minLevel": lo, "maxLevel": hi,
              "season": SEASON}
    params.update(extra or {})
    return curl_json(f"{API}{path}?" + urllib.parse.urlencode(params))


def total(cls, skill, lo, hi):
    d = query("/characters", cls, skill, lo, hi, {"page": 1, "pageSize": 1})
    return (d or {}).get("total", 0)


def stats(force=False):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "stats.json")
    cache = json.load(open(path)) if os.path.exists(path) and not force else {}
    names = skill_names()
    for cls, main in build_pairs():
        key = f"{cls}|{main}"
        if key in cache:
            continue
        hiim_name = names.get((cls.lower(), main), main.replace("_", " ").title())
        rec = {"skill": None}
        for cand in [hiim_name] + ALIASES.get(hiim_name, []):
            n90 = total(cls, cand, 90, 99)
            if n90 > 0:
                rec = {"skill": cand, "n80": total(cls, cand, 80, 89), "n90": n90, "n95": total(cls, cand, 95, 99)}
                items = query("/characters/stats/item-usage", cls, cand, 90, 99) or []
                mercs = query("/characters/stats/merc-type-usage", cls, cand, 90, 99) or []
                rec["items"] = [[x["item"], round(x["pct"])] for x in items[:15]]
                rec["mercs"] = [[x.get("name") or x.get("mercType"), round(x["pct"])] for x in mercs[:3]]
                break
        cache[key] = rec
        json.dump(cache, open(path, "w"), indent=1)
        print(key, rec.get("skill"), rec.get("n90"), flush=True)
        time.sleep(0.1)


def respec(force=False):
    path = os.path.join(OUT, "respec.json")
    cache = json.load(open(path)) if os.path.exists(path) and not force else {}
    st = json.load(open(os.path.join(OUT, "stats.json")))
    for key, rec in st.items():
        if key in cache or not rec.get("skill") or rec.get("n90", 0) < 15:
            continue
        cls = key.split("|")[0]
        d = query("/characters", cls, rec["skill"], 90, 99, {"page": 1, "pageSize": 20}) or {}
        early = same = 0
        days95 = []
        first_main = {}
        for c in d.get("characters", []):
            name = urllib.parse.quote(c["character"]["name"])
            sn = (curl_json(f"{API}/characters/{name}/snapshots?gameMode=softcore&season={SEASON}") or {}).get("snapshots", [])
            if not sn:
                continue
            sn.sort(key=lambda s: s["snapshot_timestamp"])
            if (sn[0]["snapshot_timestamp"] - SEASON_START) / 864e5 > 4.5:
                continue
            early += 1
            for s in sn:
                if s["level"] >= 95:
                    days95.append((s["snapshot_timestamp"] - SEASON_START) / 864e5)
                    break
            snap = curl_json(f"{API}/characters/{name}/snapshots/{sn[0]['snapshot_id']}") or {}
            mains = [s["skill"] for s in snap.get("realSkills", []) if s["baseLevel"] >= 15]
            if rec["skill"] in mains:
                same += 1
            for m in mains:
                first_main[m] = first_main.get(m, 0) + 1
            time.sleep(0.05)
        days95.sort()
        cache[key] = {"early": early, "same": same,
                      "day95": round(days95[len(days95) // 2], 1) if days95 else None,
                      "firstSkills": sorted(first_main.items(), key=lambda kv: -kv[1])[:6]}
        json.dump(cache, open(path, "w"), indent=1)
        print(key, cache[key]["same"], "/", cache[key]["early"], flush=True)


def usage(force=False):
    """Delež likov 90-99 (vsi razredi), ki nosijo posamezen predmet."""
    path = os.path.join(OUT, "item_usage.json")
    if os.path.exists(path) and not force:
        return
    params = {"gameMode": "softcore", "classes": "", "items": "", "mercTypes": "", "mercItems": "",
              "minLevel": 90, "maxLevel": 99, "season": SEASON}
    rows = curl_json(f"{API}/characters/stats/item-usage?" + urllib.parse.urlencode(params)) or []
    out = {"total": rows[0]["totalSample"] if rows else 0,
           "items": {x["item"]: round(x["pct"], 1) for x in rows}}
    json.dump(out, open(path, "w"), indent=1)
    print("item usage:", len(out["items"]), "predmetov,", out["total"], "likov")


def skill_usage(force=False):
    """Delež likov 90-99 po razredu, ki imajo skill na 20 (za builde, ki jih Hiim nima)."""
    path = os.path.join(OUT, "skill_usage.json")
    if os.path.exists(path) and not force:
        return
    out = {}
    for cls in ["Amazon", "Assassin", "Barbarian", "Druid", "Necromancer", "Paladin", "Sorceress"]:
        params = {"gameMode": "softcore", "classes": cls, "items": "", "mercTypes": "", "mercItems": "",
                  "minLevel": 90, "maxLevel": 99, "season": SEASON}
        rows = curl_json(f"{API}/characters/stats/skill-usage?" + urllib.parse.urlencode(params)) or []
        out[cls] = {"total": rows[0]["totalSample"] if rows else 0, "skills": {x["name"]: round(x["pct"], 1) for x in rows}}
    json.dump(out, open(path, "w"), indent=1)
    print("skill usage:", {k: v["total"] for k, v in out.items()})


if __name__ == "__main__":
    if "--respec" in sys.argv:
        respec("--force" in sys.argv)
    else:
        stats("--force" in sys.argv)
        usage("--force" in sys.argv)
        skill_usage("--force" in sys.argv)
