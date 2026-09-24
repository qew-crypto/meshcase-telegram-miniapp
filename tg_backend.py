"""Telegram-only account, moderation and support API. No client balance is trusted."""
import json
import re
import time
from urllib.parse import parse_qs, urlsplit
import os
import stars_payments
import game_backend
import bot_messages
from pathlib import Path


def is_admin(user):
    ids = {int(x.strip()) for x in os.environ.get('MESHCASE_ADMIN_IDS', (Path(__file__).parent/'admin_ids.txt').read_text().strip()).split(',') if x.strip().isdigit()}
    return bool(user and user['tg_id'] in ids)


def migrate(db):
    game_backend.migrate(db)
    for table, column, definition in [('tg_users','banned','INTEGER NOT NULL DEFAULT 0'),('tg_users','ban_reason','TEXT NOT NULL DEFAULT ""'),('tg_tickets','status','TEXT NOT NULL DEFAULT "open"')]:
        if column not in {r[1] for r in db.execute('PRAGMA table_info('+table+')')}:
            db.execute('ALTER TABLE '+table+' ADD COLUMN '+column+' '+definition)
    db.execute('CREATE TABLE IF NOT EXISTS ticket_messages (id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL, sender_id INTEGER NOT NULL, staff INTEGER NOT NULL, body TEXT NOT NULL, created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS admin_audit (id INTEGER PRIMARY KEY, actor INTEGER NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, details TEXT NOT NULL, created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS balance_events (id INTEGER PRIMARY KEY, tg_id INTEGER NOT NULL, delta INTEGER NOT NULL, reason TEXT NOT NULL, created INTEGER NOT NULL)')


def integer(data, key, low, high):
    value=data.get(key)
    if type(value)!=int or not low<=value<=high:raise ValueError('Неверное поле: '+key)
    return value


def text(data, key, low=1, high=2000):
    value=data.get(key)
    if not isinstance(value,str) or not low<=len(value.strip())<=high:raise ValueError('Проверьте поле: '+key)
    return value.strip()


def audit(db,user,action,target,details):
    db.execute('INSERT INTO admin_audit(actor,action,target,details,created) VALUES(?,?,?,?,?)',(user['tg_id'],action,str(target),json.dumps(details,ensure_ascii=False),int(time.time())))


def ticket_data(db,row):
    item=dict(row)
    item['messages']=[{'staff':0,'body':item['body'],'created':item['created']}]
    if item['answer']:item['messages'].append({'staff':1,'body':item['answer'],'created':item['created']})
    item['messages'] += [dict(r) for r in db.execute('SELECT staff,body,created FROM ticket_messages WHERE ticket_id=? ORDER BY id',(item['id'],))]
    return item


