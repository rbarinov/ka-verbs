import json, collections, re
order = ['A1','A2','A2+','B1']
merged = {}
for l in order:
    for e in json.load(open(f'verbs/{l}.json')):
        f = (e.get('fut3') or '').strip(' -—')
        p = (e.get('pres3') or '').strip(' -—')
        m = (e.get('masdar') or '').strip(' -—')
        key = f or ('P:' + p) or ('M:' + m)
        if key in ('', 'P:', 'M:'): continue
        g = merged.setdefault(key, {'masdar': m, 'pres3': p, 'fut3': f, 'ru': [], 'attested': [], 'notes': [], 'agent_levels': []})
        if not g['masdar'] and m: g['masdar'] = m
        if not g['pres3'] and p: g['pres3'] = p
        if e.get('ru') and e['ru'] not in g['ru']: g['ru'].append(e['ru'])
        for a in e.get('attested') or []:
            if a not in g['attested']: g['attested'].append(a)
        if e.get('note'): g['notes'].append(f"[{l}] {e['note']}")
        g['agent_levels'].append(l)
items = sorted(merged.values(), key=lambda g: (g['pres3'] or g['masdar'], g['fut3']))
for i, g in enumerate(items): g['id'] = i
json.dump(items, open('verbs/merged.json', 'w'), ensure_ascii=False, indent=0)
print(len(items))
