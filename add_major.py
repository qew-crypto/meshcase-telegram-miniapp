"""Add locally cached DashCase Major artwork and its disclosed drop pool to the offline demo."""
from pathlib import Path
import requests, json, re
from PIL import Image
from io import BytesIO
root=Path('projects/minecraft-cases'); assets=root/'assets'
r=requests.get('https://dashcase.xyz/api/cases/list',timeout=20);r.raise_for_status()
source=next(c for c in r.json() if c['id']==26)
assert source['name']=='Мажор' and source['price']==1499
p=json.loads(re.search(r'const products=(\[.*?\]);',(root/'index.html').read_text())[1]); existing={x['id'] for x in p}
# Canonical catalogue identifiers may differ from ids in the source case's list.
catalog=json.loads((root/'catalog-data.js').read_text().removeprefix('window.DASH_CATALOG=').rstrip(';'))
raw={ (i['category'],i['name'],i['price'],i['type']):i for i in catalog['items'] }
# catalog-data items contain the complete canonical unique list; use SKU values to match local products.
local={(x['name'],x['value']):x['id'] for x in p if x['source']=='DashCase'}
drops=[]
for item in source['items']:
 label=item['category']+' · '+item['name']+' · '+item['type']
 ident=local.get((label,item['price']))
 if not ident:
  label=item['category']+' · '+item['name']
  ident=local.get((label,item['price']))
 assert ident in existing,(label,item['price'])
 drops.append([ident,max(1,round((source['price']/max(1,item['price']))**1.4*10))])
url='https://dashcase.xyz/cases/major.webp';resp=requests.get(url,timeout=20);resp.raise_for_status();Image.open(BytesIO(resp.content)).verify();(assets/'ref-case-major.webp').write_bytes(resp.content)
case=dict(id='major',name='Мажор',brand='DASHCASE · ПРИМЕР',type='special',price=source['price'],desc='Состав дропа и цена — DashCase; шансы здесь демонстрационные, не оригинальные',accent='#f6c377',cover='ref-case-major.webp',drops=drops)
for f in root.glob('*.html'):
 s=f.read_text(encoding='utf-8');m=re.search(r'const cases=(\[.*?\]);',s);assert m,f
 cases=json.loads(m[1]);assert not any(c['id']=='major' for c in cases)
 s=s[:m.start(1)]+json.dumps(cases+[case],ensure_ascii=False,separators=(',',':'))+s[m.end(1):]
 old="c.id==='monthly'?'ref-case-'+c.id+'.webp':'case-'+c.id+'.svg'"
 # Existing pages use a slightly different expression; patch both render paths explicitly.
 s=s.replace("c.id==='monthly'?'ref-case-'+c.id+'.webp':'case-'+c.id+'.svg'", "c.id==='monthly'?'ref-case-'+c.id+'.webp':c.cover||'case-'+c.id+'.svg'")
 s=s.replace("['holyworld','reallyworld','clients','spooky','monthly'].includes(c.id)?'ref-case-'+c.id+'.webp':'case-'+c.id+'.svg'", "['holyworld','reallyworld','clients','spooky','monthly'].includes(c.id)?'ref-case-'+c.id+'.webp':c.cover||'case-'+c.id+'.svg'")
 f.write_text(s,encoding='utf-8')
f=root/'case-major.html';s=(root/'case-legend.html').read_text(encoding='utf-8').replace('data-case="legend"','data-case="major"').replace('data-heading="Легенда"','data-heading="Мажор"').replace('Кейс «Легенда»','Кейс «Мажор»');f.write_text(s,encoding='utf-8')
print('Added case',case['name'],'items',len(drops),'cover bytes',len(resp.content))
