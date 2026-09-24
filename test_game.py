import os
import sqlite3
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
import server
import game_backend as g
import tg_backend

class Games(unittest.TestCase):
    def setUp(self):
        self.path=Path('test-game-'+uuid.uuid4().hex+'.sqlite3')
        self.previous=server.DB;server.DB=self.path
        with server.connect() as db:
            for uid in (1,2):db.execute('INSERT INTO tg_users VALUES(?,?,?, ?,?,?,?)',(uid,'test','Test',100000,0,0,''))
    def tearDown(self):
        server.DB=self.previous
        for suffix in ('','-wal','-shm'):
            Path(str(self.path)+suffix).unlink(missing_ok=True)
    def call(self, action, data, uid=1):
        with server.connect() as db:
            user=db.execute('SELECT * FROM tg_users WHERE tg_id=?',(uid,)).fetchone()
            return g.handle(db,user,'/api/tg/game/'+action,data)
    def request(self,**kw):return dict(request_id=uuid.uuid4().hex,**kw)
    def test_open_retry_concurrent(self):
        c=next(iter(g.CASES.values()));data=self.request(case_id=c['id'])
        with ThreadPoolExecutor(4) as pool:r=list(pool.map(lambda _:self.call('open',data),range(4)))
        self.assertTrue(all(x==r[0] for x in r));self.assertEqual(r[0]['balance'],100000-c['price'])
        self.assertEqual(len(self.call('inventory',None)['inventory']),1)
        with self.assertRaises(ValueError):self.call('sell',data)
    def test_sale_ownership_and_reuse(self):
        r=self.call('open',self.request(case_id=next(iter(g.CASES))))
        iid=r['prize']['id'];data=self.request(inventory_id=iid)
        with self.assertRaises(ValueError):self.call('sell',data,2)
        sold=self.call('sell',data);self.assertEqual(sold['balance'],r['balance']+r['prize']['item']['value'])
        self.assertEqual(self.call('sell',data),sold)
        with self.assertRaises(ValueError):self.call('sell',self.request(inventory_id=iid))
    def test_upgrade_success_failure(self):
        items=sorted((g.ITEMS[i] for i in g.TARGETS),key=lambda p:p['value']);source=items[0];target=next(p for p in items if p['value']>source['value'])
        for roll,success in [(0,True),(999999,False)]:
            with server.connect() as db:iid=g.grant(db,1,source)['id']
            data=self.request(inventory_id=iid,target_id=target['id'])
            with patch.object(g.secrets,'randbelow',return_value=roll):result=self.call('upgrade',data)
            self.assertEqual(result['success'],success);self.assertEqual(result['balance'],100000)
            self.assertEqual(self.call('upgrade',data),result)
            with self.assertRaises(ValueError):self.call('upgrade',self.request(inventory_id=iid,target_id=target['id']))
    def test_funds_ban_admin(self):
        with server.connect() as db:db.execute('UPDATE tg_users SET balance=0 WHERE tg_id=1')
        with self.assertRaises(ValueError):self.call('open',self.request(case_id=next(iter(g.CASES))))
        self.assertEqual(self.call('inventory',None)['inventory'],[])
        with server.connect() as db:db.execute('UPDATE tg_users SET banned=1 WHERE tg_id=1')
        with self.assertRaises(ValueError):self.call('open',self.request(case_id=next(iter(g.CASES))))
        with patch.dict(os.environ,{},clear=True):
            self.assertTrue(tg_backend.is_admin({'tg_id':1842295433}))
            self.assertFalse(tg_backend.is_admin({'tg_id':1}))
        with patch.dict(os.environ,{'MESHCASE_ADMIN_IDS':''}):self.assertFalse(tg_backend.is_admin({'tg_id':1842295433}))

if __name__=='__main__':unittest.main(verbosity=2)
