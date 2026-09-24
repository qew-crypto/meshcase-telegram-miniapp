"""Transactional case opening, inventory, sale and upgrade. No external fulfillment."""
import json
import secrets
import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parent
ITEMS = {p['id']: p for p in json.loads((ROOT/'items.js').read_text().split('=',1)[1].rstrip(';\n'))}
CASES = {c['id']: c for c in json.loads((ROOT/'cases.json').read_text())}
TARGETS = {i for c in CASES.values() for i, chance in c['drops'] if chance > 0}

def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS game_inventory (id INTEGER PRIMARY KEY, tg_id INTEGER NOT NULL, item TEXT NOT NULL, state TEXT NOT NULL DEFAULT "available", created INTEGER NOT NULL)')
    db.execute('CREATE INDEX IF NOT EXISTS inventory_owner ON game_inventory(tg_id,state)')
    db.execute('CREATE TABLE IF NOT EXISTS game_operations (tg_id INTEGER NOT NULL, request_id TEXT NOT NULL, payload TEXT NOT NULL, result TEXT NOT NULL, created INTEGER NOT NULL, PRIMARY KEY(tg_id,request_id))')

def grant(db, uid, item):
    iid=db.execute('INSERT INTO game_inventory(tg_id,item,created) VALUES(?,?,?)',(uid,json.dumps(item,ensure_ascii=False),int(time.time()))).lastrowid
    return {'id':iid,'item':item,'state':'available'}

def handle(db, user, path, data):
    uid=user['tg_id']
    if data is None:
        if path != '/api/tg/game/inventory': raise ValueError('Неизвестная операция')
        return {'inventory':[{'id':r['id'],'item':json.loads(r['item']),'state':r['state']} for r in db.execute('SELECT * FROM game_inventory WHERE tg_id=? AND state="available" ORDER BY id DESC',(uid,))], 'operations':[json.loads(r[0]) for r in db.execute('SELECT result FROM game_operations WHERE tg_id=? ORDER BY created DESC,rowid DESC LIMIT 30',(uid,))]}
    key=data.get('request_id')
    if not isinstance(key,str) or not 16<=len(key)<=80: raise ValueError('Нужен ключ операции')
    payload=json.dumps([path,data],sort_keys=True)
    db.execute('BEGIN IMMEDIATE')
    current=db.execute('SELECT * FROM tg_users WHERE tg_id=?',(uid,)).fetchone()
    if current['banned']: raise ValueError('Аккаунт заблокирован')
    old=db.execute('SELECT * FROM game_operations WHERE tg_id=? AND request_id=?',(uid,key)).fetchone()
    if old:
        if old['payload']!=payload: raise ValueError('Ключ уже использован для другой операции')
        db.commit()
        return json.loads(old['result'])
    action=path.rsplit('/',1)[-1]
    result={'action':action,'request_id':key}
    delta=0
    if action=='open':
        c=CASES.get(str(data.get('case_id')))
        if not c: raise ValueError('Кейс не найден')
        count=data.get('count',1)
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
    elif action=='sell_all':
        ids=data.get('inventory_ids')
        if not isinstance(ids,list) or not ids or len(ids)>10000 or any(type(i)!=int for i in ids) or len(set(ids))!=len(ids):
            raise ValueError('Неверный список предметов')
        # Snapshot IDs only: newly acquired items cannot accidentally be sold.
        available={r['id']:r for r in db.execute('SELECT * FROM game_inventory WHERE tg_id=? AND state="available"',(uid,))}
        if any(i not in available for i in ids): raise ValueError('Состав инвентаря изменился. Обнови список перед продажей')
        delta=sum(json.loads(available[i]['item'])['value'] for i in ids)
        db.executemany('UPDATE game_inventory SET state="sell" WHERE id=? AND tg_id=?',[(i,uid) for i in ids])
        result.update(count=len(ids),sold_ids=ids,total=delta)
        reason='Продажа предметов × '+str(len(ids))
    elif action in ('sell','upgrade'):
        iid=data.get('inventory_id')
        if type(iid)!=int: raise ValueError('Неверный предмет')
        row=db.execute('SELECT * FROM game_inventory WHERE id=? AND tg_id=? AND state="available"',(iid,uid)).fetchone()
        if not row: raise ValueError('Предмет недоступен или уже использован')
        source=json.loads(row['item']);result['source']=source
        if action=='sell':
            delta=source['value'];reason='Продажа: '+source['name']
        else:
            tid=str(data.get('target_id'))
            if tid not in TARGETS: raise ValueError('Цель недоступна')
            target=ITEMS[tid]
            if target['value']<=source['value']: raise ValueError('Цель должна быть дороже исходного предмета')
            threshold=source['value']*900000//target['value']
            if threshold<100: raise ValueError('Минимальный шанс апгрейда 0,01%')
            result['chance']=threshold/10000;result['target']=target
            result['success']=secrets.randbelow(1000000)<threshold
            if result['success']: result['prize']=grant(db,uid,target)
            reason='Апгрейд: '+source['name']+' → '+target['name']+(' (успех)' if result['success'] else ' (неудача)')
        db.execute('UPDATE game_inventory SET state=? WHERE id=?',(action,iid))
    else: raise ValueError('Неизвестная операция')
    if not 0<=current['balance']+delta<=10**12: raise ValueError('Недопустимый баланс')
    db.execute('UPDATE tg_users SET balance=balance+? WHERE tg_id=?',(delta,uid))
    db.execute('INSERT INTO balance_events(tg_id,delta,reason,created) VALUES(?,?,?,?)',(uid,delta,reason,int(time.time())))
    result['balance']=current['balance']+delta
    db.execute('INSERT INTO game_operations VALUES(?,?,?,?,?)',(uid,key,payload,json.dumps(result,ensure_ascii=False),int(time.time())))
    db.commit()
    return result
