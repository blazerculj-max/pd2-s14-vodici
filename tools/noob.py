"""Vsebina za začetnike: kaj pobirati za svoj razred in build, socketi za preživetje, zgodnji runewordi,
kje gledaš škodo in JuxtAPoserjeva S14 tier lista (leveling, early farming, mapperji, bossing).

Podatki: Hiim katalog (staffmodi, affixi za drevesa in class skille, gemi in rune v socketih), PD2 wiki
(delež škode orožja pri skillih), data/juxt/tierlist.json (fetch_juxt.py) in content/juxt-map.json."""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "data", "hiim", "catalog")


def e(s):
    return html.escape(str(s), quote=True)


CLASS_CODE = {"amazon": "ama", "sorceress": "sor", "necromancer": "nec", "paladin": "pal", "barbarian": "bar",
              "druid": "dru", "assassin": "ass"}
# številka drevesa v affixih (skilltab) = začetek razreda + (3 − stolpec drevesa v Hiim katalogu)
TAB_BASE = {"ama": 0, "sor": 3, "nec": 6, "pal": 9, "bar": 12, "dru": 15, "ass": 18}
TREE_NAME = {0: "Bow and Crossbow Skills", 1: "Passive and Magic Skills", 2: "Javelin and Spear Skills",
             3: "Fire Skills", 4: "Lightning Skills", 5: "Cold Skills", 6: "Curses", 7: "Poison and Bone Skills",
             8: "Summoning Skills", 9: "Combat Skills", 10: "Offensive Auras", 11: "Defensive Auras",
             12: "Combat Skills", 13: "Masteries", 14: "Warcries", 15: "Summoning Skills", 16: "Shape Shifting Skills",
             17: "Elemental Skills", 18: "Traps", 19: "Shadow Disciplines", 20: "Martial Arts"}
ITYPE_SL = {"h2h": "kremplji (claws)", "knif": "bodala", "orb": "orbi", "staf": "staffi", "wand": "wandi",
            "head": "necro glave", "scep": "žezla (scepters)", "phlm": "barb helmi", "pelt": "druid pelti",
            "club": "kiji (clubs)", "glov": "rokavice", "amul": "amuleti", "circ": "circleti", "helm": "helmi",
            "tors": "oklepi", "weap": "vsa orožja", "miss": "loki in samostreli", "misl": "tulci", "spea": "kopja",
            "shld": "ščiti", "ashd": "paladin ščiti", "swor": "meči", "mace": "maci", "aspe": "amazon kopja",
            "ajav": "amazon javelini", "abow": "amazon loki", "lcha": "grand charmi"}
SKIP_ITYPE = {"lchp", "cloa", "h2h2"}
SECTION_SL = {"Leveling": "Leveling", "Early Farming": "Zgodnji farming", "Early Bossing": "Zgodnji bossing (T0)",
              "CMapper": "Cenen mapper", "EMapper": "Endgame mapper", "T2Bosser": "T2 bossing"}
RATING_SL = {"Speed": "hitrost", "Safety": "varnost", "Versatility": "vsestranskost", "Ubers": "Uberji",
             "DClone": "DClone", "Rathma": "Rathma", "Lucion": "Lucion", "Gear Req": "oprema",
             "Difficulty": "težavnost", "Farming Areas": "kje"}
SECTION_DESC_SL = {"Leveling": "Pot skozi kampanjo in oprema za leveling.", "Early Farming": "Farmanje takoj po kampanji.",
                   "Early Bossing": "T0 bossi z realno zgodnjo opremo.",
                   "CMapper": "En večji runeword in nekaj ključnih uniquov, brez endgame BIS opreme in GG korupcij.",
                   "EMapper": "Konec sezone: GG korupcije, BIS uniqui in veliki runewordi.", "T2Bosser": "T2 bossi in endgame."}
GEAR_REQ_SL = {"Low": "nizka", "Medium": "srednja", "High": "visoka", "Easy": "lahko", "Hard": "težko"}

_affixes = json.load(open(os.path.join(CAT, "affixes.json")))
_itypes = json.load(open(os.path.join(CAT, "item-types.json")))
_jp = os.path.join(ROOT, "data", "juxt", "tierlist.json")
JUXT = json.load(open(_jp)) if os.path.exists(_jp) else None
JUXT_MAP = {k: v for k, v in json.load(open(os.path.join(ROOT, "content", "juxt-map.json"))).items() if not k.startswith("_")}


def _cat(cls):
    return {s["id"]: s for s in json.load(open(os.path.join(CAT, f"skills.{cls}.json")))["skills"]}


