import json, pathlib, re, math
from PIL import Image, ImageDraw, ImageFont
root=pathlib.Path('projects/minecraft-cases'); base=(root/'index.html').read_text(); dec=json.JSONDecoder(); products,_=dec.raw_decode(base.split('const products=',1)[1]); old,_=dec.raw_decode(base.split('const cases=',1)[1]); P={p['id']:p for p in products}
# Case pools strictly from existing named server/client reference catalog; no invented prizes.
specs=[('hw-start','HolyWorld · старт','HOLYWORLD','server',19,[14,15,16,17,18]),('hw-ghast','HolyWorld · Гаст','HOLYWORLD','server',149,[17,19,20,21,23]),('hw-elite','HolyWorld · Элита','HOLYWORLD','server',490,[20,22,24,25,26,29]),('hw-legend','HolyWorld · Легенда','HOLYWORLD','server',1490,[23,24,26,27,28,29,30]),('rw-start','ReallyWorld · старт','REALLYWORLD','server',59,[40,41,42,43]),('rw-elite','ReallyWorld · Элита','REALLYWORLD','server',249,[40,42,43,44,45]),('rw-legend','ReallyWorld · Дракон','REALLYWORLD','server',790,[42,43,44,45,46]),('spooky-start','SpookyTime · Старт','SPOOKYTIME','server',15,[47,48,49,50]),('spooky-tokens','SpookyTime · Токены','SPOOKYTIME','server',120,[48,49,50,51,52]),('britva','Britva','BRITVA','client',250,[1,2,3]),('celestial','Celestial','CELESTIAL','client',250,[4,5,6]),('delta','Delta','DELTA','client',330,[7,8,9]),('nursultan','Nursultan','NURSULTAN','client',350,[31,32,33]),('pulse','Pulse Visual','PULSE','client',170,[34,35,36]),('reallyvisuals','ReallyVisuals','REALLYVISUALS','client',170,[37,38,39]),('wexside','Wexside','WEXSIDE','client',350,[53,54,55]),('wild','Wild','WILD','client',290,[56,57,58]),('allin-hw','ALL IN · HolyWorld','HOLYWORLD','allin',30,[14,17,25,30]),('allin-rw','ALL IN · ReallyWorld','REALLYWORLD','allin',55,[40,41,44,46]),('allin-spooky','ALL IN · SpookyTime','SPOOKYTIME','allin',25,[47,48,50,52])]
colors=['#6de4cb','#ffa86b','#ae86ff','#f5d27e','#74c8ef','#ef7cbf']; cases=[]
for i,(cid,name,cat,typ,price,nums) in enumerate(specs):
 ids=['ref-'+str(n) for n in nums];assert all(P[n]['category']==cat for n in ids)
 if typ=='allin': weights=[94,5,.99,.01]
 elif len(ids)==3:weights=[80,19.99,.01]
 else:
  # Last prize 0.01%, balance exact 100%.
  raw=[max(1, 2**(len(ids)-2-j)) for j in range(len(ids)-1)];weights=[round(99.99*v/sum(raw),4) for v in raw];weights[-1]=round(99.99-sum(weights[:-1]),4);weights.append(.01)
 cases.append(dict(id=cid,name=name,brand=cat,type=typ,price=price,desc='Товары '+cat+' из каталога',accent=colors[i%len(colors)],drops=list(zip(ids,weights)),**({'minCount':10} if typ=='allin' else {})))
