"""Iz data/site.json in content/ zgradi statično stran v docs/ (GitHub Pages)."""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
CONTENT = os.path.join(ROOT, "content")
CAT = os.path.join(ROOT, "data", "hiim", "catalog")

TAGLINE = {
    "amazon": "Loki, samostreli, kopja in valkira.",
    "assassin": "Pasti, borilne veščine in senca.",
    "barbarian": "Whirlwind, metanje in bojni kriki.",
    "druid": "Elementi, preobrazbe in živali.",
    "necromancer": "Okostnjaki, golemi, strup in kosti.",
    "paladin": "Aure, Sacrifice in sveti napadi.",
    "sorceress": "Ogenj, led in strela.",
}
SLOT_LABEL = {"weapon": "Orožje", "offhand": "Druga roka", "helm": "Helm", "armor": "Oklep", "gloves": "Rokavice",
              "belt": "Pas", "boots": "Škornji", "amulet": "Amulet", "ring1": "Prstan", "ring2": "Prstan",
              "swapWeapon": "Switch", "swapOffhand": "Switch 2"}
PHASE_LABEL = {"start": "Začetek in leveling", "mid": "Prvi teden", "end": "Endgame"}
BOSS_LABEL = {"Easy": "lahko", "Moderate": "srednje", "Hard": "težko"}
BOSS_NAME = {"dclone": "Diablo Clone", "rathma": "Rathma", "lucion": "Lucion"}
MERC_LABEL = {"Fire Arrow": "Act 1 Fire (Vigor)", "Cold Arrow": "Act 1 Cold (Meditation)", "Physical Arrow": "Act 1 Physical",
              "Defensive Auras": "Act 2 Defiance", "Offensive Auras": "Act 2 Blessed Aim", "Combat Auras": "Act 2 Thorns",
              "Fire Spells": "Act 3 Fire (Cleansing)", "Cold Spells": "Act 3 Cold (Prayer)", "Lightning Spells": "Act 3 Lightning (Holy Shock)",
              "Might Merc": "Act 5 Might", "Warcries": "Act 5 Warcries"}
GROUP_LABEL = {"generalist": "splošna", "physical": "fizična", "elemental": "elementalna"}
OUR_GUIDES = {  # (razred, id builda) -> datoteka v content/builds
    ("assassin", "wake-of-fire"): "assassin--wake-of-fire.html",
    ("assassin", "chain-lightning-sentry"): "assassin--chain-lightning-sentry.html",
    ("sorceress", "charged-bolt"): "sorceress--charged-bolt.html",
    ("necromancer", "elemental-summoner-mage-skeles-ele-revives"): "necromancer--elemental-summoner-mage-skeles-ele-revives.html",
    ("druid", "cold-elemental-arctic-blast-hurricane"): "druid--cold-elemental-arctic-blast-hurricane.html",
}
DRUID_PLAN_BUILDS = {"summon-druid", "pure-poison-creeper", "rabies", "summons"}

e = html.escape


def load_names():
    names = {}
    items = json.load(open(os.path.join(CAT, "items.json")))["items"]
    for it in items:
        if it.get("image"):
            names.setdefault(it["name"], it["image"])
    for c in json.load(open(os.path.join(CAT, "charms.json"))):
        if c.get("image"):
            names.setdefault(c["name"], c["image"])
    return names


ITEM_IMG = load_names()


def _norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("'s", "s"))


_TN = json.load(open(os.path.join(ROOT, "data", "tip_names.json"))) if os.path.exists(os.path.join(ROOT, "data", "tip_names.json")) else {}
TIP_BY_NORM = {_norm(k): v for k, v in _TN.items()}


def tip_for_name(name):
    import difflib
    n = _norm(html.unescape(name))
    if n in TIP_BY_NORM:
        return TIP_BY_NORM[n]
    near = difflib.get_close_matches(n, list(TIP_BY_NORM), n=1, cutoff=0.88)
    return TIP_BY_NORM[near[0]] if near else None


def add_tips_to_fragment(frag):
    """V naših vodičih doda tooltipe imenom predmetov (span.item in td.q-r)."""
    def repl(m):
        key = tip_for_name(re.sub(r"<[^>]+>", "", m.group(3)))
        if not key:
            return m.group(0)
        return f'<{m.group(1)} class="{m.group(2)}" data-tip="{e(key)}" tabindex="0">{m.group(3)}</{m.group(1)}>'
    frag = re.sub(r'<(span) class="(item q-[usrmy])">(.*?)</span>', repl, frag)
    frag = re.sub(r'<(td) class="(q-r)">(.*?)</td>', repl, frag)
    return frag


def has_img(path):
    return path and os.path.exists(os.path.join(DOCS, "img", path))