CATALOG = {c: _cat(c) for c in CLASS_CODE}


# ---------- razredni predmeti in +skilli ----------

def _types(codes):
    out = []
    for c in codes:
        n = ITYPE_SL.get(c)
        if n and n not in out:
            out.append(n)
    return out


def staffmod_types(code):
    """Tipi predmetov, na katerih so +1–3 na posamezne skille razreda (staffmodi)."""
    return _types(t for t, v in _itypes.items() if v.get("staffMods") == code and t not in SKIP_ITYPE)


def staffmod_skills(code):
    return {s["name"] for s in _affixes["staffmods"].get(code, {}).get("skills", [])}


def affix_tiers(code, param=None):
    """{+N: (najnižji level, [tipi])} za affix drevesa (param) ali vseh class skillov (param None)."""
    tiers = {}
    for kind in ("magicPrefixes", "magicSuffixes", "automagic"):
        for p in _affixes[kind]:
            for m in p.get("mods", []):
                ok = (m.get("code") == "skilltab" and param is not None and int(m.get("param", -1)) == param) or \
                     (param is None and m.get("code") == code)
                if not ok:
                    continue
                its = [t for t in p.get("itypes", []) if t not in SKIP_ITYPE]
                if kind == "automagic":  # amazon orožje ima drevo kot samodejni affix
                    its = ["aspe", "ajav", "abow"] if code == "ama" else []
                if not its:
                    continue
                lv, ts = tiers.get(m["min"], (99, []))
                tiers[m["min"]] = (min(lv, p.get("levelReq") or 1), ts + [t for t in its if t not in ts])
    return dict(sorted(tiers.items()))


def tree_of(cls, skill_id):
    s = CATALOG[cls].get(skill_id)
    if not s:
        return None
    return TAB_BASE[CLASS_CODE[cls]] + 3 - s["tab"]


def tiers_text(tiers):
    parts = []
    for n, (lv, ts) in tiers.items():
        gc = "lcha" in ts
        ts = [t for t in ts if t != "lcha"]
        parts.append(f"+{n} od levela {lv}: {', '.join(_types(ts))}" + (" (in grand charmi)" if gc else ""))
    return "; ".join(parts)


def class_items_html(cls, cls_name):
    """Za stran Začetniki: staffmodi, drevesa in class skilli razreda."""
    code = CLASS_CODE[cls]
    st = staffmod_types(code)
    trees = []
    for p in range(TAB_BASE[code], TAB_BASE[code] + 3):
        trees.append(f"<li><b>+X to {e(TREE_NAME[p])} ({e(cls_name)} Only)</b>: {e(tiers_text(affix_tiers(code, p)))}</li>")
    cs = affix_tiers(code, None)
    staff = (f"<b>+1 do +3 na posamezen skill</b> (npr. »+3 to {e(example_skill(cls))} ({e(cls_name)} Only)«): {e(', '.join(st))}"
             if st else "Amazon nima predmetov s +skilli na posamezne skille; njena orožja (amazon loki, kopja, javelini) imajo vedno +1 do +3 na drevo.")
    return (f"<p class=\"note-s\">{staff}</p><ul class=\"plain\">{''.join(trees)}</ul>"
            f"<p class=\"note-s\"><b>+X to {e(cls_name)} Skill Levels:</b> {e(tiers_text(cs))}</p>")


EXAMPLE_SKILL = {"amazon": "Magic Arrow", "assassin": "Lightning Sentry", "barbarian": "Battle Orders", "druid": "Summon Grizzly",
                 "necromancer": "Teeth", "paladin": "Holy Bolt", "sorceress": "Meteor"}


def example_skill(cls):
    return EXAMPLE_SKILL.get(cls, "skill")


# ---------- kje gledaš škodo ----------

def _wiki_weapon():
    out = {}
    for cls in CLASS_CODE:
        p = os.path.join(ROOT, "data", "wiki", f"All_{cls.capitalize()}_Skills.txt")
        if not os.path.exists(p):
            continue
        text = open(p).read()
        for m in re.finditer(r"^## (.+?)\[edit\]\n(.*?)(?=^## |\Z)", text, re.S | re.M):
            body = re.split(r"^Changelog", m.group(2), flags=re.M)[0]
            w = re.search(r"^(\d+)% Weapon Damage [Aa]dded to (?:Skill Damage|primary Bolt)(?:, and (\d+)% of Physical Damage converted to (\w+) Damage)?", body, re.M)
            if w:
                out[(cls, m.group(1).strip())] = (int(w.group(1)), int(w.group(2)) if w.group(2) else None, w.group(3))
            elif re.search(r"converts 100% of most Weapon Damage into Elemental", body):
                out[(cls, m.group(1).strip())] = (100, 100, "elemental")
    return out


