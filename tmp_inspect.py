from pathlib import Path
import json,re
s=Path('index.html').read_text()
for k,nextk in [('const products=','const cases='),('const cases=',';\nlet state')]:
 x=s.split(k,1)[1].split(nextk,1)[0]
 d=json.loads(x.rstrip(';\n'))
 print(k,len(d))
 if k.endswith('cases='):
  for c in d: print(c['id'],c['name'],c['price'],c.get('type'),c.get('minCount'),len(c['drops']),sum(w for _,w in c['drops']))
