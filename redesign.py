from pathlib import Path
import json,re,html,hashlib,random
root=Path('.')
files=list(root.glob('*.html'))
cs=json.loads(re.search(r'const cases=(\[.*?\]);', (root/'index.html').read_text()).group(1))
# Every case illustration is generated locally as original SVG geometry, without borrowed case covers.
from colorsys import hsv_to_rgb
shapes=[
'<path d="M200 55 260 160 200 259 140 160Z"/><path d="M200 55v204M140 160h120"/>',
'<path d="M122 213 143 99 200 133 257 99 278 213Z"/><circle cx="200" cy="177" r="16"/>',
'<path d="M126 186 200 65 274 186 200 247Z"/><path d="M126 186h148M200 65v182"/>',
'<circle cx="200" cy="158" r="79"/><circle cx="200" cy="158" r="44"/><path d="M200 51v214M93 158h214"/>',
'<path d="M200 54 227 129 305 140 244 189 263 267 200 226 137 267 156 189 95 140 173 129Z"/>',
'<path d="M120 226V126l80-52 80 52v100l-80 52Z"/><path d="M120 126 200 177 280 126M200 177v101"/>',
'<path d="M200 53c-73 75-106 116-75 179 26 48 124 48 150 0 31-63-2-104-75-179Z"/><path d="M161 216q39-93 78 0"/>',
'<path d="M100 157q100-139 200 0-100 139-200 0Z"/><circle cx="200" cy="157" r="35"/>',
'<path d="M200 50 285 110v102l-85 60-85-60V110Z"/><path d="M115 110h170M115 212h170M200 50v222"/>',
'<path d="M200 51 254 110 247 170 286 218 200 268 114 218 153 170 146 110Z"/><path d="M146 110h108M153 170h94"/>',
'<path d="M121 104h158v36h-38v109h-82V140h-38Z"/><path d="M173 177h54"/>',
'<path d="M200 51 236 111 298 124 254 176 264 244 200 217 136 244 146 176 102 124 164 111Z"/><circle cx="200" cy="162" r="22"/>'
]
for i,c in enumerate(cs):
    rng=random.Random(int(hashlib.sha256(c['id'].encode()).hexdigest()[:12],16))
    r,g,b=hsv_to_rgb((i*0.61803398875+.08)%1,.54,.98)
    bright='#%02x%02x%02x'%(int(r*255),int(g*255),int(b*255))
    dark='#%02x%02x%02x'%(int(r*65),int(g*65),int(b*65))
    dots=''.join(f'<circle cx="{rng.randrange(23,377)}" cy="{rng.randrange(18,258)}" r="{rng.choice([2,3,4])}" fill="{bright}" opacity=".46"/>' for _ in range(17))
    motif=shapes[i%len(shapes)]
    glyph=''.join(w[0] for w in c['id'].split('-'))[:2].upper()
    name=html.escape(c['name'])
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 320" role="img" aria-label="Оригинальная иллюстрация: {name}">
<defs><radialGradient id="a"><stop stop-color="{bright}" stop-opacity=".36"/><stop offset="1" stop-color="{bright}" stop-opacity="0"/></radialGradient><linearGradient id="b" x2="1" y2="1"><stop stop-color="{bright}" stop-opacity=".85"/><stop offset="1" stop-color="{dark}"/></linearGradient></defs>
<circle cx="200" cy="151" r="147" fill="url(#a)"/>{dots}
<path d="M94 87 200 31 306 87v144l-106 57-106-57Z" fill="#101c25" stroke="{bright}" stroke-opacity=".48" stroke-width="3"/>
<path d="M106 96 200 46 294 96v126l-94 52-94-52Z" fill="{dark}" fill-opacity=".28" stroke="{bright}" stroke-opacity=".21" stroke-width="2"/>
<g fill="none" stroke="{bright}" stroke-width="8" stroke-linejoin="round" stroke-linecap="round" transform="translate({(i%3-1)*3} {(i%4-2)*2})">{motif}</g>
<path d="M115 241h170" stroke="{bright}" stroke-opacity=".34"/>
<text x="200" y="265" fill="#f8f9ff" font-family="system-ui,sans-serif" font-size="16" font-weight="900" text-anchor="middle" letter-spacing="2">{html.escape(glyph)} · {i+1:02d}</text>
</svg>'''
    (root/'assets'/f'case-{c["id"]}.svg').write_text(svg)
# Categories reflect theme AND price, not the original catch-all special group.
groups=[('start','Доступные','Первые открытия и небольшие находки','✦'),('worlds','Миры и стихии','Путешествия по разным мирам','◈'),('servers','Серверы и подписки','Привилегии и игровые возможности','▣'),('adventure','Приключения','Пираты, рыцари и легенды','✧'),('tech','Магия и технологии','Тайны, механизмы и кристаллы','⬡'),('premium','Премиум','Дорогие кейсы для виртуальной коллекции','★')]
worlds={'nether','mystic','caverns','sunset','frost','jungle','volcano','sakura','nightfall','sky-islands','desert','deep-sea','toxic','moonlight'}
adventure={'pirates','samurai','dragon-hoard','knight','phantom','legend','royal-gold'}
tech={'cyberpunk','arcane','steampunk','crystal','diamond','emerald-vault','galaxy','obsidian'}
def group(c):
    if c['price']>=2499:return 'premium'
    if c['id'] in {'starter','caverns','sunset','mystic','frost'}:return 'start'
    if c['id'] in worlds:return 'worlds'
    if c['id'] in adventure:return 'adventure'
    if c['id'] in tech:return 'tech'
    return 'servers'
labels={g[0]:g for g in groups}
nav='<div class="filters" role="group" aria-label="Фильтр категорий"><button class="filter active" data-filter="all">Все категории</button>'+''.join(f'<button class="filter" data-filter="{k}">{icon} {title}</button>' for k,title,_,icon in groups)+'</div>'
start="<div class=\"filters\" role=\"group\" aria-label=\"Фильтр кейсов\">"
newrender='''function renderCases(){let filtered=cases.filter(c=>activeFilter==='all'||caseGroup(c)===activeFilter);$('#caseGrid').innerHTML=categorySections.map(([key,title,description,icon])=>{let list=filtered.filter(c=>caseGroup(c)===key);if(!list.length)return '';return `<section class="category-section" id="category-${key}"><div class="category-heading"><div class="category-mark" aria-hidden="true">${icon}</div><div><h3>${title} <span class="category-count">${list.length}</span></h3><p>${description}</p></div></div><div class="case-grid">${list.map(c=>`<article class="case-card" style="--accent:${c.accent}"><div class="case-top"><span class="tag">${c.brand}</span><span style="color:${c.accent}" aria-hidden="true">✦</span></div><div class="case-pic"><img src="${A+'case-'+c.id+'.svg'}" alt="Оригинальная иллюстрация кейса ${c.name}" loading="lazy"></div><h3 class="case-name">${c.name}</h3><p class="case-desc">${c.desc}</p><div class="case-loot" title="Примеры дропов">${c.drops.slice(0,4).map(([id])=>`<img src="${itemImage(P[id])}" alt="" loading="lazy">`).join('')}</div><div class="case-bottom"><span class="price"><span class="coin">✦</span> ${format(c.price)}</span><a class="btn btn-primary" href="case-${c.id}.html">Открыть →</a></div></article>`).join('')}</div></section>`}).join('')}
const categorySections='''+json.dumps(groups,ensure_ascii=False)+''';function caseGroup(c){if(c.price>=2499)return 'premium';if(['starter','caverns','sunset','mystic','frost'].includes(c.id))return 'start';if('''+json.dumps(sorted(worlds))+'''.includes(c.id))return 'worlds';if('''+json.dumps(sorted(adventure))+'''.includes(c.id))return 'adventure';if('''+json.dumps(sorted(tech))+'''.includes(c.id))return 'tech';return 'servers'}
'''
for p in files:
    s=p.read_text()
    pos=s.index(start)
    end=s.index('</div><div class="case-grid" id="caseGrid">',pos)+len('</div>')
    s=s[:pos]+nav+s[end:]
    a=s.index('function renderCases(){');b=s.index('function render(){',a)
    s=s[:a]+newrender+s[b:]
    # Everywhere case cover art is referenced, switch to self-produced illustrations.
    s=re.sub(r"\(c\.id==='holyworld'\|\|c\.id==='reallyworld'\|\|c\.id==='clients'\|\|c\.id==='spooky'\|\|c\.id==='monthly'\?'ref-case-'\+c\.id\+'\.webp':c\.cover\|\|'case-'\+c\.id\+'\.svg'\)","('case-'+c.id+'.svg')",s)
    s=re.sub(r"\(\['holyworld','reallyworld','clients','spooky','monthly'\]\.includes\(c\.id\)\?'ref-case-'\+c\.id\+'\.webp':c\.cover\|\|'case-'\+c\.id\+'\.svg'\)","('case-'+c.id+'.svg')",s)
    # Relative CSS link is present on every page.
    s=s.replace('<link rel="stylesheet" href="theme.css">','<link rel="stylesheet" href="theme.css">\n<link rel="stylesheet" href="mesh-redesign.css">')
    s=s.replace('42 кейсов доступно','42 кейса · 6 категорий')
    p.write_text(s)
(root/'mesh-redesign.css').write_text('''/* MeshCase original design: editorial dashboard + grouped collections */
:root{--bg:#09141b;--panel:#12232c;--line:#304551;--text:#f2f7f8;--muted:#a4b7bd;--violet:#74f0ca;--aqua:#74f0ca;--gold:#ffd78a}
body{background:radial-gradient(ellipse 75% 350px at 50% 0,#1c4345 0,transparent 100%),#09141b;color:var(--text)}
.topline{background:#0f292c;border-color:#2d5250;color:#a6dfce}header{background:#091a20ef;border-color:#28414a}.logo em{color:#71f4ca}.logo-icon{background:linear-gradient(145deg,#60d9bb,#208177);box-shadow:0 0 24px #40daa64d}.nav a:hover,.nav a.active{color:#8cf9ce}
.balance{background:#102a30;border-color:#345a59}.btn-primary{background:linear-gradient(120deg,#95f6d1,#48bda8);box-shadow:0 7px 25px #36cba439;color:#092621}.btn-ghost{background:#163039;border-color:#325257}.hero{background:#102a32;border-color:#2e4950}.hero:before{background:linear-gradient(90deg,#091b22fa 4%,#0b2530ed 38%,#102f3888 75%),linear-gradient(0deg,#09141b,transparent 40%),url('assets/landscape.png') center / cover no-repeat}.hero:after{background:radial-gradient(circle at 69% 51%,#4bf0bb33,transparent 38%)}.eyebrow{background:#4ce1ab1a;border-color:#60e3b551;color:#a3ffd5}.dot{background:#76f4c8;box-shadow:0 0 12px #76f4c8}.hero h1 span{color:#89f7d1}.hero-visual:before{background:#30bda45c}.stats{background:#0e2229;border-color:#284550}.stat-icon{background:#193a3d}
.main{padding-top:54px}.section-title{letter-spacing:-.04em}.pill{background:#15353a;border-color:#37605b;color:#a1f4d3}.filters{gap:9px;position:relative;margin:26px 0 30px}.filter{background:#112831;border-color:#31515a;color:#bdd3d6;border-radius:100px;padding:10px 16px}.filter:hover,.filter.active{background:#88f1ca;border-color:#88f1ca;color:#0a262a}.case-grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}#caseGrid{display:flex;flex-direction:column;gap:56px}.category-section{min-width:0;scroll-margin-top:105px}.category-heading{display:flex;align-items:center;gap:15px;margin:0 0 19px;padding-bottom:16px;border-bottom:1px solid #34515a}.category-mark{width:49px;height:49px;flex:none;border-radius:13px;background:#19463f;border:1px solid #428369;display:grid;place-items:center;color:#9df6d3;font-size:23px}.category-heading h3{margin:0;font:700 clamp(18px,2.3vw,26px)/1.3 Unbounded,sans-serif;letter-spacing:-.04em}.category-count{color:#9cf4cd;font:700 12px Manrope,sans-serif;vertical-align:middle;margin-left:8px}.category-heading p{color:#a5b9bc;margin:3px 0 0}.case-card{background:linear-gradient(155deg,#192f38,#102129 78%);border-color:#2e4b52;border-radius:16px}.case-card:hover{border-color:#75d9bd}.case-pic:before{opacity:.22}.case-name{line-height:1.4}.case-bottom{border-color:#304c51}.tag{background:#ffffff15;color:#d4e6e4}.case-loot img{background:#183039}.upgrade-panel,.upgrade-center{background:linear-gradient(145deg,#1b3038,#10232b);border-color:#335059}.foot,footer{border-color:#2c4a50}
@media(max-width:950px){.case-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:680px){.case-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.filters{flex-wrap:nowrap;overflow-x:auto;padding-bottom:9px;scrollbar-width:thin}.filter{flex:none}.category-heading{align-items:flex-start}.category-mark{width:42px;height:42px}}@media(max-width:430px){.case-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.case-card{padding:10px}.case-pic{height:130px}.case-pic>img{height:135px}.case-card .btn{padding:8px;font-size:10px}.case-name{font-size:12px}.case-desc{font-size:10px}.category-heading h3{font-size:18px}}
''')
print('Updated',len(files),'pages,',len(cs),'original illustrations, 6 groups')
