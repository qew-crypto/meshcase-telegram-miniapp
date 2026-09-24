from pathlib import Path
import re
root=Path('projects/minecraft-cases')
files=list(root.glob('*.html'))
# Add quantity controls to the standard case modal and make batch opening functional.
for f in files:
    s=f.read_text()
    old=re.search(r'function showCase\(c\)\{.*?\nfunction roll\(c\)',s,re.S)
    if old:
        new='''function showCase(c){if(c.type==='allin'){location.href='case-'+c.id+'.html';return}currentCase=c;$('#modalTitle').textContent='Кейс «'+c.name+'»';$('#modalSub').textContent='Открытие за ✦ '+format(c.price)+' · виртуальные предметы';let drops=c.drops.map(([id,w])=>{let p=P[id];return `<span class="drop-chip"><img src="${itemImage(p)}" alt="">${p.name}${p.duration?' · '+p.duration:''} <span>${dropPercent(c,w)}</span></span>`}).join('');$('#modalContent').innerHTML=`<div style="text-align:center"><img src="${A+('case-'+c.id+'.svg')}" alt="" style="height:155px"></div><p style="font-size:11px;color:#b1adbd;margin:4px 0">ВОЗМОЖНОЕ СОДЕРЖИМОЕ · ШАНСЫ</p><div class="drop-list">${drops}</div><p style="font-size:11px;color:#9895a9">Шансы указаны с точностью до 0,01%. Все предметы и монеты виртуальные.</p><div class="batch-row"><b>Количество:</b><button class="btn btn-ghost" data-batch="1">1</button><button class="btn btn-ghost" data-batch="2">2</button><button class="btn btn-ghost" data-batch="3">3</button><button class="btn btn-ghost" data-batch="5">5</button><button class="btn btn-ghost" data-batch="10">10</button></div><div class="modal-buttons"><button class="btn btn-primary" id="confirmOpen">Открыть 1 · ✦ ${format(c.price)}</button><button class="btn btn-ghost" id="cancelOpen">Не сейчас</button></div>`;let n=1;const refresh=()=>{$('#confirmOpen').textContent='Открыть '+n+' · ✦ '+format(c.price*n);$('#confirmOpen').disabled=state.balance<c.price*n;document.querySelectorAll('[data-batch]').forEach(x=>x.classList.toggle('active',Number(x.dataset.batch)===n))};document.querySelectorAll('[data-batch]').forEach(x=>x.addEventListener('click',()=>{n=Number(x.dataset.batch);refresh()}));refresh();openModal()}
function openBatch(c,count){if(busy||state.balance<c.price*count){notify('Недостаточно демо-монет');return}busy=true;state.balance-=c.price*count;let won=Array.from({length:count},()=>chooseDrop(c));won.forEach(p=>state.inventory.push({id:p.id,uid:Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,10)}));save();render();$('#modalContent').innerHTML='<h3 style="margin:0 0 12px">Результат · '+count+' открытий</h3><div class="batch-results">'+won.map(p=>itemMarkup(p)+'<div><b>'+p.name+'</b><small>✦ '+format(p.value)+'</small></div>').join('')+'</div><div class="modal-buttons"><button class="btn btn-primary" id="againBatch">Открыть ещё</button><button class="btn btn-ghost" id="doneBtn">В инвентарь →</button></div>';busy=false}
function roll(c){if(c.type==='allin'){location.href='case-'+c.id+'.html';return}if(busy||state.balance<c.price){notify('Недостаточно демо-монет');return}openBatch(c,1)}
'''
        s=s[:old.start()]+new+s[old.end():]
    # Existing event listener should accept data batch selection via confirm button.
    s=s.replace("if(b.id==='confirmOpen'&&currentCase)roll(currentCase);", "if(b.id==='confirmOpen'&&currentCase){let n=Number(document.querySelector('[data-batch].active')?.dataset.batch||1);openBatch(currentCase,n);}")
    # Add allin/ordinary controls on detail pages after their generated detail block.
    marker='/* mesh-withdraw-v3 */'
    inject='''/* Batch case controls: ALL IN = 10/50/100, ordinary = 1/2/3/5/10. */
(function(){const id=document.body.dataset.case;if(!id)return;const c=cases.find(x=>x.id===id);if(!c)return;const host=document.querySelector('.case-detail');if(!host)return;const counts=c.type==='allin'?[10,50,100]:[1,2,3,5,10];const box=document.createElement('div');box.className='case-open-panel';box.innerHTML='<h3>Открыть кейс</h3><p>'+ (c.type==='allin'?'ALL IN открывается пачками 10 / 50 / 100.':'Выберите количество: 1 / 2 / 3 / 5 / 10.')+'</p><div class="batch-row">'+counts.map(n=>'<button class="btn btn-primary" data-page-batch="'+n+'">'+n+' · ✦ '+format(c.price*n)+'</button>').join('')+'</div><p class="batch-note">Шансы указаны в процентах, минимум 0.01%. Дроп добавляется в инвентарь.</p>';host.parentNode.insertBefore(box,host);box.addEventListener('click',e=>{const b=e.target.closest('[data-page-batch]');if(!b)return;currentCase=c;openBatch(c,Number(b.dataset.pageBatch));});})();
'''
    if marker in s and 'Batch case controls:' not in s:
        s=s.replace(marker,inject+'\n'+marker,1)
    f.write_text(s)
# CSS append to all pages
css='''\n/* Batch opening UI */\n.batch-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:14px 0}.batch-row .btn.active{border-color:#d3a6ff;background:#62428a}.batch-results{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:9px;max-height:52vh;overflow:auto;padding:6px}.batch-results>div{display:flex;flex-direction:column;align-items:center;text-align:center;padding:9px;background:#252238;border:1px solid #403858;border-radius:10px;font-size:10px}.batch-results .item-icon{width:54px;height:54px}.batch-results small{color:#ffc977;margin-top:4px}.case-open-panel{margin:16px 0;padding:18px;border:1px solid #514579;border-radius:16px;background:linear-gradient(120deg,#241c35,#171624)}.case-open-panel h3{margin:0 0 6px}.case-open-panel p{color:#bdb4c9;font-size:12px}.batch-note{margin:10px 0 0!important;font-size:11px!important}\n'''
for f in files:
    s=f.read_text()
    if '/* Batch opening UI */' not in s:
        s=s.replace('</head>', '<style>'+css+'</style></head>',1)
        f.write_text(s)
print('patched',len(files))
