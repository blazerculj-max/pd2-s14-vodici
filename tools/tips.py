"""Tooltipi za predmete in skille.

Vsak tooltip je HTML niz pod ključem (npr. "u:harlequin_crest", "sk:druid:rabies").
Besedilo statsov je v angleščini, kot v igri; razponi so zapisani kot [min-max].
"""
import difflib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "data", "hiim", "catalog")
e = html.escape

CLASS_NAMES = {"ama": "Amazon", "sor": "Sorceress", "nec": "Necromancer", "pal": "Paladin", "bar": "Barbarian",
               "dru": "Druid", "ass": "Assassin"}
TABS = ["Bow and Crossbow Skills (Amazon Only)", "Passive and Magic Skills (Amazon Only)",
        "Javelin and Spear Skills (Amazon Only)", "Fire Skills (Sorceress Only)", "Lightning Skills (Sorceress Only)",
        "Cold Skills (Sorceress Only)", "Curses (Necromancer Only)", "Poison and Bone Skills (Necromancer Only)",
        "Summoning Skills (Necromancer Only)", "Combat Skills (Paladin Only)", "Offensive Auras (Paladin Only)",
        "Defensive Auras (Paladin Only)", "Combat Skills (Barbarian Only)", "Masteries (Barbarian Only)",
        "Warcries (Barbarian Only)", "Summoning Skills (Druid Only)", "Shape Shifting Skills (Druid Only)",
        "Elemental Skills (Druid Only)", "Traps (Assassin Only)", "Shadow Disciplines (Assassin Only)",
        "Martial Arts (Assassin Only)"]
PRESET_TABS = {
    "summoning_necromancer": 8, "poisonBone": 7, "curses": 6, "passives": 1, "javelins": 2, "bows": 0,
    "martial": 20, "shadow": 19, "traps": 18, "lightning": 4, "fire": 3, "cold": 5, "shapeshifting": 16,
    "elemental": 17, "summoning_druid": 15, "offensive": 10, "defensive": 11, "combat_paladin": 9,
    "masteries": 13, "combat_barbarian": 12, "warcries": 14,
}
ELEM = {"f": "Fire", "c": "Cold", "l": "Lightning", "p": "Poison", "m": "Magic"}


def rng(lo, hi):
    if lo is None:
        return str(hi)
    if hi is None or lo == hi:
        return str(lo)
    return f"[{lo}-{hi}]"


# ---------- katalog ----------

def _load(name):
    return json.load(open(os.path.join(CAT, f"{name}.json")))


SKILL_BY_GAMEID = {}
SKILLS = {}
for _cls in ["amazon", "assassin", "barbarian", "druid", "necromancer", "paladin", "sorceress"]:
    for _s in _load(f"skills.{_cls}")["skills"]:
        SKILLS[(_cls, _s["id"])] = _s
        if _s.get("gameId") is not None:
            SKILL_BY_GAMEID[_s["gameId"]] = _s["name"]


def skill_name(param):
    if isinstance(param, int) or (isinstance(param, str) and param.isdigit()):
        return SKILL_BY_GAMEID.get(int(param), f"skill {param}")
    return str(param).replace("_", " ")


# ---------- D2 kode lastnosti (custom predmeti, rune, charmi) ----------

