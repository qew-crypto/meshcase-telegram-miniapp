from test_game import Games
import game_backend as g
from concurrent.futures import ThreadPoolExecutor

class Bulk(Games):
    def test_allowed_counts(self):
        for kind,counts in [('server',[1,2,3,5,10]),('allin',[10,25,50,100])]:
            c=next(c for c in g.CASES.values() if c['type']==kind)
            for count in counts:
                before=len(self.call('inventory',None)['inventory'])
                r=self.call('open',self.request(case_id=c['id'],count=count))
                self.assertEqual(len(r['prizes']),count)
                self.assertEqual(len(self.call('inventory',None)['inventory']),before+count)
    def test_invalid_counts(self):
        for c in [next(c for c in g.CASES.values() if c['type']==t) for t in ('server','allin')]:
            for count in [0,-1,True,'10',1.5,101,4]+([1,2,3,5] if c['type']=='allin' else [25,50,100]):
                with self.assertRaises(ValueError):self.call('open',self.request(case_id=c['id'],count=count))
        self.assertEqual(self.call('inventory',None)['inventory'],[])
    def test_bulk_retry_and_cost(self):
        c=next(c for c in g.CASES.values() if c['type']=='allin')
        data=self.request(case_id=c['id'],count=100)
        with ThreadPoolExecutor(4) as pool:r=list(pool.map(lambda _:self.call('open',data),range(4)))
        self.assertTrue(all(x==r[0] for x in r))
        self.assertEqual(r[0]['balance'],100000-c['price']*100)
        self.assertEqual(len(self.call('inventory',None)['inventory']),100)
    def test_insufficient_bulk(self):
        import server
        c=next(c for c in g.CASES.values() if c['type']=='allin')
        with server.connect() as db:db.execute('UPDATE tg_users SET balance=? WHERE tg_id=1',(c['price']*10-1,))
        with self.assertRaises(ValueError):self.call('open',self.request(case_id=c['id'],count=10))
        self.assertEqual(self.call('inventory',None)['inventory'],[])
