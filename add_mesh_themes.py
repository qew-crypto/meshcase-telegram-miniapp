"""Add original themed demo cases to the existing offline MeshCase site."""
from pathlib import Path
import json,re,html,random,math
root=Path(__file__).parent
pages=list(root.glob('*.html'))
s=(root/'index.html').read_text()
products=json.loads(re.search(r'const products=(\[.*?\]);',s).group(1))
existing=json.loads(re.search(r'const cases=(\[.*?\]);',s).group(1))
# All themes and odds below are original demo content; no claim that MineDrop publishes these cases.
themes=[
('starter','Стартовый набор','НОВИЧКА',39,'#91f5ab','server','✦'),
('caverns','Пещерные сокровища','ПОДЗЕМЕЛЬЕ',59,'#8bbefb','special','◆'),
('sunset','Закатный дроп','ЗАКАТ',79,'#ffae77','special','☀'),
('frost','Ледяное королевство','ЗИМА',99,'#92eaff','special','❄'),
('jungle','Сердце джунглей','ДЖУНГЛИ',129,'#71dc92','special','✿'),
('pirates','Пиратский сундук','ПИРАТЫ',159,'#ecbc74','special','⚓'),
('volcano','Пламя вулкана','ОГОНЬ',179,'#ff756b','special','▲'),
('sakura','Сакура','ВЕСНА',199,'#ffa9d4','special','✿'),
('nightfall','Ночной дозор','НОЧЬ',249,'#aa9aff','special','☾'),
('emerald-vault','Изумрудный сейф','ИЗУМРУДЫ',299,'#76f7cc','server','◇'),
('sky-islands','Небесные острова','НЕБО',349,'#83ddf9','special','✧'),
('cyberpunk','Киберпанк','НЕОН',399,'#e68cff','client','⌁'),
('samurai','Путь самурая','ВОСТОК',449,'#ff878c','special','✕'),
('arcane','Тайная магия','МАГИЯ',499,'#bf91ff','special','✺'),
('desert','Пески времени','ПУСТЫНЯ',549,'#f5ca84','special','⌛'),
('deep-sea','Глубокое море','ОКЕАН',599,'#66d9e9','special','≈'),
('steampunk','Шестерёнки','МЕХАНИЗМЫ',699,'#ddad75','special','⚙'),
('dragon-hoard','Сокровища дракона','ДРАКОН',799,'#f8ae64','special','♢'),
('toxic','Заражение','ХАРДКОР',899,'#c4e769','special','✳'),
('galaxy','Галактика','КОСМОС',999,'#a99bfa','special','✦'),
('knight','Орден рыцарей','РЫЦАРИ',1199,'#c0d7f5','server','⚔'),
('phantom','Призрачный мир','ПРИЗРАК',1399,'#b9ace8','special','☽'),
('crystal','Кристальная башня','КРИСТАЛЛЫ',1699,'#93f2ef','special','◇'),
('royal-gold','Золотая корона','КОРОНА',1999,'#ffe18a','special','♛'),
('moonlight','Лунный свет','ЛУНА',2499,'#c5c4ff','special','☾'),
('obsidian','Обсидиановый трон','ТРОН',2999,'#dc8fed','special','◆'),
('titan','Пробуждение титана','ТИТАН',3999,'#fbc183','special','♜'),
('infinity','Бесконечность','УЛЬТРА',4999,'#ab9cff','special','∞'),
('celestial','Небесный престол','ЛЕГЕНДА',7499,'#ffddaa','special','✧'),
('mythic','Мифический артефакт','МИФ',9999,'#fc9bd8','special','✺'),
]
# Only existing local images; product values are catalog estimates, not official case contents.
pool=sorted((p for p in products if p.get('source')=='DashCase' and p.get('value',0)>0 and (root/'assets'/p['img']).exists()),key=lambda p:p['value'])
assert len(pool)>50
new=[]
for i,(slug,name,brand,price,color,kind,symbol) in enumerate(themes):
 rng=random.Random(190+i)
 # Choose 6 distinct local products from increasingly costly tiers; odds total exactly 100%.
 multipliers=(.12,.27,.55,1.0,2.1,5.0)
 selected=[]
 for m in multipliers:
  target=price*m
  candidates=sorted((p for p in pool if p['id'] not in {q['id'] for q in selected}), key=lambda p:abs(math.log(max(p['value'],1)/max(target,1))))[:max(4,min(15,len(pool)//10))]
  selected.append(rng.choice(candidates[:min(6,len(candidates))]))
 drops=[[p['id'],w] for p,w in zip(selected,[38,27,17,10,6,2])]
 assert len({d[0] for d in drops})==6
 cover=f'case-{slug}.svg'
 esc=html.escape(name); sym=html.escape(symbol)
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 320" role="img" aria-label="{esc}"><defs><radialGradient id="glow"><stop stop-color="{color}" stop-opacity=".65"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient><linearGradient id="box" x2="1" y2="1"><stop stop-color="{color}"/><stop offset="1" stop-color="#30243f"/></linearGradient></defs><ellipse cx="200" cy="150" rx="170" ry="148" fill="url(#glow)"/><g fill="{color}" opacity=".6"><path d="M65 49h9v9h-9zm286 175h8v8h-8zM41 189h6v6h-6zm263-139h6v6h-6z"/><circle cx="321" cy="94" r="4"/><circle cx="97" cy="244" r="3"/></g><path d="M78 124 200 69 322 124 200 181Z" fill="url(#box)" stroke="#f2ecff" stroke-width="5" stroke-linejoin="round"/><path d="M78 124 200 181v105L78 231Z" fill="#352743" stroke="{color}" stroke-width="5" stroke-linejoin="round"/><path d="M322 124 200 181v105l122-55Z" fill="#513d65" stroke="{color}" stroke-width="5" stroke-linejoin="round"/><path d="M78 124 200 181l122-57" fill="none" stroke="{color}" stroke-width="7"/><text x="200" y="156" text-anchor="middle" font-size="58" font-family="DejaVu Sans,Arial,sans-serif" fill="#fff">{sym}</text><path d="M132 210h136" stroke="{color}" stroke-width="3" opacity=".75"/><text x="200" y="245" text-anchor="middle" font-size="16" font-weight="bold" font-family="Arial,sans-serif" fill="#fff">MESHCASE</text></svg>'''
 (root/'assets'/cover).write_text(svg)
 new.append(dict(id=slug,name=name,brand=brand,type=kind,price=price,desc='Тематический демо-кейс · виртуальные призы',accent=color,cover=cover,drops=drops))
assert not ({c['id'] for c in new}&{c['id'] for c in existing})
serialized=json.dumps(existing+new,ensure_ascii=False,separators=(',',':'))
for file in pages:
 text=file.read_text()
 text,n=re.subn(r'const cases=\[.*?\];','const cases='+serialized+';',text,count=1)
 assert n==1,file
 text=text.replace('BLOCKDROP','MeshCase').replace('BLOCK<em>DROP</em>','Mesh<em>Case</em>').replace('Blockdrop','MeshCase')
 text=text.replace('✦ 10 кейсов доступно',f'✦ {len(existing)+len(new)} кейсов доступно')
 # Keep existing localStorage key to preserve the visitor's demo inventory and balance.
 file.write_text(text)
template=(root/'case-legend.html').read_text()
for c in new:
 name=c['name'];doc=template.replace('data-case="legend"',f'data-case="{c["id"]}"').replace('Легенда сервера',name)
 (root/f'case-{c["id"]}.html').write_text(doc)
(root/'README.md').write_text((root/'README.md').read_text().replace('BLOCKDROP','MeshCase').replace('13 демо-кейсов',f'{len(existing)+len(new)} демо-кейсов')+'\n\nДобавлены 30 оригинальных тематических демо-кейсов разных ценовых категорий (по мотивам многообразия тематик MineDrop). Иллюстрации этих кейсов авторские SVG; состав дропа и шансы демонстрационные, иллюстрации товаров уже сохранены локально.\n')
print('total cases',len(existing)+len(new),'new pages',len(new),'available products',len(pool))
