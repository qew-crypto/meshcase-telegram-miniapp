import json, math
from pathlib import Path
P=Path(__file__).parent
items={x['id']:x for x in json.loads((P/'items.js').read_text().split('=',1)[1].rstrip(';\n'))}
cases=json.loads((P/'cases.json').read_text())
def allocate(ids, target):
    vals=[items[i]['value'] for i in ids]
    assert min(vals)<target<max(vals), (target,vals)
    def probs(t):
        logs=[-t*v/target for v in vals]; m=max(logs)
        w=[math.exp(max(-700,x-m)) for x in logs]; return [x/sum(w) for x in w]
    lo,hi=-100.,100.
    for _ in range(100):
        mid=(lo+hi)/2; w=probs(mid)
        if sum(v*p for v,p in zip(vals,w))>target:lo=mid
        else:hi=mid
    return probs((lo+hi)/2)
def rounded(ids,w):
    raw=[p*100000 for p in w]; units=[int(x) for x in raw]
    for k in sorted(range(len(ids)),key=lambda k:raw[k]-units[k],reverse=True)[:100000-sum(units)]:units[k]+=1
    return [[i,u/1000] for i,u in zip(ids,units) if u]
report=['Баланс каталога: номинальная оценка предметов, не денежная выплата.','Целевой средний номинал: 92% цены. ALL IN — отдельный высокорисковый формат.','Обычные кейсы: минимум 40% цены; предметы с шансом ниже 0.01% исключены.','']
for c in cases:
    ids=[i for i,_ in c['drops']]
    if c['type']=='allin':
        # Existing items only; no invented low-value rewards for ReallyWorld.
        low=[i for i in ids if items[i]['value']<= (46 if c['id']=='allin-rw' else 30)]
        high=[i for i in ids if items[i]['value']>=5000]
        c['price']=95 if c['id']=='allin-rw' else 65
        a=sum(items[i]['value'] for i in low)/len(low)
        b=sum(items[i]['value'] for i in high)/len(high)
        q=(c['price']*.92-a)/(b-a)
        ids=low+high; w=[(1-q)/len(low)]*len(low)+[q/len(high)]*len(high)
        c['desc']='ALL IN: дешёвый дроп или редкий топ-приз. Промежуточных наград нет. Высокий риск.'
    else:
        ids=[i for i in ids if items[i]['value']>=c['price']*.4]
        while True:
            w=allocate(ids,c['price']*.92)
            keep=[i for i,p in zip(ids,w) if p>=.0001]
            if keep==ids:break
            ids=keep
        c['desc']='Минимальный номинал дропа — 40% цены кейса. Вероятности указаны в содержимом; окупаемость не гарантирована.'
    c['drops']=rounded(ids,w)
    ev=sum(items[i]['value']*p/100 for i,p in c['drops'])
    profit=sum(p for i,p in c['drops'] if items[i]['value']>=c['price'])
    c['metrics'].update(items=len(c['drops']),minValue=min(items[i]['value'] for i,_ in c['drops']),maxValue=max(items[i]['value'] for i,_ in c['drops']),profitChance=round(profit,3),rtp=round(ev/c['price']*100,3),expectedValue=round(ev,3))
    report.append(f"{c['id']}: цена {c['price']}, диапазон {c['metrics']['minValue']}–{c['metrics']['maxValue']}, шанс >= цены {profit:.3f}%, RTP {ev/c['price']*100:.3f}%")
(P/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
(P/'catalog-audit.txt').write_text('\n'.join(report)+'\n')
print('\n'.join(report))
