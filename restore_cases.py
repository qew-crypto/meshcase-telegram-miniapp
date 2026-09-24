from pathlib import Path
import json,re
r=Path('projects/minecraft-cases'); a=r/'assets'
htmls=list(r.glob('*.html'))
dec=json.JSONDecoder()
original=(r/'index.html').read_text()
all_cases,n=dec.raw_decode(original.split('const cases=',1)[1])
keep=[c for c in all_cases if c['type'] in ('server','client','allin')]
removed={c['id'] for c in all_cases if c not in keep}
new=json.dumps(keep,ensure_ascii=False,separators=(',',':'))
old=original.split('const cases=',1)[1][:n]
old_cat=re.search(r'const categorySections=\[.*?\];function caseGroup\(c\)\{.*?\}',original).group(0)
new_cat='const categorySections=[["servers","Серверные кейсы","Привилегии и наборы для серверов","▣"],["clients","Клиенты","Подписки и клиенты","◈"],["allin","ALL IN","Открытия по 10, 50 или 100","★"]];function caseGroup(c){return c.type===\'server\'?\'servers\':c.type===\'client\'?\'clients\':\'allin\'}'
old_filters=re.search(r'<div class="filters" role="group" aria-label="Фильтр категорий">.*?</div>',original).group(0)
new_filters='<div class="filters" role="group" aria-label="Фильтр категорий"><button class="filter active" data-filter="all">Все кейсы</button><button class="filter" data-filter="servers">▣ Серверы</button><button class="filter" data-filter="clients">◈ Клиенты</button><button class="filter" data-filter="allin">★ ALL IN</button></div>'
# Keep references for older inventory, but remove unrelated cases from the storefront and bundle.
for path in htmls:
 s=path.read_text()
 if 'const cases=' not in s: continue
 arr,count=dec.raw_decode(s.split('const cases=',1)[1]); assert len(arr)==len(all_cases),path
 s=s.replace('const cases='+s.split('const cases=',1)[1][:count],'const cases='+new,1)
 assert old_cat in s,path
 s=s.replace(old_cat,new_cat,1)
 assert old_filters in s,path
 s=s.replace(old_filters,new_filters,1)
 s=re.sub(r'✦ 47 кейсов · 7 категорий',f'✦ {len(keep)} кейсов · 3 категории',s)
 s=s.replace('Выбирай вселенную. Содержимое кейсов придумано специально для демо.','Выбирай кейсы серверов, клиентов или ALL IN. Виртуальное демо.')
 # Use explicit local asset paths instead of rewriting item image filenames based on source.
 old_img="function itemImage(p){if(!p)return A+'image-fallback.svg';return p.source==='Вымышленный товар'?A+(String(p.img||'').startsWith('drop-')?String(p.img):'drop-'+String(p.img||'').replace('.png','.svg')):A+(p.img||'image-fallback.svg')}"
 assert old_img in s,path
 s=s.replace(old_img,"function itemImage(p){return A+(p&&p.img?p.img:'image-fallback.svg')}")
 path.write_text(s)
for cid in removed:
 p=r/f'case-{cid}.html'
 if p.exists():p.unlink()
print('kept',len(keep),[x['id'] for x in keep]);print('removed',len(removed),'case pages')
