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
GENERIC_IMG = {"amu": "items/amulet/Amulet_1.png", "rin": "items/ring/Ring_1.png",
               "amul": "items/amulet/Amulet_1.png", "ring": "items/ring/Ring_1.png"}

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
        out.update(name=rw["name"], q="r", runes=runes, base=base_name(bcode), img=base_img(bcode), bc=bcode)
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


# ---------- recepti (wiki: Horadric cube, Hiim: crafti) ----------
ITYPES = load("item-types")
CRAFTS = load("crafts")
RUNE_RANK = {s["id"]: int(s["code"][1:]) for s in SOCK.values() if s.get("kind") == "rune" and s.get("code")}
CRAFT_TYPE = {"weapon": "weap", "swapWeapon": "weap", "offhand": "shld", "swapOffhand": "shld", "helm": "helm",
              "armor": "tors", "gloves": "glov", "belt": "belt", "boots": "boot", "amulet": "amul",
              "ring1": "ring", "ring2": "ring"}
SOCKET_KIND_SL = {"weapon": "orožje", "shield": "ščit", "chest": "oklep", "helm": "čelada"}


def type_is(t, target, depth=0):
    if t == target:
        return True
    if depth > 8:
        return False
    return any(type_is(e, target, depth + 1) for e in (ITYPES.get(t) or {}).get("equiv") or [])


def type_chain(t, acc=None):
    acc = acc if acc is not None else []
    if t and t not in acc:
        acc.append(t)
        for e in (ITYPES.get(t) or {}).get("equiv") or []:
            type_chain(e, acc)
    return acc


def max_sockets(b):
    ms = (ITYPES.get(b["type"]) or {}).get("maxSockets")
    return min(b.get("sockets") or 0, ms[2]) if ms else (b.get("sockets") or 0)


def socket_kind(code):
    b = BASES.get(code)
    if not b:
        return None
    if b["kind"] == "weapon":
        return "weapon"
    if type_is(b["type"], "shld"):
        return "shield"
    if type_is(b["type"], "helm"):
        return "helm"
    if b["type"] == "tors":
        return "chest"
    return None


def cube_recipes():
    path = os.path.join(ROOT, "data", "wiki", "Horadric_cube.txt")
    txt = open(path).read() if os.path.exists(path) else ""
    sock = {}
    for m in re.finditer(r"\| ([\w' ]+ Rune \+ [\w' ]+ Rune \+ Perfect \w+) \+ Standard/Superior Regular ([\w/]+)\s*\n \| Adds (\d+)-(\d+) sockets", txt):
        for kind in m.group(2).lower().split("/"):
            sock[kind] = {"recipe": m.group(1).replace(" Rune", ""), "lo": int(m.group(3)), "hi": int(m.group(4))}
    upgrade = {}
    for m in re.finditer(r"\| ([\w' ]+ Rune \+ [\w' ]+ Rune \+ Perfect \w+) \+ (Normal|Exceptional) (Unique/Set|Rare/Crafted) ([\w/]+)\s*\n", txt):
        for kind in m.group(4).lower().split("/"):
            upgrade[(m.group(3).split("/")[0].lower(), kind, m.group(2).lower())] = m.group(1).replace(" Rune", "")
    promote = {}
    for m in re.finditer(r"\| (\d) (\w+) Runes \(#\d+\) \+ Key\s*\n \| 1 (\w+) Rune", txt):
        promote[m.group(3)] = f"{m.group(1)}× {m.group(2)}"  # S14: za recepte s stacki ključ ni več potreben
    return sock, upgrade, promote


SOCKET_RECIPE, UPGRADE_RECIPE, RUNE_PROMOTE = cube_recipes()


def craft_for(name, slot):
    """Craft preset (npr. »Caster Craft Gloves«) → recept iz crafts.json."""
    m = re.match(r"(\w+) Craft", name or "")
    itype = CRAFT_TYPE.get(slot)
    if not m or not itype:
        return None
    for c in CRAFTS:
        if c["category"].lower() == m.group(1).lower() and c["itemType"] == itype:
            return c
    return None


