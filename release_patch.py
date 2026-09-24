from pathlib import Path
import json,re,html,shutil
p=Path('projects/minecraft-cases');assets=p/'assets';base=(p/'index.html').read_text()
oldcases=json.loads(re.search(r'const cases=(\[.*?\]);',base).group(1));oldproducts=json.loads(re.search(r'const products=(\[.*?\]);',base).group(1))
# Original locally drawn item art; no remote images or borrowed brand marks.
servers=[('spark','ALL IN MINI (RW)',10,'REALLYWORLD','#e7a36d',5,5000),('meme','ALL IN DRAGON (RW)',35,'REALLYWORLD','#a877e9',12,5000),('jackpot','ALL IN CUSTOM (HW)',65,'HOLYWORLD','#67d5da',20,6990),('shadow','ALL IN TITAN (SPOOKY)',95,'SPOOKYTIME','#ed8cac',30,7479),('royal','ALL IN ETERNITY (HW)',149,'HOLYWORLD','#dcb971',45,7690)]
newproducts=[];newcases=[]
for slug,name,price,server,color,common,rare in servers:
 low=f'allin-{slug}-basic';mid=f'allin-{slug}-mid';jack=f'allin-{slug}-grand'
 for iid,label,value,kind,mark in [(low,'Серверный набор',common,'common','▣'),(mid,'Привилегия сервера',max(common+1,round(price*.9)),'rare','✦'),(jack,'Редкая привилегия',rare,'legendary','◆')]:
  newproducts.append(dict(id=iid,name=f'{server} · {label}',value=value,img=iid+'.png',rarity=kind,duration='Демо-предмет',source='Вымышленный товар',category=server))
  (assets/f'drop-{iid}.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="{color}"/><stop offset="1" stop-color="#29233f"/></linearGradient></defs><rect width="128" height="128" rx="20" fill="#171525"/><path d="M20 34 64 18l44 16v57l-44 23-44-23Z" fill="url(#g)" stroke="#e9d8ff" stroke-width="3"/><path d="M20 35 64 56l44-21M64 56v58" fill="none" stroke="#e9d8ff" stroke-opacity=".6" stroke-width="3"/><text x="64" y="86" text-anchor="middle" fill="white" font-size="27" font-family="sans-serif">{mark}</text></svg>''')
 newcases.append(dict(id='allin-'+slug,name=name,brand=server,type='allin',price=price,desc=f'Сервер {server} · редкий приз до ✦ {rare} · шанс 0,1%',accent=color,drops=[[low,899],[mid,100],[jack,1]],minCount=1))
 # Use the original detailed chest template instead of the simplified ALL IN clip-art.
 original=(assets/'case-holyworld.svg').read_text()
 original=original.replace('Кейс Священный мир','Кейс '+html.escape(name)).replace('#fcc079',color).replace('Священный мир',html.escape(name))
 (assets/f'case-allin-{slug}.svg').write_text(original)
# Replace three original joke products and three original joke cases.
products=[x for x in oldproducts if not x['id'].startswith('allin-')]+newproducts
cases=[x for x in oldcases if x['type']!='allin']+newcases
# Create pages for new cases using the shared page template.
template=(p/'case-allin-spark.html').read_text()
for slug,*_ in servers[3:]:
 (p/f'case-allin-{slug}.html').write_text(template.replace('allin-spark','allin-'+slug))
