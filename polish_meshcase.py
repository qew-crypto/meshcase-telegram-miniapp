from pathlib import Path
root=Path('projects/minecraft-cases')
css='''
/* MeshCase polish: real chest presentation, motion and visible mini loot icons */
:root{--mc-glow:#9b72ff;--mc-cyan:#5fe2d1}
.case-card,.case-play,.inv-card,.detail-item{animation:mc-in .45s both;animation-delay:calc(var(--i,0)*35ms)}
@keyframes mc-in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.case-card:after,.case-play:after{content:"";position:absolute;inset:0;pointer-events:none;border-radius:inherit;background:linear-gradient(115deg,transparent 28%,#fff1 44%,transparent 57%);transform:translateX(-120%);transition:transform .75s ease}
.case-card:hover:after{transform:translateX(120%)}
.case-card{isolation:isolate}.case-pic>img{filter:drop-shadow(0 16px 18px #0009);animation:mc-float 4s ease-in-out infinite}.case-card:nth-child(3n) .case-pic>img{animation-delay:-1.4s}.case-card:nth-child(3n+1) .case-pic>img{animation-delay:-2.5s}
@keyframes mc-float{0%,100%{transform:translateY(0) rotate(-1deg)}50%{transform:translateY(-7px) rotate(1deg)}}
.case-loot{position:relative;padding:7px 6px 6px;border:1px solid #ffffff12;border-radius:10px;background:#0c0d18aa;box-shadow:inset 0 1px #fff1;min-height:48px}.case-loot:before{content:"ВОЗМОЖНЫЕ ПРЕДМЕТЫ";display:block;color:#8f8ba7;font-size:8px;letter-spacing:.1em;margin:0 0 4px}.case-loot img{width:34px!important;height:34px!important;transition:transform .2s,filter .2s}.case-loot img:hover{transform:translateY(-4px) scale(1.12);filter:drop-shadow(0 5px 7px #9b72ff99)}
.item-mini{display:flex;align-items:center;gap:6px;margin-top:8px;padding:5px 7px;border-radius:8px;background:#10111d;border:1px solid #ffffff12;color:#aaa6bd;font-size:10px}.item-mini img{width:22px;height:22px;object-fit:contain}.item-mini b{color:#ded9ed;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.inv-card .item-actions{position:relative;z-index:2}.inv-card .item-actions button{transition:background .2s,transform .2s}.inv-card .item-actions button:hover{transform:translateY(-2px)}
.withdraw-preview-item{display:flex;align-items:center;gap:12px;padding:10px;border:1px solid #ffffff18;border-radius:12px;background:#11121e}.withdraw-preview-item img{width:58px!important;height:58px!important;object-fit:contain}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
'''
for path in root.glob('*.html'):
 s=path.read_text()
 # CSS once per page
 if 'MeshCase polish:' not in s:
  s=s.replace('</style>',css+'</style>',1)
 # Every inventory card has a clear mini icon strip immediately below its value.
 old='</div><div class="item-actions"><button type="button" data-sell="${item.uid}"'
 new='</div><div class="item-mini"><img src="${itemImage(p)}" alt=""><b>Мини-иконка предмета</b></div><div class="item-actions"><button type="button" data-sell="${item.uid}"'
 s=s.replace(old,new)
 # Improve QR picker: phone camera/gallery can be used, but it remains local-only demo.
 s=s.replace('accept="image/png,image/jpeg,image/webp">','accept="image/png,image/jpeg,image/webp" capture="environment">')
 # Add explicit semantic labels beneath possible drops if old detail markup exists.
 s=s.replace('<div class="detail-item"><img src="${itemImage(p)}" alt=""><b>${p.name}</b>', '<div class="detail-item"><img src="${itemImage(p)}" alt=""><div class="item-mini"><img src="${itemImage(p)}" alt=""><b>Мини-иконка</b></div><b>${p.name}</b>')
 path.write_text(s)
print('polished',len(list(root.glob('*.html'))),'pages')
