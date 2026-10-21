"""Iz data/site.json in content/ zgradi statično stran v docs/ (GitHub Pages)."""
import hashlib
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
            f'<div class="rec-body">{body}<span class="muted note-s">Rune v cubu: 3 enake (od Pul naprej 2) dajo naslednjo, v S14 brez ključa. '
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


_vp = os.path.join(CONTENT, "videos.json")
VIDEOS = {k: v for k, v in json.load(open(_vp)).items() if not k.startswith("_")} if os.path.exists(_vp) else {}
MISSING_VIDEO_ITEMS = set()


def item_q(key):
    """Kakovost predmeta (barva) iz kataloga predmetov po ključu tooltipa."""
    if not key:
        return None
    for it in ITEMS.get("items", []):
        if it["k"] == key or key in (it.get("a") or []):
            return it["q"]
    return None


def vid_text(s):
    """Besedilo povzetka: {{Ime}} postane predmet s tooltipom."""
    out, pos = [], 0
    for m in re.finditer(r"\{\{(.+?)\}\}", s or ""):
        out.append(e(s[pos:m.start()]))
        name = m.group(1)
        key = tip_for_name(name)
        if key:
            out.append(f'<span class="item q-{item_q(key) or "u"}" data-tip="{e(key)}" tabindex="0">{e(name)}</span>')
        else:
            MISSING_VIDEO_ITEMS.add(name)
            out.append(e(name))
        pos = m.end()
    out.append(e((s or "")[pos:]))
    return "".join(out)


def videos_html(cls, b):
    vs = VIDEOS.get(f'{cls["id"]}/{b["id"]}')
    if not vs:
        return ""
    cards = []
    for v in vs:
        season_cls = "t-starter" if v["season"].startswith("S14") else "t-brez-ocene"
        rows = "".join(f"<dt>{lab}</dt><dd>{vid_text(v[k])}</dd>" for k, lab in
                       (("skills", "Skilli"), ("stats", "Stati"), ("gear", "Oprema"), ("merc", "Merc")) if v.get(k))
        tips = "".join(f"<li>{vid_text(t)}</li>" for t in v.get("tips") or [])
        vs_h = ""
        if v.get("vs_hiim"):
            vs_h = ('<div class="vid-vs"><b>Primerjava s Hiim S14 planerjem</b><ul class="plain">'
                    + "".join(f"<li>{vid_text(t)}</li>" for t in v["vs_hiim"]) + "</ul></div>")
        cards.append(f'<article class="vid"><div class="vid-h"><a href="{e(v["url"])}" target="_blank" rel="noopener">{e(v["title"])}</a>'
                     f'<span class="vid-meta"><span class="badge {season_cls}">{e(v["season"])}</span> {e(v["author"])} · {e(v["date"])}</span>'
                     f'<span class="muted note-s">{e(v["part"])}</span></div>'
                     + (f'<dl class="kv">{rows}</dl>' if rows else "")
                     + (f'<ul class="plain">{tips}</ul>' if tips else "") + vs_h + "</article>")
    return ('<div class="vids"><h4>Iz videa</h4>' + "".join(cards)
            + '<p class="muted note-s">Povzetki so narejeni iz samodejnih angleških podnapisov videov; imena predmetov so preverjena v katalogu. '
              'Pri starejših sezonah preveri, ali se je kaj spremenilo (glej S14 dele in Hiim planer spodaj).</p></div>')


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
    if VIDEOS.get(f'{cls["id"]}/{b["id"]}'):
        badges.append('<span class="badge">video</span>')
    summary = (f'<summary>{img_tag(main.get("img"), "skico lg", main.get("name", ""))}'
               f'<span class="bn"><b>{e(b["name"])}</b><span class="meta">{"".join(f"<span>{m}</span>" for m in meta)}</span></span>'
               f'<span class="badges">{"".join(badges)}</span></summary>')
    body = [ratings_html(b), f"<div><h4>Leveling</h4>{lev}</div>"]
    if guide_file:
        body.append('<div><h4>Naš vodič</h4>' + add_tips_to_fragment(open(os.path.join(CONTENT, "builds", guide_file)).read()) + "</div>")
    vid = videos_html(cls, b)
    if vid:
        body.append(vid)
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

def versioned(html_text):
    """Doda ?v=<hash vsebine> k CSS in JS v assets/, da brskalnik po posodobitvi ne uporabi stare različice."""
    def rep(m):
        path = os.path.join(DOCS, "assets", m.group(2))
        if not os.path.exists(path):
            return m.group(0)
        h = hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
        return f'{m.group(1)}="assets/{m.group(2)}?v={h}"'
    return re.sub(r'(href|src)="assets/([\w.-]+\.(?:css|js))"', rep, html_text)