SIMPLE = {
    "hp": "+{v} to Life", "mana": "+{v} to Mana", "str": "+{v} to Strength", "dex": "+{v} to Dexterity",
    "vit": "+{v} to Vitality", "enr": "+{v} to Energy", "res-all": "All Resistances +{v}",
    "res-fire": "Fire Resist +{v}%", "res-cold": "Cold Resist +{v}%", "res-ltng": "Lightning Resist +{v}%",
    "res-pois": "Poison Resist +{v}%", "lifesteal": "{v}% Life Stolen per Hit", "manasteal": "{v}% Mana Stolen per Hit",
    "ac%": "+{v}% Enhanced Defense", "ac": "+{v} Defense", "base_defense": "+{v} Defense",
    "ac-miss": "+{v} Defense vs. Missile", "ac-hth": "+{v} Defense vs. Melee",
    "red-dmg%": "Physical Damage Taken Reduced by {v}%", "red-dmg": "Physical Damage Taken Reduced by {v}",
    "red-mag": "Magic Damage Taken Reduced by {v}", "openwounds": "{v}% Chance of Open Wounds",
    "deep-wounds": "+{v} Open Wounds Damage per Second", "cast1": "+{v}% Faster Cast Rate",
    "cast2": "+{v}% Faster Cast Rate", "cast3": "+{v}% Faster Cast Rate", "move1": "+{v}% Faster Run/Walk",
    "move2": "+{v}% Faster Run/Walk", "move3": "+{v}% Faster Run/Walk", "balance1": "+{v}% Faster Hit Recovery",
    "balance2": "+{v}% Faster Hit Recovery", "balance3": "+{v}% Faster Hit Recovery",
    "block": "{v}% Increased Chance of Blocking", "block1": "+{v}% Faster Block Rate",
    "swing1": "+{v}% Increased Attack Speed", "swing2": "+{v}% Increased Attack Speed", "swing3": "+{v}% Increased Attack Speed",
    "att": "+{v} to Attack Rating", "att%": "{v}% Bonus to Attack Rating", "crush": "{v}% Chance of Crushing Blow",
    "deadly": "{v}% Deadly Strike", "dmg-max": "+{v} to Maximum Damage", "dmg-min": "+{v} to Minimum Damage",
    "dmg%": "+{v}% Enhanced Damage", "regen-mana": "Regenerate Mana {v}%", "regen": "Replenish Life +{v}",
    "allskills": "+{v} to All Skills", "mana-kill": "+{v} to Mana after each Kill", "heal-kill": "+{v} Life after each Kill",
    "extra-pois": "+{v}% to Poison Skill Damage", "extra-cold": "+{v}% to Cold Skill Damage",
    "extra-fire": "+{v}% to Fire Skill Damage", "extra-ltng": "+{v}% to Lightning Skill Damage",
    "pierce-cold": "-{v}% to Enemy Cold Resistance", "pierce-fire": "-{v}% to Enemy Fire Resistance",
    "pierce-ltng": "-{v}% to Enemy Lightning Resistance", "pierce-pois": "-{v}% to Enemy Poison Resistance",
    "light": "+{v} to Light Radius", "addxp": "+{v}% to Experience Gained", "dmg-to-mana": "{v}% Damage Taken Goes to Mana",
    "mag%": "{v}% Better Chance of Getting Magic Items", "gold%": "{v}% Extra Gold from Monsters",
    "cheap": "Reduces All Vendor Prices {v}%", "stamdrain": "{v}% Slower Stamina Drain", "pierce": "{v}% Chance to Pierce",
    "sock": "Socketed ({v})", "splash": "+{v}% Increased Melee Splash Radius", "dmg-undead": "+{v}% Damage to Undead",
    "dmg-demon": "+{v}% Damage to Demons", "slow": "Slows Target by {v}%", "res-pois-len": "Poison Length Reduced by {v}%",
    "rep-dur": "Repairs 1 Durability in {v} Seconds", "ease": "Requirements {v}%", "thorns": "Attacker Takes Damage of {v}",
    "res-fire-max": "+{v}% to Maximum Fire Resist", "res-cold-max": "+{v}% to Maximum Cold Resist",
    "res-ltng-max": "+{v}% to Maximum Lightning Resist", "res-pois-max": "+{v}% to Maximum Poison Resist",
    "res-mag": "Magic Resist +{v}%", "stupidity": "Hit Blinds Target", "freeze": "Freezes Target +{v}",
    "crit-strike-chance": "+{v}% Chance of Critical Strike", "crit-strike-multiplier": "+{v}% Critical Strike Multiplier",
    "howl": "Hit Causes Monster to Flee {v}%", "regen-stam": "Heal Stamina Plus {v}%",
    "fire-max": "+{v} to Maximum Fire Damage", "cold-max": "+{v} to Maximum Cold Damage", "ltng-max": "+{v} to Maximum Lightning Damage",
    "abs-cold": "+{v} Cold Absorb", "abs-fire": "+{v} Fire Absorb", "abs-ltng": "+{v} Lightning Absorb",
    "reduce-ac": "-{v}% Target Defense", "block2": "+{v}% Faster Block Rate", "hp%": "Increase Maximum Life {v}%",
    "mana%": "Increase Maximum Mana {v}%", "curse-res": "Curse Resistance +{v}%", "all-stats": "+{v} to All Attributes",
}
FLAG = {"knock": "Knockback", "half-freeze": "Half Freeze Duration", "nofreeze": "Cannot Be Frozen", "indestruct": "Indestructible",
        "ethereal": "Ethereal", "noheal": "Prevent Monster Heal", "ignore-ac": "Ignore Target's Defense"}
