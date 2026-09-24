import concurrent.futures
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

import server

class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir='.',prefix='test-db-')
        server.DB=Path(cls.tmp.name)/'test.sqlite3'
        os.environ['MESHCASE_BOT_TOKEN']='test-only-not-a-real-token'
        os.environ['MESHCASE_ADMIN_IDS']='9001'
        os.environ['MESHCASE_PUBLIC_ORIGIN']='https://meshcase.test'
        server.bootstrap()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.port=cls.http.server_address[1]
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.cookies={}
        for uid in (9001,9002,9003,9004):cls.cookies[uid]=cls.auth(uid)
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
    @classmethod
    def request(cls,path,data=None,uid=9001,origin='https://meshcase.test'):
        req=urllib.request.Request('http://127.0.0.1:'+str(cls.port)+path,data=None if data is None else json.dumps(data).encode(),headers={'Origin':origin,'Cookie':cls.cookies.get(uid,''),'Content-Type':'application/json'})
        try:r=urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:r=e
        body=r.read()
        return r.status,json.loads(body) if r.headers.get_content_type()=='application/json' else body,r.headers
    @classmethod
    def auth(cls,uid):
        d={'auth_date':str(int(time.time())),'user':json.dumps({'id':uid,'username':'user'+str(uid),'first_name':'Игрок <script>'})}
        secret=hmac.new(b'WebAppData',os.environ['MESHCASE_BOT_TOKEN'].encode(),hashlib.sha256).digest()
        d['hash']=hmac.new(secret,'\n'.join(k+'='+v for k,v in sorted(d.items())).encode(),hashlib.sha256).hexdigest()
        status,_,headers=cls.request('/api/tg/auth',{'initData':urllib.parse.urlencode(d)},uid=0)
        assert status==200
        return headers['Set-Cookie'].split(';')[0]
    def post(self,path,data,uid=9001,status=200):
        code,j,_=self.request('/api/tg/'+path,data,uid);self.assertEqual(code,status,j);return j
    def test_01_roles_and_origin(self):
        self.assertTrue(self.request('/api/tg/me')[1]['user']['is_admin'])
        self.assertFalse(self.request('/api/tg/me',uid=9002)[1]['user']['is_admin'])
        self.assertEqual(self.request('/api/tg/admin',uid=9002)[0],403)
        self.assertEqual(self.request('/api/tg/admin',uid=0)[0],401)
        self.assertEqual(self.request('/api/tg/admin/ban',{'tg_id':9002,'banned':True,'reason':'test'},origin='https://evil.test')[0],403)
        self.post('auth',{'initData':'user=bad&hash=bad'},status=400)
    def test_02_balance_and_bans(self):
        self.post('admin/balance',{'tg_id':9002,'delta':100,'reason':'Начисление'})
        self.post('admin/balance',{'tg_id':9002,'delta':-30,'reason':'Списание'})
        self.assertEqual(self.request('/api/tg/me',uid=9002)[1]['user']['balance'],70)
        self.post('admin/balance',{'tg_id':9002,'delta':-71,'reason':'Списание'},status=400)
        self.post('admin/balance',{'tg_id':9002,'delta':99,'reason':'Обход'},uid=9002,status=403)
        self.post('admin/balance',{'tg_id':9002,'delta':True,'reason':'Обход'},status=400)
        self.post('admin/ban',{'tg_id':9001,'banned':True,'reason':'Самобан'},status=400)
        self.post('admin/ban',{'tg_id':9002,'banned':True,'reason':'Проверка бана'})
        self.post('tickets',{'body':'Заблокированный'},uid=9002,status=403)
        self.post('redeem',{'code':'TEST'},uid=9002,status=403)
        self.cookies[9002]=self.auth(9002)
        self.post('tickets',{'body':'Новая сессия'},uid=9002,status=403)
        self.post('admin/ban',{'tg_id':9002,'banned':False})
        self.assertFalse(self.request('/api/tg/me',uid=9002)[1]['user']['banned'])
    def test_03_promos_concurrent(self):
        self.post('admin/promo',{'code':'RACE','amount':20,'limit':1,'expires':0})
        def redeem(uid):return self.request('/api/tg/redeem',{'code':'RACE'},uid)[0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(redeem,[9003,9004]))
        self.assertEqual(sorted(result),[200,400])
        with server.connect() as db:
            winner=db.execute('SELECT tg_id FROM promo_uses WHERE code="RACE"').fetchone()[0]
            self.assertEqual(db.execute('SELECT count(*) FROM promo_uses WHERE code="RACE"').fetchone()[0],1)
        self.post('redeem',{'code':'RACE'},uid=winner,status=400)
        self.post('admin/promo',{'code':'DISABLED','amount':20,'limit':5,'expires':0})
        self.post('admin/toggle',{'code':'DISABLED','active':False})
        self.post('redeem',{'code':'DISABLED'},uid=9002,status=400)
        self.post('admin/toggle',{'code':'DISABLED','active':True})
        self.post('redeem',{'code':'DISABLED'},uid=9002)
        self.post('admin/promo',{'code':'PAST','amount':20,'limit':1,'expires':1},status=400)
    def test_04_support(self):
        self.post('tickets',{'body':'Помогите с аккаунтом'},uid=9002)
        ticket=self.request('/api/tg/tickets',uid=9002)[1]['tickets'][0]['id']
        self.post('tickets/message',{'id':ticket,'body':'Попытка чужого доступа'},uid=9003,status=404)
        self.post('tickets/status',{'id':ticket,'status':'closed'},uid=9003,status=404)
        self.post('admin/reply',{'id':ticket,'answer':'Здравствуйте!'},uid=9002,status=403)
        self.post('admin/reply',{'id':ticket,'answer':'Здравствуйте!'})
        self.post('tickets/message',{'id':ticket,'body':'Спасибо'},uid=9002)
        messages=self.request('/api/tg/tickets',uid=9002)[1]['tickets'][0]['messages']
        self.assertEqual([m['body'] for m in messages],['Помогите с аккаунтом','Здравствуйте!','Спасибо'])
        self.assertEqual([m['staff'] for m in messages],[0,1,0])
        self.post('tickets/status',{'id':ticket,'status':'closed'})
        self.post('tickets/message',{'id':ticket,'body':'Закрыто'},uid=9002,status=400)
        self.post('tickets/status',{'id':ticket,'status':'open'},uid=9002)
    def test_05_audit_history_disabled_payments(self):
        data=self.request('/api/tg/admin?q=9002')[1]
        self.assertEqual(len(data['users']),1)
        self.assertTrue(any(x['action']=='balance' for x in data['audit']))
        self.assertGreaterEqual(len(self.request('/api/tg/history',uid=9002)[1]['events']),2)
        self.post('invoice',{'stars':100},uid=9002,status=503)
    def test_06_static(self):
        status,body,headers=self.request('/')
        self.assertEqual(status,200)
        self.assertIn(b'miniapp.js',body)
        self.assertNotIn('X-Frame-Options',headers)
        self.assertIn('https://web.telegram.org',headers['Content-Security-Policy'])
        for path in ['/server.py','/tg_backend.py','/.env','/meshcase.sqlite3']:
            self.assertEqual(self.request(path)[0],404)
        for c in json.loads(Path('cases.json').read_text()):
            self.assertTrue(Path('assets/'+c.get('image','case-'+c['id']+'.png')).exists(),c['id'])
            self.assertAlmostEqual(sum(drop[1] for drop in c['drops']),100,places=2)

if __name__=='__main__':unittest.main(verbosity=2)
