from pathlib import Path
import re,json
p=Path('.')
slugs=['spark','meme','jackpot','shadow','royal']
scales={'spark':(2,50,500,5000),'meme':(5,100,1000,8000),'jackpot':(8,180,1800,12000),'shadow':(12,250,2500,18000),'royal':(20,400,4000,30000)}
colors={'spark':'#9b9aaa','meme':'#68d7c7','jackpot':'#b873ff','shadow':'#ed8cac','royal':'#e8c56d'}
# icon assets for every all-in drop
for slug in slugs:
    for key,label,symbol in [('trash','Мусор','×'),('month','Месяц','30'),('90d','90 дней','90'),('forever','Навсегда','∞')]:
        color=colors[slug]
        (p/'assets'/f'drop-allin-{slug}-{key}.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="{color}" stop-opacity=".9"/><stop offset="1" stop-color="#171425"/></linearGradient></defs><rect width="160" height="160" rx="32" fill="url(#g)"/><circle cx="80" cy="80" r="57" fill="#11121e88" stroke="{color}" stroke-width="4"/><text x="80" y="98" text-anchor="middle" fill="white" font-family="Arial,sans-serif" font-size="{48 if key not in ('month','90d') else 34}" font-weight="800">{symbol}</text><text x="80" y="128" text-anchor="middle" fill="{color}" font-family="Arial,sans-serif" font-size="13">{label.upper()}</text></svg>''')

def patch_file(f):
    s=f.read_text()
    # products array
    m=re.search(r'const products=(\[.*?\]);',s)
    if not m:return
    products=json.loads(m.group(1))
    # replace all-in products, retaining names and server labels
    for c in products:
        if c.get('id','').startswith('allin-') and c.get('id','').split('-')[-1] in ('basic','mid','grand','dust','joke'):
            pass
    for slug in slugs:
        prefix='allin-'+slug
        old=[x for x in products if x.get('id','').startswith(prefix+'-')]
        server=(old[0].get('category','СЕРВЕР') if old else 'СЕРВЕР')
        products=[x for x in products if not x.get('id','').startswith(prefix+'-')]
        vals=scales[slug]
        for key,label,val in zip(['trash','month','90d','forever'],['Мусор','Месяц','90 дней','Навсегда'],vals):
            products.append({'id':f'{prefix}-{key}','name':f'{server} · {label}','value':val,'img':f'{prefix}-{key}.png','rarity':'common' if key=='trash' else ('rare' if key in ('month','90d') else 'legendary'),'duration':label,'source':'Вымышленный товар','category':server})
    s=s[:m.start()]+'const products='+json.dumps(products,ensure_ascii=False,separators=(',',':'))+';'+s[m.end():]
    # cases array has products now reparse after offset
    m=re.search(r'const cases=(\[.*?\]);',s)
    if not m:return
    cases=json.loads(m.group(1))
    for c in cases:
        if c.get('id') in slugs:
            pass
        if c.get('id','').startswith('allin-'):
            slug=c['id'][6:]
            if slug in slugs:
                c['drops']=[[f'allin-{slug}-trash',7000],[f'allin-{slug}-month',2000],[f'allin-{slug}-90d',999],[f'allin-{slug}-forever',1]]
                c['minCount']=10
                c['desc']='Серверный ALL IN · мусор, месяц, 90 дней и навсегда · редкий шанс окупиться'
    s=s[:m.start()]+'const cases='+json.dumps(cases,ensure_ascii=False,separators=(',',':'))+';'+s[m.end():]
    # batch buttons: ALL IN 10/50/100, regular 1/2/3/5/10
    s=s.replace("${[1,2,3,5,10].map(n=>", "${(c.type==='allin'?[10,50,100]:[1,2,3,5,10]).map(n=>")
    # robust percentage display: never show 0%, minimum 0.01%
    old="return (pct<1?pct.toFixed(1):pct.toFixed(1).replace(/\\.0$/,''))+'%'"
    s=s.replace(old,"return (pct<0.01?'0.01':pct.toFixed(2).replace(/0$/,'').replace(/\\.$/,''))+'%'")
    # make label explicit fast upgrade everywhere
    s=s.replace('Быстрый выбор цели','Фаст апгрейд · быстрый выбор цели')
    f.write_text(s)
for f in p.glob('*.html'):patch_file(f)
