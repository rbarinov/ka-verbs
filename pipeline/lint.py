import json, glob, re, collections
G = re.compile(r"^[ა-ჿ]+( / [ა-ჿ]+)*$")
flags = collections.defaultdict(list)
for f in sorted(glob.glob("verbs/conj*.jsonl")):
    for line in open(f):
        o = json.loads(line)
        if o["status"] != "ok": continue
        F = o["forms"]; t = o["type"]; vid = o["id"]
        def fl(msg): flags[vid].append(msg)
        for k, arr in F.items():
            for i, x in enumerate(arr):
                if x is not None and not G.match(x): fl(f"{k}[{i}] bad chars: {x}")
            # 1sg vs 3sg identical (except impersonal) suggests missing person marker
            if t not in ("impersonal",) and arr[0] and arr[2] and arr[0] == arr[2]: fl(f"{k}: 1sg==3sg {arr[0]}")
            if arr[0] and arr[1] and arr[0] == arr[1] and t != "indirect": fl(f"{k}: 1sg==2sg {arr[0]}")
            if arr[3] and arr[3] == arr[4] and t != "indirect" : fl(f"{k}: 1pl==2pl {arr[3]}")
        if t != "indirect" and t != "impersonal":
            for k in F:
                x = F[k][0]
                if x and "ვ" not in x and not x.startswith(("ვ",)): 
                    # 1sg normally contains ვ (ვ-prefix); exceptions: forms with ვარ copula contain ვ anyway
                    fl(f"{k}: 1sg lacks ვ: {x}")
        if t == "indirect":
            for k in F:
                x = F[k][0]
                if x and not re.search(r"მ", x[:4]): fl(f"{k}: indirect 1sg lacks მ: {x}")
        imp = F.get("imperfect") or []
        if imp and imp[2] and "დ" not in imp[2] and "ოდა" not in imp[2] and imp[2] not in ("იყო",): fl(f"imperfect 3sg odd: {imp[2]}")
        opt = F.get("optative") or []
        if opt and opt[2] and not opt[2].endswith(("ს","ა","ე","ო","დეს","ოს")): fl(f"optative 3sg odd: {opt[2]}")
        for k in ("present","future","aorist","imperfect","optative"):
            x = F[k][5] if F[k] else None
            if x and not re.search(r"(ენ|ან|ეს|ნენ|ონ|ენენ|ნ|თ|ათ|ია|ი)$", x): fl(f"{k} 3pl odd: {x}")
tot = sum(1 for _ in flags)
print("flagged verbs", tot)
c = collections.Counter(m.split(":")[0] for v in flags.values() for m in v)
print(c.most_common(25))
json.dump(flags, open("verbs/lint.json","w"), ensure_ascii=False, indent=0)
