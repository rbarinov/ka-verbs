import os
import json, glob, re, collections, sys

S = os.environ.get("WORK", "work")
LEVELS = ["A1", "A2", "A2+", "B1"]
KIND = {"შემსწავლელის წიგნი": "учебник", "შემსწავლელის რვეული": "тетрадь", "მასწავლებლის წიგნი": "книга учителя"}

# word-form sets per (level, kind); hyphenated line-break joins are counted too
files = {}
for lvl in LEVELS:
    for k, ru in KIND.items():
        p = f"{S}/text/{lvl} {k}.txt"
        try:
            t = open(p).read()
        except FileNotFoundError:
            continue
        t = re.sub(r"([ა-ჿ])-\s*\n\s*([ა-ჿ])", r"\1\2", t)
        files[(lvl, ru)] = set(re.findall(r"[ა-ჿ]+", t))
anyform = set().union(*files.values())

merged = {g["id"]: g for g in json.load(open(f"{S}/verbs/merged.json"))}
conj = {}
for f in sorted(glob.glob(f"{S}/verbs/conj*.jsonl")):
    for line in open(f):
        line = line.strip()
        if line:
            o = json.loads(line)
            conj[o["id"]] = o

# verbs added by the gap sweep carry their own conjugation; give them a merged stub
try:
    for line in open(f"{S}/verbs/gap.jsonl"):
        line = line.strip()
        if line:
            o = json.loads(line)
            o["status"] = "ok"
            conj[o["id"]] = o
            merged[o["id"]] = {"id": o["id"], "masdar": o.get("masdar") or "", "pres3": o.get("pres3") or "",
                               "ru": [o.get("ru") or ""], "attested": o.get("attested") or [], "agent_levels": [o.get("level") or "B1"]}
except FileNotFoundError:
    pass

patched = collections.Counter()
for f in sorted(glob.glob(f"{S}/verbs/patch_*.jsonl")):
    for line in open(f):
        line = line.strip()
        if not line:
            continue
        p = json.loads(line)
        c = conj.get(p["id"])
        if not c:
            continue
        if p.get("action") == "drop":
            c["status"] = "dropped"
        else:
            for k in ("masdar", "pres3", "ru", "type", "forms", "note_ru"):
                if k in p and p[k] is not None:
                    c[k] = p[k]
            c["status"] = "ok"
        patched[p.get("action")] += 1
print("patches", dict(patched))

def wordset(c, g):
    cells = [x for k in ("present", "future", "aorist", "imperfect", "optative") for x in ((c.get("forms") or {}).get(k) or []) if x]
    w = set()
    for x in cells + [c.get("masdar") or "", c.get("pres3") or ""]:
        w |= set(re.findall(r"[\u10d0-\u10ff]+", x))
    return w | set(g["attested"])
owners = collections.Counter()
for vid, g in merged.items():
    c = conj.get(vid)
    if c and c.get("status") == "ok":
        owners.update(wordset(c, g))

out, problems = [], collections.Counter()
for vid, g in merged.items():
    c = conj.get(vid)
    if not c:
        problems["missing"] += 1
        continue
    if c.get("status") != "ok":
        problems[c.get("status")] += 1
        continue
    forms = c["forms"]
    cells = [x for k in ("present", "future", "aorist", "imperfect", "optative") for x in (forms.get(k) or []) if x]
    # cells may hold variants like "ვწერ / ვწერავ"; split for matching
    words = set()
    for x in cells + [c.get("masdar") or "", c.get("pres3") or ""]:
        words |= set(re.findall(r"[ა-ჿ]+", x))
    words |= set(g["attested"])
    own = {w for w in words if owners[w] == 1}
    found = {key for key, s in files.items() if own & s} or {key for key, s in files.items() if words & s}
    if not found:
        problems["no_corpus_hit"] += 1
        found = {(l, "учебник") for l in (g["agent_levels"] or ["B1"])}
    level = next(l for l in LEVELS if any(k[0] == l for k in found))
    kinds = sorted({k[1] for k in found}, key=["учебник", "тетрадь", "книга учителя"].index)
    att = sorted({x for x in cells if all(w in anyform for w in re.findall(r"[ა-ჿ]+", x))})
    out.append({
        "id": vid, "level": level, "src": kinds, "teacher_only": kinds == ["книга учителя"],
        "masdar": c.get("masdar") or g["masdar"], "pres3": c.get("pres3") or g["pres3"],
        "ru": c.get("ru") or "; ".join(g["ru"]), "type": c.get("type") or "other",
        "forms": {k: forms.get(k) or [None] * 6 for k in ("present", "future", "aorist", "imperfect", "optative")},
        "note": c.get("note_ru") or "", "attested_forms": att,
    })

ex = {}
for f in sorted(glob.glob(f"{S}/verbs/ex_out_*.jsonl")):
    for line in open(f):
        line = line.strip()
        if line:
            o = json.loads(line)
            ex[o["id"]] = [{k: e[k] for k in ("ka", "ru", "src", "where") if e.get(k)} for e in o["examples"]]
for v in out:
    v["examples"] = ex.get(v["id"], [])
print("with examples", sum(1 for v in out if v["examples"]), "book", sum(e["src"] == "book" for v in out for e in v["examples"]))

out.sort(key=lambda v: (LEVELS.index(v["level"]), v["pres3"] or v["masdar"]))
json.dump(out, open(f"{S}/verbs/final.json", "w"), ensure_ascii=False)
cnt = collections.Counter(v["level"] for v in out)
tch = collections.Counter(v["level"] for v in out if v["teacher_only"])
print("verbs", len(out), dict(cnt), "teacher_only", dict(tch), "problems", dict(problems))

meta = (f"Источник: учебники, рабочие тетради и книги учителя серии «აღმართი» (geofl.ge), уровни A1–B1. "
        f"Всего {len(out)} глаголов.")
html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")).read()
html = html.replace("__DATA__", json.dumps(out, ensure_ascii=False)).replace("__META__", json.dumps(meta, ensure_ascii=False))
open(f"{S}/aghmarti-verbs.html", "w").write(html)
print("html bytes", len(html.encode()))
