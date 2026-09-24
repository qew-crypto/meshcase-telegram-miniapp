from pathlib import Path
import json, re, quickjs
from PIL import Image, ImageDraw, ImageFont
root=Path('projects/minecraft-cases'); assets=root/'assets'
files=[root/'index.html',*sorted(root.glob('case-*.html')),root/'profile.html',root/'upgrades.html',root/'catalog.html',root/'about.html',root/'topup.html']
for file in files:
 s=file.read_text(encoding='utf-8')
 def get_array(name):
  start=s.index('const '+name+'=')+len('const '+name+'=')
  obj,end=json.JSONDecoder().raw_decode(s[start:]);return obj,start,start+end
 products,a,b=get_array('products');cases,c,d=get_array('cases')
 products=[p for p in products if p.get('source')=='DashCase']
 P={p['id']:p for p in products}
 for case in cases:
  if case['type']=='allin':
   # Only existing, pictured catalogue items. No fictional durations for ReallyWorld / SpookyTime.
   choices={'allin-spark':['ref-40','ref-41','ref-43','ref-46'],
            'allin-meme':['ref-40','ref-42','ref-44','ref-46'],
            'allin-jackpot':['ref-14','ref-17','ref-29','catalog-291'],
            'allin-shadow':['ref-47','ref-49','ref-51','catalog-256'],
            'allin-royal':['ref-14','ref-20','ref-29','catalog-220']}[case['id']]
   case['drops']=[[id,w] for id,w in zip(choices,[94,5,0.99,0.01])]
   case['desc']='Только реальные товары сервера · редкий приз 0,01%'
   case['price']={'allin-spark':10,'allin-meme':35,'allin-jackpot':65,'allin-shadow':95,'allin-royal':149}[case['id']]
  else:
   case['drops']=[[id if id in P else None,w] for id,w in case['drops']]
   if any(id is None for id,w in case['drops']):
    available=[p for p in products if p.get('category','').upper()==case['brand'].upper()] if case['brand'].upper() in ['HOLYWORLD','REALLYWORLD','SPOOKYTIME'] else products
    # rare genuine catalog item, priced above other drops
    prior=[P[id]['value'] for id,w in case['drops'] if id in P]
    high=max(available,key=lambda p:p['value'] if p['value']>max(prior or [0]) else -1)
    case['drops']=[[id or high['id'],w] for id,w in case['drops']]
 # catalog actual products represented by previously missing fake high-tier prizes
 catalog=json.loads((root/'catalog-data.js').read_text().split('=',1)[1].rstrip(';'))['items']
 for num in [291,256,220]:
  x=next(x for x in catalog if x['id']==num)
  products.append(dict(id='catalog-'+str(num),name=x['category']+' · '+x['name']+' · '+x['type'],value=x['price'],img=x['img'],rarity='legendary',duration=x['type'],source='DashCase',category=x['category']))
 # rename old misleading allin labels / promises
 for case in cases:
  if case['id']=='allin-shadow':case['name']='ALL IN SPOOKYTIME'
  if case['id']=='allin-jackpot':case['name']='ALL IN HOLYWORLD'
  if case['id']=='allin-royal':case['name']='ALL IN ETERNITY'
 # Desc not suggesting unavailable items
 replacements=[(c,d,json.dumps(cases,ensure_ascii=False,separators=(',',':'))),(a,b,json.dumps(products,ensure_ascii=False,separators=(',',':')))]
 for start,end,val in sorted(replacements,reverse=True):s=s[:start]+val+s[end:]
 s=s.replace("A+'case-'+c.id+'.svg'","A+'case-'+c.id+'.png'")
 s=s.replace('Оригинальное изображение кейса','Иконка кейса')
 s=s.replace("${c.type==='allin'?'ALL IN · предметы выбранного сервера':'Выбери количество'}","${c.type==='allin'?'ALL IN · товары сервера':'Выбери количество'}")
 s=s.replace('Серверный ALL IN · мусор, месяц, 90 дней и навсегда · редкий дорогой лут','Только существующие призы сервера')
 s=s.replace('Вымышленное · демо','Демо-предмет')
 # fast upgrade is already available in section, make it prominent and obvious
 s=s.replace('<div class="upgrade-presets" id="upgradePresets"','<strong class="quick-title">⚡ Фаст апгрейд — выбрать цель</strong><div class="upgrade-presets" id="upgradePresets"')
 # fast opening toggle: bypass animation, still pay and save exactly once
 s=s.replace('<button class="btn btn-primary play-submit" id="playOpen">Открыть</button>','<label class="fast-toggle"><input type="checkbox" id="fastOpen"> ⚡ Фаст открытие (без прокрутки)</label><button class="btn btn-primary play-submit" id="playOpen">Открыть</button>')
 s=s.replace("let stack=$('#rollStack');stack.replaceChildren();","let stack=$('#rollStack');stack.replaceChildren();if($('#fastOpen').checked){busy=false;render();updatePlay();status.textContent=`Открыто ${count} кейсов в фаст-режиме!`;updateBatch();notify('Открыто кейсов: '+count);return;}")
 # explicit probability formatting, extremely rare items should not be displayed as zero
 s=s.replace("(pct<0.01?'0.01':pct.toFixed(2).replace(/0$/,'').replace(/\\.$/,''))+'%'","(pct<0.01?'0.01':pct.toFixed(2).replace(/0$/,'').replace(/\\.$/,''))+'%'")
 s=s.replace('</style>','.fast-toggle{display:flex;align-items:center;justify-content:center;gap:10px;margin:16px auto;color:#e7d8ff;font-weight:700;cursor:pointer}.fast-toggle input{accent-color:#9e63ff;width:19px;height:19px}.quick-title{display:block;color:#e4d6ff;margin:12px 0 8px}</style>')
 # suppress old fake catalog claims outside current inventory
 if '<script>' in s:
  js=s.split('<script>',1)[1].split('</script>',1)[0]
  try:quickjs.Context().eval('new Function('+json.dumps(js)+')')
  except Exception as e:raise RuntimeError(f'{file}: {e}')
 file.write_text(s,encoding='utf-8')
for case in cases:
 f=assets/('case-'+case['id']+'.png')
 color=tuple(int(case['accent'][i:i+2],16) for i in (1,3,5))
 im=Image.new('RGBA',(600,480),(0,0,0,0));dr=ImageDraw.Draw(im)
 for r in range(190,20,-4):
  dr.ellipse((300-r,230-r*.75,300+r,230+r*.75),fill=(*color,max(0,int(18*(190-r)/190))))
 dr.ellipse((100,398,500,445),fill=(4,5,12,90))
 dr.rounded_rectangle((124,139,476,381),radius=32,fill=(38,33,52),outline=(*color,255),width=9)
 dr.polygon([(123,185),(300,245),(477,185),(468,294),(300,348),(132,294)],fill=(53,43,65))
 dr.line([(300,246),(300,347)],fill=(*color,255),width=9)
 dr.rounded_rectangle((106,101,494,195),radius=22,fill=(65,51,76),outline=(*color,255),width=10)
 dr.rounded_rectangle((257,191,343,274),radius=13,fill=(*color,255),outline=(255,255,255),width=5)
 dr.ellipse((288,217,312,241),fill=(35,28,42))
 im.save(f)
print('Updated',len(files),'pages;',len(products),'catalog items;',len(cases),'cases; PNG case icons created')
