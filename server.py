"""MeshCase development server. Run: python server.py . No payment or fulfillment integration."""
import base64
import tg_backend
import stars_payments
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import urllib.request
from urllib.parse import parse_qsl
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
_db_path = Path(os.environ.get('MESHCASE_DB_PATH', 'meshcase.sqlite3'))
if _db_path.is_absolute() or '..' in _db_path.parts:
    raise ValueError('MESHCASE_DB_PATH must be relative to the project')
DB = ROOT / _db_path
DB.parent.mkdir(parents=True, exist_ok=True)
ADMIN = 'Crypa228'

def connect():
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, nick TEXT NOT NULL UNIQUE COLLATE NOCASE, salt TEXT NOT NULL, digest TEXT NOT NULL, role TEXT NOT NULL DEFAULT "user", created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, body TEXT NOT NULL, answer TEXT NOT NULL DEFAULT "", created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS tg_users (tg_id INTEGER PRIMARY KEY, username TEXT NOT NULL, first_name TEXT NOT NULL, balance INTEGER NOT NULL DEFAULT 0, created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS tg_sessions (token_hash TEXT PRIMARY KEY, tg_id INTEGER NOT NULL, expires INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS promos (code TEXT PRIMARY KEY, kind TEXT NOT NULL, amount INTEGER NOT NULL, uses_limit INTEGER NOT NULL, expires INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1)')
    db.execute('CREATE TABLE IF NOT EXISTS promo_uses (code TEXT NOT NULL, tg_id INTEGER NOT NULL, PRIMARY KEY(code,tg_id))')
    db.execute('CREATE TABLE IF NOT EXISTS tg_tickets (id INTEGER PRIMARY KEY, tg_id INTEGER NOT NULL, body TEXT NOT NULL, answer TEXT NOT NULL DEFAULT "", created INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS invoices (payload TEXT PRIMARY KEY, tg_id INTEGER NOT NULL, stars INTEGER NOT NULL, credit INTEGER NOT NULL, created INTEGER NOT NULL, charge_id TEXT UNIQUE)')
    tg_backend.migrate(db)
    return db

def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),350000).hex()

def bootstrap():
    with connect() as db:
        if not db.execute('SELECT id FROM users WHERE nick=?',(ADMIN,)).fetchone():
            password = os.environ.get('MESHCASE_ADMIN_PASSWORD')
            if not password:
                return  # Legacy admin is disabled until a password is set explicitly.
            salt=secrets.token_hex(16)
            db.execute('INSERT INTO users (nick,salt,digest,role,created) VALUES (?,?,?,?,?)',(ADMIN,salt,password_hash(password,salt),'admin',int(time.time())))

def validate_init(init_data):
    token=os.environ.get('MESHCASE_BOT_TOKEN','')
    if not token:raise ValueError('Telegram-бот не настроен')
    if not isinstance(init_data,str) or len(init_data)>8192:raise ValueError('Некорректные данные Telegram')
    pairs=parse_qsl(init_data,keep_blank_values=True,strict_parsing=True)
    fields=dict(pairs)
    if len(fields)!=len(pairs) or 'hash' not in fields:raise ValueError('Неверная подпись Telegram')
    check='\n'.join(k+'='+v for k,v in sorted(fields.items()) if k!='hash')
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