def craft_tip(c):
    key = f"cr:{c['id']}"
    if key not in TIPS:
        main, *alt = c.get("ingredients") or [[]]
        extra = ["Kocka: " + " + ".join(main + [f"magic/rare {c['typeName'].lower()}"])]
        extra += ["ali: " + " + ".join(a + [f"magic/rare {c['typeName'].lower()}"]) for a in alt]
        extra.append(f"Ilvl craft = clvl/2 + ilvl/2 · do 4 dodatni affixi")
        TIPS[key] = tips.tip_html(c["name"], "c", base=c["typeName"] + (" (brez circletov)" if "circ" in (c.get("excludeTypes") or []) else ""),
                                  req=None, lines=tips.mods_text(c.get("mods") or []), extra=extra, extra_title="Recept",
                                  extra_cls="tt-rec")
    return key


def base_tip(b):
    key = f"b:{b['code']}"
    if key not in TIPS:
        info = []
        if b.get("damage"):
            info.append(f"Damage: {b['damage'][0]}-{b['damage'][1]}")
        if b.get("defense"):
            info.append(f"Defense: {b['defense'][0]}-{b['defense'][1]}")
        if b.get("block"):
            info.append(f"Block: {b['block']}%")
        if b.get("reqStr"):
            info.append(f"Required Strength: {b['reqStr']}")
        if b.get("reqDex"):
            info.append(f"Required Dexterity: {b['reqDex']}")
        t = (ITYPES.get(b["type"]) or {}).get("name") or b["type"]
        TIPS[key] = tips.tip_html(b["name"], "n", base=f"{t} · {b['tier']}", req=b.get("levelReq") or None, info=info,
                                  lines=[f"Max socketov: {max_sockets(b)}"])
    return key


def rune_name(rid):
    return (SOCK.get(rid) or {}).get("name", rid).replace(" Rune", "")


def planner_recipes(p):
    """Runewordi, crafti in rune enega planerja."""
    rws, crafts, runes = [], [], {}

    def add_rune(rid, why):
        s = SOCK.get(rid)
        if not s:
            return
        r = runes.setdefault(rid, {"name": rune_name(rid), "img": s.get("image"), "tip": tip_socket(rid), "n": 0,
                                   "rank": RUNE_RANK.get(rid, 0), "for": []})
        r["n"] += 1
        if why.startswith(("socket:", "craft:")):
            r["sn"] = r.get("sn", 0) + 1
        if why not in r["for"]:
            r["for"].append(why)

    for owner, gear in (("", p["gear"]), ("merc", ((p.get("merc") or {}).get("gear") or {}))):
        for slot, it in gear.items():
            who = f"merc {slot}" if owner else slot
            if it.get("tip", "").startswith("rw:"):
                rw = RW.get(it["tip"][3:])
                if rw:
                    for rid in rw["runes"]:
                        add_rune(rid, rw["name"])
                    b = BASES.get(it.get("bc")) or {}
                    kind = socket_kind(it.get("bc"))
                    sr = SOCKET_RECIPE.get(kind)
                    n = len(rw["runes"])
                    rws.append({"name": rw["name"], "tip": it["tip"], "slot": who, "base": it.get("base"), "n": n,
                                "eth": bool(it.get("eth")),
                                "runes": [rune_name(r) for r in rw["runes"]],
                                "larzuk": bool(b) and max_sockets(b) == n,
                                "cube": f"{sr['recipe']} + {SOCKET_KIND_SL[kind]} (naključno {sr['lo']}–{min(sr['hi'], max_sockets(b) or sr['hi'])})" if sr and b else None})
            for so in it.get("sockets") or []:
                sid = (so.get("tip") or "")[3:]
                if sid in RUNE_RANK:
                    for _ in range(so["n"]):
                        add_rune(sid, f"socket: {who}")
            if it.get("q") == "c":
                c = craft_for(it["name"], slot)
                if c:
                    main, *alt = c["ingredients"]
                    for ing in main:
                        rid = slug(ing).replace("-", "_")
                        if rid in RUNE_RANK:
                            add_rune(rid, f"craft: {it['name']}")
                    crafts.append({"name": it["name"], "tip": craft_tip(c), "slot": who, "type": c["typeName"],
                                   "ing": main, "alt": [a for alt_ in alt for a in alt_],
                                   "eth": bool(c.get("ethereal")), "lvl": c.get("playerLevel")})
    rl = sorted(runes.values(), key=lambda r: r["rank"])
    for r in rl:
        img(r["img"])
    return {"runes": rl, "rw": rws, "crafts": crafts} if (rl or rws or crafts) else None


