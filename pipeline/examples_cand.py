import os
import json, re, collections
S = os.environ.get("WORK", "work")
LEVELS = ["A1", "A2", "A2+", "B1"]
KINDS = [("შემსწავლელის წიგნი", "учебник"), ("შემსწავლელის რვეული", "тетрадь"), ("მასწავლებლის წიგნი", "книга учителя")]
verbs = json.load(open(f"{S}/verbs/final.json"))

sents = []  # (level, kind, text)
for lvl in LEVELS:
    for k, ru in KINDS:
        try: t = open(f"{S}/text/{lvl} {k}.txt").read()
        except FileNotFoundError: continue
        t = re.sub(r"=== PAGE \d+ ===", "\n\n", t)
        t = re.sub(r"([ა-ჿ])-\s*\n\s*([ა-ჿ])", r"\1\2", t)
        for para in re.split(r"\n\s*\n", t):
            para = re.sub(r"\s*\n\s*", " ", para).strip()
            for s in re.split(r"(?<=[.!?…])\s+", para):
                s = s.strip()
                geo = re.findall(r"[ა-ჿ]+", s)
                if 3 <= len(geo) <= 18 and len(s) < 160 and len(geo) >= 0.7 * len(s.split()) and not re.search(r"_{2,}|\.{3,}|…{2,}", s):
                    sents.append((lvl, ru, s, set(geo)))
print("sentences", len(sents))

def words(v):
    w = set()
    for k, cells in v["forms"].items():
        for x in cells or []:
            if x: w |= set(re.findall(r"[ა-ჿ]+", x))
    return w
own = collections.Counter()
W = {v["id"]: words(v) for v in verbs}
for w in W.values(): own.update(w)
index = collections.defaultdict(list)
for i, s in enumerate(sents):
    for w in s[3]: index[w].append(i)

out, nocand = [], 0
for v in verbs:
    ws = {w for w in W[v["id"]] if own[w] == 1 and len(w) > 2}
    hits = set()
    for w in ws: hits.update(index.get(w, []))
    seen, cands = set(), []
    lv = LEVELS.index(v["level"])
    for i in sorted(hits, key=lambda i: (abs(LEVELS.index(sents[i][0]) - lv), sents[i][1] == "книга учителя", abs(len(sents[i][3]) - 7))):
        key = sents[i][2]
        if key in seen: continue
        seen.add(key); cands.append({"ka": key, "where": f"{sents[i][0]} {sents[i][1]}"})
        if len(cands) >= 8: break
    nocand += not cands
    out.append({"id": v["id"], "pres3": v["pres3"], "masdar": v["masdar"], "ru": v["ru"], "level": v["level"],
                "forms": {k: v["forms"][k] for k in ("present", "future", "aorist")}, "candidates": cands})
print("no candidates", nocand, "of", len(out))
n = 6
for j in range(n):
    json.dump(out[j::n], open(f"{S}/verbs/ex_in_{j+1}.json", "w"), ensure_ascii=False, indent=0)