PAIRS = {("fire-min", "fire-max"): "Adds {a}-{b} Fire Damage", ("cold-min", "cold-max"): "Adds {a}-{b} Cold Damage",
         ("ltng-min", "ltng-max"): "Adds {a}-{b} Lightning Damage", ("pois-min", "pois-max"): "Adds {a}-{b} Poison Damage",
         ("dmg-min", "dmg-max"): "+{a}-{b} Damage", ("mag-min", "mag-max"): "Adds {a}-{b} Magic Damage"}


def mods_text(mods):
    """Seznam D2 mod zapisov ({code, min, max} ali {code, value, param}) → vrstice besedila."""
    by_code = {m.get("code"): m for m in mods}
    used, out = set(), []

    def val(m):
        if "value" in m:
            return str(m["value"])
        return rng(m.get("min"), m.get("max"))

    for (a, b), tpl in PAIRS.items():
        if a in by_code and b in by_code:
            out.append(tpl.format(a=val(by_code[a]), b=val(by_code[b])))
            used.update([a, b])
    for m in mods:
        code = m.get("code")
        if code in used:
            continue
        v = val(m)
        param = m.get("param")
        if code in SIMPLE:
            out.append(SIMPLE[code].format(v=v).replace("+-", "-"))
        elif code in FLAG:
            out.append(FLAG[code])
        elif code == "skilltab" and isinstance(param, int) and 0 <= param < len(TABS):
            out.append(f"+{v} to {TABS[param]}")
        elif code in CLASS_NAMES:
            out.append(f"+{v} to {CLASS_NAMES[code]} Skill Levels")
        elif code in ("skill", "oskill"):
            out.append(f"+{v} to {skill_name(param)}")
        elif code in ("gethit-skill", "hit-skill", "att-skill", "levelup-skill", "death-skill", "kill-skill", "cast-skill"):
            when = {"gethit-skill": "when Struck", "hit-skill": "on Striking", "att-skill": "on Attack",
                    "levelup-skill": "when you Level Up", "death-skill": "when you Die", "kill-skill": "when you Kill an Enemy",
                    "cast-skill": "on Casting"}[code]
            out.append(f"{m.get('min')}% Chance to cast level {m.get('max')} {skill_name(param)} {when}")
        elif code == "charged":
            out.append(f"Level {m.get('max')} {skill_name(param)} ({m.get('min')} Charges)")
        elif code == "aura":
            out.append(f"Level {v} {skill_name(param)} Aura when Equipped")
        elif code in ("dmg/lvl", "att/lvl"):
            out.append(("+Maximum Damage" if code == "dmg/lvl" else "+Attack Rating") + " (based on Character Level)")
        elif code == "equipped-skill":
            out.append(f"Level {v} {skill_name(param)} when Equipped" if param else "Grants a skill when Equipped")
        elif code and code.startswith("randclassskill"):
            out.append(f"+{v} to [Random Class] Skills")
        elif code:
            out.append(f"{code}: {v}")
    return out


# ---------- Hiim stats ključi (magic/rare presetti, socketables) ----------

