from pathlib import Path
p=Path('server.py');s=p.read_text();s=s.replace('import time\n','import time\nimport urllib.request\nfrom urllib.parse import parse_qsl\n')
s=s.replace("    return db\n",'''    db.execute('CREATE TABLE IF NOT EXISTS tg_users (tg_id INTEGER PRIMARY KEY, username TEXT NOT NULL, first_name TEXT NOT NULL, balance INTEGER NOT NULL DEFAULT 0, created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS tg_sessions (token_hash TEXT PRIMARY KEY, tg_id INTEGER NOT NULL, expires INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS promos (code TEXT PRIMARY KEY, kind TEXT NOT NULL, amount INTEGER NOT NULL, uses_limit INTEGER NOT NULL, expires INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1)')
    db.execute('CREATE TABLE IF NOT EXISTS promo_uses (code TEXT NOT NULL, tg_id INTEGER NOT NULL, PRIMARY KEY(code,tg_id))')
    db.execute('CREATE TABLE IF NOT EXISTS tg_tickets (id INTEGER PRIMARY KEY, tg_id INTEGER NOT NULL, body TEXT NOT NULL, answer TEXT NOT NULL DEFAULT "", created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS invoices (payload TEXT PRIMARY KEY, tg_id INTEGER NOT NULL, stars INTEGER NOT NULL, credit INTEGER NOT NULL, created INTEGER NOT NULL, charge_id TEXT UNIQUE)')
    return db
''',1)
pos=s.index('class Handler(')
s=s[:pos]+'''def validate_init(init_data):
    token=os.environ.get('MESHCASE_BOT_TOKEN','')
    if not token:raise ValueError('Telegram-бот не настроен')
    if not isinstance(init_data,str) or len(init_data)>8192:raise ValueError('Некорректные данные Telegram')
    pairs=parse_qsl(init_data,keep_blank_values=True,strict_parsing=True)
    fields=dict(pairs)
    if len(fields)!=len(pairs) or 'hash' not in fields:raise ValueError('Неверная подпись Telegram')
    check='\\n'.join(k+'='+v for k,v in sorted(fields.items()) if k!='hash')
    secret=hmac.new(b'WebAppData',token.encode(),hashlib.sha256).digest()
    signature=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,fields['hash']):raise ValueError('Неверная подпись Telegram')
    now=int(time.time());auth=int(fields.get('auth_date','0'))
    if auth>now+60 or auth<now-86400:raise ValueError('Сессия Telegram устарела — перезапустите приложение')
    user=json.loads(fields['user']);tg_id=user.get('id')
    if not isinstance(tg_id,int) or tg_id<=0:raise ValueError('Неверный ID Telegram')
    return user

def tg_cookie(handler,db):
    cookie=SimpleCookie()
    try:cookie.load(handler.headers.get('Cookie',''))
    except Exception:return None
    entry=cookie.get('mc_tg');token=entry.value if entry else ''
    return db.execute('SELECT tg_users.* FROM tg_sessions JOIN tg_users ON tg_users.tg_id=tg_sessions.tg_id WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone() if token else None

def bot_api(method,data):
    token=os.environ.get('MESHCASE_BOT_TOKEN','')
    if not token:raise ValueError('Бот не настроен')
    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as resp:result=json.load(resp)
    if not result.get('ok'):raise ValueError('Telegram API отклонил запрос')
    return result['result']

def promo_row(db,code,kind):
    row=db.execute('SELECT * FROM promos WHERE code=? AND kind=? AND active=1 AND (expires=0 OR expires>?)',(code,kind,int(time.time()))).fetchone()
    if not row or db.execute('SELECT count(*) FROM promo_uses WHERE code=?',(code,)).fetchone()[0]>=row['uses_limit']:raise ValueError('Промокод недействителен или закончился')
    return row

''' +s[pos:]
s=s.replace("                if path=='/api/me':",'''                if path=='/api/tg/me':
                    tg=tg_cookie(self,db)
                    return self.json_out(200,{'user':dict(tg) if tg else None})
                if path=='/api/tg/tickets':
                    tg=tg_cookie(self,db)
                    if not tg:return self.json_out(401,{'error':'Откройте приложение через Telegram'})
                    return self.json_out(200,{'tickets':[dict(r) for r in db.execute('SELECT id,body,answer,created FROM tg_tickets WHERE tg_id=? ORDER BY id DESC',(tg['tg_id'],))]})
                if path=='/api/tg/admin':
                    tg=tg_cookie(self,db)
                    if not tg or tg['tg_id']!=1842295433:return self.json_out(403,{'error':'Доступ только создателю'})
                    return self.json_out(200,{'promos':[dict(r) for r in db.execute('SELECT * FROM promos ORDER BY rowid DESC LIMIT 100')], 'tickets':[dict(r) for r in db.execute('SELECT t.id,t.body,t.answer,t.created,u.username,u.tg_id FROM tg_tickets t JOIN tg_users u ON t.tg_id=u.tg_id ORDER BY t.id DESC LIMIT 200')]})
                if path=='/api/me':''',1)
