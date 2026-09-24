from pathlib import Path
import json, re
root=Path('projects/minecraft-cases')
index=(root/'index.html').read_text()
products=json.JSONDecoder().raw_decode(index.split('const products=',1)[1])[0]
cases=json.JSONDecoder().raw_decode(index.split('const cases=',1)[1])[0]
byid={p['id']:p for p in products}
# Assign higher odds to cheaper drops, preserving the existing odds distribution per case.
for c in cases:
    if c['type']=='allin':continue
    weighted=sorted((w for _,w in c['drops']),reverse=True)
    ordered=sorted(range(len(c['drops'])),key=lambda i:(byid[c['drops'][i][0]]['value'],i))
    for idx,w in zip(ordered,weighted):c['drops'][idx][1]=w
    # the explicitly advertised 0.01% jackpot must be exactly 0.01%, not rounded from 0.009%.
    if any(id.startswith('jackpot-') for id,_ in c['drops']):
        total=sum(w for id,w in c['drops'] if not id.startswith('jackpot-'))
        for drop in c['drops']:
            if drop[0].startswith('jackpot-'):drop[1]=0.01
            else:drop[1]=round(drop[1]*99.99/total,6)

old_cases=index.split('const cases=',1)[1].split(';',1)[0]
new_cases=json.dumps(cases,ensure_ascii=False,separators=(',',':'))
old_preview='c.drops.slice(0,4).map(([id])=>`<img src="${itemImage(P[id])}" alt="" loading="lazy">`).join(\'\')'
# The first four unique images rather than two variants of the same product logo.
new_preview='[...new Map(c.drops.map(([id])=>[itemImage(P[id]),id])).values()].slice(0,4).map(id=>`<img src="${itemImage(P[id])}" alt="${P[id].name}" loading="lazy">`).join(\'\')'
old_detail='<div class="item-mini"><img src="${itemImage(p)}" alt=""><b>Мини-иконка</b></div>'
# The catalogue may reuse product logo for different durations; show the duration instead of duplicating the icon.
new_detail='<span class="drop-duration">${p.duration||\'Демо-предмет\'}</span>'
old_links="a.textContent='Подробнее →';b.replaceWith(a)"
new_links="a.textContent='Открыть →';b.replaceWith(a)"
css='\n/* Catalog sections take full width; inner grids contain all cases. */\n#caseGrid{display:flex;flex-direction:column;gap:44px;grid-template-columns:none}\n#caseGrid>.category-section{width:100%;min-width:0}\nbody.page-case #caseGrid{display:none}\n.drop-duration{font-size:11px;color:#dcb4ff;padding:3px 9px;border-radius:20px;background:#493050}\n'
files=[root/'index.html',*sorted(root.glob('case-*.html')),root/'catalog.html',root/'about.html',root/'profile.html',root/'topup.html',root/'upgrades.html']
for path in files:
    s=path.read_text()
    assert 'const cases='+old_cases in s,path
    s=s.replace('const cases='+old_cases,'const cases='+new_cases,1)
    assert old_preview in s,path
    s=s.replace(old_preview,new_preview)
    assert old_detail in s,path
    s=s.replace(old_detail,new_detail)
    assert old_links in s,path
    s=s.replace(old_links,new_links)
    s=s.replace('</style>','</style>',1) # layout CSS shipped as standalone stylesheet
    path.write_text(s)
with (root/'case-categories.css').open('a') as f:f.write(css)
print('Updated',len(files),'pages and',len(cases),'case drop tables')