def page(title, body, current, desc, extra_head="", body_class=""):
    nav = [("index.html", "Razredi")] + [(f'{c["id"]}.html', c["name"]) for c in SITE["classes"]] + [
        ("predmeti.html", "Predmeti"), ("runewordi.html", "Runewordi"), ("mape.html", "Mape"), ("crafting.html", "Crafting"),
        ("druid-nacrt.html", "Druid plan"), ("vodic.html", "Vodič")]
    nav_html = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{e(t)}</a>' for h, t in nav)
    return versioned(f"""<!doctype html>
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
""")


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
<a class="class-card" href="mape.html"><h3>Mape in imunitete</h3><span class="muted">Vse S14 mape s pošastmi in imunitetami, filter po tvojem elementu, najhitrejši buildi, orbi in map eventi.</span></a>
<a class="class-card" href="crafting.html"><h3>Crafting vodič</h3><span class="muted">Kako item postane uporaben ali vreden: socketi, nadgradnje, korupcija, reroll, crafti in affixi z alvl.</span></a>
<a class="class-card" href="predmeti.html"><h3>Wiki predmetov</h3><span class="muted">Iskalnik po vseh uniquih, setih, runewordih, craftih, runah in bazah: statsi z razponi, recepti in kateri buildi jih nosijo.</span></a>
<a class="class-card" href="runewordi.html"><h3>Runewordi</h3><span class="muted">Vsi runewordi s filtri po bazi (orožje po vrstah, oklep, ščit, helm) in socketih. Vpiši rune, ki jih imaš, in poišči, kje se uporabijo ali kaj že lahko sestaviš.</span></a>
<a class="class-card" href="vodic.html"><h3>Splošni vodič</h3><span class="muted">Kaj pobirati, budget runewordi, crafting, recepti v cubu, mape za začetnika in S14 spremembe.</span></a>
<div class="class-card"><h3>PDF za tisk</h3><span class="muted">Druid plan in budget mapper vodič na A4, s kvadratki za kljukice.</span><span class="links"><a href="pdf/Druid-nacrt-S14.pdf">Druid plan (PDF)</a><a href="pdf/Budget-mapper-S14.pdf">Budget mapper (PDF)</a></span></div>
<a class="class-card" href="assassin.html#b-chain-lightning-sentry"><h3>Za novinca</h3><span class="muted">Najlažji budget mapperji: lightning trapsin, Fire Blast trapsin, Arctic Blast druid, skeleton necro in lightning sorc imajo naš podroben vodič in povzetke video vodičev.</span></a>
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