WIKI_WEAPON = _wiki_weapon()
KICK = {"dragon_talon", "dragon_tail", "dragon_flight"}
# glavnina škode je iz skilla (strup, charge-up efekti, procs), orožje šteje za hitrost napada in zadetek
HYBRID = {"necromancer/poison-strike", "druid/rabies", "assassin/cobra-sin", "assassin/phoenix-strike",
          "assassin/claws-of-thunder", "assassin/fists-of-fire", "paladin/blessed-hammer-procs"}
EL_SL = {"Fire": "ogenj", "Cold": "mraz", "Lightning": "strelo", "Magic": "magic", "Poison": "strup", "elemental": "vse tri elemente"}
KIND_SL = {"weapon": "orožje", "kick": "brca (škornji)", "spell": "skill", "minion": "minioni", "hybrid": "skill + orožje"}


def damage_kind(cls, b, arch):
    """(vrsta, opomba z wikija) za glavni skill builda."""
    main = b.get("main") or {}
    key = f'{cls}/{b["id"]}'
    note = WIKI_WEAPON.get((cls, main.get("name")))
    if main.get("id") in KICK:
        return "kick", None
    if key in HYBRID:
        return "hybrid", note
    if note or arch in ("melee", "bow", "throw"):
        return "weapon", note
    if arch == "summon":
        return "minion", None
    return "spell", None


def damage_html(cls, b, arch):
    kind, note = damage_kind(cls, b, arch)
    skill = (b.get("main") or {}).get("name") or b["name"]
    if kind == "weapon":
        w = ""
        if note:
            pct, conv, el = note
            w = f" Po PD2 wikiju {e(skill)} doda {pct} % škode orožja" + (
                f", {conv} % fizične škode pa se pretvori v {e(EL_SL.get(el, el))}" if conv else "") + "."
        what = {"bow": " (lok ali samostrel)", "throw": " (metalno orožje)"}.get(arch, "")
        return (f"<p class=\"note-s\"><b>Škoda pride iz orožja</b>{e(what)}.{w} Pri orožju primerjaj razpon škode "
                "(»One-Hand/Two-Hand Damage: 30 to 60« ali »Throw Damage«), % Enhanced Damage, +min/+max damage in IAS. "
                "Najhitreje: daj orožje v roko, odpri character screen (C) in poglej številko škode ob skillu na levem ali desnem kliku.</p>")
    if kind == "kick":
        return ("<p class=\"note-s\"><b>Škoda pride iz brce</b>: kick damage na škornjih ter Strength in Dexterity. "
                "Orožje (claws) šteje le za charge-up skille in IAS. Škodo brce vidiš na character screenu (C), ko je skill na klik.</p>")
    if kind == "hybrid":
        return (f"<p class=\"note-s\"><b>Mešano</b>: glavnina škode {e(skill)} pride iz skilla (tooltip v skill drevesu), "
                "orožje pa šteje za hitrost napada (IAS), attack rating in fizični del udarca. Za skill iščeš +skills, za orožje IAS in razpon škode.</p>")
    if kind == "minion":
        return ("<p class=\"note-s\"><b>Škodo delajo minioni.</b> Moč jim dvigujejo +skills (vsak +1 je močnejši summon) in aure; "
                "tvoje orožje na njih ne vpliva. Življenje in škodo miniona vidiš v tooltipu skilla v drevesu (T). "
                "Sinergije štejejo samo točke, ki si jih vložil, +skills pa dvignejo skill sam.</p>")
    return (f"<p class=\"note-s\"><b>Škoda pride iz skilla, ne iz orožja.</b> Koliko dela {e(skill)}, vidiš v skill drevesu (T): "
            "premakni miško na skill, tooltip pokaže škodo z vsemi +skills. Iščeš +skills, FCR (hitrejše castanje), kasneje −% enemy resistance; "
            "škoda na orožju (ED, min/max) ti nič ne pomaga. Sinergije štejejo samo vložene točke.</p>")


# ---------- kaj pobirati za build ----------

