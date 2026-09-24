from test_game import Games
from concurrent.futures import ThreadPoolExecutor

class BulkSales(Games):
    def prizes(self):
        import game_backend as g
        c=next(c for c in g.CASES.values() if c['type']!='allin')
        return self.call('open',self.request(case_id=c['id'],count=3))
    def test_batch_sale_and_retry(self):
        r=self.prizes();ids=[x['id'] for x in r['prizes']];data=self.request(inventory_ids=ids)
        with ThreadPoolExecutor(3) as pool: results=list(pool.map(lambda _:self.call('sell_all',data),range(3)))
        self.assertTrue(all(x==results[0] for x in results))
        self.assertEqual(results[0]['balance'],r['balance']+sum(x['item']['value'] for x in r['prizes']))
        self.assertEqual(self.call('inventory',None)['inventory'],[])
    def test_atomic_ownership_stale_and_validation(self):
        r=self.prizes();ids=[x['id'] for x in r['prizes']]
        for bad in ([],[True],[ids[0],ids[0]],ids+[999999]):
            with self.assertRaises(ValueError):self.call('sell_all',self.request(inventory_ids=bad))
        with self.assertRaises(ValueError):self.call('sell_all',self.request(inventory_ids=ids),2)
        self.assertEqual(len(self.call('inventory',None)['inventory']),3)
        self.call('sell',self.request(inventory_id=ids[0]))
        with self.assertRaises(ValueError):self.call('sell_all',self.request(inventory_ids=ids))
        self.assertEqual(len(self.call('inventory',None)['inventory']),2)
    def test_snapshot_does_not_sell_new_items(self):
        a=self.prizes();b=self.prizes()
        self.call('sell_all',self.request(inventory_ids=[x['id'] for x in a['prizes']]))
        self.assertEqual({x['id'] for x in self.call('inventory',None)['inventory']},{x['id'] for x in b['prizes']})