STAT_SIMPLE = {
    "fcr": "+{v}% Faster Cast Rate", "frw": "+{v}% Faster Run/Walk", "fhr": "+{v}% Faster Hit Recovery",
    "fbr": "+{v}% Faster Block Rate", "ias": "+{v}% Increased Attack Speed", "life": "+{v} to Life", "mana": "+{v} to Mana",
    "all_res": "All Resistances +{v}", "all_skills": "+{v} to All Skills", "damage_max": "+{v} to Maximum Damage",
    "damage_min": "+{v} to Minimum Damage", "ar": "+{v} to Attack Rating", "poison_length_reduced": "Poison Length Reduced by {v}%",
    "life_per_kill": "+{v} Life after each Kill", "mana_per_kill": "+{v} to Mana after each Kill", "vitality": "+{v} to Vitality",
    "energy": "+{v} to Energy", "strength": "+{v} to Strength", "dexterity": "+{v} to Dexterity", "mf": "{v}% Better Chance of Getting Magic Items",
    "gf": "{v}% Extra Gold from Monsters", "experience": "+{v}% to Experience Gained", "light_radius": "+{v} to Light Radius",
    "mana_regen": "Regenerate Mana {v}%", "discount": "Reduces All Vendor Prices {v}%", "life_leech": "{v}% Life Stolen per Hit",
    "mana_leech": "{v}% Mana Stolen per Hit", "e_damage": "+{v}% Enhanced Damage", "req": "Requirements {v}%",
    "damage_vs_demons": "+{v}% Damage to Demons", "ar_vs_demons": "+{v} to Attack Rating against Demons",
    "cblow": "{v}% Chance of Crushing Blow", "pdr": "Physical Damage Taken Reduced by {v}%", "defense": "+{v} Defense",
    "skills_class": "+{v} to Class Skills",
    "damage_vs_undead": "+{v}% Damage to Undead", "ar_vs_undead": "+{v} to Attack Rating against Undead",
    "owounds": "{v}% Chance of Open Wounds", "owounds_dps": "+{v} Open Wounds Damage per Second",
    "slower_stam_drain": "{v}% Slower Stamina Drain", "block": "{v}% Increased Chance of Blocking",
    "missile_defense": "+{v} Defense vs. Missile", "target_defense": "{v}% Target Defense",
    "damage_to_mana": "{v}% Damage Taken Gained as Mana when Hit", "thorns": "Attacker Takes Damage of {v}",
    "damage_reduced": "Physical Damage Taken Reduced by {v}", "life_replenish": "Replenish Life +{v}",
    "e_def": "+{v}% Enhanced Defense", "mDamage_reduced": "Magic Damage Taken Reduced by {v}",
    "ar_bonus": "{v}% Bonus to Attack Rating", "pRes_max": "+{v}% to Maximum Poison Resist",
    "fRes_max": "+{v}% to Maximum Fire Resist", "cRes_max": "+{v}% to Maximum Cold Resist",
    "lRes_max": "+{v}% to Maximum Lightning Resist", "dstrike": "{v}% Deadly Strike",
    "max_mana": "Increase Maximum Mana {v}%", "max_life": "Increase Maximum Life {v}%",
    "freezes_target": "Freezes Target +{v}",
}
STAT_FLAG_EXTRA = {"knockback": "Knockback", "pmh": "Prevent Monster Heal", "itd": "Ignore Target's Defense",
                   "indestructible": "Indestructible"}
STAT_FLAG = {"half_freeze": "Half Freeze Duration", "cbf": "Cannot Be Frozen"}
STAT_FLAG.update(STAT_FLAG_EXTRA)


def stats_text(stats):
    out = []
    used = set()
    for el, name in ELEM.items():
        lo, hi = stats.get(f"{el}Damage_min"), stats.get(f"{el}Damage_max")
        if lo is not None and hi is not None:
            out.append(f"Adds {lo}-{hi} {name} Damage")
            used.update([f"{el}Damage_min", f"{el}Damage_max"])
    if "pDamage_all" in stats:
        out.append(f"+{stats['pDamage_all']} Poison Damage over {stats.get('pDamage_duration', '?')} Seconds")
        used.update(["pDamage_all", "pDamage_duration"])
    for k, v in stats.items():
        if k in used:
            continue
        if k in STAT_SIMPLE:
            out.append(STAT_SIMPLE[k].format(v=v))
        elif k in STAT_FLAG:
            out.append(STAT_FLAG[k])
        elif re.fullmatch(r"[fclpm]Res", k):
            out.append(f"{ELEM[k[0]]} Resist +{v}%")
        elif re.fullmatch(r"enemy_[fclp]Res", k):
            out.append(f"-{v}% to Enemy {ELEM[k[6]]} Resistance")
        elif re.fullmatch(r"[fclpm]Damage", k):
            out.append(f"+{v}% to {ELEM[k[0]]} Skill Damage")
        elif k.startswith("skills_"):
            tab = k[len("skills_"):]
            if tab in PRESET_TABS:
                out.append(f"+{v} to {TABS[PRESET_TABS[tab]]}")
            else:
                out.append(f"+{v} to {tab.title()} Skill Levels")
        elif k.startswith("skill_"):
            out.append(f"+{v} to {k[len('skill_'):].replace('_', ' ')}")
        elif k == "ctc" and isinstance(v, list):
            for row in v:
                if isinstance(row, list) and len(row) >= 4:
                    out.append(f"{row[0]}% Chance to cast level {row[1]} {row[2]} {row[3]}")
        else:
            out.append(f"{k}: {v}")
    return out