def img_tag(path, cls="", alt=""):
    if not has_img(path):
        return ""
    src = "img/" + "/".join(p for p in path.split("/"))
    return f'<img class="{cls}" src="{e(src)}" alt="{e(alt)}" loading="lazy">'


def tier_class(t):
    return "t-" + re.sub(r"[^a-z]+", "-", (t or "").lower()).strip("-")


def fmt_time(sec):
    return f"{sec // 60}:{sec % 60:02d}"


# ---------- komponente ----------

def item_html(slot, it):
    q = it.get("q", "m")
    name = e(it["name"]) + (" (eth)" if it.get("eth") else "")
    parts = []
    if it.get("runes"):
        rn = "".join(f'<span class="rn"{(" data-tip=" + chr(34) + e(r["tip"]) + chr(34)) if r.get("tip") else ""}>{img_tag(r.get("img"), alt=r["name"])}{e(r["name"])}</span>' for r in it["runes"])
        parts.append(rn)
    if it.get("base") and q in ("r", "y", "c", "m"):
        parts.append(e(it["base"]))
    if it.get("sockets"):
        parts.append("v socketih: " + ", ".join((f'{s["n"]}× ' if s.get("n", 1) > 1 else "") + e(s["name"]) for s in it["sockets"]))
    if it.get("corr"):
        parts.append("korupcija: " + e(it["corr"]))
    sub = f'<span class="sub2">{" · ".join(parts)}</span>' if parts else ""
    label = f'<span class="sl">{e(SLOT_LABEL.get(slot, slot))}</span>' if slot else ""
    attrs = ""
    if it.get("tip"):
        attrs = f' data-tip="{e(it["tip"])}" tabindex="0"'
        if it.get("eth"):
            attrs += ' data-eth="1"'
        if it.get("corr"):
            attrs += f' data-corr="{e(it["corr"])}"'
        if it.get("sockets"):
            attrs += ' data-sock="' + e(", ".join((f'{s["n"]}× ' if s.get("n", 1) > 1 else "") + s["name"] for s in it["sockets"])) + '"'
    return (f'<div class="it"{attrs}><span class="ic">{img_tag(it.get("img"), alt=it["name"])}</span>'
            f'{label}<span class="nm q-{q}">{name}</span>{sub}</div>')


def plural(n, one, two, few, many):
    """Slovenska dvojina in množina: 1 runa, 2 runi, 3 rune, 5 run (101 runa, 102 runi ...)."""
    k = n % 100
    word = one if k == 1 else two if k == 2 else few if k in (3, 4) else many
    return f"{n} {word}"


def slot_label(who):
    merc = who.startswith("merc ")
    slot = who[5:] if merc else who
    lab = SLOT_LABEL.get(slot, slot)
    return ("Merc · " + lab) if merc else lab


def rune_chips(runes):
    out = []
    for r in runes:
        why = ", ".join(r.get("for") or [])
        cls = "rch hr" if r.get("rank", 0) >= 21 else "rch"
        out.append(f'<span class="{cls}" data-tip="{e(r["tip"])}" tabindex="0"' + (f' title="{e(why)}"' if why else "") + '>'
                   f'{img_tag(r.get("img"), alt=r["name"])}{e(r["name"])}' + (f' <b>×{r["n"]}</b>' if r["n"] > 1 else "") + "</span>")
    return '<div class="rune-row">' + "".join(out) + "</div>"