def pickup_html(cls, cls_name, b):
    main = b.get("main") or {}
    code = CLASS_CODE[cls]
    parts = []
    if main.get("name") in staffmod_skills(code) and staffmod_types(code):
        parts.append(f"»+1 do +3 to {e(main['name'])} ({e(cls_name)} Only)« na: {e(', '.join(staffmod_types(code)))}")
    tree = tree_of(cls, main.get("id"))
    if tree is not None:
        parts.append(f"»+X to {e(TREE_NAME[tree])} ({e(cls_name)} Only)«: {e(tiers_text(affix_tiers(code, tree)))}")
    parts.append(f"»+X to {e(cls_name)} Skill Levels«: {e(tiers_text(affix_tiers(code, None)))}")
    return "<ul class=\"plain\">" + "".join(f"<li>{p}</li>" for p in parts) + "</ul>"


# ---------- JuxtAPoser ----------

def juxt_for_build(cls, bid):
    if not JUXT:
        return []
    m = JUXT_MAP.get(cls, {})
    out = []
    for s in JUXT["classes"].get(cls, {}).get("sections", []):
        for jb in s["builds"]:
            ids = m.get(jb["name"])
            ids = ids if isinstance(ids, list) else [ids]
            if bid in ids:
                out.append((s["type"], jb))
    return out


def rating_text(jb):
    bits = [f'{RATING_SL.get(k, k)} {v}' for k, v in (jb.get("ratings") or {}).items()]
    for k, v in jb.get("details") or []:
        if k == "Farming Areas":
            continue
        bits.append(f'{RATING_SL.get(k, k)} {GEAR_REQ_SL.get(v, v)}')
    return ", ".join(bits)


def juxt_entry_html(stype, jb, link_name=False, ids=None):
    area = next((v for k, v in jb.get("details") or [] if k == "Farming Areas"), None)
    gear = ", ".join(g for g in jb.get("gear") or [] if g)
    merc = ", ".join(x for x in jb.get("mercs") or [] if x and x != "N/A")
    notes = (jb.get("notes") or "").strip()
    links = []
    for lab, url in jb.get("links") or []:
        if url.startswith("http"):
            links.append(f'<a href="{e(url)}" target="_blank" rel="noopener">{e(lab if not lab.startswith("http") else "JuxtAPoser")}</a>')
    name = f"<b>{e(jb['name'])}</b> " if link_name else ""
    bits = [f'{name}<span class="badge jx">{e(jb.get("rank") or "?")}</span> <span class="muted">{e(SECTION_SL.get(stype, stype))}</span>']
    rt = rating_text(jb)
    if rt:
        bits.append(e(rt))
    if area:
        bits.append("kje: " + e(area))
    if gear:
        bits.append("oprema: " + e(gear))
    if merc:
        bits.append("merc: " + e(merc))
    if notes and notes != "Leveling Tips":
        bits.append(f'<i>{e(notes)}</i>')
    if links:
        bits.append("video: " + ", ".join(links))
    return " · ".join(bits)


def juxt_build_html(cls, bid):
    rows = juxt_for_build(cls, bid)
    if not rows:
        return ""
    lis = "".join(f"<li>{juxt_entry_html(t, jb, link_name=True)}</li>" for t, jb in rows)
    return (f'<p class="note-s"><b>JuxtAPoser S14</b> (<a href="{e(JUXT["url"])}" target="_blank" rel="noopener">pd2guides</a>, '
            f'ocene S–D):</p><ul class="plain jxl">{lis}</ul>')


def build_box_html(cls, cls_name, b, arch):
    """Blok »Za začetnike« v načrtu builda."""
    return ('<h4>Za začetnike</h4>'
            + damage_html(cls, b, arch)
            + f'<p class="note-s"><b>Kaj pobirati za ta build:</b></p>{pickup_html(cls, cls_name, b)}'
            + juxt_build_html(cls, b["id"])
            + '<p class="note-s">Socketi za preživetje, zgodnji runewordi in rari: <a href="zacetniki.html">stran Začetniki</a>.</p>')


# ---------- socketi ----------

