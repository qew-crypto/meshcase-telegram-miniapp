/* Presentation only: every outcome is supplied by the server. */
(()=>{'use strict';
const node=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
const dialog=node('dialog','game-fx'),title=node('h2'),stage=node('div','fx-stage'),status=node('p','fx-status'),controls=node('div','fx-controls'),skip=node('button','text-button','Показать результат'),close=node('button','primary','Готово');
close.type=skip.type='button';controls.append(skip,close);dialog.append(title,stage,status,controls);document.body.append(dialog);status.setAttribute('role','status');status.setAttribute('aria-live','polite');title.id='fx-title';dialog.setAttribute('aria-labelledby',title.id);
let running=false,current=null;const sell=node('button','primary','Продать всё');sell.type='button';sell.hidden=true;controls.prepend(sell);
const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const haptic=kind=>{try{window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(kind)}catch{}};
close.onclick=()=>dialog.close();skip.onclick=()=>current?.finish();dialog.addEventListener('cancel',e=>{if(running){e.preventDefault();current?.finish()}});
function card(item){const c=node('div','fx-item'),img=node('img');img.src='assets/'+item.img;img.alt='';img.onerror=()=>{img.onerror=null;img.src='assets/image-fallback.svg'};c.append(img,node('strong','',item.name),node('b','',Number(item.value).toLocaleString('ru-RU')+' ◆'));return c}
async function animate(element,frames,duration){if(reduced()||!element.animate)return;current=element.animate(frames,{duration,easing:'cubic-bezier(.12,.7,.12,1)',fill:'forwards'});const timer=setTimeout(()=>current?.finish(),duration+300);try{await current.finished}catch{}finally{clearTimeout(timer);current=null}}
document.addEventListener('visibilitychange',()=>{if(document.hidden)current?.finish()});
window.MeshFX={waiting(action){if(action==='sell'||action==='sell_all')return;sell.hidden=true;running=true;stage.replaceChildren(node('div','fx-loader'));title.textContent=action==='open'?'Открытие кейса':'Апгрейд';status.textContent='Ждём подтверждение сервера…';close.hidden=true;skip.hidden=true;if(!dialog.open)dialog.showModal()},error(text){running=false;stage.replaceChildren();status.textContent=text;skip.hidden=true;close.hidden=false},async result(j,catalog){if(j.action==='sell'||j.action==='sell_all')return;try{
 stage.replaceChildren();skip.hidden=reduced();status.textContent=j.action==='open'?'Приз определён сервером. Прокручиваем…':'Результат определён сервером. Проверяем апгрейд…';
 if(j.action==='open'&&j.count>1){
 const grid=node('div','bulk-results');stage.append(grid);title.textContent='Открываем ×'+j.count;
 for(const prize of j.prizes)grid.append(card(prize.item));
 await animate(grid,[{opacity:0,transform:'translateY(30px)'},{opacity:1,transform:'translateY(0)'}],1800);
 title.textContent='Получено '+j.count+' предметов';status.textContent='Все предметы в инвентаре · '+j.prizes.reduce((n,p)=>n+p.item.value,0).toLocaleString('ru-RU')+' ◆';haptic('success');
 }else if(j.action==='open'){
 const c=catalog.find(c=>c.id===j.case_id),items=new Map((window.MESH_ITEMS||[]).map(p=>[p.id,p]));
 const pool=(c?.drops||[]).filter(d=>items.has(d[0]));
 function sample(){let roll=Math.random()*pool.reduce((s,d)=>s+d[1],0);for(const [id,w] of pool){roll-=w;if(roll<0)return items.get(id)}return j.prize.item}
 const viewport=node('div','fx-viewport'),track=node('div','fx-track'),marker=node('div','fx-marker');marker.setAttribute('aria-hidden','true');track.setAttribute('aria-hidden','true');
 const winner=26;for(let i=0;i<32;i++)track.append(card(i===winner?j.prize.item:sample()));viewport.append(track,marker);stage.append(viewport);
 // Percent translation follows the viewport width, including rotation/resizing.
 track.style.width='100%';const end=`translateX(calc(50% - ${winner*144+68}px))`;
 await animate(track,[{transform:'translateX(calc(50% - 68px))'},{transform:end}],2600);track.style.transform=end;
 stage.replaceChildren(card(j.prize.item));title.textContent='Твой приз';status.textContent=j.prize.item.name+' · '+j.prize.item.value.toLocaleString('ru-RU')+' ◆ — в инвентаре';haptic('success');
 }else{
 const pair=node('div','fx-pair');pair.append(card(j.source),node('span','fx-arrow','→'),card(j.target));
 const ring=node('div','fx-ring'),pointer=node('div','fx-pointer'),label=node('span','fx-chance',j.chance.toLocaleString('ru-RU')+'%');
 ring.style.background=`conic-gradient(#ff9d43 0deg ${j.chance*3.6}deg, #29303c ${j.chance*3.6}deg 360deg)`;ring.append(pointer,label);stage.append(pair,ring);
 const angle=j.success?j.chance*3.6/2:j.chance*3.6+(360-j.chance*3.6)/2;
 await animate(pointer,[{transform:'rotate(0deg)'},{transform:`rotate(${1080+angle}deg)`}],2100);pointer.style.transform=`rotate(${angle}deg)`;
 title.textContent=j.success?'Апгрейд успешен':'Апгрейд не удался';status.textContent=j.success?j.prize.item.name+' — в инвентаре':'Исходный предмет израсходован. Новый предмет не получен.';haptic(j.success?'success':'warning');
 }
 if(j.action==='open'){const prizes=j.prizes||[j.prize];sell.hidden=false;sell.disabled=false;sell.textContent='Продать всё · '+prizes.reduce((n,p)=>n+p.item.value,0).toLocaleString('ru-RU')+' ◆';sell.onclick=async()=>{sell.disabled=true;try{const sold=await window.MeshSellBatch(prizes);if(sold){sell.hidden=true;status.textContent='Все предметы этого открытия проданы · +'+sold.total.toLocaleString('ru-RU')+' ◆'}}catch(e){status.textContent=e.message}finally{sell.disabled=false}};}stage.classList.remove('fx-reveal');void stage.offsetWidth;stage.classList.add('fx-reveal');
 }finally{running=false;skip.hidden=true;close.hidden=false;close.focus()}}};
})();