def recipes_html(rec):
    if not rec:
        return ""
    n_runes = sum(r["n"] for r in rec["runes"])
    head = []
    if n_runes:
        head.append(plural(n_runes, "runa", "runi", "rune", "run"))
    if rec["rw"]:
        head.append(plural(len(rec["rw"]), "runeword", "runeworda", "runewordi", "runewordov"))
    if rec["crafts"]:
        head.append(plural(len(rec["crafts"]), "craft", "crafta", "crafti", "craftov"))
    rows = []
    for rw in rec["rw"]:
        base = f'{e(rw["base"] or "baza")}{" (eth)" if rw.get("eth") else ""}, {rw["n"]} os'
        how = []
        if rw.get("larzuk"):
            how.append(f'Larzuk (A5 quest) na beli bazi da točno {rw["n"]} os')
        if rw.get("cube"):
            how.append("cube: " + e(rw["cube"]))
        rows.append(f'<div class="rrow"><span><span class="nm q-r" data-tip="{e(rw["tip"])}" tabindex="0">{e(rw["name"])}</span>'
                    f'<span class="sl">{e(slot_label(rw["slot"]))}</span></span>'
                    f'<span class="runes-c">{" · ".join(e(x) for x in rw["runes"])}</span>'
                    f'<span>Bela ali superior baza: {base}' + (f'<span class="muted">{" · ".join(how)}</span>' if how else "") + "</span></div>")
    for c in rec["crafts"]:
        alt = (f'<span class="muted">ali: {e(" + ".join(c["alt"]))} + baza (infuzije padajo od Treasure Fallen v mapah)</span>' if c.get("alt") else "")
        rows.append(f'<div class="rrow"><span><span class="nm q-c" data-tip="{e(c["tip"])}" tabindex="0">{e(c["name"])}</span>'
                    f'<span class="sl">{e(slot_label(c["slot"]))}</span></span>'
                    f'<span class="runes-c">{e(" + ".join(c["ing"]))}</span>'
                    f'<span>+ magic ali rare {e(c["type"].lower())}{"; eth baza da eth craft" if c.get("eth") else ""}{alt}</span></div>')
    body = (rune_chips(rec["runes"]) if rec["runes"] else "") + ('<div class="rtable">' + "".join(rows) + "</div>" if rows else "")
    return (f'<details class="recipes"><summary>Recepti in rune <span class="muted">· {", ".join(head)}</span></summary>'
            f'<div class="rec-body">{body}<span class="muted note-s">Rune v cubu: 3 enake (od Pul naprej 2) + Key da naslednjo. '
            f'Vse rune in baze: <a href="predmeti.html">wiki predmetov</a>.</span></div></details>')


def planner_html(p):
    head = (f'<div class="planner-head"><span class="ph">{e(PHASE_LABEL[p["phase"]])}</span>'
            f'<b>{e(p.get("title") or p.get("label") or "")}</b>'
            f'<span class="muted">level {p.get("level") or "?"}'
            + (f' · {e(p["author"])}' if p.get("author") else "") + "</span></div>")
    stats = p.get("stats") or {}
    st = ""
    if any(stats.values()):
        st = (f'<div class="muted" style="font-size:0.9rem">Stati: Str {stats.get("str", 0)} · Dex {stats.get("dex", 0)} · '
              f'Vit {stats.get("vit", 0)} · Ene {stats.get("ene", 0)}</div>')
    skills = "".join(
        f'<span class="sk{" max" if s["pts"] >= 20 else ""}" data-skill="{e(s["id"])}" data-pts="{s["pts"]}"'
        + (f' data-tip="{e(s["tip"])}" tabindex="0"' if s.get("tip") else "") + '>'
        f'{img_tag(s.get("img"), alt=s["name"])}{e(s["name"])} <span class="pts">{s["pts"]}</span></span>' for s in p["skills"])
    gear = "".join(item_html(slot, it) for slot, it in p["gear"].items())
    out = [head, st]
    if skills:
        out.append(f'<div class="skills">{skills}</div>')
    if p.get("progression"):
        prog = " → ".join(f'{e(r["skill"])} {r["target"]}' for r in p["progression"])
        out.append(f'<div class="muted" style="font-size:0.9rem">Vrstni red točk: {prog}</div>')
    if gear:
        out.append(f'<div class="gearset">{gear}</div>')
    if p.get("charms"):
        out.append('<div class="gearset">' + "".join(item_html("", c) for c in p["charms"]) + "</div>")
    m = p.get("merc")
    if m:
        mg = "".join(item_html(slot, it) for slot, it in m["gear"].items())
        out.append(f'<div class="merc"><h4>Merc: {e(m["name"])}</h4><div class="gearset">{mg}</div></div>')
    out.append(recipes_html(p.get("recipes")))
    if p.get("url"):
        out.append(f'<div class="links"><a href="{e(p["url"])}" target="_blank" rel="noopener">Odpri v Hiim planerju</a>'
                   + (f' <a href="{e(p["video"])}" target="_blank" rel="noopener">Video</a>' if p.get("video") else "") + "</div>")
    return '<div class="planner">' + "".join(out) + "</div>"


