from pathlib import Path
root=Path('projects/minecraft-cases')
css='''
/* Inventory and withdrawal refresh */
.inv-card{display:flex;flex-direction:column;min-height:260px;transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease;overflow:hidden}
.inv-card:hover{transform:translateY(-5px);border-color:#b58cfa;box-shadow:0 16px 35px #0007}
.inv-card .item-icon{width:88px;height:88px;transition:transform .3s ease}.inv-card:hover .item-icon{transform:scale(1.12) rotate(-3deg)}
.inv-card .value{margin-bottom:8px}.inv-card .item-actions{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:6px;padding-top:9px}
.inv-card .item-actions button{margin:0;padding:9px 3px;min-height:38px;background:#30273e;border:1px solid #66547c;border-radius:9px;color:#fff;font-size:11px;text-decoration:none}
.inv-card .item-actions button:hover{background:#694296;text-decoration:none}.inv-card .item-actions button[data-withdraw]{background:#1b3936;border-color:#4c8078}
.inv-card .item-actions button[data-withdraw]:hover{background:#306d63}
.withdraw-panel{display:none}.withdraw-history{margin:12px 0 25px}.withdraw-entry img{border-radius:8px;background:#282536}
.withdraw-dialog{border:1px solid #705580;border-radius:20px;padding:24px;background:#1c1b29;color:#fff;width:min(480px,calc(100% - 28px));box-shadow:0 30px 100px #000b}
.withdraw-dialog::backdrop{background:#060510cf;backdrop-filter:blur(6px)}.withdraw-dialog h3{margin:0 0 10px}.withdraw-dialog p{color:#bdb3ca}.withdraw-dialog img{width:60px;height:60px;object-fit:contain;vertical-align:middle;margin-right:12px}
.withdraw-dialog label{display:block;margin:12px 0 6px}.withdraw-dialog input[type=text],.withdraw-dialog input[type=file]{display:block;width:100%;padding:11px;background:#11131b;color:#fff;border:1px solid #594863;border-radius:9px}
.withdraw-dialog .withdraw-options{display:flex;gap:9px}.withdraw-dialog .withdraw-options button{flex:1;padding:12px;border:1px solid #624d76;background:#30283c;color:#fff;border-radius:10px}.withdraw-dialog .withdraw-options button.selected{border-color:#ad84ff;background:#573d75}
.withdraw-dialog .dialog-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.withdraw-dialog .dialog-actions button{flex:1;min-width:125px}.withdraw-dialog [hidden]{display:none!important}
@media(prefers-reduced-motion:reduce){.inv-card,.inv-card .item-icon{transition:none!important}}
'''
section='''<h3>Мои демо-заявки</h3><div class="withdraw-history" id="withdrawHistory"></div><div class="inventory-grid" id="inventoryGrid"></div></section>'''
dialog='''<dialog id="withdrawDialog" class="withdraw-dialog" aria-labelledby="withdrawTitle"><form id="withdrawForm"><h3 id="withdrawTitle">Вывести предмет · демо</h3><div id="withdrawPreview"></div><p>Как указать получателя?</p><div class="withdraw-options"><button type="button" id="methodNick" class="selected" aria-pressed="true">По нику</button><button type="button" id="methodQr" aria-pressed="false">По фото QR</button></div><div id="nickFields"><label for="withdrawNickInput">Ник получателя</label><input type="text" id="withdrawNickInput" maxlength="40" placeholder="Ник в игре" autocomplete="off"></div><div id="qrFields" hidden><label for="withdrawQrFile">Фото QR (PNG, JPG или WebP, до 5 МБ)</label><input type="file" id="withdrawQrFile" accept="image/png,image/jpeg,image/webp"><p id="qrFileName">Фото остаётся только в этом окне: не отправляется и не сохраняется.</p></div><p>Заявка сохраняется только в этом браузере. Реальной выдачи предметов нет.</p><div class="dialog-actions"><button type="button" class="btn btn-ghost" id="withdrawClose">Отмена</button><button type="submit" class="btn btn-primary">Создать демо-заявку</button></div></form></dialog>'''
js='''
// Local-only demo withdrawal, no file uploads or real fulfillment.
if(!Array.isArray(state.withdrawals))state.withdrawals=[];
state.withdrawals=state.withdrawals.filter(w=>w&&P[w.id]&&typeof w.uid==='string');
let pendingWithdrawUid=null,withdrawMethod='nick';
const withdrawDialog=$('#withdrawDialog');
function safeText(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function renderWithdrawals(){let el=$('#withdrawHistory');if(!el)return;el.innerHTML=state.withdrawals.length?state.withdrawals.slice().reverse().map(w=>`<div class="withdraw-entry"><img src="${itemImage(P[w.id])}" alt=""><span><strong>${safeText(P[w.id].name)}</strong><small>${w.method==='qr'?'Фото QR (не сохранено)':'Ник: '+safeText(w.recipient||'')} · заявка только в браузере</small></span><button type="button" data-cancel-withdraw="${safeText(w.uid)}">Отменить и вернуть</button></div>`).join(''):'<p>Демо-заявок пока нет.</p>'}
const originalRender=render;render=function(){originalRender();renderWithdrawals()};
function selectWithdrawMethod(method){withdrawMethod=method;$('#nickFields').hidden=method!=='nick';$('#qrFields').hidden=method!=='qr';$('#methodNick').classList.toggle('selected',method==='nick');$('#methodQr').classList.toggle('selected',method==='qr');$('#methodNick').setAttribute('aria-pressed',method==='nick');$('#methodQr').setAttribute('aria-pressed',method==='qr')}
$('#methodNick').addEventListener('click',()=>selectWithdrawMethod('nick'));
$('#methodQr').addEventListener('click',()=>selectWithdrawMethod('qr'));
$('#withdrawQrFile').addEventListener('change',e=>{$('#qrFileName').textContent=e.target.files[0]?`Выбрано: ${e.target.files[0].name} (фото не сохраняется)`:'Фото остаётся только в этом окне: не отправляется и не сохраняется.'});
function closeWithdraw(){withdrawDialog.close();pendingWithdrawUid=null;$('#withdrawForm').reset();$('#qrFileName').textContent='Фото остаётся только в этом окне: не отправляется и не сохраняется.'}
$('#withdrawClose').addEventListener('click',closeWithdraw);
withdrawDialog.addEventListener('close',()=>{pendingWithdrawUid=null;$('#withdrawForm').reset()});
$('#inventoryGrid').addEventListener('click',e=>{let b=e.target.closest('[data-withdraw]');if(!b||busy)return;let item=state.inventory.find(x=>x.uid===b.dataset.withdraw);if(!item)return;pendingWithdrawUid=item.uid;selectWithdrawMethod('nick');$('#withdrawPreview').innerHTML=`<img src="${itemImage(P[item.id])}" alt="">${safeText(P[item.id].name)}`;withdrawDialog.showModal()});
$('#withdrawForm').addEventListener('submit',e=>{e.preventDefault();if(busy||!pendingWithdrawUid)return;let idx=state.inventory.findIndex(x=>x.uid===pendingWithdrawUid);if(idx<0){closeWithdraw();return}let nick=$('#withdrawNickInput').value.trim(),file=$('#withdrawQrFile').files[0];if(withdrawMethod==='nick'&&!/^[\\p{L}\\p{N}_ .-]{2,40}$/u.test(nick)){notify('Введите ник от 2 до 40 символов');return}if(withdrawMethod==='qr'&&(!file||!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>5*1024*1024||file.size===0)){notify('Выберите фото PNG, JPG или WebP до 5 МБ');return}let item=state.inventory[idx];if(!confirm(`Создать демо-заявку для «${P[item.id].name}»? Предмет исчезнет из инвентаря, но его можно вернуть. Реальной выдачи нет.`))return;state.inventory.splice(idx,1);state.withdrawals.push({id:item.id,uid:item.uid,method:withdrawMethod,recipient:withdrawMethod==='nick'?nick:''});if(sourceUid===item.uid){sourceUid=null;targetId=null}closeWithdraw();save();render();notify('Демо-заявка создана. Фото QR не сохранено.')});
$('#withdrawHistory').addEventListener('click',e=>{let b=e.target.closest('[data-cancel-withdraw]');if(!b||busy)return;let idx=state.withdrawals.findIndex(w=>w.uid===b.dataset.cancelWithdraw);if(idx<0)return;let w=state.withdrawals.splice(idx,1)[0];state.inventory.push({id:w.id,uid:w.uid});save();render();notify('Предмет возвращён в инвентарь')});
renderWithdrawals();
'''
for path in root.glob('*.html'):
 s=path.read_text()
 if 'mesh-withdraw-v3' in s: continue
 start=s.find('<div class="withdraw-panel" id="withdrawPanel">');
 if start<0: start=s.find('<div class="inventory-grid" id="inventoryGrid"></div></section>')
 end=s.find('<div class="inventory-grid" id="inventoryGrid"></div></section>',start)
 if start<0 or end<0: print('skip',path);continue
 end+=len('<div class="inventory-grid" id="inventoryGrid"></div></section>')
 s=s[:start]+section+dialog+s[end:]
 s=s.replace('</style>',css+'</style>',1)
 old='<button data-sell="${item.uid}" aria-label="Продать ${p.name}">Продать за ✦ ${format(p.value)}</button>'
 new='<div class="item-actions"><button type="button" data-sell="${item.uid}" aria-label="Продать ${p.name}">Продать</button><button type="button" data-withdraw="${item.uid}" aria-label="Вывести ${p.name}">Вывести</button></div>'
 assert old in s,path;s=s.replace(old,new)
 pos=s.find('\n})();',s.find('function render(){'))
 assert pos!=-1,path;s=s[:pos]+'\n/* mesh-withdraw-v3 */'+js+s[pos:]
 path.write_text(s)
print('patched pages')