css='''<style id="mesh-release-style">
/* Two visible five-case groups, instead of hiding five rolls. */
.roll-stack{display:flex;flex-direction:column;gap:20px}.roll-group{border:1px solid #75599555;border-radius:18px;background:linear-gradient(130deg,#332546,#191825);padding:15px;min-width:0}.roll-group h4{margin:0 0 12px;color:#d3b4ff;font-size:14px}.roll-group .roll-lane{margin:5px 0}.roll-wins{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;max-height:none!important}.roll-win{min-width:0;overflow:hidden}.roll-win strong{overflow-wrap:anywhere}.roll-count-note{margin:8px 0}.upgrade-presets{display:flex;gap:7px;flex-wrap:wrap;justify-content:center}.upgrade-presets button{border:1px solid #76549a;background:#292137;color:#e4d6ff;border-radius:9px;padding:9px 13px;font-weight:800;cursor:pointer;transition:.2s}.upgrade-presets button:hover,.upgrade-presets button.active{background:#7448a3;color:#fff;transform:translateY(-2px);box-shadow:0 5px 18px #a052e552}.upgrade-presets button:disabled{opacity:.5;cursor:not-allowed;transform:none}.upgrade-center{border:1px solid #8159ac88!important;box-shadow:inset 0 1px #ffffff18,0 15px 40px #0004}.upgrade-panel{box-shadow:0 12px 28px #0002}.upgrade-center .chance{box-shadow:0 0 25px #a368f538}.upgrade-center .up-info{flex:1;min-width:190px}.upgrade-center #upgradeBtn{min-width:155px}@media(max-width:750px){.roll-wins{grid-template-columns:repeat(2,minmax(0,1fr))}.roll-group{padding:9px}.upgrade-center{flex-wrap:wrap;justify-content:center;text-align:center}}
</style>'''
for f in p.glob('*.html'):
 s=f.read_text();s=re.sub(r'const products=\[.*?\];',lambda m:'const products='+json.dumps(products,ensure_ascii=False,separators=(',',':'))+';',s,count=1)
 s=re.sub(r'const cases=\[.*?\];',lambda m:'const cases='+json.dumps(cases,ensure_ascii=False,separators=(',',':'))+';',s,count=1)
 # Count is now 47; remove misleading old labels and unnecessary minimum-of-ten copy.
 s=s.replace('42 кейса · 6 категорий',f'{len(cases)} кейсов · 7 категорий').replace('13 демо-кейсов',f'{len(cases)} демо-кейсов')
 s=s.replace('Большой риск: 99,4% мелочь, 0,6% редкий приз · только пакетами','Серверный дроп: редкий приз с шансом 0,1% · 1, 5 или 10 открытий')
 s=s.replace("c.type==='allin'?'ALL IN · минимальный пакет — 10 кейсов':'Выбери количество'","c.type==='allin'?'ALL IN · предметы выбранного сервера':'Выбери количество'")
 s=s.replace("(c.type==='allin'?[10,50,100]:[1,2,3,5,10])","[1,2,3,5,10]")
 s=s.replace('let lanes=[];for(let j=0;j<Math.min(5,count);j++){', '''let lanes=[];for(let j=0;j<Math.min(10,count);j++){if(j%5===0){let group=document.createElement('div');group.className='roll-group';group.innerHTML=`<h4>${count>5?`Сторона ${j===0?'I':'II'} · кейсы ${j+1}–${Math.min(j+5,count)}`:`Кейсы ${j+1}–${Math.min(j+5,count)}`}</h4>`;stack.append(group)}''')
 s=s.replace('stack.append(lane);lanes.push([lane,strip])','stack.lastElementChild.append(lane);lanes.push([lane,strip])')
 s=s.replace('if(count>5){let note=', 'if(count>10){let note=')
 s=s.replace('`Показаны 5 из ${count} барабанов · все ${count} результатов появятся ниже`','`Показаны 10 из ${count} барабанов · все ${count} результатов появятся ниже`')
 # Wheel presets choose nearest ACTUAL available item; odds always derive from actual value.
 s=s.replace('<div class="up-info"><h3>Рискни ради большего</h3>','<div class="up-info"><h3>Рискни ради большего</h3><div class="upgrade-presets" id="upgradePresets" role="group" aria-label="Быстрый выбор цели"><button type="button" data-up-preset="2">×2</button><button type="button" data-up-preset="5">×5</button><button type="button" data-up-preset="10">×10</button><button type="button" data-up-preset="30">30%</button><button type="button" data-up-preset="75">75%</button></div>')
 s=s.replace("$('#upgradeBtn').disabled=!src||!dst||busy;", "$('#upgradeBtn').disabled=!src||!dst||busy;$('#upgradePresets').querySelectorAll('button').forEach(b=>{b.disabled=!src||!targets.length||busy;b.classList.toggle('active',b.dataset.upPreset===activeUpgradePreset)});")
 s=s.replace('function renderUpgrade(){','let activeUpgradePreset=null;function renderUpgrade(){')
 s=s.replace('sourceUid=b.dataset.source;targetId=null;', 'sourceUid=b.dataset.source;targetId=null;activeUpgradePreset=null;')
 s=s.replace('targetId=b.dataset.target;', 'targetId=b.dataset.target;activeUpgradePreset=null;')
 s=s.replace("$('#upgradeBtn').addEventListener('click',upgrade);",'''$('#upgradePresets').addEventListener('click',e=>{let b=e.target.closest('[data-up-preset]');if(!b||busy)return;let owned=state.inventory.find(x=>x.uid===sourceUid),src=owned&&P[owned.id];if(!src)return;let choices=products.filter(x=>x.value>src.value);if(!choices.length)return;let v=Number(b.dataset.upPreset),wanted=v===30||v===75?src.value*80/v:src.value*v;let best=choices.reduce((a,x)=>Math.abs(x.value-wanted)<Math.abs(a.value-wanted)?x:a);targetId=best.id;activeUpgradePreset=b.dataset.upPreset;renderUpgrade();$('#targetSelection').scrollIntoView({block:'nearest',behavior:'smooth'})});$('#upgradeBtn').addEventListener('click',upgrade);''')
 s=s.replace('sourceUid=null;targetId=null;busy=false;save();render();wheel.style', 'sourceUid=null;targetId=null;activeUpgradePreset=null;busy=false;save();render();wheel.style')
 s=s.replace('</head>',css+'</head>',1)
 f.write_text(s)
print('updated',len(list(p.glob('*.html'))),'pages',len(cases),'cases')