def leveling_html(b, cls):
    main = b.get("main") or {}
    req = main.get("req")
    r = b.get("respec") or {}
    early, same = r.get("early", 0), r.get("same", 0)
    has_start = any(p["phase"] == "start" for p in b["planners"])
    starters = [s for s in cls["starters"] if s != (b.get("starter") or {}).get("name")]
    if b.get("starter") or (early >= 3 and same / early >= 0.6):
        mode = "direct"
    elif early >= 3:
        mode = "mixed" if same / early >= 0.35 else "respec"
    else:
        mode = "direct" if (req or 99) <= 18 else "unknown"
    title = {"direct": "Brez respeca", "mixed": "Brez respeca ali z njim, oboje je pogosto",
             "respec": "Najlažje z drugim buildom in respecom", "unknown": "Leveling z drugim buildom, respec kasneje"}[mode]
    lines = []
    if main.get("name") and req:
        lines.append(f'Glavni skill {e(main["name"])} je na voljo od levela {req}.')
    end_pl = next((p for p in reversed(b["planners"]) if p["skills"]), None)
    used = {s["name"] for s in end_pl["skills"]} if end_pl else set()
    syn = [n for n in main.get("syn", []) if n in used]
    if req and req >= 18 and mode in ("direct", "mixed") and syn:
        lines.append(f"Do levela {req} vlagaj v sinergije, ki jih build kasneje rabi ({e(', '.join(syn))}), potem v {e(main['name'])}.")
    if b.get("starter"):
        tags = ", ".join(b["starter"]["tags"])
        lines.append("Hiim ga ima za starter build" + (f" (farma: {e(tags)})." if tags else "."))
    if early >= 3:
        lines.append(f"V S13 je {same} od {early} najhitrejših igralcev imelo ta skill že na levelu 80."
                     + (f" Do levela 95 so prišli v mediani {str(r['day95']).replace('.', ',')}. dan sezone." if r.get("day95") else ""))
        other = [n for n, _ in r.get("firstSkills", []) if n != (b.get("stats") or {}).get("skill")]
        if mode != "direct" and other:
            lines.append("Ostali so na levelu 80 večinoma igrali: " + e(", ".join(other[:3])) + ".")
    if has_start:
        lines.append("Med planerji spodaj je tudi začetni (leveling) planer.")
    if mode != "direct" and starters:
        lines.append("Starter buildi za ta razred (Hiim): " + e(", ".join(starters)) + ". Respec: Akara (enkrat na težavnost) ali Token of Absolution.")
    return (f'<div class="leveling"><span class="mode">{title}</span>'
            + "".join(f"<span>{l}</span>" for l in lines) + "</div>"), mode


def ratings_html(b):
    cells = []
    clear = b.get("clear")
    cv = (f'{e(clear["map"])} {fmt_time(clear["time"])} (S{clear["season"]})' if clear else "še ni časa")
    cells.append(f'<div class="rate"><span class="rl">Mapping (solo)</span><span class="rv {tier_class(b["tier"])}">{e(b["tier"])}</span>'
                 f'<span class="muted" style="font-size:0.88rem">Najhitrejša mapa: {cv}</span></div>')
    boss = b.get("boss") or {}
    if boss:
        rows = "".join(
            f'<tr><td>{BOSS_NAME.get(k, k)}</td>'
            f'<td class="b-{(v.get("t0") or "").lower()}">{BOSS_LABEL.get(v.get("t0"), "—")}</td>'
            f'<td class="b-{(v.get("t2") or "").lower()}">{BOSS_LABEL.get(v.get("t2"), "—")}</td></tr>'
            for k, v in sorted(boss.items()))
        cells.append(f'<div class="rate"><span class="rl">Bossing</span><table><tr><th></th><th>T0</th><th>T2</th></tr>{rows}</table></div>')
    else:
        cells.append('<div class="rate"><span class="rl">Bossing</span><span class="muted">Hiim ga ne ocenjuje</span></div>')
    if b.get("group"):
        g = ", ".join(f'{GROUP_LABEL.get(x["list"], x["list"])}: <span class="{tier_class(x["tier"])}">{e(x["tier"])}</span>' for x in b["group"])
        cells.append(f'<div class="rate"><span class="rl">Party</span><span>{g}</span></div>')
    st = b.get("stats")
    if st:
        ratio = round(st["n95"] / st["n90"] * 100) if st.get("n90") else 0
        cells.append(f'<div class="rate"><span class="rl">S13 (pd2.tools)</span><span class="rv">{st["n90"]} likov 90+</span>'
                     f'<span class="muted" style="font-size:0.88rem">{ratio} % jih je prišlo do 95+</span></div>')
    return '<div class="ratings">' + "".join(cells) + "</div>"


def stats_html(st):
    if not st:
        return ""
    def top_item(n, p):
        key = tip_for_name(n)
        attr = f' data-tip="{e(key)}" tabindex="0"' if key else ""
        return f'<span{attr}>{img_tag(ITEM_IMG.get(n), alt=n)}{e(n)} <span class="muted">{p} %</span></span>'
    top = "".join(top_item(n, p) for n, p in st.get("items", [])[:12])
    merc = ", ".join(f"{e(MERC_LABEL.get(n, n))} {p} %" for n, p in st.get("mercs", []))
    return (f'<div class="stats13"><h4>Kaj nosijo liki 90+ v S13 (skill {e(st["skill"])} na 20)</h4>'
            f'<div class="top">{top}</div>' + (f'<span class="muted">Merc: {merc}</span>' if merc else "") + "</div>")


