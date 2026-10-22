import re, glob, collections, json, os
lv = {}
allc = collections.Counter()
for lvl in ["A1","A2","A2+","B1"]:
    c = collections.Counter()
    for f in glob.glob(f"text/{lvl} *.txt"):
        t = open(f).read()
        c.update(re.findall(r"[ა-ჿ]+", t))
    lv[lvl] = c
    allc.update(c)
    print(lvl, "tokens", sum(c.values()), "unique", len(c))
print("all unique", len(allc), "freq>=2", sum(1 for v in allc.values() if v>=2))
json.dump({k: dict(v) for k, v in lv.items()}, open("tokens_by_level.json","w"), ensure_ascii=False)
