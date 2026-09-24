from pathlib import Path
root=Path('.')
css='''/* Two synchronized columns only in the case-opening screen, not on the homepage. */
body.page-case .roll-stack{display:grid;gap:14px;max-width:980px;margin:16px auto}
body.page-case .roll-group{display:grid;gap:8px;min-width:0;padding:10px;border:1px solid #3e3150;border-radius:16px;background:linear-gradient(145deg,#211a2c,#15121d)}
body.page-case .roll-group h4{margin:0 4px 3px;color:#d9c8e8;font-size:12px;text-align:left}
body.page-case .roll-group .roll-lane{min-width:0}
@media(min-width:681px){body.page-case .roll-stack:has(.roll-group:nth-child(2)){grid-template-columns:repeat(2,minmax(0,1fr));align-items:start}body.page-case .roll-stack:has(.roll-group:nth-child(2)) .roll-count-note{grid-column:1/-1}}
@media(max-width:680px){body.page-case .roll-group{padding:8px}body.page-case .roll-group h4{font-size:11px}}
'''
(root/'bulk-layout.css').write_text(css)
count=0
for p in root.glob('case-*.html'):
    s=p.read_text()
    if "group.className='roll-group';" not in s: continue
    s=s.replace("group.className='roll-group';", "group.className='roll-group';", 1)
    if 'bulk-layout.css' not in s:
        s=s.replace('</head>', '<link rel="stylesheet" href="bulk-layout.css">\n</head>', 1)
    p.write_text(s)
    count+=1
print('updated',count,'case detail pages; home page untouched')