def allowed_request_origin(headers, origin):
    """Validate browser POSTs against the configured public origin, or direct host locally."""
    if not origin:
        return True  # Non-browser webhook requests authenticate using their own secret.
    public = os.environ.get('MESHCASE_PUBLIC_ORIGIN', '').strip().rstrip('/')
    if public:
        parsed = urlsplit(public)
        if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError('MESHCASE_PUBLIC_ORIGIN должен быть адресом вида https://example.com')
        return origin == public
    proto = 'https' if headers.get('X-Forwarded-Proto') == 'https' else 'http'
    return origin == proto + '://' + headers.get('Host', '')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy', "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org")
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def json_out(self, status, data, cookie=None):
        blob=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(blob)))
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(blob)
    def get_user(self,db):
        cookie=SimpleCookie()
        try:cookie.load(self.headers.get('Cookie',''))
        except Exception:return None
        token=cookie.get('mc_session')
        if not token:return None
        return db.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?',(hashlib.sha256(token.value.encode()).hexdigest(),int(time.time()))).fetchone()
    def body(self):
        size=int(self.headers.get('Content-Length',0))
        if size<1 or size>10000:raise ValueError('Неверный размер запроса')
        data=json.loads(self.rfile.read(size));
        if not isinstance(data,dict):raise ValueError('Неверный формат')
        return data
    def do_GET(self):
        path=urlsplit(self.path).path
        if path == '/healthz':return self.json_out(200, {'ok': True})
        if path.startswith('/api/'):
            with connect() as db:
                u=self.get_user(db)
                if path.startswith('/api/tg/'):
                    return tg_backend.handle(self,db,path,None,tg_cookie(self,db))
                if path=='/api/me':return self.json_out(200,{'user':{'nick':u['nick'],'role':u['role']} if u else None})
                if not u:return self.json_out(401,{'error':'Войдите в аккаунт'})
                if path=='/api/tickets':
                    rows=db.execute('SELECT id,body,answer,created FROM tickets WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall()
                    return self.json_out(200,{'tickets':[dict(r) for r in rows]})
                if path=='/api/admin':
                    if u['role']!='admin':return self.json_out(403,{'error':'Нет доступа'})
                    users=db.execute('SELECT id,nick,role,created FROM users ORDER BY id DESC LIMIT 200').fetchall()
                    tickets=db.execute('SELECT tickets.id,users.nick,tickets.body,tickets.answer,tickets.created FROM tickets JOIN users ON users.id=tickets.user_id ORDER BY tickets.id DESC LIMIT 200').fetchall()
                    return self.json_out(200,{'users':[dict(r) for r in users],'tickets':[dict(r) for r in tickets]})
            return self.json_out(404,{'error':'Не найдено'})
        path=unquote(path)
        if path.endswith('.html') and path!='/miniapp.html':
            target={'/profile.html':'profile','/support.html':'support','/admin.html':'admin'}.get(path,'cases')
            self.send_response(302);self.send_header('Location','/miniapp.html#'+target);self.end_headers();return
        if path=='/':
            self.path='/miniapp.html'
            return super().do_GET()
        if '..' in path.split('/') or '\\' in path or any(part.startswith('.') for part in path.split('/') if part):return self.send_error(404)
        suffix=Path(path).suffix.lower()
        if path!='/cases.json' and suffix not in {'.html','.css','.js','.png','.jpg','.jpeg','.svg','.webp','.ico'}:return self.send_error(404)
        return super().do_GET()
    def webhook(self,data):
        msg=data.get('message') or {}
        pre=data.get('pre_checkout_query')
        if pre:
            with connect() as db:
                valid=bool(stars_payments.valid(db,pre,pre.get('from',{}).get('id'),checkout=True))
            bot_api('answerPreCheckoutQuery',{'pre_checkout_query_id':pre['id'],'ok':valid,**({} if valid else {'error_message':'Счёт недействителен'})})
        pay=msg.get('successful_payment')
        if pay:
            with connect() as db:
                stars_payments.settle(db,pay,msg.get('from',{}).get('id'))
        return self.json_out(200,{'ok':True})
    def do_POST(self):
        path=urlsplit(self.path).path
        if not path.startswith('/api/'):return self.send_error(404)
        try:
            if path!='/api/tg/webhook' and not allowed_request_origin(self.headers, self.headers.get('Origin')):return self.json_out(403,{'error':'Неверный Origin'})
            data=self.body()
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
                    return tg_backend.handle(self,db,path,data,tg_cookie(self,db),bot_api)
                user=self.get_user(db)
                if path in ('/api/register','/api/login'):
                    nick=str(data.get('nick','')).strip();password=data.get('password','')
                    if not re.fullmatch(r'[A-Za-z0-9_]{3,24}',nick) or not isinstance(password,str) or len(password)<8 or len(password)>128:
                        raise ValueError('Ник: 3–24 символа (латиница, цифры, _); пароль: 8–128 символов')
                    if path=='/api/register':
                        if nick.lower()==ADMIN.lower():raise ValueError('Ник занят')
                        if db.execute('SELECT id FROM users WHERE nick=?',(nick,)).fetchone():raise ValueError('Ник занят')
                        salt=secrets.token_hex(16)
                        db.execute('INSERT INTO users (nick,salt,digest,created) VALUES (?,?,?,?)',(nick,salt,password_hash(password,salt),int(time.time())))
                    account=db.execute('SELECT * FROM users WHERE nick=?',(nick,)).fetchone()
                    if not account or not hmac.compare_digest(password_hash(password,account['salt']),account['digest']):return self.json_out(401,{'error':'Неверный ник или пароль'})
                    token=secrets.token_urlsafe(32)
                    db.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),account['id'],int(time.time())+30*86400));db.commit()
                    secure='; Secure' if self.headers.get('X-Forwarded-Proto')=='https' else ''
                    return self.json_out(200,{'user':{'nick':account['nick'],'role':account['role']}},'mc_session='+token+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=2592000'+secure)
                if path=='/api/logout':
                    cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''))
                    if cookie.get('mc_session'):db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(cookie['mc_session'].value.encode()).hexdigest(),));db.commit()
                    return self.json_out(200,{'ok':True},'mc_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
                if not user:return self.json_out(401,{'error':'Войдите в аккаунт'})
                if path=='/api/tickets':
                    body=str(data.get('body','')).strip()
                    if not 5<=len(body)<=2000:raise ValueError('Сообщение: от 5 до 2000 символов')
                    db.execute('INSERT INTO tickets (user_id,body,created) VALUES (?,?,?)',(user['id'],body,int(time.time())));db.commit()
                    return self.json_out(200,{'ok':True})
                if path=='/api/admin/reply':
                    if user['role']!='admin':return self.json_out(403,{'error':'Нет доступа'})
                    answer=str(data.get('answer','')).strip();ticket=data.get('id')
                    if not isinstance(ticket,int) or not 1<=len(answer)<=2000:raise ValueError('Неверный ответ')
                    db.execute('UPDATE tickets SET answer=? WHERE id=?',(answer,ticket));db.commit()
                    if not db.execute('SELECT 1 FROM tickets WHERE id=?',(ticket,)).fetchone():raise ValueError('Заявка не найдена')
                    return self.json_out(200,{'ok':True})
            return self.json_out(404,{'error':'Не найдено'})
        except (ValueError,json.JSONDecodeError) as exc:return self.json_out(400,{'error':str(exc)})
        except sqlite3.IntegrityError:return self.json_out(409,{'error':'Запись уже существует'})
        except sqlite3.OperationalError:return self.json_out(503,{'error':'База временно занята. Повторите запрос'})

if __name__=='__main__':
    bootstrap()
    print('MeshCase Python server; port=' + os.environ.get('PORT', '8000'), flush=True)
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8000'))),Handler).serve_forever()
