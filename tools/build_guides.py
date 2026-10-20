"""Podatki za vodiča Mape in Crafting → data/guides.json.

Mape: S14 seznam map in pošasti z odpornostmi (Hiim Maps explorer), orbi, affixi in korupcije map (PD2 wiki),
najhitrejši buildi po mapi (Hiim tier lista).
Crafting: S14 recepti (Hiim), affixi, ki jih craft lahko dobi, in zahtevani alvl (Hiim affixes.json),
korupcije po slotu (PD2 wiki + S14 spremembe iz patch notes).
"""
import html
import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIIM = os.path.join(ROOT, "data", "hiim")
CAT = os.path.join(HIIM, "catalog")
MAPS = os.path.join(HIIM, "maps")
WIKI = os.path.join(ROOT, "data", "wiki", "html")

_spec = importlib.util.spec_from_file_location("tips", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tips.py"))
tips = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tips)

EL = ["phys", "magic", "fire", "light", "cold", "poison"]
NEW_S14 = {"Poisoned Well", "Descent from Mount Arreat", "Dark Temple"}  # patch notes: prvo sezono brez imunitet
MAP_NOTES = {
    "Blood Moon": "Samo Hell Bovine (kravji level) in Cow Queen: brez imunitet, odlično za fizične builde.",
    "Kyovoshad": "Brez imunitet.",
    "Sanatorium": "V S14 premaknjena v T1, manj Soulov.",
}


def load(path):
    return json.load(open(path))


def clean(c):
    c = re.sub(r"<br\s*/?>", " / ", c)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()


def wiki_tables(page):
    """Tabele wiki strani po naslovih razdelkov: {naslov: [tabela, ...]}, tabela = [[celice], ...]."""
    path = os.path.join(WIKI, f"{page}.json")
    if not os.path.exists(path):
        return {}
    h = json.load(open(path))["parse"]["text"]
    out, cur = {}, None
    for part in re.split(r"(<h[2345][^>]*>.*?</h[2345]>)", h, flags=re.S):
        m = re.match(r"<h[2345][^>]*>(.*?)</h[2345]>", part, re.S)
        if m:
            cur = clean(m.group(1)).replace("[edit]", "").strip()
            continue
        for t in re.findall(r"<table.*?</table>", part, re.S):
            rows = [[clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
                    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)]
            out.setdefault(cur, []).append(rows)
    return out


# ---------- mape ----------

def maps_data(site):
    levels = {l["id"]: l for l in load(os.path.join(MAPS, "levels.json"))}
    mons = load(os.path.join(MAPS, "monsters.json"))
    tiers = load(os.path.join(MAPS, "explorer-tiers.json"))
    meta_path = os.path.join(MAPS, "map_meta.json")
    meta = {m["name"]: m for m in load(meta_path)} if os.path.exists(meta_path) else {}
    best = {}
    for c in site["classes"]:
        for b in c["builds"]:
            cl = b.get("clear")
            if cl and cl.get("map"):
                best.setdefault(cl["map"], []).append({"cls": c["id"], "id": b["id"], "name": b["name"], "tier": b["tier"],
                                                       "time": cl["time"], "season": cl.get("season")})
    out = []
    for t in tiers["tiers"]:
        if t.get("auto"):
            continue
        for m in t["maps"]:
            l = levels.get(m["id"])
            if not l:
                continue
            base_name = m["name"].split(" - ")[0]
            ms = []
            for mid in dict.fromkeys(l.get("monsters") or []):
                mo = mons.get(mid)
                if not mo:
                    continue
                ms.append({"name": mo["name"], "res": mo["res"], "u": bool(mo.get("lUndead") or mo.get("hUndead")),
                           "d": bool(mo.get("demon")), "boss": bool(mo.get("boss"))})
            imm = []
            for i, el in enumerate(EL):
                hit = [(x["name"], x["res"][i]) for x in ms if x["res"][i] >= 100]
                if hit:
                    imm.append({"el": el, "res": max(r for _, r in hit), "mon": sorted({n for n, _ in hit})})
            mt = meta.get(m["name"]) or meta.get(base_name.replace("Djinns", "Djinn's")) or {}
            extra = [el for el in (mt.get("elems") or {}) if el not in {x["el"] for x in imm}]
            note = MAP_NOTES.get(m["name"], "")
            if m["name"] in NEW_S14:
                note = "Nova v S14: prvo sezono brez imunitet."
            out.append({
                "tier": t["label"], "zone": l.get("monLvlEx") or l.get("monLvl") or t.get("zoneLevel"),
                "name": m["name"], "slug": mt.get("slug"), "inside": bool(l.get("inside")),
                "imm": imm, "extra": extra, "monsters": ms,
                "undead": sum(1 for x in ms if x["u"]), "demon": sum(1 for x in ms if x["d"]),
                "note": note, "best": sorted(best.get(m["name"], []), key=lambda x: x["time"]),
            })
    return out