def others_html(c):
    """Buildi zunaj glavnega seznama: Hiim Mid/Bad in neocenjeni, galerija skupnosti, S13 popularni."""
    hiim = [o for o in c["others"] if o["src"] == "hiim"]
    gal = [o for o in c["others"] if o["src"] == "gallery"]
    s13 = [o for o in c["others"] if o["src"] == "s13"]
    if not (hiim or gal or s13):
        return ""
    rows = []
    for o in hiim:
        note = ("Hiim ga še ni ocenil (pogosto nov S14 build) in nima planerja." if o["tier"] == "brez ocene"
                else f'Hiim solo lista: {o["tier"]}. Igrljiv, a počasnejši od buildov zgoraj.')
        rows.append(f'<tr><td>{e(o["name"])}</td><td><span class="badge">{e("Hiim " + o["tier"])}</span></td><td>{note}</td></tr>')
    for o in gal:
        tags = ", ".join(o.get("tags") or [])
        sk = ", ".join(o.get("skills") or [])
        rows.append(f'<tr><td><a href="{e(o["url"])}" target="_blank" rel="noopener">{e(o["name"])}</a></td>'
                    f'<td><span class="badge">skupnost</span></td>'
                    f'<td>Javni S14 planer v Hiim galeriji (avtor {e(o.get("author") or "?")}, {o["opens"]} ogledov'
                    + (", skupaj " + plural(o["n"], "planer", "podobna planerja", "podobni planerji", "podobnih planerjev") if o.get("n", 1) > 1 else "") + ")."
                    + (f" Skilli na 20: {e(sk)}." if sk else "") + (f" Oznake: {e(tags)}." if tags else "")
                    + " Na Hiim tier listah ga ni.</td></tr>")
    for o in s13:
        rows.append(f'<tr><td>{e(o["name"])}</td><td><span class="badge">S13</span></td>'
                    f'<td>V S13 je imelo ta skill na 20 {str(o["pct"]).replace(".", ",")} % likov 90+ tega razreda '
                    f'(pd2.tools, {o["total"]} likov), na Hiim S14 listah pa ga ni.</td></tr>')
    return (f'<section class="extra-builds"><div class="sec-head"><div class="eyebrow">Zunaj seznama</div>'
            f'<h2>Ostali buildi</h2><p>Buildi, ki jih Hiim ne uvršča med viable, ali jih sploh ne ocenjuje, ter buildi '
            f'iz drugih virov. Uporabni za ideje; za mapping so buildi zgoraj zanesljivejši.</p></div>'
            f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Build</th><th>Vir</th><th>Opomba</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></section>')


def class_html(c):
    builds = "".join(build_html(b, c) for b in c["builds"])
    others = others_html(c)
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


def runewords_page_html():
    mains = [("", "Vse"), ("weapon", "Orožje"), ("armor", "Oklep"), ("shield", "Ščit"), ("helm", "Helm")]
    mbtn = "".join(f'<button type="button" data-m="{k}" aria-pressed="{str(not k).lower()}">{e(t)}</button>' for k, t in mains)
    sopt = '<option value="">Vsi</option>' + "".join(f'<option value="{n}">{n} os</option>' for n in range(2, 7))
    sorts = [("use", "Največ buildov"), ("req", "Level naraščajoče"), ("cheap", "Najcenejše rune"), ("dear", "Najdražje rune"), ("name", "Ime")]
    sortopt = "".join(f'<option value="{k}">{e(t)}</option>' for k, t in sorts)
    modes = [("any", "Vsebuje katero od njih"), ("all", "Vsebuje vse izbrane"), ("make", "Lahko sestavim"), ("one", "Manjka največ 1 runa")]
    modebtn = "".join(f'<button type="button" data-mode="{k}" aria-pressed="{str(k == "any").lower()}">{e(t)}</button>' for k, t in modes)
    s14 = json.load(open(os.path.join(CONTENT, "runewords-s14.json")))
    s14.pop("_opis", None)
    s14_json = json.dumps(s14, ensure_ascii=False).replace("</", "<\\/")
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Runewordi · S14</div>
<h1>Runewordi</h1>
<p class="lead">Vsi runewordi s filtri po bazi in številu socketov. Vpiši ali izberi rune, ki jih imaš: poišče, kje se uporabijo, kaj že lahko sestaviš in kje manjka samo še ena runa.</p>
</div></header>
<main class="wrap"><section>
<form class="wfilters" role="search" onsubmit="return false">
<label class="wsearch"><span class="sr-only">Iskanje</span><input type="search" id="rq" placeholder="Išči po imenu ali statsu: Enigma, Faster Cast Rate, Crushing Blow" autocomplete="off" spellcheck="false"></label>
<div class="filters" role="group" aria-label="Kam gre runeword" id="rmain">{mbtn}</div>
<div class="filters rsub" role="group" aria-label="Vrsta baze" id="rsub" hidden></div>
<div class="wsel">
<label>Socketi<select id="rsock">{sopt}</select></label>
<label>Level do<input type="number" id="rreq" min="1" max="99" inputmode="numeric" placeholder="99"></label>
<label>Razvrsti<select id="rsort">{sortopt}</select></label>
<label class="chk"><input type="checkbox" id="rused"> samo iz buildov</label>
<label class="chk"><input type="checkbox" id="rs14"> novi in spremenjeni v S14</label>
</div>
<fieldset class="rpick">
<legend>Moje rune</legend>
<label class="wsearch"><span class="sr-only">Rune, ki jih imaš</span><input type="text" id="rhave" placeholder="Vpiši rune, npr. Ber, Mal, 2 Ist" autocomplete="off" spellcheck="false"></label>
<div class="rpal" id="rpal" role="group" aria-label="Izberi rune"></div>
<div class="filters rmode" role="group" aria-label="Način iskanja po runah" id="rmode">{modebtn}<button type="button" class="linkbtn" id="rclear" hidden>Počisti rune</button></div>
<p class="muted note-s">Tapni runo za en kos več (do 3), po tretjem jo odstraniš. Pri »Lahko sestavim« štejejo tudi ponovitve, na primer Infinity rabi dva Ber.</p>
</fieldset>
</form>
<div class="wcount" id="rcount" aria-live="polite">Nalagam runeworde …</div>
<div id="rlist" class="wlist"></div>
<button type="button" id="rmore" class="wmore" hidden>Pokaži več</button>
<noscript><p>Iskalnik runewordov potrebuje JavaScript.</p></noscript>
<script type="application/json" id="rw-s14">{s14_json}</script>
<p class="muted note-s" style="margin-top:18px">Statsi so s PD2 wikija (stanje pred S14), novi S14 runewordi s Hiim planerja; S14 spremembe so povzete iz tentative patch notes in prikazane nad statsi. Baze in vrste orožja so izračunane iz tipov baz v Hiim katalogu. Podrobnosti posameznega runeworda so tudi v <a href="predmeti.html">wikiju predmetov</a>.</p>
</section></main>"""
    return page("Runewordi · PD2 S14 buildi", body, "runewordi.html",
                "Runewordi za Project Diablo 2 S14: filtri po bazi in socketih ter iskanje po runah, ki jih imaš.",
                extra_head='<script src="assets/runewords.js" defer></script>', body_class="page-items")


EL_NAME = {"phys": "Physical", "magic": "Magic", "fire": "Fire", "light": "Lightning", "cold": "Cold", "poison": "Poison"}
EL_ORDER = ["phys", "magic", "fire", "light", "cold", "poison"]


def imm_badges(m):
    out = []
    for x in m["imm"]:
        out.append(f'<span class="el el-{x["el"]}" title="{e(", ".join(x["mon"]))}">{EL_NAME[x["el"]]} {x["res"]}</span>')
    if not out:
        out.append('<span class="el el-none">brez imunitet</span>')
    return "".join(out)


def map_card(m):
    rows = []
    for mo in m["monsters"]:
        typ = ", ".join(t for t, ok in (("undead", mo["u"]), ("demon", mo["d"]), ("boss", mo["boss"])) if ok)
        cells = "".join(f'<td class="{"imm" if v >= 100 else "hi" if v >= 75 else ""}">{v}</td>' for v in mo["res"])
        rows.append(f'<tr><td>{e(mo["name"])}</td><td class="muted">{e(typ)}</td>{cells}</tr>')
    head = "".join(f'<th class="el-{k}">{EL_NAME[k][:4]}</th>' for k in EL_ORDER)
    best = ""
    if m["best"]:
        best = ('<p class="note-s"><b>Najhitrejši Hiim buildi na tej mapi:</b> ' + ", ".join(
            f'<a href="{b["cls"]}.html#b-{e(b["id"])}">{e(b["name"])}</a> <span class="muted">({fmt_time(b["time"])}, S{b["season"]})</span>'
            for b in m["best"]) + "</p>")
    extra = ""
    if m["extra"]:
        extra = (f'<p class="note-s muted">Hiimova tabela map navaja še: {e(", ".join(EL_NAME[x] for x in m["extra"]))} '
                 '(v podatkih o pošastih tega nismo našli).</p>')
    link = (f'<a href="https://hiimpd2.com/map-pathing#map={e(m["slug"])}&amp;size=Medium" target="_blank" rel="noopener">Postavitev in pot (Hiim)</a>'
            if m.get("slug") else "")
    els = " ".join(x["el"] for x in m["imm"])
    meta = [f'zone level {m["zone"]}', "notranja" if m["inside"] else "zunanja"]
    if m["undead"]:
        meta.append(f'{m["undead"]} undead')
    if m["demon"]:
        meta.append(f'{m["demon"]} demon')
    return (f'<details class="mapc" data-imm="{els}"><summary><span class="mn"><b>{e(m["name"])}</b>'
            f'<span class="meta">{" · ".join(meta)}' + (f' · {len(m["best"])}× najhitrejša' if m["best"] else "") + '</span></span>'
            f'<span class="els">{imm_badges(m)}</span><span class="fit" aria-hidden="true"></span></summary>'
            f'<div class="mapb">' + (f'<p class="note-s">{e(m["note"])}</p>' if m["note"] else "") + best + extra +
            f'<div class="tbl-wrap"><table class="tbl mon"><thead><tr><th>Pošast</th><th>Tip</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div><div class="links">{link}</div></div></details>')


def maps_page_html():
    g = GUIDES
    tiers = []
    for m in g["maps"]:
        if m["tier"] not in tiers:
            tiers.append(m["tier"])
    sections = []
    for t in tiers:
        ms = [m for m in g["maps"] if m["tier"] == t]
        zone = ms[0]["zone"]
        intro = {"Tier 4": "Dungeoni: skupinska vsebina. Vsak ima pošasti s 145 % na vse elemente in 120 % physical.",
                 "Unique Maps": "Wiki: unique mape nimajo stalnih imunitet. Spodaj so vse pošasti, ki jih Hiim navaja za posamezne dele mape (tudi bossove sobe)."}.get(t, "")
        sections.append(f'<div class="tier-block"><h3>{e(t)} <span class="muted">· zone level {zone}</span></h3>'
                        + (f'<p class="note-s">{intro}</p>' if intro else "") + "".join(map_card(m) for m in ms) + "</div>")
    ebtn = '<button type="button" data-el="" aria-pressed="true">Vsi</button>' + "".join(
        f'<button type="button" data-el="{k}" aria-pressed="false" class="el-{k}">{EL_NAME[k]}</button>' for k in EL_ORDER)
    mt = g["map_tables"]
    orbs = "".join(f'<tr><td>{e(o["name"])}</td><td>{e(o["with"])}</td><td>{e(o["effect"])}</td></tr>' for o in mt["orbs"])
    inf = "".join(f'<tr><td>{e(o["in"])}</td><td>{e(o["out"])}</td></tr>' for o in mt["infuse"])
    aff = "".join(f'<tr><td>{e(a["name"])}</td><td>{e(a["attr"])}</td><td>{e(a["range"])}</td><td>{e(a["exp"])}</td>'
                  f'<td>{e(a["density"])}</td><td>{e(a["mf"])}</td><td class="muted">{e(a["note"])}</td></tr>' for a in mt["affixes"])
    corr = mt.get("corruptions") or {}
    corr_rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in corr.get("rows", []))
    corr_head = "".join(f"<th>{e(h)}</th>" for h in corr.get("head", []))
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Endgame · S14</div>
<h1>Mape</h1>
<p class="lead">Vse S14 mape z imunitetami pošasti, najhitrejšimi buildi in postavitvijo. Izberi svoj element in takoj vidiš, katere mape so zate brez imunitet.</p>
</div></header>
<main class="wrap">
<section><div class="sec-head"><div class="eyebrow">Začetek</div><h2>Kako začneš</h2></div>
<div class="cols">
<div class="panel"><h4>Pogoji</h4><p>Level 80+ in premagani Hell Ancients. Mapo odpreš z desnim klikom v Harrogathu (Hell). V eni igri lahko odpreš eno mapo. Prvo T1 mapo ti da Anya, nato mape padajo v mapah samih (višji tier redkeje).</p></div>
<div class="panel"><h4>Tierji</h4><p>T1 (zone level 87), T2 (88), T3 (89) za solo. T4 so dungeoni za skupino. Unique mape padajo redko (v S14 +25 %). Višji tier pomeni več XP, gostote in MF na rare mapah.</p></div>
<div class="panel"><h4>S14 novosti</h4><p>Nove mape Poisoned Well (T1), Descent from Mount Arreat in Dark Temple (T2) prvo sezono nimajo imunitet. Sanatorium je zdaj T1. Števec preostalih pošasti za mape in corrupted zone.</p></div>
</div></section>

<section><div class="sec-head"><div class="eyebrow">Imunitete</div><h2>Mape po imunitetah</h2>
<p>Imuniteta pomeni 100 % ali več odpornosti. Klikni mapo za vse pošasti in njihove odpornosti. Podatki: Hiim Maps explorer (S14), preverjeni s PD2 wikijem.</p></div>
<div class="filters" role="group" aria-label="Tvoj element"><span class="muted">Tvoj element:</span>{ebtn}</div>
<label class="chk muted note-s"><input type="checkbox" id="hide-imm"> skrij mape z imuniteto na moj element</label>
<p class="wcount" id="mcount" aria-live="polite"></p>
{"".join(sections)}
</section>

<section><div class="sec-head"><div class="eyebrow">Mehanika</div><h2>Kako zlomiš imuniteto</h2>
<p>V PD2 sunder charmi ne obstajajo. Imuniteto zlomijo samo učinki, ki odpornost znižajo na pošasti; »pierce« z opreme (-% to Enemy Resistance, Rainbow Facet, Cold Mastery) deluje šele, ko je imuniteta zlomljena.</p></div>
<div class="cols">
<div class="panel"><h4>Zlomijo imuniteto</h4><ul class="plain">
<li><b>Fire, Cold, Lightning:</b> Conviction (Infinity na mercu), Lower Resist</li>
<li><b>Fire:</b> Inferno · <b>Cold:</b> Arctic Blast · <b>Lightning:</b> Static Field</li>
<li><b>Poison:</b> Lower Resist, Poison Creeper</li>
<li><b>Physical:</b> Amplify Damage, Decrepify, Battle Cry</li>
<li><b>Magic:</b> Sanctuary</li>
<li>Throwing Potions (vsi elementi)</li></ul></div>
<div class="panel"><h4>Pol učinka proti imunim</h4><p>Proti pošasti s 100 % ali več deluje vsak tak učinek s polovično močjo (zaokroženo navzdol). Primer: 120 % fire in Conviction -40 %: 120 − 20 = 100, še vedno imun. Dodaš Lower Resist -30 %: 100 − 15 = 85, imuniteta je zlomljena in šele zdaj začne delovati tvoj pierce z opreme.</p></div>
<div class="panel"><h4>Kaj to pomeni zate</h4><p>Ena imuniteta na mapi ni nujno konec: preskočiš tisti paket ali ga ubije merc. Pri dveh elementih (npr. Fire + Cold sorc, Wind + Arctic druid) lahko vzameš skoraj vsako mapo. Horazonov portal v mapi odpre mapo, kjer imajo vse pošasti 0 % odpornosti.</p></div>
</div></section>

<section><div class="sec-head"><div class="eyebrow">Izbira mape</div><h2>Katero mapo vzeti</h2></div>
<div class="cols">
<div class="panel"><h4>Za začetnika</h4><p>Vzemi mape brez imunitete na tvoj element. Najprej T1, nato T2. Rare mape imajo več gostote, XP in MF, a tudi nevarne affixe. Če affix ubije tvoj build (npr. -resi pri nizkih resih), mapo zavrzi ali jo z Orb of Destruction vrni na regular.</p></div>
<div class="panel"><h4>Za farmo</h4><p>Gostota (Density) in MF/GF sta glavna razloga za rare mapo. Map korupcija z Worldstone Shardom doda še en modifikator. Standard of Heroes (od Uber Ancients) da +10 % XP, +20 % gostote in +20 % MF.</p></div>
<div class="panel"><h4>Najhitrejše mape</h4><p>Pri vsaki mapi je seznam buildov, ki imajo na njej svoj najhitrejši čas na Hiim tier listi. Največ jih ima Throne of Insanity, River of Blood, Sewers of Harrogath in Ancestral Trial.</p></div>
</div>
<details class="recipes" style="margin-top:14px"><summary>Vsi affixi map (wiki) <span class="muted">· učinek, razpon za T1 / T2 / T3, bonus XP, gostote in MF</span></summary>
<div class="rec-body"><div class="tbl-wrap"><table class="tbl"><thead><tr><th>Affix</th><th>Učinek</th><th>X</th><th>XP %</th><th>Gostota %</th><th>MF/GF %</th><th></th></tr></thead><tbody>{aff}</tbody></table></div></div></details>
</section>

<section><div class="sec-head"><div class="eyebrow">Horadric Cube</div><h2>Orbi in nadgradnja map</h2>
<p>Orbe kupiš pri Anyi (Hell). Infused orb ne potrebuje dodatnih sestavin, zato ga lahko pripraviš vnaprej.</p></div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Predmet</th><th>Z</th><th>Učinek</th></tr></thead><tbody>{orbs}</tbody></table></div>
<h4 class="sub-h">Infuzije in menjava map</h4>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Sestavine</th><th>Rezultat</th></tr></thead><tbody>{inf}</tbody></table></div>
<details class="recipes" style="margin-top:14px"><summary>Korupcije map (Worldstone Shard + magic ali rare mapa)</summary>
<div class="rec-body"><div class="tbl-wrap"><table class="tbl"><thead><tr>{corr_head}</tr></thead><tbody>{corr_rows}</tbody></table></div></div></details>
</section>

<section><div class="sec-head"><div class="eyebrow">Dogodki</div><h2>Map eventi</h2>
<p>Možnost za event: 33 % na rare mapi, 22 % na magic, 11 % na regular.</p></div>
<div class="cols">
<div class="panel"><h4>Dark Wanderer</h4><p>Postane naključen boss z več življenja in škode. Dropa dodatne Worldstone Sharde (v S14 4–10).</p></div>
<div class="panel"><h4>Shadow of Mendeln</h4><p>Valovi undead pošasti. V S14 vedno dropa Splinter of the Void.</p></div>
<div class="panel"><h4>Horazon</h4><p>Po zmagi odpre portal v mapo istega ali višjega tiera z istimi modifikatorji, kjer imajo pošasti 0 % odpornosti. Dropa 6 map (10 % za unique).</p></div>
<div class="panel"><h4>Treasure Fallen</h4><p>Bezi in ob udarcih spušča gem-e, rune do Zod, mape, orbe in Craft Infusion.</p></div>
<div class="panel"><h4>Spire of Darkness</h4><p>Ob kliku zatemni mapo, senčne pošasti lahko dropajo uber ključe (do 6).</p></div>
<div class="panel"><h4>Corrupted heroes</h4><p>Močne kopije igralcev: vsak dropa rare predmete in uho za modifikatorje map. S14: +100 % življenja, +55 % loota, uho poveča drop baz glede na razred.</p></div>
</div></section>
</main>"""
    return page("Mape · PD2 S14 buildi", body, "mape.html",
                "PD2 S14 mape: imunitete pošasti po mapah, najhitrejši buildi, orbi, affixi in korupcije map.",
                extra_head='<script src="assets/maps.js" defer></script>', body_class="page-maps")


CRAFT_TARGETS = [
    ("Caster amulet", "Amulet + Jewel + Ral + Perfect Amethyst", "Fiksno 5–10 % FCR in mana. Cilj: +2 razredni skilli (alvl 90), resi, moč ali spretnost. Za alvl 90 rabiš ilvl 90: pri levelu 88 gamblaj amulet (ilvl do 92) in ga craftaj."),
    ("Blood rokavice", "Rokavice + Jewel + Nef + Perfect Ruby", "Fiksno life leech, življenje, crushing blow. Cilj: 20 % IAS (alvl 43), +2 drevo skillov (amazon, assassin, barb), do 60 % ED (S14)."),
    ("Caster pas", "Pas + Jewel + Ith + Perfect Amethyst", "Fiksno 10 % FCR. Cilj: FHR, življenje, moč, resi, v S14 še +2–3 % max res (alvl 60)."),
    ("Brilliant ali Caster prstan", "Prstan + Jewel + Hel ali Amn + Perfect Diamond ali Amethyst", "Prstani nimajo stalnih velikih affixov: išči FCR 10 %, resi, življenje, leech. Prstan in amulet imata alvl = ilvl."),
    ("Ščit (S14)", "Ščit + Jewel + runa + gem kategorije", "V S14 lahko craft ščit dobi +3–5 % max res (alvl 80), FCR 20 %, vse rese in +2 paladin skille na paladinovih ščitih."),
    ("Bountiful (MF)", "Amulet + Ko ali prstan + Lum, + Perfect Topaz", "Za MF swap ali MF build. V S14 namesto light radiusa extra gold."),
]


def crafting_page_html():
    g = GUIDES
    cats = []
    order = ["Caster", "Blood", "Brilliant", "Hitpower", "Safety", "Vampiric", "Bountiful"]
    gem = {"Caster": "Perfect Amethyst", "Blood": "Perfect Ruby", "Brilliant": "Perfect Diamond", "Hitpower": "Perfect Sapphire",
           "Safety": "Perfect Emerald", "Vampiric": "Perfect Skull", "Bountiful": "Perfect Topaz"}
    what = {"Caster": "FCR, mana", "Blood": "life leech, življenje, CB/OW", "Brilliant": "IAS, resi, atributi",
            "Hitpower": "AR, pierce, FHR", "Safety": "PDR, MDR, resi, obramba", "Vampiric": "mana leech, DS, PLR",
            "Bountiful": "MF in gold"}
    for cat in order:
        rows = g["crafts"].get(cat) or []
        trs = "".join(f'<tr><td>{e(r["type"])}</td><td class="runes-c">{e(r["ing"][1].replace(" Rune", "") if len(r["ing"]) > 1 else "")}</td>'
                      f'<td>{"<br>".join(e(x) for x in r["mods"])}</td></tr>' for r in rows)
        cats.append(f'<details class="recipes"><summary>{e(cat)} <span class="muted">· {e(gem[cat])} · {e(what[cat])}</span></summary>'
                    f'<div class="rec-body"><div class="tbl-wrap"><table class="tbl"><thead><tr><th>Slot</th><th>Runa</th><th>Fiksni modi</th></tr></thead>'
                    f'<tbody>{trs}</tbody></table></div></div></details>')
    aff = []
    for typ, v in g["craft_affixes"].items():
        trs = []
        for r in v["rows"]:
            def fmt(x):
                t = re.sub(r"to \w+ Skill Levels", "to [razred] Skill Levels", x["text"])
                t = re.sub(r"to [A-Z][\w ]+ \(\w+ Only\)", "to [drevo] Skills", t)
                return f'<b>{x["alvl"]}</b> · {e(t)}'
            same = r["first"]["text"] == r["best"]["text"]
            trs.append(f'<tr><td>{e(r["what"])}</td><td>{fmt(r["first"])}</td><td>{"" if same else fmt(r["best"])}</td></tr>')
        aff.append(f'<details class="recipes"><summary>{e(v["label"])} <span class="muted">· {len(v["rows"])} vrst affixov</span></summary>'
                   f'<div class="rec-body"><div class="tbl-wrap"><table class="tbl"><thead><tr><th>Kaj</th><th>Najnižji alvl</th><th>Najboljši tier</th></tr></thead>'
                   f'<tbody>{"".join(trs)}</tbody></table></div></div></details>')
    corr = []
    for c in g["corruptions"]:
        head = "".join(f"<th>{e(h)}</th>" for h in c["head"])
        trs = "".join("<tr>" + "".join(f'<td>{e(x)}</td>' for x in r) + "</tr>" for r in c["rows"])
        corr.append(f'<details class="recipes"><summary>{e(c["slot"])}</summary><div class="rec-body"><div class="tbl-wrap"><table class="tbl">'
                    f'<thead><tr>{head}</tr></thead><tbody>{trs}</tbody></table></div></div></details>')
    used = []
    for it in ITEMS.get("items", []):
        if it.get("c") == "craft" and it.get("u"):
            used.append((len(it["u"]), it["n"], it["k"]))
    used.sort(reverse=True)
    used_html = ", ".join(f'<a href="predmeti.html#k={e(k)}">{e(n)}</a> ({c})' for c, n, k in used)
    targets = "".join(f'<tr><td><b>{e(n)}</b></td><td class="runes-c">{e(r)}</td><td>{e(t)}</td></tr>' for n, r, t in CRAFT_TARGETS)
    body = f"""
<header class="hero"><div class="wrap">
<div class="eyebrow">Horadric Cube · S14</div>
<h1>Crafting in izboljšave</h1>
<p class="lead">Kako iz navadnega predmeta narediš uporabnega ali vrednega: socketi, nadgradnje, korupcija, reroll in crafting. Recepti in affixi so iz S14 podatkov (Hiim), mehanike s PD2 wikija.</p>
</div></header>
<main class="wrap">
<section><div class="sec-head"><div class="eyebrow">Pregled</div><h2>Kako predmet izboljšaš</h2></div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Kaj</th><th>Recept</th><th>Kdaj</th></tr></thead><tbody>
<tr><td><b>Socketi</b></td><td>Larzuk (A5, 1. quest): bel item dobi maksimum socketov, magic 1–2, ostali 1. Cube na belem ali superior itemu: orožje Ral + Amn + P. Amethyst (1–6), oklep Tal + Thul + P. Topaz (1–4), helm Ral + Thul + P. Sapphire (1–3), ščit Tal + Amn + P. Ruby (1–4). Larzuk's Puzzlebox: 2–4 na dvoročnem, 1–2 drugje. Puzzlepiece enako, a ne na unique/set. Malus (pri Larzuku): +1 socket.</td><td>Baze za runeworde in socketi na uniquih brez socketov.</td></tr>
<tr><td><b>Nadgradnja baze</b></td><td>Unique/set: normal → exceptional Ral + Sol + P. Emerald (orožje) ali Tal + Shael + P. Diamond (oklep); exceptional → elite Lum + Pul + P. Emerald ali Ko + Lem + P. Diamond. Rare/craft: Ort + Amn + P. Sapphire, Ral + Thul + P. Amethyst, Fal + Um + P. Sapphire, Ko + Pul + P. Amethyst.</td><td>Več obrambe ali škode, več socketov (npr. Vampire Gaze → Bone Visage za 3 sockete). Zahteve narastejo z bazo.</td></tr>
<tr><td><b>Korupcija</b></td><td>Worldstone Shard + item. Bel item: 50 % socketi do maksimuma, 50 % naključen rare. Ostali, ki lahko dobijo sockete: 25 % socketi, 50 % modifikator, 25 % naključen rare. Brez socketov: 75 % modifikator, 25 % rare.</td><td>Na končnih uniquih. Korumpiraj pred Puzzleboxom. 25 % da item pokvariš.</td></tr>
<tr><td><b>Reroll</b></td><td>Magic item + 3 perfect gemi (isti ilvl). Rare item + 3 Perfect Skulls (ilvl pade na clvl×0,4 + ilvl×0,4). Demonic Cube + unique/set: novi razponi statsov, socketi ostanejo.</td><td>Magic: grand charmi s +1 drevo skillov. Rare: prstani, diademi. Demonic Cube: slab roll dobrega uniqua.</td></tr>
<tr><td><b>Imbue</b></td><td>Charsi (A1 quest Tools of the Trade) naredi bel item brez socketov v rare z ilvl = clvl + 4.</td><td>Prihrani do levela 71+: diadem ali razredni item (claw, orb, wand, pelt) z veliko več možnosti za +3 skille.</td></tr>
<tr><td><b>Eth in kopija</b></td><td>Vial of Lightsong + item: postane ethereal. Lilith's Mirror + magic/rare/craft: kopija (obe označeni, brez nadaljnjih receptov).</td><td>Zelo redka; za končno opremo.</td></tr>
</tbody></table></div>
</section>

<section><div class="sec-head"><div class="eyebrow">Crafting</div><h2>Kako deluje crafting</h2></div>
<div class="cols">
<div class="panel"><h4>Recept</h4><p>Magic ali rare baza + Jewel + runa + perfect gem kategorije. Namesto jewela, rune in gema lahko uporabiš Craft Infusion (dropa Treasure Fallen v mapah). Eth baza da eth craft. Rare predmete lahko uporabiš kot bazo, craft pa lahko kasneje nadgradiš (kot rare).</p></div>
<div class="panel"><h4>Item level</h4><p>ilvl crafta = clvl/2 + ilvl baze/2 (navzdol). Affixi: ilvl 1–30 1–4, 31–50 2–4, 51–70 3–4, 71+ vedno 4 dodatni affixi. Trgovci prodajajo ilvl = clvl + 4, gamble da clvl − 5 do clvl + 4.</p></div>
<div class="panel"><h4>Affix level (alvl)</h4><p>Pri amuletu in prstanu je alvl enak ilvl. Pri ostalih bazah je alvl nižji za polovico quality levela baze, zato za craft vzemi normal bazo (Leather Gloves, Sash, Boots, Cap) in ne elite.</p></div>
</div>
<h4 class="sub-h">Recepti po kategorijah (S14)</h4>
{"".join(cats)}
<p class="muted note-s">S14: Hitpower helm in amulet izgubita FHR in dobita pierce. Bountiful namesto light radiusa dobi extra gold. Blood oklep in ščit: max life 5–7 %. Za nadgradnjo run in gemov ključ ni več potreben.</p>
</section>

<section><div class="sec-head"><div class="eyebrow">Vrednost</div><h2>Kaj craft naredi vrednega</h2>
<p>Fiksni modi so le osnova. Vrednost določijo 4 naključni affixi, za dobre pa rabiš dovolj visok alvl. Spodaj so za vsak slot affixi, ki jih craft lahko dobi, z najnižjim alvl in alvl najboljšega tiera (S14 affix tabele).</p></div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Craft</th><th>Recept</th><th>Kaj iskati</th></tr></thead><tbody>{targets}</tbody></table></div>
<h4 class="sub-h">Affixi po slotu (alvl)</h4>
{"".join(aff)}
<p class="muted note-s">Nekateri najboljši affixi so v S14 samo na dropanih rare predmetih in jih craft ne more dobiti: +2 razredni skilli na helmu, oklepu in ščitu, 20 % FCR na amuletu, pasu in rokavicah (»of the Magus«), crushing in deadly strike 10–30 % na rokavicah in helmu. Crafti, ki jih nosijo naši buildi: {used_html}.</p>
</section>

<section><div class="sec-head"><div class="eyebrow">Worldstone Shard</div><h2>Korupcije po slotu</h2>
<p>Možnosti za modifikator: nizka 48–50 %, srednja 30–32 %, visoka 20 %. S14: Indestructible zamenja popravljanje durabilityja, na čevljih, rokavicah in pasu Replenish Life zamenja Half Freeze Duration, na oklepu sta FCR in curse res zamenjala stopnjo.</p></div>
{"".join(corr)}
</section>

<section><div class="sec-head"><div class="eyebrow">Loot</div><h2>Kaj pobirati za crafting</h2></div>
<div class="cols">
<div class="panel"><h4>Vedno</h4><p>Jewele (vsak magic jewel je sestavina), perfect geme ali flawless za nadgradnjo, rune do Lum, Worldstone Sharde, Puzzlebox in Puzzlepiece, Craft Infusion.</p></div>
<div class="panel"><h4>Baze za craft</h4><p>Magic in rare amulete, prstane, rokavice, pase, škornje z visokim ilvl (iz map). Na visokem levelu gamblaj amulete in prstane pri Anyi ali Gheedu za ilvl 90+.</p></div>
<div class="panel"><h4>Za prodajo</h4><p>Craft je vreden, ko ima vse 4 affixe za isto vlogo: npr. caster amulet +2 skilli, FCR, resi; blood rokavice 20 % IAS, +2 drevo, ED. Rare z enim odličnim in tremi slabimi affixi je reroll material.</p></div>
</div></section>
</main>"""
    return page("Crafting · PD2 S14 buildi", body, "crafting.html",
                "PD2 S14 crafting vodič: recepti, affixi z alvl, korupcije, socketi, reroll in nadgradnje.")


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
    global SITE, GUIDES, ITEMS
    SITE = json.load(open(os.path.join(ROOT, "data", "site.json")))
    GUIDES = json.load(open(os.path.join(ROOT, "data", "guides.json")))
    ITEMS = json.load(open(os.path.join(DOCS, "assets", "items.json")))
    os.makedirs(DOCS, exist_ok=True)
    open(os.path.join(DOCS, "index.html"), "w").write(index_html())
    for c in SITE["classes"]:
        open(os.path.join(DOCS, f"{c['id']}.html"), "w").write(class_html(c))
    open(os.path.join(DOCS, "vodic.html"), "w").write(guide_html())
    open(os.path.join(DOCS, "druid-nacrt.html"), "w").write(druid_plan_html())
    open(os.path.join(DOCS, "predmeti.html"), "w").write(items_page_html())
    open(os.path.join(DOCS, "runewordi.html"), "w").write(runewords_page_html())
    open(os.path.join(DOCS, "mape.html"), "w").write(maps_page_html())
    open(os.path.join(DOCS, "crafting.html"), "w").write(crafting_page_html())
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    if MISSING_VIDEO_ITEMS:
        print("povzetki videov: predmeti brez tooltipa:", sorted(MISSING_VIDEO_ITEMS))
    sizes = {f: os.path.getsize(os.path.join(DOCS, f)) for f in os.listdir(DOCS) if f.endswith(".html")}
    print(sizes)


if __name__ == "__main__":
    main()
