"""Načrt skill točk po levelih iz Hiim planerjev in skill dreves (Hiim katalog).

Ciljna razporeditev je planer (začetni za leveling, končni za endgame). Točke delimo level
za levelom: najprej skilli z 1–3 točkami (predpogoji, teleport, aure za buff), takoj ko
so na voljo; nato glavni skill, njegove sinergije in ostali maxani skilli. Če noben ciljni
skill še ni na voljo (level zahteva), točko prihranimo.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "data", "hiim", "catalog")

# predvideni leveli questov s skill točkami (Den of Evil, Radament, Izual ×2 na težavnost)
QUEST_SKILL = {6: 1, 15: 1, 25: 2, 38: 1, 43: 1, 50: 2, 62: 1, 66: 1, 72: 2}
# Lam Esen's Tome: 5 stat točk na težavnost
QUEST_STAT = {22: 5, 48: 5, 70: 5}
# paladinove aure za škodo po prednosti; prvo, ki je v planerju, dvigaš skupaj z glavnim skillom
DAMAGE_AURAS = ["conviction", "fanaticism", "concentration", "holy_shock", "holy_fire", "holy_freeze", "might", "sanctuary"]

# največ levelov v eni vrstici načrta
SPAN = 8

_CAT = {}


def catalog(cls):
    if cls not in _CAT:
        d = json.load(open(os.path.join(CAT, f"skills.{cls}.json")))
        _CAT[cls] = {s["id"]: s for s in d["skills"]}
    return _CAT[cls]


def skill_points(level):
    return level - 1 + sum(q for lv, q in QUEST_SKILL.items() if lv <= level)


def stat_points(level):
    return 5 * (level - 1) + sum(q for lv, q in QUEST_STAT.items() if lv <= level)


def aura(targets, main):
    """Aura za škodo, ki jo dvigaš izmenično z glavnim skillom (ali None)."""
    return next((a for a in DAMAGE_AURAS if a != main and targets.get(a, 0) > 3), None)


def order(cls, targets, main):
    """Prednost maxanih skillov: glavni, aura za škodo, sinergije glavnega, ostali po številu točk."""
    cat = catalog(cls)
    syn = [s.get("skill") for s in cat.get(main, {}).get("synergies", []) if s.get("skill")] if main in cat else []
    core = [s for s, t in targets.items() if t > 3]
    lead_aura = aura(targets, main)

    def key(s):
        if s == main:
            return (0, 0, 0)
        if s == lead_aura:
            return (1, 0, 0)
        if s in syn:
            return (2, syn.index(s), 0)
        return (3, -targets[s], cat.get(s, {}).get("reqLevel", 1))
    return sorted(core, key=key)


def available(cls, skill, level, alloc):
    s = catalog(cls).get(skill)
    if not s:
        return False
    return s.get("reqLevel", 1) <= level and all(alloc.get(p, 0) >= 1 for p in s.get("prereqs") or [])


def allocate(cls, targets, main, start_level, end_level, alloc=None, banked=0):
    """Vrne (časovnica, končna razporeditev, prihranjene točke).
    časovnica: [(level, {skill: nova vrednost}, prihranjeno)]"""
    alloc = dict(alloc or {})
    cat = catalog(cls)
    prio = order(cls, targets, main)
    lead = [s for s in prio if s in (main, aura(targets, main))]  # dvigujeta se izmenično
    syn = [x.get("skill") for x in cat.get(main, {}).get("synergies", []) if x.get("skill")]
    # koristni skilli z več točkami (teleport, BO …): prvo točko takoj, ostale na koncu
    utility = [s for s in prio if s not in lead and s not in syn]
    small = sorted((s for s, t in targets.items() if t <= 3), key=lambda s: cat.get(s, {}).get("reqLevel", 1))
    timeline = []

    def missing_prereq(skill, lv):
        """Predpogoj, ki manjka, da bi bil skill na voljo (level zahteva je izpolnjena)."""
        sk = cat.get(skill, {})
        if sk.get("reqLevel", 1) > lv:
            return None
        for p in sk.get("prereqs") or []:
            if alloc.get(p, 0) == 0 and available(cls, p, lv, alloc):
                return p
        return None

    for lv in range(start_level, end_level + 1):
        if lv == start_level:  # vse točke do tega levela, ki še niso razporejene ali prihranjene
            gained = skill_points(lv) - sum(alloc.values()) - banked
        else:
            gained = 1 + QUEST_SKILL.get(lv, 0)
        banked += max(0, gained)
        changes = {}
        while banked > 0:
            pick = next((s for s in small if alloc.get(s, 0) == 0 and available(cls, s, lv, alloc)), None)
            if pick is None:
                pick = next((s for s in utility if alloc.get(s, 0) == 0 and available(cls, s, lv, alloc)), None)
            if pick is None:
                ready = [s for s in lead if alloc.get(s, 0) < targets[s] and available(cls, s, lv, alloc)]
                if ready:
                    pick = min(ready, key=lambda s: (alloc.get(s, 0), lead.index(s)))
            if pick is None:
                for s in prio:
                    if alloc.get(s, 0) >= targets[s]:
                        continue
                    if available(cls, s, lv, alloc):
                        pick = s
                        break
                    pick = missing_prereq(s, lv)
                    if pick:
                        break
            if pick is None:
                pick = next((s for s in small if alloc.get(s, 0) < targets[s] and available(cls, s, lv, alloc)), None)
            if pick is None:
                break
            alloc[pick] = alloc.get(pick, 0) + 1
            changes[pick] = alloc[pick]
            banked -= 1
        timeline.append((lv, changes, banked))
    return timeline, alloc, banked


def rows(timeline, prev=None):
    """Strne časovnico v vrstice. Zaporedni leveli, ki vlagajo v iste (največ tri) skille, so ena
    vrstica, ki pa ne pokrije več kot SPAN levelov. Vrstica: {"from", "to", "skills": [(skill, od, do)], "bank"}"""
    out, prev = [], dict(prev or {})
    for lv, ch, bank in timeline:
        items = {s: (prev.get(s, 0), v) for s, v in ch.items()}
        prev.update(ch)
        last = out[-1] if out else None
        if last and last["to"] == lv - 1:
            if not items and not last["skills"]:
                last["to"], last["bank"] = lv, bank
                continue
            names = set(last["skills"]) | set(items)
            if items and last["skills"] and len(names) <= 3 and lv - last["from"] < SPAN and not last["bank"] and not bank:
                for sk, (a, b) in items.items():
                    last["skills"][sk] = (last["skills"].get(sk, (a, a))[0], b)
                last["to"] = lv
                continue
        out.append({"from": lv, "to": lv, "skills": dict(items), "bank": bank})
    return [{**r, "skills": [(s, a, b) for s, (a, b) in r["skills"].items()]} for r in out if r["skills"] or r["bank"]]


def skill_name(cls, sid):
    return catalog(cls).get(sid, {}).get("name", sid)


def targets_of(p):
    return {k["id"]: k["pts"] for k in p["skills"]}


def needs_respec(alloc, targets):
    """Ali razporeditev presega cilj (1 točka v predpogoju, ki ga planer nima, ne šteje)."""
    return any(v > targets.get(k, 0) and not (v == 1 and k not in targets) for k, v in alloc.items())


def series(planners):
    """Pot skozi planerje: planerji avtorja z največ planerji (po levelu, brez podvojenih levelov),
    na koncu še endgame planer drugega avtorja, če pot nima planerja na levelu 90+. Endgame planerja
    (level 80+), ki bi mu sledil še en respec, izpustimo: ciljamo naravnost v naslednjega."""
    ps = [p for p in planners if p.get("skills") and p.get("level")]
    if not ps:
        return []
    count = {}
    for p in ps:
        count[p.get("author")] = count.get(p.get("author"), 0) + 1
    author = max(count, key=lambda a: (count[a], -min(p["level"] for p in ps if p.get("author") == a)))
    seq, seen = [], set()
    for p in sorted([p for p in ps if p.get("author") == author], key=lambda p: p["level"]):
        if p["level"] not in seen:
            seen.add(p["level"])
            seq.append(p)
    if seq[-1]["level"] < 90:
        end = sorted([p for p in ps if p.get("author") != author and p["level"] > seq[-1]["level"]], key=lambda p: -p["level"])
        if end:
            seq.append(end[0])
    i = 0
    while i < len(seq) - 1:
        if seq[i]["level"] >= 80 and needs_respec(targets_of(seq[i]), targets_of(seq[i + 1])):
            del seq[i]
        else:
            i += 1
    return seq


def chain(cls, main, seq, start_level=1, alloc=None, end=None):
    """Razdeli točke skozi zaporedje planerjev. Če planer zahteva manj točk v skillu, kot jih že imaš,
    je na njegovem začetku respec. Z »end« se zadnji odsek konča na tem levelu (krajše ali daljše od
    planerja). Odsek: {"planner", "from", "to", "respec", "rows", "alloc", "bank"}"""
    out, alloc, bank, lv0 = [], dict(alloc or {}), 0, start_level
    for i, p in enumerate(seq):
        if p["level"] < lv0 and not (end and i == len(seq) - 1):
            continue
        stop = min(p["level"], end) if end else p["level"]
        if end and i == len(seq) - 1:
            stop = end
        targets = targets_of(p)
        respec = bool(alloc) and needs_respec(alloc, targets)
        if respec:
            alloc, bank = {}, 0
        before = dict(alloc)
        tl, alloc, bank = allocate(cls, targets, main, lv0, stop, alloc, bank)
        if respec:  # prvi level po respecu je razporeditev, ostalo so vrstice
            out.append({"planner": p, "from": lv0, "to": stop, "respec": True, "start_alloc": dict(tl[0][1]),
                        "rows": rows(tl[1:], tl[0][1]), "alloc": dict(alloc), "bank": bank})
        else:
            out.append({"planner": p, "from": lv0, "to": stop, "respec": False, "start_alloc": None,
                        "rows": rows(tl, before), "alloc": dict(alloc), "bank": bank})
        lv0 = stop + 1
        if lv0 > 99 or (end and lv0 > end):
            break
    return out


def build_plan(cls, main, planners, route=None, respec_level=None):
    """Celoten načrt za build. route = (ime, planerji, glavni skill) za leveling drugega builda.
    Vrne {"route": odseki ali None, "respec_level", "respec_alloc", "segs": odseki}."""
    seq = series(planners)
    if not seq:
        return None
    if not route:
        return {"route": None, "segs": chain(cls, main, seq)}
    rname, rplanners, rmain = route
    rseq = series(rplanners)
    rl = respec_level or 75
    route_segs = []
    if rseq:
        # leveling po poti do levela respeca: brez vmesnega respeca, zadnji odsek se konča na rl
        cut = [rseq[0]]
        for p in rseq[1:]:
            if cut[-1]["level"] >= rl or needs_respec(targets_of(cut[-1]), targets_of(p)):
                break
            cut.append(p)
        route_segs = chain(cls, rmain, cut, end=rl - 1)
    first = next((p for p in seq if p["level"] >= rl), seq[-1])
    targets = targets_of(first)
    tl, alloc, bank = allocate(cls, targets, main, rl, rl, {}, 0)
    rest = chain(cls, main, [p for p in seq if p["level"] >= rl], rl + 1, alloc) if rl < 99 else []
    return {"route": {"name": rname, "segs": route_segs}, "respec_level": rl, "respec_alloc": alloc,
            "respec_planner": first, "respec_bank": bank, "segs": rest}


def early_bank(plan, before=40):
    """Največ prihranjenih točk pred levelom »before« in level, ko so spet vse porabljene."""
    rws = [r for sg in plan["segs"] for r in sg["rows"]]
    peak = max([r["bank"] for r in rws if r["to"] < before] or [0])
    if not peak:
        return 0, None
    at = next(r["from"] for r in rws if r["bank"] == peak)
    return peak, next((r["from"] for r in rws if r["from"] > at and not r["bank"]), None)