def map_tables():
    t = wiki_tables("Maps")
    orbs = []
    for rows in t.get("Modification", [])[:1]:
        for r in rows[1:]:
            cells = [c for c in r if c != ""]
            if len(cells) >= 2:
                orbs.append({"name": cells[0], "with": cells[1], "effect": cells[2] if len(cells) > 2 else ""})
    infuse = []
    for rows in t.get("Modification", [])[1:2]:
        infuse = [{"in": r[0], "out": r[1]} for r in rows[1:] if len(r) >= 2]
    affixes = []
    for rows in t.get("Affixes", [])[:1]:
        head = rows[0]
        for r in rows[1:]:
            if len(r) == len(head):
                affixes.append(dict(zip(["name", "ps", "attr", "range", "exp", "density", "mf", "note"], r)))
    corr = []
    for rows in wiki_tables("Corruption").get("Map Corruptions", [])[:1]:
        head = rows[0]
        for r in rows[1:]:
            corr.append(r)
        corr = {"head": head, "rows": corr}
    return {"orbs": orbs, "infuse": infuse, "affixes": affixes, "corruptions": corr}


# ---------- crafting ----------

ITYPES = load(os.path.join(CAT, "item-types.json"))
SLOT_TYPES = [("amul", "Amulet"), ("ring", "Prstan"), ("glov", "Rokavice"), ("belt", "Pas"), ("boot", "Škornji"),
              ("helm", "Helm"), ("tors", "Oklep"), ("shld", "Ščit")]
WANT = [  # (oznaka, kode modov)
    ("+2 razredni skilli", ["ama", "sor", "nec", "pal", "bar", "dru", "ass"]),
    ("+ drevo skillov", ["skilltab"]),
    ("+ vsi skilli", ["allskills"]),
    ("FCR", ["cast1", "cast2", "cast3"]),
    ("IAS", ["swing1", "swing2", "swing3"]),
    ("FHR", ["balance1", "balance2", "balance3"]),
    ("FRW", ["move1", "move2", "move3"]),
    ("Vsi resi", ["res-all"]),
    ("Max res", ["res-fire-max", "res-cold-max", "res-ltng-max", "res-pois-max"]),
    ("Življenje", ["hp"]),
    ("Moč", ["str"]),
    ("Spretnost", ["dex"]),
    ("Life leech", ["lifesteal"]),
    ("Crushing Blow", ["crush"]),
    ("Deadly Strike", ["deadly"]),
    ("Enhanced Damage", ["dmg%"]),
    ("PDR %", ["red-dmg%"]),
    ("Magic Find", ["mag%"]),
]


def chain(t, acc=None):
    acc = acc if acc is not None else set()
    if t and t not in acc:
        acc.add(t)
        for e in (ITYPES.get(t) or {}).get("equiv") or []:
            chain(e, acc)
    return acc