# Preserve existing layout while giving all pages the same verified data.
casejson=json.dumps(cases,ensure_ascii=False,separators=(',',':'))
original=re.search(r'const cases=(\[.*?\]);',base).group(1)
base=base.replace('const cases='+original+';', 'const cases='+casejson+';')
# Hide unsupported real-money and self-credit flows; do not pretend fulfillment exists.
base=base.replace('<div class="topline">', '<div class="topline">',1)
base=re.sub(r'<section class="section" id="topup">.*?(?=<section class="section"|<footer|</main>)',lambda m:m.group(0),base,flags=re.S) if False else base
base=base.replace('47 демо-кейсов',str(len(cases))+' кейсов')
base=base.replace('Тематический демо-кейс','Кейс').replace('демо-кейс','кейс').replace('демо-кейсов','кейсов').replace('ДЕМО-ПРОЕКТ','ПРОЕКТ В РАЗРАБОТКЕ').replace('· демо','').replace(' · ДЕМО','')
# Remove misleading claims; virtual balances have no monetary value until real integrations exist.
base=base.replace('Демо-заявок пока нет.','Заявок пока нет.').replace('Здесь нельзя внести деньги. Используются только виртуальные монеты.','Платежи пока не подключены. Используются виртуальные монеты.')
base=base.replace('id="demoCreditForm"','id="demoCreditForm" hidden').replace('id="resetBtn"','id="resetBtn" hidden')
base=base.replace("let targets=src?products.filter(p=>p.value>src.value):[]", "let targets=src?products.filter(p=>p.id!==src.id&&p.value>src.value&&p.id.startsWith('ref-')):[]")
base=base.replace('let choices=products.filter(x=>x.value>src.value)',"let choices=products.filter(x=>x.id!==src.id&&x.value>src.value&&x.id.startsWith('ref-'))")
# Upgrade picker lists each target product once (not every physical instance); source inventory instances remain distinct by uid.
base=base.replace("let targets=src?products.filter(p=>p.id!==src.id&&p.value>src.value&&p.id.startsWith('ref-')):[]", "let targets=src?[...new Map(products.filter(p=>p.id!==src.id&&p.value>src.value&&p.id.startsWith('ref-')).map(p=>[p.name+'|'+p.duration,p])).values()]:[]")
base=base.replace('function upgrade(){','function upgrade(){').replace("pointer.style.transition='transform 4s cubic-bezier(.12,.64,.12,1)'", "pointer.style.transition=$('#fastUpgrade').checked?'none':'transform 4s cubic-bezier(.12,.64,.12,1)'").replace('},4100)}',"},$('#fastUpgrade').checked?0:4100)}")
base=base.replace('<button class="btn btn-primary" id="upgradeBtn"', '<label class="fast-toggle"><input type="checkbox" id="fastUpgrade"> ⚡ Фаст апгрейд (без анимации)</label><button class="btn btn-primary" id="upgradeBtn"')
# New shared auth UI starts before the original inline script (auth initialization blocks use of controls).
base=base.replace('</head>', '<link rel="stylesheet" href="account.css"></head>')
base=base.replace('<div class="right-head">','<div class="right-head"><button type="button" id="accountBtn" class="btn btn-ghost btn-small">Войти / регистрация</button><a id="supportLink" href="support.html" class="btn btn-ghost btn-small">ТП</a>')
base=base.replace('</body></html>','<script src="account.js"></script></body></html>')
# Use auth server-side storage only through HTTP; local progress remains local until game logic migrates to server.
base=base.replace('const KEY=\'blockdrop-demo-v2\'','const KEY=\'meshcase-local-v3\'')
base=base.replace('const pageCase=document.body.dataset.case;', 'const pageCase=document.body.dataset.case;')
# Generate new case artwork from actual product images, not missing SVGs.
fontfile=None
for i,c in enumerate(cases):
 color=colors[i%len(colors)];rgb=tuple(int(color[j:j+2],16) for j in (1,3,5));im=Image.new('RGBA',(400,300),(21,21,36,255));d=ImageDraw.Draw(im)
 d.rounded_rectangle((16,12,384,288),radius=35,fill=(*rgb,35),outline=(*rgb,230),width=5)
 icon=root/'assets'/P[c['drops'][0][0]]['img']
 if icon.exists():
  try:
   inner=Image.open(icon).convert('RGBA');inner.thumbnail((205,175),Image.Resampling.LANCZOS);im.alpha_composite(inner,((400-inner.width)//2,34))
  except Exception:pass
 f=ImageFont.load_default(size=24);label=c['brand'];w=d.textbbox((0,0),label,font=f)[2];d.text(((400-w)//2,241),label,font=f,fill='white');im.convert('RGB').save(root/'assets'/('case-'+c['id']+'.png'))
# Remove old case html pages; replace with new pages from same base document.
for page in root.glob('case-*.html'):page.unlink()
for page in root.glob('*.html'):
 if page.name.startswith('case-'):continue
 text=page.read_text();text=text.replace('const cases='+original+';', 'const cases='+casejson+';')
 # all pages were copies of same app, apply shared edits by using base with correct body class/head meta/title where possible
 if page.name=='index.html':text=base
 else:
  match=re.search(r'<body class="([^"]+)"(?: data-case="([^"]+)")?',text)
  bodyclass=match.group(1) if match else 'page-home'
  text=base.replace('<body class="page-home"','<body class="'+bodyclass+'"',1)
  text=text.replace('<title>Minecraft кейсы — MeshCase', '<title>'+page.stem.title()+' — MeshCase',1)
 page.write_text(text)
for c in cases:
 text=base.replace('<body class="page-home"','<body class="page-case" data-case="'+c['id']+'"',1)
 text=text.replace('<title>Minecraft кейсы — MeshCase','<title>'+c['name']+' — MeshCase',1)
 (root/('case-'+c['id']+'.html')).write_text(text)
(root/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
print('Generated',len(cases),'cases / images / pages')