s=s.replace("            data=self.body()\n            with connect() as db:\n",'''            data=self.body()
            if path=='/api/tg/webhook':
                secret=os.environ.get('MESHCASE_WEBHOOK_SECRET','')
                if not secret or not hmac.compare_digest(self.headers.get('X-Telegram-Bot-Api-Secret-Token',''),secret):return self.json_out(403,{'error':'Forbidden'})
                return self.webhook(data)
            with connect() as db:
                if path=='/api/tg/auth':
                    info=validate_init(data.get('initData'))
                    tg_id=info['id'];name=str(info.get('first_name',''))[:80];username=str(info.get('username',''))[:80]
                    db.execute('INSERT INTO tg_users(tg_id,username,first_name,created) VALUES(?,?,?,?) ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name',(tg_id,username,name,int(time.time())))
                    token=secrets.token_urlsafe(32)
                    db.execute('INSERT INTO tg_sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),tg_id,int(time.time())+7*86400))
                    db.commit()
                    return self.json_out(200,{'ok':True},'mc_tg='+token+'; HttpOnly; Secure; SameSite=None; Path=/; Max-Age=604800')
                if path.startswith('/api/tg/'):
                    tg=tg_cookie(self,db)
                    if not tg:return self.json_out(401,{'error':'Откройте приложение через Telegram'})
                    if path=='/api/tg/tickets':
                        body=str(data.get('body','')).strip()
                        if not 5<=len(body)<=2000:raise ValueError('Сообщение: 5–2000 символов')
                        db.execute('INSERT INTO tg_tickets(tg_id,body,created) VALUES(?,?,?)',(tg['tg_id'],body,int(time.time())));db.commit()
                        return self.json_out(200,{'ok':True})
                    if path=='/api/tg/redeem':
                        code=str(data.get('code','')).strip().upper()
                        with db:
                            row=promo_row(db,code,'balance')
                            if db.execute('SELECT 1 FROM promo_uses WHERE code=? AND tg_id=?',(code,tg['tg_id'])).fetchone():raise ValueError('Вы уже использовали этот код')
                            db.execute('INSERT INTO promo_uses VALUES(?,?)',(code,tg['tg_id']))
                            db.execute('UPDATE tg_users SET balance=balance+? WHERE tg_id=?',(row['amount'],tg['tg_id']))
                        return self.json_out(200,{'ok':True,'balance':db.execute('SELECT balance FROM tg_users WHERE tg_id=?',(tg['tg_id'],)).fetchone()[0]})
                    if path=='/api/tg/promo-check':
                        code=str(data.get('code','')).strip().upper()
                        row=promo_row(db,code,'percent')
                        if db.execute('SELECT 1 FROM promo_uses WHERE code=? AND tg_id=?',(code,tg['tg_id'])).fetchone():raise ValueError('Вы уже использовали этот код')
                        return self.json_out(200,{'percent':row['amount']})
                    if path=='/api/tg/invoice':
                        if os.environ.get('MESHCASE_ENABLE_STARS')!='1':return self.json_out(503,{'error':'Пополнения временно недоступны: игровые операции ещё не переведены на сервер'})
                        stars=data.get('stars');code=str(data.get('code','')).strip().upper()
                        if type(stars)!=int or not 1<=stars<=10000:raise ValueError('Введите от 1 до 10000 звёзд')
                        pct=0
                        if code:
                            row=promo_row(db,code,'percent')
                            if db.execute('SELECT 1 FROM promo_uses WHERE code=? AND tg_id=?',(code,tg['tg_id'])).fetchone():raise ValueError('Промокод уже использован')
                            pct=row['amount']
                        credit=stars*(100+pct)//100
                        payload=secrets.token_urlsafe(24)
                        # No client-supplied price/bonus is trusted. Invoice is bound to the Telegram user.
                        with db:db.execute('INSERT INTO invoices(payload,tg_id,stars,credit,created) VALUES(?,?,?,?,?)',(payload,tg['tg_id'],stars,credit,int(time.time())))
                        url=bot_api('createInvoiceLink',{'title':'MeshCase · игровые монеты','description':str(credit)+' игровых монет (внутренний баланс)','payload':payload,'currency':'XTR','prices':[{'label':'Монеты MeshCase','amount':stars}]})
                        return self.json_out(200,{'url':url})
                    if tg['tg_id']!=1842295433:return self.json_out(403,{'error':'Доступ только создателю'})
                    if path=='/api/tg/admin/promo':
                        code=str(data.get('code','')).strip().upper();kind=data.get('kind');amount=data.get('amount');limit=data.get('limit');expires=data.get('expires',0)
                        if not re.fullmatch(r'[A-Z0-9_-]{4,32}',code) or kind not in ('balance','percent') or type(amount)!=int or not 1<=amount<=(100000 if kind=='balance' else 100) or type(limit)!=int or not 1<=limit<=100000 or type(expires)!=int or expires<0:raise ValueError('Проверьте поля промокода')
                        db.execute('INSERT INTO promos(code,kind,amount,uses_limit,expires) VALUES(?,?,?,?,?)',(code,kind,amount,limit,expires));db.commit()
                        return self.json_out(200,{'ok':True})
                    if path=='/api/tg/admin/toggle':
                        code=str(data.get('code','')).strip().upper()
                        db.execute('UPDATE promos SET active=0 WHERE code=?',(code,));db.commit()
                        return self.json_out(200,{'ok':True})
                    if path=='/api/tg/admin/reply':
                        answer=str(data.get('answer','')).strip();ticket=data.get('id')
                        if type(ticket)!=int or not 1<=len(answer)<=2000:raise ValueError('Неверный ответ')
                        cur=db.execute('UPDATE tg_tickets SET answer=? WHERE id=?',(answer,ticket));db.commit()
                        if not cur.rowcount:raise ValueError('Обращение не найдено')
                        return self.json_out(200,{'ok':True})
                    return self.json_out(404,{'error':'Не найдено'})
''',1)
pos=s.index('    def do_POST(self):')
s=s[:pos]+'''    def webhook(self,data):
        msg=data.get('message') or {}
        pre=data.get('pre_checkout_query')
        if pre:
            with connect() as db:
                row=db.execute('SELECT * FROM invoices WHERE payload=?',(pre.get('invoice_payload'),)).fetchone()
                valid=bool(row and row['tg_id']==pre.get('from',{}).get('id') and row['stars']==pre.get('total_amount') and pre.get('currency')=='XTR' and not row['charge_id'] and row['created']>time.time()-3600)
            bot_api('answerPreCheckoutQuery',{'pre_checkout_query_id':pre['id'],'ok':valid,**({} if valid else {'error_message':'Счёт недействителен'})})
        pay=msg.get('successful_payment')
        if pay:
            payload=pay.get('invoice_payload');charge=pay.get('telegram_payment_charge_id')
            with connect() as db:
                with db:
                    row=db.execute('SELECT * FROM invoices WHERE payload=?',(payload,)).fetchone()
                    if row and row['tg_id']==msg.get('from',{}).get('id') and row['stars']==pay.get('total_amount') and pay.get('currency')=='XTR' and isinstance(charge,str) and charge and not row['charge_id']:
                        cur=db.execute('UPDATE invoices SET charge_id=? WHERE payload=? AND charge_id IS NULL',(charge,payload))
                        if cur.rowcount:db.execute('UPDATE tg_users SET balance=balance+? WHERE tg_id=?',(row['credit'],row['tg_id']))
        return self.json_out(200,{'ok':True})
''' +s[pos:]
p.write_text(s)