def build_runes_total(b):
    """Rune za vse faze builda: vsak runeword šteje enkrat (največ kosov v eni fazi), socketi in crafti prav tako."""
    rw_need, sock_need = {}, {}
    for p in b["planners"]:
        rec = p.get("recipes")
        if not rec:
            continue
        per = {}
        for rw in rec["rw"]:
            per[rw["tip"]] = per.get(rw["tip"], 0) + 1
        for key, cnt in per.items():
            rw_need[key] = max(rw_need.get(key, 0), cnt)
        for r in rec["runes"]:
            if r.get("sn"):
                sock_need[r["tip"]] = max(sock_need.get(r["tip"], 0), r["sn"])
    total = {}
    for key, cnt in rw_need.items():
        for rid in RW[key[3:]]["runes"]:
            total[rid] = total.get(rid, 0) + cnt
    for key, cnt in sock_need.items():
        total[key[3:]] = total.get(key[3:], 0) + cnt
    out = []
    for rid, n in sorted(total.items(), key=lambda x: RUNE_RANK.get(x[0], 0)):
        s = SOCK[rid]
        out.append({"name": rune_name(rid), "img": s.get("image"), "tip": tip_socket(rid), "n": n, "rank": RUNE_RANK[rid]})
    return out


# ---------- wiki predmetov ----------
SLOT_OF_TYPE = [("tors", "armor"), ("helm", "helm"), ("shld", "offhand"), ("glov", "gloves"), ("belt", "belt"),
                ("boot", "boots"), ("amul", "amulet"), ("ring", "ring"), ("weap", "weapon"), ("misl", "offhand"),
                ("pala", "offhand"), ("necr", "offhand"), ("sorc", "weapon"), ("assn", "weapon"), ("amaz", "weapon"),
                ("drui", "helm"), ("barb", "helm")]
CRAFT_IMG_BASE = {"helm": "hlm", "boot": "mbt", "glov": "vgl", "belt": "vbl", "shld": "kit", "tors": "brs",
                  "weap": "lsd", "misl": "aqv"}


def slots_for_types(types):
    out = []
    for t in types:
        for target, slot in SLOT_OF_TYPE:
            if type_is(t, target) and slot not in out:
                out.append(slot)
                break
    return out


