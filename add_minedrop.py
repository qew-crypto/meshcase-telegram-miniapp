"""One-time import of two MineDrop reference case inventories into the offline demo."""
from pathlib import Path
import requests, bs4, re, json, concurrent.futures, html
from urllib.parse import urljoin
root=Path('projects/minecraft-cases'); assets=root/'assets'
ses=requests.Session(); ses.headers['User-Agent']='Mozilla/5.0 (compatible; BlockdropDemo/1.0)'
configs=[(36,'major-demo','Большой приз','ПРЕМИУМ',2799,'#ffb763'),(66,'prime-demo','Прайм-комплект','HOLYWORLD',1490,'#9cc8ff')]
products=[]; cases=[]; images=[]
for cid,slug,title,brand,price,accent in configs:
 url=f'https://minedrop.art/case/{cid}'; resp=ses.get(url,timeout=18);resp.raise_for_status(); doc=bs4.BeautifulSoup(resp.text,'html.parser')
 cards=doc.select('.case-v2-item');assert len(cards)>10,(cid,len(cards))
 drops=[]
 for idx,card in enumerate(cards):
  name=card.select_one('.cv2-item-name').get_text(' ',strip=True);category=card.select_one('.cv2-item-server').get_text(' ',strip=True) if card.select_one('.cv2-item-server') else 'ДРУГОЕ'
  value=int(re.search(r'\d+',card.select_one('.cv2-item-price').get_text(' ',strip=True).replace(' ', '')).group())
  src=urljoin(url,card.select_one('img')['src']); ext=src.split('?')[0].rsplit('.',1)[-1].lower();ext=ext if ext in ('png','webp','jpg','jpeg') else 'png'
  filename=f'minedrop-{cid}-{idx}.{ext}';id=f'md-{cid}-{idx}'
  products.append(dict(id=id,name=f'{category} · {name}',value=value,img=filename,rarity='legendary' if value>=2000 else 'epic' if value>=700 else 'rare' if value>=200 else 'common',duration='по описанию товара',source='MineDrop',category=category))
  # The source publishes the inventory, not the odds. Approximate demo weights favour inexpensive items.
  drops.append([id,max(1,min(200,round((price/max(value,1))**1.65*10)))])
  images.append((src,filename))
 hero=doc.find('img',alt=re.compile('Case',re.I))
 # Use original artwork only when its alt text matches this particular source case.
 source_names={36:'Major-Case',66:'HOLY-VIPRIME-CASE'}
 hero=doc.find('img',alt=source_names[cid]); assert hero,(cid,'hero')
 images.append((urljoin(url,hero['src']),f'case-{slug}.webp'))
 cases.append(dict(id=slug,name=title,brand=brand,type='special',price=price,desc=f'По мотивам {source_names[cid]} MineDrop · цены товаров в коинах источника · шансы демо',accent=accent,drops=drops))

def download(entry):
 url,name=entry
 if (assets/name).exists():return len((assets/name).read_bytes())
 try:
  r=ses.get(url,timeout=12);r.raise_for_status(); data=r.content
  if len(data)<100 or not (data.startswith(b'\x89PNG') or data.startswith(b'RIFF') or data.startswith(b'\xff\xd8') or data.startswith(b'GIF8')):raise ValueError('invalid image')
  (assets/name).write_bytes(data)
  return len(data)
 except (requests.RequestException, ValueError):
  # Some assets are rate-limited (HTTP 429); keep the offline page usable with an original illustration.
  svgname=name.rsplit('.',1)[0]+'.svg'
  (assets/svgname).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" rx="32" fill="#27223a"/><path d="M120 24 203 80 178 178 120 217 62 178 37 80Z" fill="#704b9f" stroke="#ddc7ff" stroke-width="9"/><text x="120" y="153" text-anchor="middle" font-size="90" fill="white">✦</text></svg>')
  for prod in products:
   if prod['img']==name:prod['img']=svgname
  return 0
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 sizes=list(pool.map(download,images))
print('downloaded',len(sizes),'bytes',sum(sizes))
for c in cases:
 if not (assets/f'case-{c["id"]}.webp').exists():
  c['cover']=f'case-{c["id"]}.svg'
  (assets/c['cover']).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 260"><rect width="320" height="260" rx="30" fill="#302546"/><path d="M55 105 160 55 265 105 265 200 160 248 55 200Z" fill="#634794" stroke="#d7bcff" stroke-width="8"/><path d="M55 105 160 155 265 105M160 155V248" fill="none" stroke="#d7bcff" stroke-width="7"/></svg>')
for file in root.glob('*.html'):
 s=file.read_text();m=re.search(r'const products=(\[.*?\]);',s);assert m,file
 existing=json.loads(m.group(1));assert not any(x['id'].startswith('md-') for x in existing)
 s=s[:m.start(1)]+json.dumps(existing+products,ensure_ascii=False,separators=(',',':'))+s[m.end(1):]
 m=re.search(r'const cases=(\[.*?\]);',s);assert m,file
 existing=json.loads(m.group(1)); assert not any(x['id'].endswith('-demo') for x in existing)
 s=s[:m.start(1)]+json.dumps(existing+cases,ensure_ascii=False,separators=(',',':'))+s[m.end(1):]
 s=s.replace("c.id==='monthly'?'ref-case-'+c.id+'.webp':'case-'+c.id+'.svg'", "c.id==='monthly'?'ref-case-'+c.id+'.webp':c.id.endsWith('-demo')?(c.cover||'case-'+c.id+'.webp'):'case-'+c.id+'.svg'")
 file.write_text(s)
for c in cases:
 p=root/f'case-{c["id"]}.html'
 s=(root/'case-legend.html').read_text().replace('data-case="legend"',f'data-case="{c["id"]}"').replace('data-heading="Легенда"',f'data-heading="{c["name"]}"').replace('Кейс «Легенда»',f'Кейс «{c["name"]}»')
 p.write_text(s)
print('cases',len(cases),'items',len(products))