def build_html(b, cls):
    main = b.get("main") or {}
    lev, mode = leveling_html(b, cls)
    badges = [f'<span class="badge {tier_class(b["tier"])}">{e(b["tier"])}</span>']
    if b.get("starter") and b["tier"] != "Starter":
        badges.append('<span class="badge t-starter">Starter</span>')
    dc = (b.get("boss") or {}).get("dclone") or {}
    meta = []
    if dc.get("t0") or dc.get("t2"):
        meta.append(f'DClone {BOSS_LABEL.get(dc.get("t0") or dc.get("t2"), "")}')
    meta.append({"direct": "brez respeca", "mixed": "respec po želji", "respec": "z respecom",
                 "unknown": "leveling z drugim buildom"}[mode])
    if b.get("stats"):
        meta.append(f'{b["stats"]["n90"]} likov 90+ v S13')
    guide_file = OUR_GUIDES.get((cls["id"], b["id"]))
    if guide_file:
        badges.append('<span class="badge" style="color:var(--accent)">naš vodič</span>')
    summary = (f'<summary>{img_tag(main.get("img"), "skico lg", main.get("name", ""))}'
               f'<span class="bn"><b>{e(b["name"])}</b><span class="meta">{"".join(f"<span>{m}</span>" for m in meta)}</span></span>'
               f'<span class="badges">{"".join(badges)}</span></summary>')
    body = [ratings_html(b), f"<div><h4>Leveling</h4>{lev}</div>"]
    if guide_file:
        body.append('<div><h4>Naš vodič</h4>' + add_tips_to_fragment(open(os.path.join(CONTENT, "builds", guide_file)).read()) + "</div>")
    if cls["id"] == "druid" and b["id"] in DRUID_PLAN_BUILDS:
        body.append('<div class="note"><b>Naš druid plan:</b> leveling kot summoner, nato Poison Creeper ali Rabies. '
                    '<a href="druid-nacrt.html">Odpri druid plan</a>.</div>')
    if b.get("runes_total"):
        n = sum(r["n"] for r in b["runes_total"])
        body.append(f'<div class="runes-total"><h4>Rune za ves build ({n})</h4>{rune_chips(b["runes_total"])}'
                    '<span class="muted">Vse faze skupaj: vsak runeword šteje enkrat, zraven so rune za sockete in crafte. '
                    'Recepti so pri vsakem planerju pod »Recepti in rune«.</span></div>')
    if b["planners"]:
        body.append("<div><h4>Planerji (Hiim)</h4>" + "".join(planner_html(p) for p in b["planners"]) + "</div>")
    else:
        body.append('<div class="muted">Hiim za ta build nima planerja.</div>')
    body.append(stats_html(b.get("stats")))
    if b.get("links"):
        links = "".join(f'<a href="{e(l["url"])}" target="_blank" rel="noopener">{e(l.get("label") or "Povezava")}</a>' for l in b["links"] if l.get("url"))
        body.append(f'<div><h4>Video in vodiči</h4><div class="links">{links}</div></div>')
    if b.get("clear") and b["clear"].get("video"):
        body.append(f'<div class="links"><a href="{e(b["clear"]["video"])}" target="_blank" rel="noopener">Video najhitrejše mape ({e(b["clear"].get("player") or "")})</a></div>')
    starter_attr = "1" if b.get("starter") else "0"
    return (f'<details class="build" id="b-{e(b["id"])}" data-tier="{e(b["tier"])}" data-starter="{starter_attr}" '
            f'data-guide="{1 if guide_file else 0}">{summary}<div class="build-body">{"".join(body)}</div></details>')


# ---------- strani ----------

def page(title, body, current, desc, extra_head="", body_class=""):
    nav = [("index.html", "Razredi")] + [(f'{c["id"]}.html', c["name"]) for c in SITE["classes"]] + [
        ("predmeti.html", "Predmeti"), ("druid-nacrt.html", "Druid plan"), ("vodic.html", "Vodič")]
    nav_html = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{e(t)}</a>' for h, t in nav)
    return f"""<!doctype html>
<html lang="sl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="img/{e(SITE["classes"][3]["builds"][0]["main"]["img"])}">
{extra_head}
</head>
<body class="{body_class}">
<div class="topbar"><div class="wrap"><a class="brand" href="index.html">PD2 <span>S14</span> buildi</a><nav aria-label="Strani">{nav_html}</nav></div></div>
{body}
<footer><div class="wrap credits">
<span>Viri: <a href="https://hiimpd2.com/solo" target="_blank" rel="noopener">Hiim PD2</a> (S14 tier liste in planerji, stanje {SITE["updated"]}), <a href="https://pd2.tools" target="_blank" rel="noopener">pd2.tools</a> (S13 statistika), <a href="https://wiki.projectdiablo2.com" target="_blank" rel="noopener">PD2 wiki</a> in S14 Alliance tentative patch notes.</span>
<span>Slike predmetov in skillov so last Blizzard Entertainmenta (Diablo II), prevzete iz Hiim planerja. Neuradna stran skupnosti, brez povezave z Blizzardom ali ekipo Project Diablo 2.</span>
</div></footer>
<script src="assets/app.js"></script>
</body>
</html>
"""