def build_catalog(site):
    """Vsi predmeti + kateri buildi jih uporabljajo → docs/assets/items.json."""
    usage_path = os.path.join(PD2T, "item_usage.json")
    s13 = json.load(open(usage_path))["items"] if os.path.exists(usage_path) else {}
    s13 = {k.lower(): v for k, v in s13.items()}
    builds, used = [], {}
    rw_group = {}
    for rw in RW.values():
        rw_group[f"rw:{rw['id']}"] = "rw:" + slug(rw.get("runeword") or rw["id"]).replace("-", "_")

    def mark(key, bi, role, phase, merc=False):
        if not key:
            return
        key = rw_group.get(key, key)
        rec = used.setdefault(key, {}).setdefault(bi, {"r": [], "p": ""})
        role = ("merc " if merc else "") + role
        if role not in rec["r"]:
            rec["r"].append(role)
        if phase[0] not in rec["p"]:
            rec["p"] += phase[0]

    for cl in site["classes"]:
        for b in cl["builds"]:
            bi = len(builds)
            builds.append([cl["id"], b["id"], b["name"], b["tier"]])
            for p in b["planners"]:
                ph = p["phase"]
                for merc, gear in ((False, p["gear"]), (True, (p.get("merc") or {}).get("gear") or {})):
                    for slot, it in gear.items():
                        mark(it.get("tip"), bi, slot, ph, merc)
                        if it.get("bc"):
                            mark(f"b:{it['bc']}", bi, f"baza: {it['name']}", ph, merc)
                        for so in it.get("sockets") or []:
                            mark(so.get("tip"), bi, f"socket: {slot}", ph, merc)
                        for r in it.get("runes") or []:
                            mark(r.get("tip"), bi, it["name"], ph, merc)
                        if it.get("q") == "c":
                            c = craft_for(it["name"], slot)
                            if c:
                                mark(f"cr:{c['id']}", bi, slot, ph, merc)
                for c in p["charms"]:
                    mark(c.get("tip"), bi, "charm", ph)

    entries = []

    def add(e):
        e["u"] = [[bi, "".join(sorted(v["p"], key="sme".index)), v["r"]] for bi, v in sorted(used.get(e["k"], {}).items())]
        pct = s13.get(e["n"].lower())
        if pct:
            e["s13"] = pct
        entries.append({k: v for k, v in e.items() if v not in (None, [], "")})

    tier_sl = {"normal": "normal", "exceptional": "exceptional", "elite": "elite"}
    for it in UNIQ.values():
        b = BASES.get(it.get("base")) or {}
        e = {"k": f"u:{it['id']}", "n": it["name"], "q": "u" if it["kind"] == "unique" else "s",
             "c": it["kind"], "s": ["ring" if it["slot"] == "ring" else it["slot"]], "b": it.get("baseName"),
             "t": tier_sl.get(b.get("tier")), "r": it.get("reqLevel"), "i": img(it.get("image")), "tip": tip_unique(it),
             "set": SET_OF.get(it["id"]), "cl": it.get("only")}
        if b and b.get("tier") in ("normal", "exceptional") and b["kind"] in ("weapon", "armor"):
            kind = "weapon" if b["kind"] == "weapon" else "armor"
            rec = UPGRADE_RECIPE.get(("unique", kind, b["tier"]))
            if rec:
                e["up"] = f"{rec} → {'exceptional' if b['tier'] == 'normal' else 'elite'}"
        add(e)

    groups = {}
    for rw in RW.values():
        groups.setdefault(rw_group[f"rw:{rw['id']}"], []).append(rw)
    for key, rws in groups.items():
        rw = rws[0]
        itypes, etypes = [], []
        for v in rws:
            for t in v.get("txt") or []:
                itypes += [x for x in t.get("itypes") or [] if x not in itypes]
                etypes += [x for x in t.get("etypes") or [] if x not in etypes]
        req = max((SOCK.get(r) or {}).get("reqLevel") or 0 for r in rw["runes"])
        name = re.sub(r" \(.*\)$", "", rw["name"]) if len(rws) > 1 else rw["name"]
        base_img_path = next((b.get("image") for b in rw.get("bases") or [] if b.get("image")), None)
        e = {"k": key, "n": name, "q": "r", "c": "runeword", "s": slots_for_types(itypes), "r": req,
             "i": img(base_img_path), "tip": tip_runeword(rw), "ru": [rune_name(r) for r in rw["runes"]],
             "ri": [img((SOCK.get(r) or {}).get("image")) for r in rw["runes"]],
             "it": itypes, "et": etypes,
             "b": " / ".join((ITYPES.get(t) or {}).get("name", t) for t in itypes),
             "a": [f"rw:{v['id']}" for v in rws]}
        if len(rws) > 1:
            e["var"] = [[re.sub(r"^.*\((.*)\)$", r"\1", v["name"]), tip_runeword(v)] for v in rws]
        add(e)

    for c in CRAFTS:
        main_, *alt = c.get("ingredients") or [[]]
        add({"k": f"cr:{c['id']}", "n": c["name"], "q": "c", "c": "craft", "s": slots_for_types([c["itemType"]]) or ["weapon"],
             "b": c["typeName"], "r": c.get("playerLevel"), "tip": craft_tip(c), "cat": c["category"],
             "ing": main_, "alt": [a for x in alt for a in x],
             "i": img(GENERIC_IMG.get(c["itemType"])) if c["itemType"] in ("amul", "ring")
             else base_img(CRAFT_IMG_BASE.get(c["itemType"]))})

    for so in SOCK.values():
        kind = so.get("kind")
        cat = {"rune": "rune", "gem": "gem", "jewel": "jewel", "facet": "jewel"}.get(kind)
        if not cat:
            continue
        e = {"k": f"so:{so['id']}", "n": so["name"], "q": "r" if kind == "rune" else ("u" if kind == "facet" else "m"),
             "c": cat, "s": ["socket"], "r": so.get("reqLevel"), "i": img(so.get("image")), "tip": tip_socket(so["id"])}
        if kind == "rune":
            e["rank"] = RUNE_RANK.get(so["id"])
            e["up"] = RUNE_PROMOTE.get(so["name"].replace(" Rune", ""))
        add(e)

    for ch in CHARM.values():
        if ch.get("rarity") != "unique":
            continue
        key = f"p:{ch['id']}"
        if key not in TIPS:
            TIPS[key] = tips.preset_tip(ch, "u")
        add({"k": key, "n": ch["name"], "q": "u", "c": "charm", "s": ["charm"], "r": ch.get("reqLevel"),
             "i": img(ch.get("image")), "tip": key, "b": (ch.get("size") or "").title() + " Charm"})

    for b in BASES.values():
        if b["kind"] not in ("weapon", "armor") or max_sockets(b) < 2:
            continue
        t = b["type"]
        add({"k": f"b:{b['code']}", "n": b["name"], "q": "n", "c": "base", "s": slots_for_types([t]),
             "b": (ITYPES.get(t) or {}).get("name", t), "t": b["tier"], "r": b.get("levelReq") or 0,
             "i": base_img(b["code"]), "tip": base_tip(b), "ms": max_sockets(b), "ta": type_chain(t),
             "sk": socket_kind(b["code"])})

    sock = {k: {"recipe": v["recipe"], "lo": v["lo"], "hi": v["hi"]} for k, v in SOCKET_RECIPE.items()}
    out = {"builds": builds, "items": entries, "socket": sock,
           "classes": {c["id"]: c["name"] for c in site["classes"]}}
    json.dump(out, open(os.path.join(ROOT, "docs", "assets", "items.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    n_used = sum(1 for e in entries if e.get("u"))
    print(f"predmetov v wikiju: {len(entries)} (v buildih: {n_used}), socket receptov: {len(SOCKET_RECIPE)}, "
          f"nadgradenj: {len(UPGRADE_RECIPE)}, rune promocij: {len(RUNE_PROMOTE)}")


# ---------- ostali buildi: galerija skupnosti in S13 ----------
GALLERY_PATH = os.path.join(HIIM, "gallery", "builds_s14.json")
GALLERY = json.load(open(GALLERY_PATH)) if os.path.exists(GALLERY_PATH) else []
_su = os.path.join(PD2T, "skill_usage.json")
SKILL_USAGE = json.load(open(_su)) if os.path.exists(_su) else {}


def _norm_name(n):
    return re.sub(r"[^a-z0-9]+", " ", (n or "").lower()).strip()


def extra_builds(cls, cname, builds):
    """Buildi, ki jih ni na Hiim listah kot viable: galerija skupnosti (S14) in S13 popularni skilli."""
    import difflib
    out = []
    mains = {b["main"]["id"] for b in builds if b.get("main")}
    names = [_norm_name(b["name"]) for b in builds]
    low_mains = set()
    for b in builds:
        end = next((p for p in reversed(b["planners"]) if p["skills"]), None)
        if end and b.get("main"):
            pts = next((x["pts"] for x in end["skills"] if x["id"] == b["main"]["id"]), 0)
            if pts < 20:
                low_mains.add(b["main"]["id"])
    clusters = {}
    for g in GALLERY:
        if g.get("className") != cls or g.get("hidden"):
            continue
        nm = g.get("name") or ""
        if re.search(r"(?i)speedrun|untitled|\(copy\)", nm):
            continue
        sk = (g.get("build") or {}).get("skills") or {}
        maxed = {k for k, v in sk.items() if v >= 20}
        if maxed & mains or any(sk.get(m) for m in low_mains):
            continue
        if difflib.get_close_matches(_norm_name(nm), names, n=1, cutoff=0.75):
            continue
        key = tuple(sorted(maxed))
        clusters.setdefault(key, []).append(g)
    rows = []
    for key, gs in clusters.items():
        gs.sort(key=lambda g: -(g.get("opens") or 0))
        opens = sum(g.get("opens") or 0 for g in gs)
        if opens < 20:
            continue
        top = gs[0]
        sk_names = [skill_info(cls, k)["name"] for k in key if (cls, k) in SKILLS]
        rows.append({"name": top["name"], "tier": "skupnost", "src": "gallery", "url": f"https://hiimpd2.com/b/{top['buildId']}",
                     "author": top.get("ownerDisplayName"), "opens": opens, "n": len(gs), "skills": sk_names,
                     "tags": top.get("tags") or []})
    rows.sort(key=lambda r: -r["opens"])
    out += rows[:6]
    # S13: napadalni ali summon skilli na 20 pri likih 90+, ki jih ni med našimi buildi
    usage = (SKILL_USAGE.get(cname) or {}).get("skills") or {}
    covered = set()
    for b in builds:
        if b.get("main"):
            covered.add(b["main"]["name"])
        if (b.get("stats") or {}).get("skill"):
            covered.add(b["stats"]["skill"])
        for p in b["planners"]:
            covered.update(x["name"] for x in p["skills"] if x["pts"] >= 20)  # sinergije in pomožni skilli
    by_name = {s["name"]: s for (c, _), s in SKILLS.items() if c == cls}
    for name, pct in usage.items():
        s = by_name.get(name)
        if pct < 5 or name in covered or not s:
            continue
        if s.get("bindable") == 2 or (s.get("description") or "").startswith("Summon"):
            out.append({"name": name, "tier": "S13", "src": "s13", "pct": pct,
                        "total": SKILL_USAGE[cname]["total"]})
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
            # brez ocene: Hiim jih še ni ocenil (večinoma novi S14 buildi); vzamemo jih, če imajo planer
            unrated_with_planner = not tier and (e.get("buildId") or any(
                l.get("kind") == "planner" and l.get("buildId") for l in e.get("links") or []))
            if tier not in VIABLE and not unrated_with_planner:
                others.append({"name": e["buildName"], "tier": tier or "brez ocene", "src": "hiim"})
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
        others += extra_builds(cls, cname, builds)
        ids = set()
        for b in builds:
            while b["id"] in ids:
                b["id"] += "-2"
            ids.add(b["id"])
        site["classes"].append({"id": cls, "name": cname, "builds": builds, "others": others,
                                "starters": [s["buildName"] for s in starters]})
    for c in site["classes"]:
        for b in c["builds"]:
            for p in b["planners"]:
                p["recipes"] = planner_recipes(p)
            b["runes_total"] = build_runes_total(b)
    json.dump(site, open(os.path.join(ROOT, "data", "site.json"), "w"), indent=1)
    for it in UNIQ.values():
        tip_unique(it)
    for rw in RW.values():
        tip_runeword(rw)
    os.makedirs(os.path.join(ROOT, "docs", "assets"), exist_ok=True)
    build_catalog(site)
    json.dump(sorted(images), open(os.path.join(ROOT, "data", "images.json"), "w"), indent=1)
    json.dump(sorted(need_bases), open(os.path.join(ROOT, "data", "base_codes.json"), "w"), indent=1)
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
