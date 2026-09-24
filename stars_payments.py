"""Stars invoice creation and verified, idempotent settlement."""
import os
import secrets
import time

PACKS = (10, 50, 100, 250, 500, 1000)

def enabled():
    return (os.environ.get('MESHCASE_STARS_ENABLED') == '1'
            and bool(os.environ.get('MESHCASE_BOT_TOKEN'))
            and bool(os.environ.get('MESHCASE_WEBHOOK_SECRET')))

def invoice(db, user, stars, bot_api):
    if not enabled():
        raise ValueError('Пополнение пока недоступно')
    if type(stars) is not int or stars not in PACKS:
        raise ValueError('Выберите пакет Stars')
    now = int(time.time())
    if db.execute('SELECT 1 FROM invoices WHERE tg_id=? AND created>?', (user['tg_id'], now-15)).fetchone():
        raise ValueError('Подождите 15 секунд перед новым счётом')
    payload = secrets.token_urlsafe(32)
    credit = stars * 11 // 10
    db.execute('INSERT INTO invoices(payload,tg_id,stars,credit,created) VALUES(?,?,?,?,?)', (payload,user['tg_id'],stars,credit,now))
    link = bot_api('createInvoiceLink', {'title':'Монеты MeshCase', 'description':f'{credit} монет · 1 Star = 1,1 монеты', 'payload':payload, 'provider_token':'', 'currency':'XTR', 'prices':[{'label':f'{credit} монет','amount':stars}]})
    db.commit()
    return {'url':link,'stars':stars,'coins':credit}

def valid(db, data, sender, checkout=False):
    row = db.execute('SELECT * FROM invoices WHERE payload=?', (data.get('invoice_payload'),)).fetchone()
    if not row or row['tg_id'] != sender or data.get('currency') != 'XTR' or type(data.get('total_amount')) is not int or row['stars'] != data['total_amount']:
        return None
    if checkout:
        u = db.execute('SELECT banned FROM tg_users WHERE tg_id=?',(sender,)).fetchone()
        if not enabled() or row['charge_id'] or row['created'] < time.time()-3600 or not u or u['banned']:
            return None
    return row

def settle(db, payment, sender):
    db.execute('BEGIN IMMEDIATE')
    row = valid(db,payment,sender)
    charge = payment.get('telegram_payment_charge_id')
    if not row or not isinstance(charge,str) or not charge or row['charge_id']:
        db.rollback()
        return False
    if db.execute('SELECT 1 FROM invoices WHERE charge_id=?',(charge,)).fetchone():
        db.rollback()
        return False
    db.execute('UPDATE invoices SET charge_id=? WHERE payload=?',(charge,row['payload']))
    db.execute('UPDATE tg_users SET balance=balance+? WHERE tg_id=?',(row['credit'],sender))
    db.execute('INSERT INTO balance_events(tg_id,delta,reason,created) VALUES(?,?,?,?)',(sender,row['credit'],f'Telegram Stars: {row["stars"]} ⭐',int(time.time())))
    db.commit()
    return True
