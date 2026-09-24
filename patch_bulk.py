from pathlib import Path
p=Path('game_backend.py');s=p.read_text();a=s.index("        if current['balance']<c['price']");b=s.index("    elif action in",a)
s=s[:a]+'''        count=data.get('count',1)
        allowed=(10,25,50,100) if c['type']=='allin' else (1,2,3,5,10)
        if type(count)!=int or count not in allowed: raise ValueError('Недопустимое количество открытий')
        cost=c['price']*count
        if current['balance']<cost: raise ValueError('Недостаточно монет')
        weights=[int(Decimal(str(p))*1000) for _,p in c['drops']]
        if sum(weights)!=100000: raise ValueError('Кейс временно недоступен: неверные шансы')
        prizes=[]
        for _ in range(count):
            roll=secrets.randbelow(100000)
            for (iid,_),weight in zip(c['drops'],weights):
                if roll<weight: break
                roll-=weight
            prizes.append(grant(db,uid,ITEMS[iid]))
        delta=-cost
        result.update(prize=prizes[0],prizes=prizes,count=count,case_id=c['id'])
        reason='Открытие: '+c['name']+' × '+str(count)
'''+s[b:];p.write_text(s)
p=Path('miniapp.html');s=p.read_text().replace('<script src="miniapp.js"','<link rel="stylesheet" href="bulk-layout.css"><script src="miniapp.js"');s=s.replace('<section class="view" id="profile"','''<section class="view" id="upgrade" hidden><h1>Апгрейд</h1><p>Выбери свой предмет и более дорогую цель. При неудаче исходный предмет сгорает.</p><div class="two-cols"><div class="card"><h2>Твой предмет</h2><select id="upgradeSource" aria-label="Твой предмет"></select><div id="sourcePreview"></div></div><div class="card"><h2>Цель апгрейда</h2><div class="filters" id="upgradePresets"><button data-mult="2">×2</button><button data-mult="5">×5</button><button data-mult="10">×10</button><button data-chance="30">30%</button><button data-chance="50">50%</button></div><select id="upgradeTarget" aria-label="Цель апгрейда"></select><div id="targetPreview"></div></div></div><p class="muted">Быстрые кнопки подбирают ближайшую доступную цель. Точный шанс показан ниже.</p><p id="upgradeChance" aria-live="polite"></p><button id="performUpgrade" class="primary" disabled>Апгрейд</button></section><section class="view" id="profile"''');s=s.replace('<button data-tab="profile"><span>','<button data-tab="upgrade"><span>↑</span>Апгрейд</button><button data-tab="profile"><span>');s=s.replace('<button id="openCase"','<div id="openCounts" class="filters" aria-label="Количество кейсов"></div><button id="openCase"');s=s.replace('Инвентарь и апгрейды','Инвентарь');p.write_text(s)
p=Path('miniapp.js');s=p.read_text().replace('let activeCase=null;','let activeCase=null,openCount=1,owned=[];');s=s.replace("['cases','profile','support','admin']","['cases','upgrade','profile','support','admin']");s=s.replace("if(id==='support')await refreshTickets();","if(id==='upgrade')await inventory();if(id==='support')await refreshTickets();");s=s.replace('activeCase=c;',"activeCase=c;openCount=c.type==='allin'?10:1;renderCounts();");s=s.replace("{case_id:activeCase.id}","{case_id:activeCase.id,count:openCount}");s=s.replace("const text=j.action==='sell'?","const text=j.action==='open'&&j.count>1?'Открыто '+j.count+' кейсов · Все предметы в инвентаре':j.action==='sell'?");s=s.replace("root=$('#inventory');root.replaceChildren();","root=$('#inventory');owned=j.inventory;renderUpgrade();root.replaceChildren();");a=s.index(' const targets=(window.MESH_ITEMS');b=s.index('root.append(card);',a);s=s[:a]+" card.append(button('В апгрейд',async()=>{await show('upgrade');$('#upgradeSource').value=String(x.id);renderTargets()}));"+s[b:];s=s.replace("(o.prize?.item.name||", "(o.action==='open'&&o.count>1?o.count+' кейсов':o.prize?.item.name||")
pos=s.index("$('#redeem').onsubmit")
s=s[:pos]+'''function renderCounts(){
 $('#openCounts').replaceChildren(...(activeCase.type==='allin'?[10,25,50,100]:[1,2,3,5,10]).map(n=>{const b=button(String(n),()=>{openCount=n;renderCounts()},n===openCount?'selected':'text-button');b.setAttribute('aria-pressed',String(n===openCount));return b}));
 $('#openCase').textContent='Открыть ×'+openCount+' · '+fmt(activeCase.price*openCount)+' ◆';
}
function preview(root,p){root.replaceChildren();if(!p)return;const img=el('img');img.src='assets/'+p.img;img.alt=p.name;img.className='upgrade-image';img.onerror=()=>{img.onerror=null;img.src='assets/image-fallback.svg'};root.append(img,el('p',p.name+' · '+fmt(p.value)+' ◆'))}
function source(){return owned.find(x=>String(x.id)===$('#upgradeSource').value)}
function targets(){const x=source(),ids=new Set(catalog.flatMap(c=>c.drops.filter(d=>d[1]>0).map(d=>d[0])));return x?(window.MESH_ITEMS||[]).filter(p=>ids.has(p.id)&&p.value>x.item.value&&Math.floor(x.item.value*900000/p.value)>=100).sort((a,b)=>a.value-b.value):[]}
function renderUpgrade(){const select=$('#upgradeSource'),old=select.value;select.replaceChildren(...owned.map(x=>{const o=el('option',x.item.name+' · '+fmt(x.item.value)+' ◆ (#'+x.id+')');o.value=x.id;return o}));if(owned.some(x=>String(x.id)===old))select.value=old;renderTargets()}
function renderTargets(){const select=$('#upgradeTarget'),old=select.value;select.replaceChildren(...targets().map(p=>{const o=el('option',p.name+' · '+fmt(p.value)+' ◆');o.value=p.id;return o}));if(targets().some(p=>p.id===old))select.value=old;renderChance()}
function renderChance(){const x=source(),p=targets().find(p=>p.id===$('#upgradeTarget').value);preview($('#sourcePreview'),x?.item);preview($('#targetPreview'),p);$('#performUpgrade').disabled=!x||!p;$('#upgradeChance').textContent=x&&p?'Шанс: '+fmt(Math.floor(x.item.value*900000/p.value)/10000)+'%. При неудаче предмет сгорает.':x?'Нет доступной цели':'Нет предметов. Сначала открой кейс.'}
$('#upgradeSource').onchange=renderTargets;$('#upgradeTarget').onchange=renderChance;
all('#upgradePresets button').forEach(b=>b.onclick=()=>{const x=source(),list=targets();if(!x||!list.length)return;const goal=b.dataset.mult?x.item.value*Number(b.dataset.mult):x.item.value*90/Number(b.dataset.chance);const p=list.reduce((best,p)=>Math.abs(p.value-goal)<Math.abs(best.value-goal)?p:best);$('#upgradeTarget').value=p.id;renderChance()});
$('#performUpgrade').onclick=safe(async()=>{const x=source(),p=targets().find(p=>p.id===$('#upgradeTarget').value);if(!x||!p)return;if(confirm($('#upgradeChance').textContent+' Продолжить?'))await gameAction('upgrade',{inventory_id:x.id,target_id:p.id})});

'''+s[pos:];p.write_text(s)
p=Path('animations.js');s=p.read_text();needle=" if(j.action==='open'){";s=s.replace(needle,""" if(j.action==='open'&&j.count>1){
 const grid=node('div','bulk-results');stage.append(grid);title.textContent='Открываем ×'+j.count;
 for(const prize of j.prizes)grid.append(card(prize.item));
 await animate(grid,[{opacity:0,transform:'translateY(30px)'},{opacity:1,transform:'translateY(0)'}],1800);
 title.textContent='Получено '+j.count+' предметов';status.textContent='Все предметы в инвентаре · '+j.prizes.reduce((n,p)=>n+p.item.value,0).toLocaleString('ru-RU')+' ◆';haptic('success');
 }else if(j.action==='open'){""");p.write_text(s)
p=Path('bulk-layout.css');p.write_text(p.read_text()+'\n.upgrade-image{width:100px;height:100px;object-fit:contain}.bulk-results{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;max-height:55vh;overflow:auto}.bulk-results .fx-item{width:auto}#tabs button{min-width:0;font-size:11px}#upgrade select{width:100%;max-width:100%}#openCounts{flex-wrap:wrap}\n')
