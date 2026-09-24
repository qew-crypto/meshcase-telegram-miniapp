import json
import os
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch
import server
import stars_payments as stars

class Payments(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
        self.db.executescript('CREATE TABLE tg_users(tg_id INTEGER PRIMARY KEY,balance INTEGER,banned INTEGER); INSERT INTO tg_users VALUES(1,0,0); CREATE TABLE invoices(payload TEXT PRIMARY KEY,tg_id INTEGER,stars INTEGER,credit INTEGER,created INTEGER,charge_id TEXT UNIQUE); CREATE TABLE balance_events(tg_id INTEGER,delta INTEGER,reason TEXT,created INTEGER);')
        self.env=patch.dict(os.environ,{'MESHCASE_STARS_ENABLED':'1','MESHCASE_BOT_TOKEN':'test','MESHCASE_WEBHOOK_SECRET':'test'})
        self.env.start()
    def tearDown(self):self.db.close();self.env.stop()
    def make(self):
        calls=[]
        def bot(method,data):calls.append((method,data));return 'https://t.me/testinvoice'
        result=stars.invoice(self.db,{'tg_id':1},10,bot)
        self.assertEqual(result['coins'],11)
        self.assertEqual(calls[0][1]['currency'],'XTR')
        return {'invoice_payload':calls[0][1]['payload'],'currency':'XTR','total_amount':10,'telegram_payment_charge_id':'charge1'}
    def test_credit_duplicate(self):
        p=self.make();self.assertTrue(stars.valid(self.db,p,1,True));self.assertTrue(stars.settle(self.db,p,1));self.assertFalse(stars.settle(self.db,p,1))
        self.assertEqual(self.db.execute('SELECT balance FROM tg_users').fetchone()[0],11)
        self.assertEqual(self.db.execute('SELECT count(*) FROM balance_events').fetchone()[0],1)
    def test_tampering(self):
        p=self.make()
        for key,val in [('total_amount',20),('currency','USD'),('invoice_payload','unknown'),('telegram_payment_charge_id','')]:
            self.assertFalse(stars.settle(self.db,{**p,key:val},1))
        self.assertFalse(stars.settle(self.db,p,2));self.assertTrue(stars.settle(self.db,p,1))
    def test_ban_and_gate(self):
        p=self.make();self.db.execute('UPDATE tg_users SET banned=1');self.db.commit()
        self.assertFalse(stars.valid(self.db,p,1,True))
        # A payment already accepted by Telegram must not be lost after a ban or a shutdown.
        os.environ['MESHCASE_STARS_ENABLED']='0'
        self.assertTrue(stars.settle(self.db,p,1))
    def test_bad_pack(self):
        for v in [1,True,10.0,100000,-10]:
            with self.assertRaises(ValueError):stars.invoice(self.db,{'tg_id':1},v,lambda *_:None)
    def test_catalog(self):
        items=json.loads(Path('items.js').read_text().split('=',1)[1].rstrip(';\n'));items={x['id']:x for x in items}
        for c in json.loads(Path('cases.json').read_text()):
            self.assertEqual(sum(round(p*1000) for _,p in c['drops']),100000)
            self.assertTrue(any(items[i]['value']>c['price'] for i,_ in c['drops']))
            for i,p in c['drops']:
                self.assertGreater(p,0);self.assertTrue(Path('assets',items[i]['img']).is_file())

if __name__=='__main__':unittest.main(verbosity=2)
