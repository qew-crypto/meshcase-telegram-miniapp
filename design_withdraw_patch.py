from pathlib import Path
import json,re
root=Path('projects/minecraft-cases')
style='''
/* Visual refresh: independent design inspired by the dark case-store layout */
:root{--bg:#0d0e13;--panel:#191b24;--line:#30313c;--text:#f5f4f8;--muted:#9a9ba9;--violet:#ac83ff;--aqua:#8de3bd;--gold:#ffd379}
body{background:radial-gradient(ellipse 65% 520px at 50% 0%,#282133 0%,transparent 85%),#0d0e13}
header{background:#14151be8;backdrop-filter:blur(18px);border-bottom:1px solid #39313c}
.topline{background:#201d27;border-color:#38313d;color:#d1c4dc}
.logo-icon{color:#ffc686}.nav a{border-radius:11px}.nav a.active,.nav a:hover{background:#30243b;color:#fff}
.hero{background:radial-gradient(circle at 72% 45%,#a75e5c24,transparent 39%),radial-gradient(circle at 25% 75%,#9156aa21,transparent 45%)}
.hero h1 span,.section-title{color:#f6f0fc}
.btn-primary{background:linear-gradient(110deg,#ad78ff,#dc82b3);border-color:transparent;color:#170f23;box-shadow:0 7px 25px #ac6fe62c;font-weight:800}
.btn-primary:hover{filter:brightness(1.13)}
.case-card,.inv-card,.pick,.case-play,.topup-box{background:linear-gradient(150deg,#24212d,#191a23 67%);border:1px solid #403845;border-radius:18px;box-shadow:0 12px 35px #0003}
.case-card:hover,.pick:hover{border-color:#a77ac4;box-shadow:0 12px 42px #a77ac422;transform:translateY(-3px)}
.case-pic{background:radial-gradient(circle,#ae78bc31,transparent 72%)}
.case-pic img,.play-art{filter:drop-shadow(0 12px 20px #0008)}
.section-head{border-bottom:1px solid #302b37;padding-bottom:16px}
.inventory-actions{gap:9px}
.withdraw-panel{background:linear-gradient(120deg,#221d2d,#171923);border:1px solid #59436b;border-radius:20px;padding:22px;margin:18px 0 24px}
.withdraw-panel h3{margin:0 0 6px;font-size:20px}.withdraw-panel p{color:#b6aec1;margin:0 0 16px}
.withdraw-controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.withdraw-controls select,.withdraw-controls input{background:#11131b;color:#fff;border:1px solid #51445d;border-radius:10px;padding:11px 12px;font:inherit;min-height:44px}
.withdraw-controls select{min-width:185px;max-width:100%}.withdraw-controls input{flex:1;min-width:175px}
.withdraw-method{display:flex;align-items:center;gap:8px;background:#14151d;padding:10px 13px;border-radius:12px;border:1px solid #3f3546}
.withdraw-method label{cursor:pointer}.withdraw-hint{font-size:12px!important;margin-top:14px!important}
.withdraw-history{display:grid;gap:10px;margin:12px 0 24px}.withdraw-entry{display:flex;align-items:center;flex-wrap:wrap;gap:12px;padding:12px;background:#1a1a23;border:1px solid #393340;border-radius:12px}.withdraw-entry img{width:48px;height:48px;object-fit:contain}.withdraw-entry span{flex:1;min-width:160px}.withdraw-entry small{display:block;color:#a4a0b1}.withdraw-entry button{background:#2b2530;color:#eee;border:1px solid #51405a;border-radius:9px;padding:8px 12px}
@media(max-width:650px){.withdraw-controls>*{width:100%}.withdraw-controls input{min-width:0}.withdraw-panel{padding:16px}}
'''
widget='''<div class="withdraw-panel" id="withdrawPanel"><h3>Вывод предмета · демо</h3><p>Выбери предмет из инвентаря и способ заявки. Это только локальная симуляция: никакой передачи предметов и денег.</p><form id="withdrawForm"><div class="withdraw-controls"><select id="withdrawItem" aria-label="Предмет для вывода" required><option value="">Выбери предмет</option></select><div class="withdraw-method"><input type="radio" name="withdrawMethod" value="nick" id="withdrawNick" checked><label for="withdrawNick">Ник</label></div><div class="withdraw-method"><input type="radio" name="withdrawMethod" value="qr" id="withdrawQr"><label for="withdrawQr">QR (СБП · макет)</label></div><input id="withdrawRecipient" maxlength="40" placeholder="Ник в игре" aria-label="Ник в игре" required autocomplete="off"><button type="submit" class="btn btn-primary">Создать демо-заявку</button></div></form><p class="withdraw-hint" id="withdrawHint">Ник нужен только для демонстрации. Не вводи настоящие платёжные реквизиты.</p></div><h3>Мои демо-заявки</h3><div class="withdraw-history" id="withdrawHistory"></div>'''
js='''
/* Local-only withdrawal simulation; no endpoints or bank details */
if(!Array.isArray(state.withdrawals))state.withdrawals=[];
state.withdrawals=state.withdrawals.filter(w=>w&&P[w.id]&&typeof w.uid==='string');
const whItem=$('#withdrawItem'),whHistory=$('#withdrawHistory'),whRecipient=$('#withdrawRecipient');
function escapeText(t){return String(t).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
function renderWithdraw(){
 if(!whItem)return;
 let selected=whItem.value;
 whItem.innerHTML='<option value="">Выбери предмет</option>'+state.inventory.map(x=>`<option value="${escapeText(x.uid)}">${escapeText(P[x.id].name)} · ✦ ${format(P[x.id].value)}</option>`).join('');
 if(state.inventory.some(x=>x.uid===selected))whItem.value=selected;
 whHistory.innerHTML=state.withdrawals.length?state.withdrawals.slice().reverse().map(w=>`<div class="withdraw-entry"><img src="${itemImage(P[w.id])}" alt=""><span><strong>${escapeText(P[w.id].name)}</strong><small>${w.method==='nick'?'Ник: '+escapeText(w.recipient):'QR (СБП) · макет'} · Заявка не отправлена</small></span><button type="button" data-cancel-withdraw="${escapeText(w.uid)}">Отменить · вернуть предмет</button></div>`).join(''):'<p>Демо-заявок пока нет.</p>';
}
const renderBeforeWithdraw=render;
render=function(){renderBeforeWithdraw();renderWithdraw()};
document.querySelectorAll('input[name="withdrawMethod"]').forEach(r=>r.addEventListener('change',()=>{
 let qr=$('#withdrawQr').checked;whRecipient.hidden=qr;whRecipient.required=!qr;
 $('#withdrawHint').textContent=qr?'СБП/QR только как макет: мы не запрашиваем QR-код и платёжные реквизиты; реальной выплаты нет.':'Ник нужен только для демонстрации. Не вводи настоящие платёжные реквизиты.';
}));
$('#withdrawForm').addEventListener('submit',e=>{e.preventDefault();if(busy)return;
 let idx=state.inventory.findIndex(x=>x.uid===whItem.value);if(idx<0){notify('Сначала выбери предмет');return}
 let qr=$('#withdrawQr').checked,nick=whRecipient.value.trim();if(!qr&&!/^[\\p{L}\\p{N}_ .-]{2,40}$/u.test(nick)){notify('Введи ник от 2 до 40 символов');return}
 let item=state.inventory[idx];if(!confirm(`Создать только демо-заявку на «${P[item.id].name}»? Реальной выдачи и выплаты не будет.`))return;
 state.inventory.splice(idx,1);state.withdrawals.push({id:item.id,uid:item.uid,method:qr?'qr':'nick',recipient:qr?'':nick});
 if(sourceUid===item.uid){sourceUid=null;targetId=null}save();render();notify('Демо-заявка создана. Её можно отменить.');
});
whHistory.addEventListener('click',e=>{let b=e.target.closest('[data-cancel-withdraw]');if(!b||busy)return;let idx=state.withdrawals.findIndex(w=>w.uid===b.dataset.cancelWithdraw);if(idx<0)return;
 let w=state.withdrawals.splice(idx,1)[0];state.inventory.push({id:w.id,uid:w.uid});save();render();notify('Предмет возвращён в инвентарь');
});
renderWithdraw();
'''
for path in root.glob('*.html'):
 if path.name=='case-funtime.html':continue
 s=path.read_text()
 # remove funtime products, case and references from the actual inline JS dataset
 for variable,keep in [('products',lambda x:not (x['id'].startswith('ft-') or 'funtime' in x['name'].lower())),('cases',lambda x:x['id']!='funtime')]:
  prefix='const '+variable+'=';start=s.find(prefix)
  if start!=-1:
   data,end=json.JSONDecoder().raw_decode(s[start+len(prefix):]);clean=[x for x in data if keep(x)]
   s=s[:start+len(prefix)]+json.dumps(clean,ensure_ascii=False,separators=(',',':'))+s[start+len(prefix)+end:]
 s=s.replace('case-funtime.html','index.html')
 s=re.sub(r'\bFunTime\b(?:, )?', '', s)
 s=s.replace('официальные сайты  и HolyWorld','официальный сайт HolyWorld').replace('Официальные сайты  и HolyWorld','Официальный сайт HolyWorld')
 s=s.replace('id="sellAllBtn" class="btn btn-primary" disabled>Продать всё</button></div></div><div class="inventory-grid"', 'id="sellAllBtn" class="btn btn-primary" disabled>Продать всё</button></div></div>'+widget+'<div class="inventory-grid"') if path.name=='profile.html' else s
 # shared changes to JS only on profile where withdrawal UI exists
 if path.name=='profile.html':
  pos=s.rfind('})();');assert pos!=-1;s=s[:pos]+js+s[pos:]
 s=s.replace('</style>',style+'</style>')
 # no duplicate navigation entries
 s=s.replace('<a href="catalog.html">Весь дроп</a><a href="catalog.html">Весь дроп</a>','<a href="catalog.html">Весь дроп</a>')
 path.write_text(s)
(root/'case-funtime.html').unlink(missing_ok=True)
for fn in ['case-funtime.svg']:
 (root/'assets'/fn).unlink(missing_ok=True)
print('Patched HTML pages:',len(list(root.glob('*.html'))))
