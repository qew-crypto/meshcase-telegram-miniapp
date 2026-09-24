from pathlib import Path
r=Path('projects/minecraft-cases')
files=list(r.glob('*.html'))+[r/'current.js']
for f in files:
 s=f.read_text(encoding='utf-8')
 if f.suffix=='.html':
  old='<span class="pill" id="inventoryCount">0 предметов</span></div><div class="inventory-grid"'
  new='<div class="inventory-actions"><span class="pill" id="inventoryCount">0 предметов</span><button type="button" id="sellAllBtn" class="btn btn-primary" disabled>Продать всё</button></div></div><div class="inventory-grid"'
  if s.count(old)!=1: raise RuntimeError(f'Inventory markup missing: {f}')
  s=s.replace(old,new)
  s=s.replace('</style>','.inventory-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.inventory-actions button:disabled{opacity:.5;cursor:not-allowed}@media(max-width:650px){.inventory-actions{width:100%;justify-content:space-between}.inventory-actions button{min-height:44px}}\n</style>')
 old="$('#inventoryCount').textContent=`${state.inventory.length} предметов`;"
 new=old+"$('#sellAllBtn').disabled=busy||!state.inventory.length;"
 if s.count(old)!=1:raise RuntimeError(f'Count missing: {f}')
 s=s.replace(old,new)
 needle="$('#inventoryGrid').addEventListener('click',e=>{"
 handler="$('#sellAllBtn').addEventListener('click',()=>{if(busy||!state.inventory.length)return;const count=state.inventory.length;const total=state.inventory.reduce((sum,x)=>sum+P[x.id].value,0);if(!confirm(`Продать все предметы (${count} шт.) за ✦ ${format(total)} демо-монет?`))return;state.balance+=total;state.inventory=[];sourceUid=null;targetId=null;save();render();notify(`Продано ${count} предметов за ✦ ${format(total)}`)});"
 if s.count(needle)!=1:raise RuntimeError(f'Handler anchor missing: {f}')
 s=s.replace(needle,handler+needle)
 f.write_text(s,encoding='utf-8')
print('Updated',len(files),'files')
