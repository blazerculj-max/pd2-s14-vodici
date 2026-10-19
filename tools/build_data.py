"""Združi Hiim tier liste, planerje, katalog in pd2.tools statistiko v data/site.json.

Zapiše tudi data/images.json: seznam slik (poti pod hiimpd2.com/planner-art/), ki jih stran rabi.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIIM = os.path.join(ROOT, "data", "hiim")
CAT = os.path.join(HIIM, "catalog")
PD2T = os.path.join(ROOT, "data", "pd2tools")

CLASSES = [
    ("amazon", "Amazon"), ("assassin", "Assassin"), ("barbarian", "Barbarian"), ("druid", "Druid"),
    ("necromancer", "Necromancer"), ("paladin", "Paladin"), ("sorceress", "Sorceress"),
]
VIABLE = ["Top", "Good", "Decent", "Utility"]
TIER_RANK = {"Top": 0, "Good": 1, "Decent": 2, "Utility": 3, "Mid": 4, "Bad": 5}
MAPS = {
    "throne": "Throne of Insanity", "riverblood": "River of Blood", "sewers": "Sewers of Harrogath",
    "ancestral": "Ancestral Trial", "canyon": "Canyon of Sescheron", "kyovoshad": "Kyovoshad",
    "citadel": "Pandemonium Citadel", "phlegethon": "Phlegethon", "torajanjungle": "Torajan Jungle",
    "bloodmoon": "Blood Moon", "zoltun": "Tomb of Zoltun Kulle", "cistern": "Ruined Cistern",
    "caldeum": "Fall of Caldeum", "sanctuaryofsin": "Sanctuary of Sin",
}
SLOTS = ["weapon", "offhand", "helm", "armor", "gloves", "belt", "boots", "amulet", "ring1", "ring2",
         "swapWeapon", "swapOffhand"]
GENERIC_IMG = {"amu": "items/amulet/Amulet_1.png", "rin": "items/ring/Ring_1.png"}

import hashlib
import importlib.util

_spec = importlib.util.spec_from_file_location("tips", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tips.py"))
tips = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tips)
TIPS = {}
TIP_NAMES = {}

images = set()
need_bases = set()
_bi = os.path.join(ROOT, "data", "base_images.json")
FOUND_BASE_IMG = json.load(open(_bi)) if os.path.exists(_bi) else {}


def load(name):
    return json.load(open(os.path.join(CAT, f"{name}.json")))


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ---------- katalog ----------
items_cat = load("items")
UNIQ = {i["id"]: i for i in items_cat["items"]}
RW = {r["id"]: r for r in load("runewords")}
SET_OF = {i: st["name"] for st in items_cat["sets"] for i in st.get("items", [])}
SOCK = {s["id"]: s for s in load("socketables")}
PRESET = {p["id"]: p for p in load("presets")}
CHARM = {c["id"]: c for c in load("charms")}
BASES = {b["code"]: b for b in load("bases")}
MERC = {m["id"]: m for m in load("mercs")["mercs"]}
CORR = {}
_corr = load("corruptions")
for group in ("corruptions", "desecrations"):
    block = _corr.get(group)
    rows = block if isinstance(block, list) else [v for vals in (block or {}).values() for v in (vals if isinstance(vals, list) else [vals])]
    for c in rows:
        if isinstance(c, dict) and c.get("id"):
            CORR[c["id"]] = c.get("label") or c.get("name") or c.get("text") or c["id"]
SKILLS = {}
for cls, _ in CLASSES:
    for s in load(f"skills.{cls}")["skills"]:
        SKILLS[(cls, s["id"])] = s
BASE_IMG = {}
for p in PRESET.values():
    if p.get("base") and p.get("image"):
        BASE_IMG.setdefault(p["base"], p["image"])
for u in UNIQ.values():
    if u.get("base") and u.get("image") and "/special/" not in u["image"]:
        BASE_IMG.setdefault(u["base"], u["image"])


def img(path):
    if path:
        images.add(path)
    return path


def base_img(code):
    if not code:
        return None
    path = BASE_IMG.get(code) or FOUND_BASE_IMG.get(code)
    if not path and code not in FOUND_BASE_IMG:
        need_bases.add(code)
    return img(path)


def base_name(code):
    b = BASES.get(code)
    return b["name"] if b else None


def tip_unique(it):
    key = f"u:{it['id']}"
    if key not in TIPS:
        TIPS[key] = tips.unique_tip(it, SET_OF.get(it["id"]))
        TIP_NAMES.setdefault(it["name"].lower(), key)
    return key


def tip_runeword(rw):
    key = f"rw:{rw['id']}"
    if key not in TIPS:
        names = [(SOCK.get(r) or {}).get("name", r).replace(" Rune", "") for r in rw.get("runes", [])]
        TIPS[key] = tips.runeword_tip(rw, names)
        TIP_NAMES.setdefault(rw["name"].lower(), key)
    return key


def tip_socket(sid):
    key = f"so:{sid}"
    if key not in TIPS and SOCK.get(sid):
        TIPS[key] = tips.socket_tip(SOCK[sid])
    return key if key in TIPS else None


def resolve_item(g):
    """Planner zapis predmeta → {name, q, img, runes, base, eth, corr}."""
    if not isinstance(g, dict) or not g.get("kind"):
        return None
    kind = g["kind"]
    out = {"eth": bool(g.get("eth"))}
    if g.get("corruption"):
        out["corr"] = CORR.get(g["corruption"].get("id"), None)
    if kind in ("unique", "set"):
        it = UNIQ.get(g.get("id"))
        if not it:
            return None
        out.update(name=it["name"], q="u" if it["kind"] == "unique" else "s", img=img(it.get("image")),
                   req=it.get("reqLevel"), base=it.get("baseName"))
        out["tip"] = tip_unique(it)
    elif kind == "runeword":
        rw = RW.get(g.get("id"))
        if not rw:
            return None
        runes = []
        for rid in rw.get("runes", []):
            s = SOCK.get(rid)
            runes.append({"name": s["name"].replace(" Rune", "") if s else rid, "img": img(s.get("image")) if s else None})
        bcode = g.get("base")
        out.update(name=rw["name"], q="r", runes=runes, base=base_name(bcode), img=base_img(bcode))
        out["tip"] = tip_runeword(rw)
        for r, rid in zip(out["runes"], rw.get("runes", [])):
            r["tip"] = tip_socket(rid)
    elif kind == "preset":
        p = PRESET.get(g.get("id")) or CHARM.get(g.get("id"))
        if not p:
            return None
        rarity = p.get("rarity", "magic")
        q = {"magic": "m", "rare": "y", "crafted": "c", "unique": "u", "set": "s"}.get(rarity, "m")
        out.update(name=p["name"], q=q, img=img(p.get("image")), req=p.get("reqLevel"), base=p.get("baseName"))
        key = f"p:{p['id']}"
        if key not in TIPS:
            TIPS[key] = tips.preset_tip(p, q)
        out["tip"] = key
    elif kind == "custom":
        it = g.get("item") or {}
        q = {"magic": "m", "rare": "y", "crafted": "c", "unique": "u", "set": "s"}.get(it.get("quality"), "y")
        code = it.get("base")
        out.update(name=it.get("name") or base_name(code) or "Rare", q=q, base=base_name(code),
                   img=img(GENERIC_IMG.get(code)) or base_img(code))
        key = "c:" + hashlib.sha1(json.dumps(it, sort_keys=True).encode()).hexdigest()[:12]
        if key not in TIPS:
            TIPS[key] = tips.custom_tip(it, q, base_name(code))
        out["tip"] = key
    else:
        return None
    socks = {}
    for s in g.get("sockets") or []:
        so = SOCK.get(s.get("id"))
        if so:
            rec = socks.setdefault(so["name"], {"name": so["name"], "img": img(so.get("image")), "n": 0, "tip": tip_socket(so["id"])})
            rec["n"] += 1
    if socks:
        out["sockets"] = list(socks.values())
    if out.get("name") and "craft" in out["name"].lower() and out.get("q") in ("m", "y"):
        out["q"] = "c"
    if out.get("corr"):
        c = out["corr"].lstrip("+ ").strip()
        out["corr"] = "socketi" if c.lower().startswith("sockets") else c
    return out


def skill_info(cls, sid):
    s = SKILLS.get((cls, sid))
    if not s:
        return {"id": sid, "name": sid.replace("_", " ").title(), "req": None, "img": None}
    path = f"skills/{cls}/{s['name']}.png"
    syn = [SKILLS[(cls, x["skill"])]["name"] for x in s.get("synergies") or [] if (cls, x.get("skill")) in SKILLS]
    key = f"sk:{cls}:{sid}"
    if key not in TIPS:
        t = tips.skill_tip(cls, sid)
        if t:
            TIPS[key] = t
    return {"id": sid, "name": s["name"], "req": s.get("reqLevel"), "img": img(path), "syn": syn,
            "tip": key if key in TIPS else None}


def resolve_planner(cls, content, label, title=None):
    skills = [dict(skill_info(cls, k), pts=v) for k, v in (content.get("skills") or {}).items() if v]
    skills.sort(key=lambda s: (-s["pts"], s["name"]))
    gear = {}
    for slot in SLOTS:
        r = resolve_item((content.get("gear") or {}).get(slot))
        if r:
            gear[slot] = r
    merc = None
    m = content.get("merc")
    if isinstance(m, dict) and m.get("type"):
        info = MERC.get(m["type"], {})
        mg = {}
        for slot, g in (m.get("gear") or {}).items():
            r = resolve_item(g)
            if r:
                mg[slot] = r
        merc = {"type": m["type"], "name": info.get("name") or m["type"], "aura": info.get("label"), "gear": mg}
    charms = []
    for c in content.get("charms") or []:
        r = resolve_item(c)
        if r and r.get("q") == "u":
            charms.append(r)
    level = content.get("level")
    return {"label": label, "title": title, "level": level, "stats": content.get("statPoints"),
            "skills": skills, "gear": gear, "merc": merc, "charms": charms,
            "phase": phase_of(label, title, level),
            "progression": [{"skill": skill_info(cls, r["skill"])["name"], "target": r["target"]}
                            for r in ((content.get("progression") or {}).get("rules") or [])]}


def phase_of(label, title, level):
    t = f"{label or ''} {title or ''}".lower()
    if any(k in t for k in ("day 1", "starter", "start", "base")):
        return "start"
    if any(k in t for k in ("day 2", "pre-end", "pre end", "mid")):
        return "mid"
    if any(k in t for k in ("end", "aspir")):
        return "end"
    if level and level <= 80:
        return "start"
    if level and level <= 90:
        return "mid"
    return "end"


def planners_for(entry, cls):
    seen, out = set(), []
    refs = []
    if entry.get("buildId"):
        refs.append((entry["buildId"], "Planner"))
    for link in entry.get("links") or []:
        if link.get("kind") == "planner" and link.get("buildId"):
            refs.append((link["buildId"], link.get("label") or "Planner"))
    # povezava z imenom ima prednost pred generično »Planner«
    labels = {}
    for bid, label in refs:
        if bid not in labels or labels[bid] == "Planner":
            labels[bid] = label
    for bid, label in labels.items():
        if bid in seen:
            continue
        seen.add(bid)
        path = os.path.join(HIIM, "builds", f"{bid}.json")
        if not os.path.exists(path):
            continue
        rec = json.load(open(path))["build"]
        b = rec["build"]
        if b.get("class") != cls:
            continue
        name = rec.get("name") or label
        p = resolve_planner(cls, b, label, name)
        p.update(id=bid, url=f"https://hiimpd2.com/b/{bid}", author=rec.get("ownerDisplayName"),
                 video=rec.get("videoUrl"))
        out.append(p)
        for st in b.get("stages") or []:
            sp = resolve_planner(cls, st.get("content") or {}, st.get("title") or "Stage", st.get("title"))
            sp.update(id=f"{bid}-{st.get('id')}", url=f"https://hiimpd2.com/b/{bid}", author=rec.get("ownerDisplayName"))
            out.append(sp)
    order = {"start": 0, "mid": 1, "end": 2}
    out.sort(key=lambda p: (order[p["phase"]], p.get("level") or 0))
    return out


def tags_of(notes):
    m = re.search(r"Tags:\s*(.+)", notes or "")
    return [t.strip() for t in m.group(1).split(",")] if m else []


def main():
    tiers = {name: json.load(open(os.path.join(HIIM, f"tiers_{name}.json")))["entries"]
             for name in ["solo", "starter", "boss", "group-generalist", "group-physical", "group-elemental"]}
    stats = json.load(open(os.path.join(PD2T, "stats.json")))
    respec_path = os.path.join(PD2T, "respec.json")
    respec = json.load(open(respec_path)) if os.path.exists(respec_path) else {}

    site = {"classes": [], "updated": max(e["updatedAt"] for e in tiers["solo"])[:10]}
    for cls, cname in CLASSES:
        starters = [e for e in tiers["starter"] if e["className"].lower() == cls and not e.get("hidden")]
        starter_by_skill = {e["mainSkill"]: e for e in starters}
        boss = {}
        for e in tiers["boss"]:
            if e["className"].lower() == cls and e.get("mainSkill") and not e.get("hidden"):
                boss.setdefault(e["mainSkill"], {})[e["boss"]] = {"t0": e.get("tier"), "t2": e.get("t2Tier"), "name": e["buildName"]}
        group = {}
        for lst in ("group-generalist", "group-physical", "group-elemental"):
            for e in tiers[lst]:
                if e["className"].lower() == cls and e.get("mainSkill") and e.get("tier") and not e.get("hidden"):
                    group.setdefault(e["mainSkill"], []).append({"list": lst.split("-")[1], "tier": e["tier"], "name": e["buildName"]})

        builds, others = [], []
        entries = [e for e in tiers["solo"] if e["className"].lower() == cls and not e.get("hidden")]
        used_starters = set()
        for e in entries:
            tier = e.get("tier")
            if tier not in VIABLE and e["buildName"] != "Pure Poison Creeper":
                if tier:
                    others.append({"name": e["buildName"], "tier": tier})
                continue
            main_skill = e.get("mainSkill")
            st = starter_by_skill.get(main_skill)
            if st:
                used_starters.add(st["entryId"])
            key = f"{cname}|{main_skill}"
            clear = e.get("bestClear") or e.get("fallbackClear")
            b = {
                "id": slug(e["buildName"]), "name": e["buildName"], "tier": tier or "Brez ocene",
                "sort": TIER_RANK.get(tier, 6) * 1000 + (e.get("sortOrder") or 0),
                "main": skill_info(cls, main_skill) if main_skill else None,
                "clear": {"map": MAPS.get(clear["map"], clear["map"]), "time": round(clear["clearTimeMs"] / 1000),
                          "season": clear.get("season"), "player": clear.get("player"), "video": clear.get("videoUrl")} if clear else None,
                "starter": {"name": st["buildName"], "tags": tags_of(st.get("notes"))} if st else None,
                "boss": boss.get(main_skill, {}),
                "group": group.get(main_skill, []),
                "stats": stats.get(key) if stats.get(key, {}).get("skill") else None,
                "respec": respec.get(key),
                "planners": planners_for(e, cls) + (planners_for(st, cls) if st else []),
                "links": [l for l in (e.get("links") or []) if l.get("kind") != "planner"],
                "notes": e.get("notes") or "",
            }
            builds.append(b)
        # starterji, ki niso na solo listi
        for st in starters:
            if st["entryId"] in used_starters:
                continue
            main_skill = st.get("mainSkill")
            key = f"{cname}|{main_skill}"
            builds.append({
                "id": slug(st["buildName"]), "name": st["buildName"], "tier": "Starter", "sort": 3500 + (st.get("sortOrder") or 0),
                "main": skill_info(cls, main_skill) if main_skill else None, "clear": None,
                "starter": {"name": st["buildName"], "tags": tags_of(st.get("notes"))},
                "boss": boss.get(main_skill, {}), "group": group.get(main_skill, []),
                "stats": stats.get(key) if stats.get(key, {}).get("skill") else None,
                "respec": respec.get(key), "planners": planners_for(st, cls),
                "links": [l for l in (st.get("links") or []) if l.get("kind") != "planner"], "notes": "",
            })
        builds.sort(key=lambda b: b["sort"])
        ids = set()
        for b in builds:
            while b["id"] in ids:
                b["id"] += "-2"
            ids.add(b["id"])
        site["classes"].append({"id": cls, "name": cname, "builds": builds, "others": others,
                                "starters": [s["buildName"] for s in starters]})
    json.dump(site, open(os.path.join(ROOT, "data", "site.json"), "w"), indent=1)
    json.dump(sorted(images), open(os.path.join(ROOT, "data", "images.json"), "w"), indent=1)
    json.dump(sorted(need_bases), open(os.path.join(ROOT, "data", "base_codes.json"), "w"), indent=1)
    for it in UNIQ.values():
        tip_unique(it)
    for rw in RW.values():
        tip_runeword(rw)
    for c in CHARM.values():
        if c.get("rarity") == "unique":
            key = f"p:{c['id']}"
            if key not in TIPS:
                TIPS[key] = tips.preset_tip(c, "u")
            TIP_NAMES.setdefault(c["name"].lower(), key)
    os.makedirs(os.path.join(ROOT, "docs", "assets"), exist_ok=True)
    json.dump(TIPS, open(os.path.join(ROOT, "docs", "assets", "tips.json"), "w"), separators=(",", ":"))
    json.dump(TIP_NAMES, open(os.path.join(ROOT, "data", "tip_names.json"), "w"), indent=1)
    print(f"tooltipov: {len(TIPS)}")
    n = sum(len(c["builds"]) for c in site["classes"])
    print(f"buildov: {n}, slik: {len(images)}")
    for c in site["classes"]:
        print(c["name"], len(c["builds"]), [b["name"] for b in c["builds"]][:12])


if __name__ == "__main__":
    main()