def index_html():
    cards = []
    for c in SITE["classes"]:
        counts = {}
        for b in c["builds"]:
            counts[b["tier"]] = counts.get(b["tier"], 0) + 1
        top = c["builds"][0]
        cnt = "".join(f'<span class="badge {tier_class(t)}">{n} {e(t)}</span>' for t, n in counts.items())
        lst = "".join(f'<li><span>{e(b["name"])}</span><span class="{tier_class(b["tier"])}">{e(b["tier"])}</span></li>' for b in c["builds"][:4])
        cards.append(f'<a class="class-card" href="{c["id"]}.html"><span class="ch">{img_tag(top["main"]["img"], "skico lg", top["main"]["name"])}'
                     f'<span><h3>{e(c["name"])}</h3><span class="muted" style="font-size:0.92rem">{e(TAGLINE[c["id"]])}</span></span></span>'
                     f'<span class="counts">{cnt}</span><ul>{lst}</ul></a>')
    total = sum(len(c["builds"]) for c in SITE["classes"])
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Project Diablo 2 · Season 14 Alliance · začetek 23. 10. 2026</div>
<h1>Buildi za <span>S14</span></h1>
<p class="lead">Izberi razred. Pri vsakem so vsi buildi, ki jih Hiim za S14 ocenjuje kot Top, Good ali Decent, in vsi njihovi starter buildi: skupaj {total}. Za vsakega je ocena za mapping in bossing, kako ga levelaš, planerji z opremo po fazah in merc ter S13 statistika s pd2.tools.</p>
</div></header>
<main class="wrap">
<section><div class="sec-head"><div class="eyebrow">Razredi</div><h2>Izberi razred</h2></div>
<div class="class-grid">{"".join(cards)}</div></section>
<section><div class="sec-head"><div class="eyebrow">Naši vodiči</div><h2>Kje začeti</h2></div>
<div class="cols">
<a class="class-card" href="druid-nacrt.html"><h3>Druid plan</h3><span class="muted">Leveling kot summoner, nato Poison Creeper ali Rabies. Točke po levelih, oprema v treh fazah, merc, breakpointi.</span></a>
<a class="class-card" href="predmeti.html"><h3>Wiki predmetov</h3><span class="muted">Iskalnik po vseh uniquih, setih, runewordih, craftih, runah in bazah: statsi z razponi, recepti in kateri buildi jih nosijo.</span></a>
<a class="class-card" href="vodic.html"><h3>Splošni vodič</h3><span class="muted">Kaj pobirati, budget runewordi, crafting, recepti v cubu, mape za začetnika in S14 spremembe.</span></a>
<div class="class-card"><h3>PDF za tisk</h3><span class="muted">Druid plan in budget mapper vodič na A4, s kvadratki za kljukice.</span><span class="links"><a href="pdf/Druid-nacrt-S14.pdf">Druid plan (PDF)</a><a href="pdf/Budget-mapper-S14.pdf">Budget mapper (PDF)</a></span></div>
<a class="class-card" href="assassin.html#b-chain-lightning-sentry"><h3>Za novinca</h3><span class="muted">Najlažji budget mapperji: lightning trapsin, Fire Blast trapsin, wind druid, skeleton necro in lightning sorc imajo naš podroben vodič.</span></a>
</div></section>
<section><div class="sec-head"><div class="eyebrow">Legenda</div><h2>Kako brati ocene</h2></div>
<div class="cols">
<div class="panel"><h4>Mapping</h4><p>Hiim solo tier lista: <span class="t-top">Top</span>, <span class="t-good">Good</span>, <span class="t-decent">Decent</span>. Ocena izhaja iz najhitrejših čiščenj map. <span class="t-starter">Starter</span> pomeni poceni build za začetek sezone.</p></div>
<div class="panel"><h4>Bossing</h4><p>Hiim bossing lista za Diablo Clone, Rathmo in Luciona: <span class="b-easy">lahko</span>, <span class="b-moderate">srednje</span>, <span class="b-hard">težko</span>. T0 je osnovna, T2 najtežja različica bossa.</p></div>
<div class="panel"><h4>Leveling</h4><p>Iz zahtevanega levela glavnega skilla, Hiim starter liste in S13 posnetkov s pd2.tools: koliko najhitrejših igralcev je imelo build že na levelu 80.</p></div>
</div></section>
</main>"""
    return page("PD2 S14 buildi", body, "index.html",
                "Vsi viable Project Diablo 2 S14 buildi po razredih: ocene, leveling, oprema, merc in bossing.")


def class_html(c):
    builds = "".join(build_html(b, c) for b in c["builds"])
    others = ""
    if c["others"]:
        others = '<p class="others">Ostali na Hiim listi (Mid ali Bad): ' + ", ".join(
            f'{e(o["name"])} ({e(o["tier"])})' for o in c["others"]) + ".</p>"
    tiers = []
    for b in c["builds"]:
        if b["tier"] not in tiers:
            tiers.append(b["tier"])
    fbtn = '<button type="button" data-f="all" aria-pressed="true">Vsi</button>' + "".join(
        f'<button type="button" data-f="{e(t)}" aria-pressed="false">{e(t)}</button>' for t in tiers if t != "Starter")
    fbtn += '<button type="button" data-f="starter" aria-pressed="false">Starter</button>'
    if any(OUR_GUIDES.get((c["id"], b["id"])) for b in c["builds"]):
        fbtn += '<button type="button" data-f="guide" aria-pressed="false">Naš vodič</button>'
    plan = ""
    if c["id"] == "druid":
        plan = '<div class="note" style="margin-bottom:14px"><b>Naš druid plan:</b> leveling kot summoner, nato Poison Creeper ali Hiimov Top Rabies. <a href="druid-nacrt.html">Odpri druid plan</a>.</div>'
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Razred · {len(c["builds"])} buildov</div>
<h1>{e(c["name"])}</h1>
<p class="lead">{e(TAGLINE[c["id"]])} Klikni build za ocene, leveling, planerje z opremo in merca. Za statse predmeta ali sinergije skilla premakni miško nanj ali ga tapni.</p>
</div></header>
<main class="wrap"><section>
{plan}
<div class="filters" role="group" aria-label="Filter">{fbtn}<span class="muted" id="fcount"></span></div>
{builds}
{others}
</section></main>"""
    return page(f"{c['name']} · PD2 S14 buildi", body, f"{c['id']}.html",
                f"Viable {c['name']} buildi za Project Diablo 2 S14 z ocenami, levelingom, opremo in mercem.")


