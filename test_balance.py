import json
import unittest
from pathlib import Path

class Balance(unittest.TestCase):
    def test_catalog_balance(self):
        items={x['id']:x for x in json.loads(Path('items.js').read_text().split('=',1)[1].rstrip(';\n'))}
        cases=json.loads(Path('cases.json').read_text())
        self.assertEqual(len(cases),25)
        for c in cases:
            with self.subTest(case=c['id']):
                values=[items[i]['value'] for i,p in c['drops']]
                self.assertEqual(sum(round(p*1000) for i,p in c['drops']),100000)
                self.assertEqual(c['metrics']['items'],len(values))
                ev=sum(items[i]['value']*p/100 for i,p in c['drops'])
                self.assertAlmostEqual(ev/c['price'],.92,delta=.001)
                self.assertEqual(min(values),c['metrics']['minValue'])
                self.assertEqual(max(values),c['metrics']['maxValue'])
                if c['type']=='allin':
                    limit=46 if c['id']=='allin-rw' else 30
                    self.assertTrue(all(v<=limit or v>=5000 for v in values))
                    top=sum(p for i,p in c['drops'] if items[i]['value']>=5000)
                    self.assertGreater(top,0);self.assertLess(top,1)
                else:
                    self.assertGreaterEqual(min(values),c['price']*.4)
                    self.assertTrue(all(p>=.01 for i,p in c['drops']))
    def test_button_before_loot(self):
        html=Path('miniapp.html').read_text()
        self.assertLess(html.index('id="openCase"'),html.index('id="detailLoot"'))

if __name__=='__main__':unittest.main(verbosity=2)