def handle(h,db,path,data,user,bot_api=None):
    get=data is None
    out=lambda status,obj:h.json_out(status,obj)
    if path=='/api/tg/me' and get:
        result=dict(user) if user else None
        if result:result['is_admin']=is_admin(user)
        if result:result['stars_enabled']=bool(stars_payments.enabled())
        return out(200,{'user':result})
    if not user:return out(401,{'error':'Откройте приложение кнопкой бота в Telegram'})
    if user['banned']:return out(403,{'error':'Аккаунт заблокирован. '+user['ban_reason']})
    admin=is_admin(user)
    if path.startswith('/api/tg/admin') and not admin:return out(403,{'error':'Нет прав администратора'})
    if path.startswith('/api/tg/game/'):
        return out(200,game_backend.handle(db,user,path,data))
    now=int(time.time())
    notification = None
    if get:
        if path=='/api/tg/tickets':
            return out(200,{'tickets':[ticket_data(db,r) for r in db.execute('SELECT * FROM tg_tickets WHERE tg_id=? ORDER BY id DESC LIMIT 50',(user['tg_id'],))]})
        if path=='/api/tg/history':
            return out(200,{'events':[dict(r) for r in db.execute('SELECT delta,reason,created FROM balance_events WHERE tg_id=? ORDER BY id DESC LIMIT 50',(user['tg_id'],))]})
        if path=='/api/tg/admin':
            query=parse_qs(urlsplit(h.path).query).get('q',[''])[0][:80]
            users=[dict(r) for r in db.execute('SELECT * FROM tg_users WHERE CAST(tg_id AS TEXT)=? OR instr(lower(username),lower(?))>0 OR instr(lower(first_name),lower(?))>0 ORDER BY created DESC,tg_id DESC LIMIT 100',(query,query,query))]
            return out(200,{'payments':[dict(r) for r in db.execute('SELECT tg_id,stars,credit,created,charge_id FROM invoices ORDER BY created DESC LIMIT 100')],'users':users,'stats':{'users':db.execute('SELECT count(*) FROM tg_users').fetchone()[0],'open':db.execute('SELECT count(*) FROM tg_tickets WHERE status="open"').fetchone()[0]},'promos':[dict(r) for r in db.execute('SELECT p.*, (SELECT count(*) FROM promo_uses u WHERE u.code=p.code) used FROM promos p ORDER BY rowid DESC LIMIT 100')],'tickets':[ticket_data(db,r) for r in db.execute('SELECT t.*,u.username FROM tg_tickets t JOIN tg_users u USING(tg_id) ORDER BY t.id DESC LIMIT 100')],'audit':[dict(r) for r in db.execute('SELECT * FROM admin_audit ORDER BY id DESC LIMIT 50')]})
        return out(404,{'error':'Не найдено'})
    # Acquire the write lock before reading counters/balances: simultaneous redemptions cannot exceed limits.
    db.execute('BEGIN IMMEDIATE')
    current=db.execute('SELECT * FROM tg_users WHERE tg_id=?',(user['tg_id'],)).fetchone()
    if current['banned']:return out(403,{'error':'Аккаунт заблокирован'})
    if path=='/api/tg/redeem':
        code=text(data,'code',4,32).upper()
        row=db.execute('SELECT * FROM promos WHERE code=? AND kind="balance" AND active=1 AND (expires=0 OR expires>?)',(code,now)).fetchone()
        count=db.execute('SELECT count(*) FROM promo_uses WHERE code=?',(code,)).fetchone()[0]
        if not row or count>=row['uses_limit']:raise ValueError('Промокод недействителен или закончился')
        if db.execute('SELECT 1 FROM promo_uses WHERE code=? AND tg_id=?',(code,user['tg_id'])).fetchone():raise ValueError('Вы уже активировали этот промокод')
        db.execute('INSERT INTO promo_uses VALUES(?,?)',(code,user['tg_id']))
        db.execute('UPDATE tg_users SET balance=balance+? WHERE tg_id=?',(row['amount'],user['tg_id']))
        db.execute('INSERT INTO balance_events(tg_id,delta,reason,created) VALUES(?,?,?,?)',(user['tg_id'],row['amount'],'Промокод '+code,now))
    elif path=='/api/tg/tickets':
        body=text(data,'body',5)
        if db.execute('SELECT count(*) FROM tg_tickets WHERE tg_id=? AND status="open"',(user['tg_id'],)).fetchone()[0]>=5:raise ValueError('У вас уже 5 открытых обращений')
        if db.execute('SELECT 1 FROM tg_tickets WHERE tg_id=? AND created>?',(user['tg_id'],now-30)).fetchone():raise ValueError('Подождите 30 секунд перед новым обращением')
        db.execute('INSERT INTO tg_tickets(tg_id,body,created) VALUES(?,?,?)',(user['tg_id'],body,now))
    elif path in ('/api/tg/tickets/message','/api/tg/admin/reply','/api/tg/tickets/status'):
        tid=integer(data,'id',1,2**53-1)
        row=db.execute('SELECT * FROM tg_tickets WHERE id=?',(tid,)).fetchone()
        if not row or (row['tg_id']!=user['tg_id'] and not admin):return out(404,{'error':'Обращение не найдено'})
        if path.endswith('/status'):
            status=data.get('status')
            if status not in ('open','closed'):raise ValueError('Неверный статус')
            db.execute('UPDATE tg_tickets SET status=? WHERE id=?',(status,tid))
        else:
            if row['status']=='closed':raise ValueError('Сначала откройте обращение заново')
            body=text(data,'answer' if path.endswith('/reply') else 'body')
            if db.execute('SELECT 1 FROM ticket_messages WHERE sender_id=? AND created>?',(user['tg_id'],now-2)).fetchone():raise ValueError('Отправляете слишком быстро. Подождите пару секунд')
            db.execute('INSERT INTO ticket_messages(ticket_id,sender_id,staff,body,created) VALUES(?,?,?,?,?)',(tid,user['tg_id'],int(admin),body,now))
        if admin:
            audit(db,user,'ticket',tid,{'operation':path.rsplit('/',1)[-1]})
            if path.endswith('/status'):
                label = 'закрыто' if status == 'closed' else 'открыто заново'
                notification = (row['tg_id'], f'Обращение №{tid} {label}.')
            else:
                notification = (row['tg_id'], f'Ответ поддержки по обращению №{tid}:\n\n{body}')
    elif path=='/api/tg/admin/balance':
        target=integer(data,'tg_id',1,2**53-1);delta=integer(data,'delta',-1000000,1000000);reason=text(data,'reason',3,200)
        if not delta:raise ValueError('Укажите ненулевую сумму')
        row=db.execute('SELECT balance FROM tg_users WHERE tg_id=?',(target,)).fetchone()
        if not row:raise ValueError('Пользователь не найден')
        if not 0<=row['balance']+delta<=10**12:raise ValueError('Недопустимый итоговый баланс')
        db.execute('UPDATE tg_users SET balance=balance+? WHERE tg_id=?',(delta,target))
        db.execute('INSERT INTO balance_events(tg_id,delta,reason,created) VALUES(?,?,?,?)',(target,delta,reason,now))
        audit(db,user,'balance',target,{'delta':delta,'reason':reason,'before':row['balance'],'after':row['balance']+delta})
    elif path=='/api/tg/admin/ban':
        target=integer(data,'tg_id',1,2**53-1);banned=data.get('banned')
        if type(banned)!=bool:raise ValueError('Неверное состояние бана')
        if is_admin({'tg_id':target}):raise ValueError('Нельзя заблокировать администратора')
        reason=text(data,'reason',3,200) if banned else ''
        cur=db.execute('UPDATE tg_users SET banned=?,ban_reason=? WHERE tg_id=?',(int(banned),reason,target))
        if not cur.rowcount:raise ValueError('Пользователь не найден')
        audit(db,user,'ban',target,{'banned':banned,'reason':reason})
    elif path=='/api/tg/admin/promo':
        code=text(data,'code',4,32).upper();amount=integer(data,'amount',1,100000);limit=integer(data,'limit',1,100000);expires=integer(data,'expires',0,2**40)
        if not re.fullmatch(r'[A-Z0-9_-]{4,32}',code):raise ValueError('Код: латинские буквы, цифры, _ и -')
        if expires and expires<=now:raise ValueError('Срок действия должен быть в будущем')
        if db.execute('SELECT 1 FROM promos WHERE code=?',(code,)).fetchone():raise ValueError('Такой код уже существует')
        db.execute('INSERT INTO promos(code,kind,amount,uses_limit,expires) VALUES(?,"balance",?,?,?)',(code,amount,limit,expires))
        audit(db,user,'promo_create',code,{'amount':amount,'limit':limit,'expires':expires})
    elif path=='/api/tg/admin/toggle':
        code=text(data,'code',4,32).upper();active=data.get('active')
        if type(active)!=bool:raise ValueError('Неверное состояние промокода')
        if not db.execute('UPDATE promos SET active=? WHERE code=?',(int(active),code)).rowcount:raise ValueError('Промокод не найден')
        audit(db,user,'promo_toggle',code,{'active':active})
    elif path=='/api/tg/invoice':
        if not stars_payments.enabled():return out(503,{'error':'Пополнение пока недоступно'})
        return out(200,stars_payments.invoice(db,current,data.get('stars'),bot_api))
    else:return out(404,{'error':'Не найдено'})
    db.commit()
    delivered = bot_messages.send(bot_api, *notification) if notification else None
    balance=db.execute('SELECT balance FROM tg_users WHERE tg_id=?',(user['tg_id'],)).fetchone()[0]
    return out(200,{'ok':True,'balance':balance,'notification_delivered':delivered})