def guide_html():
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Za vse razrede</div>
<h1>Splošni vodič</h1>
<p class="lead">Kaj pobirati, budget runewordi, crafting, recepti v Horadric Cubu, mape za začetnika in S14 spremembe.</p>
</div></header>
<main class="wrap">{add_tips_to_fragment(open(os.path.join(CONTENT, "guide-general.html")).read())}</main>"""
    return page("Splošni vodič · PD2 S14 buildi", body, "vodic.html",
                "Loot, runewordi, crafting, recepti in mape za Project Diablo 2 S14.")


def items_page_html():
    cats = [("all", "Vse"), ("unique", "Unique"), ("set", "Set"), ("runeword", "Runeword"), ("craft", "Craft"),
            ("rune", "Rune"), ("gemjewel", "Jeweli in dragulji"), ("charm", "Charmi"), ("base", "Baze")]
    cbtn = "".join(f'<button type="button" data-c="{k}" aria-pressed="{str(k == "all").lower()}">{e(t)}</button>' for k, t in cats)
    slots = [("", "Vsi"), ("weapon", "Orožje"), ("offhand", "Druga roka"), ("helm", "Helm"), ("armor", "Oklep"),
             ("gloves", "Rokavice"), ("belt", "Pas"), ("boots", "Škornji"), ("amulet", "Amulet"), ("ring", "Prstan"),
             ("charm", "Charm"), ("socket", "Socket")]
    sopt = "".join(f'<option value="{k}">{e(t)}</option>' for k, t in slots)
    copt = '<option value="">Vsi</option>' + "".join(f'<option value="{c["id"]}">{e(c["name"])}</option>' for c in SITE["classes"])
    phopt = "".join(f'<option value="{k}">{e(t)}</option>' for k, t in [("", "Vse"), ("s", "Začetek in leveling"), ("m", "Prvi teden"), ("e", "Endgame")])
    sorts = [("use", "Največ buildov"), ("s13", "S13 priljubljenost"), ("name", "Ime"), ("req", "Level naraščajoče"), ("reqd", "Level padajoče")]
    sortopt = "".join(f'<option value="{k}">{e(t)}</option>' for k, t in sorts)
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Wiki predmetov · S14</div>
<h1>Predmeti</h1>
<p class="lead">Uniqui, seti, runewordi, crafti, rune, jeweli, charmi in baze. Pri vsakem so statsi z razponi, recept (rune, socketi, craft, nadgradnja) in buildi s te strani, ki ga nosijo, po fazah.</p>
</div></header>
<main class="wrap"><section>
<form class="wfilters" role="search" onsubmit="return false">
<label class="wsearch"><span class="sr-only">Iskanje</span><input type="search" id="wq" placeholder="Išči po imenu ali statsu: Shako, Enigma, Faster Cast Rate, Ber" autocomplete="off" spellcheck="false"></label>
<div class="filters" role="group" aria-label="Vrsta predmeta">{cbtn}</div>
<div class="wsel">
<label>Slot<select id="wslot">{sopt}</select></label>
<label>Razred v buildih<select id="wcls">{copt}</select></label>
<label>Faza<select id="wph">{phopt}</select></label>
<label>Level do<input type="number" id="wreq" min="1" max="99" inputmode="numeric" placeholder="99"></label>
<label>Razvrsti<select id="wsort">{sortopt}</select></label>
<label class="chk"><input type="checkbox" id="wused"> samo predmeti iz buildov</label>
</div>
</form>
<div class="wcount" id="wcount" aria-live="polite">Nalagam predmete …</div>
<div id="wlist" class="wlist"></div>
<button type="button" id="wmore" class="wmore" hidden>Pokaži več</button>
<noscript><p>Wiki predmetov potrebuje JavaScript.</p></noscript>
<p class="muted note-s" style="margin-top:18px">Statsi so s PD2 wikija (stanje pred S14, razponi v oglatih oklepajih), novi S14 predmeti s Hiim planerja. Recepti za sockete, nadgradnje in rune so z wikija (Horadric Cube), crafti s Hiim planerja. »S13« je delež likov 90+ v S13, ki so predmet nosili (pd2.tools).</p>
</section></main>"""
    return page("Predmeti · PD2 S14 buildi", body, "predmeti.html",
                "Wiki predmetov za Project Diablo 2 S14: statsi, recepti in buildi, ki predmet uporabljajo.",
                extra_head='<script src="assets/items.js" defer></script>', body_class="page-items")