# vrednosti od chipped do perfect (perfect se ujema s Hiim katalogom)
GEMS = [
    ("Ruby", "Perfect_Ruby", "+10 / 17 / 24 / 31 / 38 life", "Fire Resist +12 / 16 / 22 / 28 / 40 %", "3-4 … 15-20 fire škode"),
    ("Diamond", "Perfect_Diamond", "+20 … +100 attack rating", "All Resistances +6 / 8 / 11 / 14 / 19", "+28 … +68 % škode proti undead"),
    ("Skull", "Perfect_Skull", "replenish life +2 … +5, mana regen 8 … 19 %", "napadalec dobi 4 … 20 škode (thorns)", "2 … 4 % life in 1 … 3 % mana leech"),
    ("Sapphire", "Perfect_Sapphire", "+10 … +38 mane", "Cold Resist +12 … 40 %", "1-3 … 10-14 cold škode"),
    ("Topaz", "Perfect_Topaz", "9 … 24 % Magic Find", "Lightning Resist +12 … 40 %", "1-8 … 1-40 lightning škode"),
    ("Emerald", "Perfect_Emerald", "+3 … +10 Dexterity", "Poison Resist +12 … 40 %", "strup 10 … 100 škode"),
    ("Amethyst", "Perfect_Amethyst", "+3 … +10 Strength", "+8 … +30 defense", "+40 … +150 attack rating"),
]
# (runa, oklep/helm, ščit, orožje, kdaj)
RUNES = [
    ("Ral", "Fire Resist +30 %", "Fire Resist +35 %", "5-30 fire škode", "ščit: 35 % resa za eno runo, najboljše zgodaj"),
    ("Tal", "Poison Resist +30 %", "Poison Resist +35 %", "75 strupa v 5 s", ""),
    ("Ort", "Lightning Resist +30 %", "Lightning Resist +35 %", "1-50 lightning škode", ""),
    ("Thul", "Cold Resist +30 %", "Cold Resist +35 %", "3-14 cold škode", ""),
    ("Amn", "napadalec dobi 20 škode", "napadalec dobi 24 škode", "7 % life leech", "orožje: leech za melee"),
    ("Sol", "Physical Damage Taken Reduced by 7", "… by 9", "+9 min škode", "zmanjša vsak udarec"),
    ("Shael", "20 % FHR", "20 % FBR", "20 % IAS", "oklep: hitrejše okrevanje po udarcu"),
    ("Dol", "replenish life +20", "replenish life +30", "+20 % ED", ""),
    ("Io", "+10 Vitality", "", "+10 Vitality", "oklep ali helm: +life za vse"),
    ("Um", "All Resistances +15", "All Resistances +22", "open wounds", "kasneje, ščit"),
]


def gem_table_html(img_tag):
    rows = "".join(f'<tr><th scope="row">{img_tag("items/socketables/gem/" + f + ".png", "skico", n)} {e(n)}</th>'
                   f'<td>{e(a)}</td><td>{e(s)}</td><td>{e(w)}</td></tr>' for n, f, a, s, w in GEMS)
    return ('<div class="tbl-wrap"><table class="tbl gemtab"><thead><tr><th>Gem (chipped → perfect)</th><th>Helm in oklep</th>'
            f'<th>Ščit</th><th>Orožje</th></tr></thead><tbody>{rows}</tbody></table></div>')


def rune_table_html(img_tag):
    rows = "".join(f'<tr><th scope="row">{img_tag("items/socketables/rune/" + r + "_Rune.png", "skico", r)} {e(r)}</th>'
                   f'<td>{e(a)}</td><td>{e(s or "—")}</td><td>{e(w)}</td><td class="muted">{e(n)}</td></tr>' for r, a, s, w, n in RUNES)
    return ('<div class="tbl-wrap"><table class="tbl gemtab"><thead><tr><th>Runa</th><th>Helm in oklep</th><th>Ščit</th>'
            f'<th>Orožje</th><th>Opomba</th></tr></thead><tbody>{rows}</tbody></table></div>')


# ---------- zgodnji runewordi iz JuxtAPoserjeve opreme ----------

def early_runewords(items):
    """Runewordi, ki jih JuxtAPoser navaja za leveling in zgodnji farming: [(item, [(razred, build)])]."""
    if not JUXT:
        return []
    rw = {}
    for it in items:
        if it.get("c") == "runeword":
            rw[re.sub(r"[^a-z]", "", it["n"].lower())] = it
    found = {}
    for cls, d in JUXT["classes"].items():
        for s in d["sections"]:
            if s["type"] not in ("Leveling", "Early Farming"):
                continue
            for jb in s["builds"]:
                for g in jb.get("gear") or []:
                    k = re.sub(r"[^a-z]", "", re.sub(r"\(.*?\)", "", g).lower())  # »Leaf RW (+3 Meteor base)« → leaf
                    k = re.sub(r"rw$", "", k)
                    if k in rw:
                        found.setdefault(rw[k]["k"], (rw[k], []))[1].append((cls, jb["name"]))
    return sorted(found.values(), key=lambda x: x[0].get("r", 99))


def tip_mods(tips, key, n=4):
    t = tips.get(key) or ""
    mods = re.findall(r"<div>(.*?)</div>", t.split('tt-mods">', 1)[1]) if 'tt-mods">' in t else []
    return [html.unescape(re.sub(r"<[^>]+>", "", m)) for m in mods[:n]]