def craft_affixes():
    """Za vsak craft slot: kateri vredni affixi so možni in od katerega alvl (prvi in najboljši tier)."""
    aff = load(os.path.join(CAT, "affixes.json"))
    rows = [(k, a) for k in ("magicPrefixes", "magicSuffixes") for a in aff[k]]
    out = {}
    for typ, label in SLOT_TYPES:
        ch = chain(typ)
        ok = []
        for kind, a in rows:
            if a.get("frequency", 1) == 0 or not a.get("rare") or a.get("rareOnly"):
                continue  # crafti dobijo le affixe, ki so možni na rare predmetih (ne »dropped rare only«)
            if not any(i in ch for i in a.get("itypes") or []) or any(e in ch for e in a.get("etypes") or []):
                continue
            if any(m.get("code") == "charged" for m in a.get("mods") or []):
                continue
            ok.append(a)
        lst = []
        for name, codes in WANT:
            hits = [a for a in ok if any(m.get("code") in codes for m in a.get("mods") or [])]
            if not hits:
                continue
            hits.sort(key=lambda a: a.get("level", 0))
            first, top = hits[0], hits[-1]
            lst.append({"what": name,
                        "first": {"alvl": first.get("level", 0), "name": first["name"], "text": "; ".join(tips.mods_text(first["mods"]))},
                        "best": {"alvl": top.get("level", 0), "name": top["name"], "text": "; ".join(tips.mods_text(top["mods"]))}})
        out[typ] = {"label": label, "rows": lst}
    return out


def crafts():
    cr = load(os.path.join(CAT, "crafts.json"))
    cats = {}
    for c in cr:
        main, *alt = c.get("ingredients") or [[]]
        cats.setdefault(c["category"], []).append({
            "id": c["id"], "type": c["typeName"], "itype": c["itemType"], "ing": main, "alt": [x for a in alt for x in a],
            "mods": tips.mods_text(c.get("mods") or []), "eth": bool(c.get("ethereal")), "lvl": c.get("playerLevel")})
    return cats


S14_CORR = [  # (slot, besedilo na wikiju (S13), novo besedilo)
    ("*", "Indestructible", "Repairs durability (S14)"),
    ("Boots", "Replenish Life +[15-25]", "Half Freeze Duration (S14)"),
    ("Gloves", "Replenish Life +[15-20]", "Half Freeze Duration (S14)"),
    ("Belt", "Replenish Life +[15-20]", "Half Freeze Duration (S14)"),
    ("Shield", "+10% Curse Resistance", "+[15-25]% Curse Resistance (S14)"),
    ("Helm", "+10% Curse Resistance", "+[10-20]% Curse Resistance (S14)"),
]


def corruptions():
    t = wiki_tables("Corruption")
    out = []
    for sec, tables in t.items():
        if not sec or not sec.endswith("Corruption Mods"):
            continue
        slot = sec.replace(" Corruption Mods", "")
        rows = [list(r) for r in tables[0]]
        head, body = rows[0], rows[1:]
        for r in body:
            for i, cell in enumerate(r):
                for s, old, new in S14_CORR:
                    if (s == "*" or s == slot) and old in cell:
                        r[i] = cell = cell.replace(old, new)
        if slot == "Chest":  # S14: curse res T3 → T2 (+10-20 %), FCR T2 → T3 (+20 %)
            for r in body:
                if len(r) == 3 and "Faster Cast Rate" in r[1] and "Curse Resistance" in r[2]:
                    r[1], r[2] = "+[10-20]% Curse Resistance (S14)", "+20% Faster Cast Rate (S14)"
        out.append({"slot": slot, "head": head, "rows": body})
    return out


def main():
    site = load(os.path.join(ROOT, "data", "site.json"))
    g = {"maps": maps_data(site), "map_tables": map_tables(), "crafts": crafts(), "craft_affixes": craft_affixes(),
         "corruptions": corruptions()}
    json.dump(g, open(os.path.join(ROOT, "data", "guides.json"), "w"), indent=1, ensure_ascii=False)
    print(f"mape: {len(g['maps'])}, orbi: {len(g['map_tables']['orbs'])}, affixi map: {len(g['map_tables']['affixes'])}, "
          f"crafti: {sum(len(v) for v in g['crafts'].values())}, korupcije: {len(g['corruptions'])} slotov")


if __name__ == "__main__":
    main()