def druid_plan_html():
    header = open(os.path.join(CONTENT, "druid-plan-header.html")).read()
    main = add_tips_to_fragment(open(os.path.join(CONTENT, "druid-plan-main.html")).read())
    script = open(os.path.join(CONTENT, "druid-plan-script.html")).read()
    druid = next(c for c in SITE["classes"] if c["id"] == "druid")
    rabies = next((b for b in druid["builds"] if b["id"] == "rabies"), None)
    rab_html = ""
    if rabies:
        rab_html = f"""
<section id="rabies">
  <div class="sec-head">
    <div class="eyebrow">Druga pot po respecu · Hiim S14 Top</div>
    <h2>Varianta: Rabies werewolf</h2>
    <p>Hiim v S14 uvršča Rabies med Top buildi za mapping, na bossih je lahek (DClone T0, Rathma). To je melee werewolf: Rabies, Feral Rage in Lycanthropy po 20, Poison Creeper in Carrion Vine pa sta sinergiji. Naš creeper plan je caster različica iste ideje. Hiim je ne ocenjuje, v S13 pa je do 95+ prišlo 23 % takih druidov. Leveling kot summoner ostane enak, razlikuje se le respec.</p>
  </div>
  {build_html(rabies, druid).replace('<details class="build"', '<details class="build" open')}
</section>"""
    reset = '<div class="wrap" style="padding-block:18px"><button type="button" class="reset" id="reset-checks">Počisti kljukice</button></div>'
    body = header + '\n<main class="wrap">' + main + rab_html + "</main>\n" + reset + "\n" + script
    return page("Druid plan · PD2 S14 buildi", body, "druid-nacrt.html",
                "Druid za PD2 S14: leveling kot summoner, nato Poison Creeper ali Rabies.", body_class="page-druid")


def main():
    global SITE
    SITE = json.load(open(os.path.join(ROOT, "data", "site.json")))
    os.makedirs(DOCS, exist_ok=True)
    open(os.path.join(DOCS, "index.html"), "w").write(index_html())
    for c in SITE["classes"]:
        open(os.path.join(DOCS, f"{c['id']}.html"), "w").write(class_html(c))
    open(os.path.join(DOCS, "vodic.html"), "w").write(guide_html())
    open(os.path.join(DOCS, "druid-nacrt.html"), "w").write(druid_plan_html())
    open(os.path.join(DOCS, "predmeti.html"), "w").write(items_page_html())
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    sizes = {f: os.path.getsize(os.path.join(DOCS, f)) for f in os.listdir(DOCS) if f.endswith(".html")}
    print(sizes)


if __name__ == "__main__":
    main()
