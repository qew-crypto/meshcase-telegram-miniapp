from pathlib import Path
import json,re
r=Path('projects/minecraft-cases');a=r/'assets'
new=[dict(id='royal',name='Королевский запас',brand='ПРЕМИУМ',type='server',price=2499,desc='Дорогой демо-кейс · привилегии и токены',accent='#e5c76c',drops=[['catalog-129',35],['catalog-128',25],['catalog-111',18],['catalog-146',12],['catalog-220',6],['catalog-256',3],['catalog-291',1]]),dict(id='cosmic',name='Космический джекпот',brand='УЛЬТРА',type='server',price=5999,desc='Дорогой дроп · виртуальные монеты',accent='#dd86fa',drops=[['catalog-166',32],['catalog-253',25],['catalog-202',19],['catalog-220',12],['catalog-255',7],['catalog-291',4],['catalog-292',1]])]
for x in new:
 (a/f'case-{x["id"]}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 260"><rect width="320" height="260" rx="36" fill="#28223d"/><path d="M70 100 160 57 250 100 250 207 160 245 70 207Z" fill="#42304a" stroke="{x["accent"]}" stroke-width="8"/><path d="M70 100 160 145 250 100M160 145V245" stroke="{x["accent"]}" stroke-width="7" fill="none"/><text x="160" y="45" text-anchor="middle" fill="white" font-size="19" font-family="sans-serif">{x["name"]}</text></svg>')
(a/'image-fallback.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="16" fill="#302743"/><path d="M15 52 50 17 85 52 50 84Z" fill="#9a72dd" stroke="#e1c7ff" stroke-width="3"/><text x="50" y="63" text-anchor="middle" font-size="36" fill="white">✦</text></svg>')
for f in r.glob('*.html'):
 s=f.read_text();m=re.search(r'<script>(.*?)</script>',s,re.S)
 if m and 'const cases=' in m.group(1):
  js=m.group(1);cm=re.search(r'const cases=(\[.*?\]);',js)
  if not cm:raise RuntimeError(f)
  cases=json.loads(cm[1]); cases.extend(new)
  js=js[:cm.start(1)]+json.dumps(cases,ensure_ascii=False,separators=(',',':'))+js[cm.end(1):]
  old='Math.min(85,Math.max(5,Math.floor(src.value/dst.value*80)))'
  if js.count(old)!=2:raise RuntimeError('chance mismatch '+str(f))
  js=js.replace(old,'Math.min(85,src.value/dst.value*80)')
  js=js.replace("chance+'%'","chance.toFixed(2).replace(/\\.00$/,'')+'%'")
  js=js.replace('${chance}%','${chance.toFixed(2).replace(/\\.00$/,\'\')}%')
  js=js.replace("const A='assets/';","const A='assets/';document.addEventListener('error',e=>{let img=e.target;if(img instanceof HTMLImageElement&&!img.dataset.fallback){img.dataset.fallback='1';img.src=A+'image-fallback.svg'}},true);")
  js=js.replace("$('#topupBonus').addEventListener('click',bonus);","$('#topupBonus').addEventListener('click',bonus);$('#demoCreditForm').addEventListener('submit',e=>{e.preventDefault();if(busy)return;let amount=Number($('#demoCreditAmount').value);if(!Number.isSafeInteger(amount)||amount<1||amount>1000000){notify('Введите целое число от 1 до 1 000 000');return}state.balance+=amount;save();render();notify('Добавлено '+format(amount)+' демо-монет')});")
  s=s[:m.start(1)]+js+s[m.end(1):]
 if 'id="topupBonus"' in s:
  s=s.replace('<p>Баланс и инвентарь сохраняются локально в этом браузере.</p>','<h3>Пополнить демо-баланс</h3><p>Впиши целое число от 1 до 1 000 000. Платежей здесь нет.</p><form id="demoCreditForm" class="credit-form"><label for="demoCreditAmount">Виртуальные монеты ✦</label><input type="number" id="demoCreditAmount" min="1" max="1000000" step="1" value="5000" required inputmode="numeric"><button type="submit" class="btn btn-primary">Добавить на демо-баланс</button></form><p>Баланс и инвентарь сохраняются локально в этом браузере.</p>')
  s=s.replace('</style>','.credit-form{display:grid;gap:10px;margin:15px 0 25px}.credit-form label{font-weight:700}.credit-form input{width:100%;box-sizing:border-box;border:1px solid #706583;border-radius:12px;background:#272338;color:#fff;padding:14px;font:inherit;font-size:18px}.credit-form button{justify-self:start}@media(max-width:650px){.credit-form button{width:100%}}\n</style>')
 f.write_text(s)
for x in new:
 s=(r/'case-legend.html').read_text().replace('data-case="legend"',f'data-case="{x["id"]}"').replace('data-heading="Легенда"',f'data-heading="{x["name"]}"').replace('Кейс «Легенда»',f'Кейс «{x["name"]}»')
 (r/f'case-{x["id"]}.html').write_text(s)
print('pages',len(list(r.glob('*.html'))))
