from pathlib import Path
import re, html
root=Path('projects/minecraft-cases'); original=(root/'index.html').read_text()
js=original.split('<script>',1)[1].split('</script>',1)[0]
import json
cases=json.loads(js.split('const cases=',1)[1].split(';',1)[0])
css='''
/* Independent pages: one shared local state across all HTML files */
body:not(.page-home) .hero,body:not(.page-home) .stats{display:none}
body:not(.page-home) .main{padding-top:30px}
body:not(.page-home) .main:before{content:attr(data-heading);display:block;font:800 clamp(25px,4vw,42px)/1.25 Unbounded,sans-serif;margin:14px 0 10px}
body:not(.page-home) .main:after{content:attr(data-description);display:block;color:#aaa9bc;margin-bottom:25px;font-size:14px}
body.page-home #upgrade,body.page-home #inventory,body.page-home #topup,body.page-home .notice,body.page-home #about{display:none}
body.page-case #upgrade,body.page-case #inventory,body.page-case #topup,body.page-case .notice,body.page-case #about{display:none}
body.page-upgrades #cases,body.page-upgrades #inventory,body.page-upgrades #topup,body.page-upgrades .notice,body.page-upgrades #about{display:none}
body.page-profile #cases,body.page-profile #upgrade,body.page-profile #topup,body.page-profile .notice,body.page-profile #about{display:none}
body.page-topup #cases,body.page-topup #upgrade,body.page-topup #inventory,body.page-topup .notice,body.page-topup #about{display:none}
body.page-about #cases,body.page-about #upgrade,body.page-about #inventory,body.page-about #topup,body.page-about .notice{display:none}
body.page-case .filters{display:none}body.page-case .case-grid{grid-template-columns:minmax(230px,370px)}
.case-detail{margin:18px 0 40px;padding:20px;background:#161624;border:1px solid #373349;border-radius:18px}
.case-detail h3{margin:0 0 14px}.case-detail-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:10px}
.detail-item{background:#222233;border:1px solid #454052;border-radius:12px;padding:12px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:5px;min-width:0}
.detail-item img{width:78px;height:78px;object-fit:contain}.detail-item b{font-size:12px;overflow-wrap:anywhere}.detail-item small{color:#b5aec5}
.topup-box{max-width:620px;background:#1b1b2b;border:1px solid #45415c;border-radius:18px;padding:26px;margin:20px 0 60px}.topup-box p{color:#b9b6cc}.topup-box .btn{white-space:normal}
@media(max-width:650px){body:not(.page-home) .main{padding-top:12px}.case-detail{padding:12px}.case-detail-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.detail-item{padding:7px}.detail-item img{width:56px;height:56px}.topup-box{padding:17px}.head{align-items:center}.case-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.right-head .btn{display:inline-flex}}
'''
nav='''<nav class="nav" aria-label="Навигация"><a href="index.html">Кейсы</a><a href="upgrades.html">Апгрейд</a><a href="profile.html">Профиль</a><a href="topup.html">Пополнение</a></nav>'''
original=re.sub(r'<nav class="nav".*?</nav>',nav,original,count=1)
original=original.replace('href="#home"','href="index.html"').replace('href="#cases"','href="index.html"').replace('href="#upgrade"','href="upgrades.html"').replace('href="#inventory"','href="profile.html"').replace('href="#about"','href="about.html"')
original=original.replace('<body>','<body class="page-home" data-heading="" data-description="">')
original=original.replace('</style>',css+'</style>')
original=original.replace('<section class="section" id="about">','<section class="section" id="topup"><div class="section-head"><div><h2 class="section-title">Демо-пополнение</h2><p class="section-sub">Здесь нельзя внести деньги. Используются только виртуальные монеты.</p></div></div><div class="topup-box"><h3>🎁 Ежедневный бонус</h3><p>+500 ✦ раз в 24 часа. Виртуальные монеты не имеют денежной стоимости и не выводятся.</p><button class="btn btn-primary" id="topupBonus">Получить +500 ✦</button><p>Баланс и инвентарь сохраняются локально в этом браузере.</p><a href="index.html" class="btn btn-ghost">Перейти к кейсам →</a></div></section><section class="section" id="about">')
# One bonus button on each of the pages (all still have the same hidden stateful sections)
js=js.replace("[$('#bonusBtn'),$('#bonusBtnBottom')]","[$('#bonusBtn'),$('#bonusBtnBottom'),$('#topupBonus')]")
js=js.replace("b.id==='bonusBtn'?'+ Бонус':'Забрать бонус ✦'","b.id==='bonusBtn'?'+ Бонус':b.id==='topupBonus'?'Получить +500 ✦':'Забрать бонус ✦'")
js=js.replace("b.id==='bonusBtn'?'Бонус получен':'Бонус уже получен'","b.id==='bonusBtn'?'Бонус получен':'Бонус уже получен'")
js=js.replace("$('#bonusBtnBottom').addEventListener('click',bonus);","$('#bonusBtnBottom').addEventListener('click',bonus);$('#topupBonus').addEventListener('click',bonus);")
js=js.replace("location.hash='#inventory'","location.href='profile.html'")
js=js.replace("renderCases();render();","renderCases();render();const pageCase=document.body.dataset.case; if(pageCase){let c=cases.find(x=>x.id===pageCase);if(c){$('#caseGrid').innerHTML=$('#caseGrid').querySelector(`[data-case=\"${c.id}\"]`)?.closest('article')?.outerHTML||'';let detail=document.createElement('div');detail.className='case-detail';detail.innerHTML='<h3>Возможные дропы · шанс выпадения</h3><div class=\"case-detail-grid\">'+c.drops.map(([id,w])=>{let p=P[id];return `<div class=\"detail-item\"><img src=\"${itemImage(p)}\" alt=\"\"><b>${p.name}</b><small>${p.duration||'Демо'} · ✦ ${format(p.value)} · ${w}%</small></div>`}).join('')+'</div><p style=\"color:#a9a6bd\">Цены предметов — ориентиры каталога DashCase, цена кейса и вероятности придуманы для демо. Реальной выдачи нет.</p>';$('#cases').append(detail);}}")
original=original.split('<script>',1)[0]+'<script>'+js+'</script>'+original.split('</script>',1)[1]
# Home case buttons become navigation links, case pages retain modal buttons.
anchor='renderCases();render();const pageCase='
js=js.replace(anchor,"renderCases();render();if(!document.body.dataset.case){document.querySelectorAll('#caseGrid [data-case]').forEach(b=>{let a=document.createElement('a');a.href='case-'+b.dataset.case+'.html';a.className=b.className;a.textContent='Подробнее →';b.replaceWith(a)})}const pageCase=")
original=original.split('<script>',1)[0]+'<script>'+js+'</script>'+original.split('</script>',1)[1]
# For each page the same shared application markup and state; assets remain external & local.
def make(page,filename,title,description,caseid=None):
 s=original.replace('class="page-home" data-heading="" data-description=""',f'class="page-{page}" data-heading="{html.escape(title,quote=True)}" data-description="{html.escape(description,quote=True)}"'+(f' data-case="{caseid}"' if caseid else ''))
 s=s.replace('<title>BLOCKDROP — Minecraft кейсы · Демо</title>',f'<title>{html.escape(title)} — BLOCKDROP · демо</title>')
 if page=='case':
  s=s.replace('<h2 class="section-title">Каталог кейсов</h2>',f'<h2 class="section-title">Кейс «{html.escape(title)}»</h2>')
  s=s.replace('Выбирай вселенную. Содержимое кейсов придумано специально для демо.','Открой кейс за виртуальные монеты. Весь дроп ниже, включая шансы и картинки.')
 if page!='home':s=s.replace('✦ 10 кейсов доступно','✦ демо')
 # Highlight active nav
 active={'home':'index.html','case':'index.html','upgrades':'upgrades.html','profile':'profile.html','topup':'topup.html'}.get(page)
 if active:s=s.replace(f'href="{active}"',f'href="{active}" class="active"',1)
 (root/filename).write_text(s)
make('home','index.html','Minecraft кейсы','')
for c in cases:make('case','case-'+c['id']+'.html',c['name'],'Отдельная страница кейса · виртуальный дроп',c['id'])
for p,heading,description in [('upgrades','Апгрейд','Вращай стрелку: попадёт на зелёный сектор — выигрыш.'),('profile','Профиль','Твой демо-инвентарь и управление находками.'),('topup','Пополнение','Никаких настоящих платежей: только ежедневный демо-бонус.'),('about','О проекте','Ответы на вопросы об источниках данных и демо.')]:make(p,p+'.html',heading,description)
print('Created',len(cases)+5,'HTML pages')