# ---------- besedilo uniquev/setov/runewordov s pd2.tools (wiki) ----------

def _norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("'s", "s"))


PD2T = {}
for _x in json.load(open(os.path.join(ROOT, "data", "pd2tools", "items.json"))):
    PD2T.setdefault(_norm(_x["gearId"]["name"]), []).append(_x)
SET_BONUS = {}
for _k, _v in list(PD2T.items()):
    for _x in _v:
        if _x["gearId"]["name"].startswith("Set Bonuses for "):
            SET_BONUS[_norm(_x["gearId"]["name"][len("Set Bonuses for "):])] = _x


def split_attrs(text):
    if not text:
        return []
    return [p.strip() for p in re.split(r",\s+(?=[^a-z\s])", text) if p.strip()]


def pd2t_lookup(name):
    n = _norm(name)
    if n in PD2T:
        return PD2T[n]
    near = difflib.get_close_matches(n, list(PD2T.keys()), n=1, cutoff=0.86)
    return PD2T[near[0]] if near else None


# ---------- aktualni wiki (glavni vir besedila za uniquee, sete, runeworde, charme) ----------

from html.parser import HTMLParser as _HP


class _WikiItems(_HP):
    """Razreže wiki stran po naslovih predmetov: info vrstice + vrstice tabele (celice)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections, self.cur = [], None
        self.in_head = self.in_info = self.in_p = self.in_td = self.in_th = False
        self.depth_info = 0
        self.buf, self.row, self.heads = [], None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h2", "h3", "h4", "h5"):
            self.in_head, self.buf = True, []
        elif tag == "div" and "item-info-box" in (a.get("class") or ""):
            self.in_info, self.depth_info = True, 1
        elif tag == "div" and self.in_info:
            self.depth_info += 1
        elif tag == "p" and self.in_info:
            self.in_p, self.buf = True, []
        elif tag == "tr" and self.cur is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.in_td, self.in_th, self.buf = tag == "td", tag == "th", []
        elif tag == "br" and (self.in_td or self.in_p):
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in ("h2", "h3", "h4", "h5") and self.in_head:
            self.in_head = False
            name = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            self.cur = {"name": name, "info": [], "rows": [], "head": []}
            self.sections.append(self.cur)
        elif tag == "p" and self.in_p:
            self.in_p = False
            line = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if line and self.cur is not None:
                self.cur["info"].append(line)
        elif tag == "div" and self.in_info:
            self.depth_info -= 1
            if self.depth_info == 0:
                self.in_info = False
        elif tag in ("td", "th") and self.row is not None and (self.in_td or self.in_th):
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if self.in_th:
                self.cur["head"].append(text)
            else:
                self.row.append(text)
            self.in_td = self.in_th = False
        elif tag == "tr" and self.row is not None:
            if self.row and self.cur is not None:
                self.cur["rows"].append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.in_head or self.in_p or self.in_td or self.in_th:
            self.buf.append(data)


WIKI = {}
_wdir = os.path.join(ROOT, "data", "wiki", "html")
if os.path.isdir(_wdir):
    for _f in sorted(os.listdir(_wdir)):
        _p = _WikiItems()
        _p.feed(json.load(open(os.path.join(_wdir, _f)))["parse"]["text"])
        for _sec in _p.sections:
            if _sec["rows"]:
                WIKI.setdefault(_norm(_sec["name"]), []).append(_sec)


def wiki_lookup(name):
    for cand in dict.fromkeys([name, name.split(" (")[0], re.sub(r"\s+(Weapon|Quiver)$", "", name.split(" (")[0])]):
        n = _norm(cand)
        if n in WIKI:
            return WIKI[n]
        near = difflib.get_close_matches(n, list(WIKI.keys()), n=1, cutoff=0.88)
        if near:
            return WIKI[near[0]]
    return None


def wiki_lines(sec):
    """Stolpec »After« (ali edini stolpec pri novih predmetih)."""
    out = []
    for row in sec["rows"]:
        cell = row[-1] if row else ""
        if cell and cell.lower() not in ("removed", "-"):
            out.append(cell)
    return out


def wiki_info(sec):
    base, req, info, runes, types = None, None, [], None, None
    for line in sec["info"]:
        if line.startswith("Required Level:"):
            req = line.split(":", 1)[1].strip()
        elif "•" in line:
            runes = " · ".join(x.strip() for x in line.split("•"))
        elif re.match(r"(Defense|Base Damage|One-Hand Damage|Two-Hand Damage|Required (Strength|Dexterity)|Block)", line):
            info.append(line)
        elif base is None and not re.match(r"(Base |Minimum Item Level|Occurrence|Durability)", line):
            base = line
    return base, req, info, runes


# ---------- HTML ----------

def tip_html(title, q, base=None, req=None, info=None, lines=(), extra=(), extra_title=None, runes=None, extra_cls="tt-set"):
    parts = [f'<div class="tt-name q-{q}">{e(title)}</div>']
    if base:
        parts.append(f'<div class="tt-base">{e(base)}</div>')
    if runes:
        parts.append(f'<div class="tt-runes">{e(runes)}</div>')
    if info:
        parts.append('<div class="tt-info">' + "".join(f"<div>{e(i)}</div>" for i in info) + "</div>")
    if req:
        parts.append(f'<div class="tt-req">Required Level: {e(str(req))}</div>')
    if lines:
        parts.append('<div class="tt-mods">' + "".join(f"<div>{e(l)}</div>" for l in lines) + "</div>")
    if extra:
        parts.append(f'<div class="{extra_cls}"><div class="tt-h">{e(extra_title or "")}</div>'
                     + "".join(f"<div>{e(l)}</div>" for l in extra) + "</div>")
    return "".join(parts)


def unique_tip(it, set_name=None):
    """Hiim unique/set zapis → (html)."""
    q = "u" if it.get("kind") == "unique" else "s"
    wk = wiki_lookup(it["name"])
    rows = None if wk else pd2t_lookup(it["name"])
    if wk:
        base, req, info, _r = wiki_info(wk[0])
        lines = wiki_lines(wk[0])
        req = req or it.get("reqLevel")
        base = base or it.get("baseName")
    elif rows:
        x = rows[0]
        lines = split_attrs(x.get("afterAttributes") or x.get("newAttributes"))
        req = (x.get("requiredLevel") or "").replace("Required Level:", "").strip() or it.get("reqLevel")
        info = [i for i in split_attrs(x.get("additionalInfo")) if re.match(r"(Defense|Base Damage|One-Hand|Two-Hand|Required (Strength|Dexterity)|Block)", i)]
        base = x.get("itemType")
    else:
        lines = mods_text(it.get("mods") or [])
        req, info, base = it.get("reqLevel"), [], it.get("baseName")
    extra = []
    if set_name:
        wsb = wiki_lookup("Set Bonuses for " + set_name)
        if wsb:
            extra = [l for l in wiki_lines(wsb[0]) if "Complete Set" in l or "Items)" in l]
        else:
            sb = SET_BONUS.get(_norm(set_name))
            if sb:
                extra = [l for l in split_attrs(sb.get("afterAttributes")) if "Complete Set" in l or "Items)" in l]
    return tip_html(it["name"], q, base=base, req=req, info=info, lines=lines, extra=extra,
                    extra_title=f"Set {set_name}" if set_name else None)


def runeword_tip(rw, runes_names):
    wk = wiki_lookup(rw["name"])
    if wk:
        out = ""
        for i, sec in enumerate(wk[:2]):
            base, req, info, runes = wiki_info(sec)
            block = tip_html(rw["name"], "r", base=base, req=req, lines=wiki_lines(sec),
                             runes=runes or " · ".join(runes_names))
            out += block if i == 0 else block.replace(f'<div class="tt-name q-r">{e(rw["name"])}</div>', "")
        return out
    rows = pd2t_lookup(rw["name"]) or []
    rows = [x for x in rows if x.get("runes")] or rows
    if rows:
        blocks = []
        for x in rows[:2]:
            blocks.append((x.get("itemType"), (x.get("requiredLevel") or "").replace("Required Level:", "").strip(),
                           split_attrs(x.get("afterAttributes") or x.get("newAttributes"))))
        base, req, lines = blocks[0]
        out = tip_html(rw["name"], "r", base=base, req=req, lines=lines, runes=" · ".join(runes_names))
        for b2, r2, l2 in blocks[1:]:
            out += tip_html("", "r", base=b2, req=r2, lines=l2).replace('<div class="tt-name q-r"></div>', "")
        return out
    lines = []
    for t in rw.get("txt", [])[:1]:
        lines = mods_text(t.get("mods") or [])
    return tip_html(rw["name"], "r", lines=lines, runes=" · ".join(runes_names))


def preset_tip(p, q):
    lines = stats_text(p.get("stats") or {}) if p.get("stats") else mods_text(p.get("mods") or [])
    wk = wiki_lookup(p["name"]) if q == "u" else None
    if wk:
        base, req, info, _r = wiki_info(wk[0])
        return tip_html(p["name"], q, base=base or p.get("baseName"), req=req or p.get("reqLevel"), lines=wiki_lines(wk[0]))
    rows = pd2t_lookup(p["name"]) if q == "u" else None
    if rows:
        lines = split_attrs(rows[0].get("afterAttributes") or rows[0].get("newAttributes")) or lines
    return tip_html(p["name"], q, base=p.get("baseName"), req=p.get("reqLevel"), lines=lines)


def custom_tip(item, q, base):
    return tip_html(item.get("name") or base or "Rare", q, base=base, lines=mods_text(item.get("mods") or []))


def socket_tip(s):
    if s.get("stats"):
        lines = stats_text(s["stats"])
    elif s.get("slots"):
        lines = []
        for slot, st in s["slots"].items():
            for l in stats_text(st):
                lines.append(f"{slot.title()}: {l}")
    else:
        lines = []
    return tip_html(s["name"], "r" if s.get("kind") == "rune" else "m", req=s.get("reqLevel"), lines=lines)


# ---------- skilli ----------

def wiki_prereqs():
    out = {}
    wdir = os.path.join(ROOT, "data", "wiki")
    for cls in ["Amazon", "Assassin", "Barbarian", "Druid", "Necromancer", "Paladin", "Sorceress"]:
        path = os.path.join(wdir, f"All_{cls}_Skills.txt")
        if not os.path.exists(path):
            continue
        t = open(path).read()
        for m in re.finditer(r"## ([^\n\[]+)\[edit\]", t):
            chunk = t[m.end():m.end() + 600]
            r = re.search(r"Required Skills: ([^\n]*)", chunk)
            if r:
                names = [re.sub(r"\s*\[\d+\]", "", x).strip() for x in r.group(1).split(",")]
                out[(cls.lower(), m.group(1).strip())] = [n for n in names if n and n != "None"]
    return out


PREREQS = wiki_prereqs()


def cooldown_text(cd):
    if isinstance(cd, list):
        vals = list(dict.fromkeys(str(x) for x in cd))
        return vals[0] if len(vals) == 1 else "–".join([vals[0], vals[-1]])
    return str(cd)


def skill_tip(cls, sid):
    s = SKILLS.get((cls, sid))
    if not s:
        return None
    desc = re.sub(r"(<br>\s*)+", "<br>", s.get("description") or "").strip("<br>")
    parts = [f'<div class="tt-name q-sk">{e(s["name"])}</div>',
             f'<div class="tt-base">{e(cls.title())} · Required Level: {s.get("reqLevel")}'
             + (f' · Cooldown: {e(cooldown_text(s["cooldown"]))} s' if s.get("cooldown") else "") + "</div>"]
    pre = PREREQS.get((cls, s["name"])) or PREREQS.get((cls, s["name"].replace("Summon Ravens", "Raven")))
    if pre:
        parts.append(f'<div class="tt-info"><div>Predpogoji: {e(", ".join(pre))}</div></div>')
    if desc:
        parts.append(f'<div class="tt-desc">{e(desc).replace("&lt;br&gt;", "<br>")}</div>')
    syn = s.get("synergies") or []
    if syn:
        parts.append('<div class="tt-syn"><div class="tt-h">Prejema bonuse od</div>'
                     + "".join(f'<div data-syn="{e(x.get("skill") or "")}">{e(x.get("text") or "")}</div>' for x in syn) + "</div>")
    gives = []
    for (c2, sid2), s2 in SKILLS.items():
        if c2 != cls:
            continue
        for x in s2.get("synergies") or []:
            if x.get("skill") == sid and x.get("text"):
                txt = x["text"].split(":", 1)[1].strip() if ":" in x["text"] else x["text"]
                gives.append((sid2, f'{s2["name"]}: {txt}'))
    if gives:
        parts.append('<div class="tt-syn"><div class="tt-h">Daje bonus</div>'
                     + "".join(f'<div data-syn="{e(k)}">{e(t)}</div>' for k, t in gives) + "</div>")
    return "".join(parts)
