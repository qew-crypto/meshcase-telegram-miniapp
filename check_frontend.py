from pathlib import Path
import quickjs
js=Path('miniapp.js').read_text()
ctx=quickjs.Context()
ctx.eval('new Function('+__import__('json').dumps(js)+')')
print('JavaScript syntax: OK')
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        browser.close()
        print('Browser launch: OK')
except Exception as exc:
    print('Browser unavailable:',str(exc)[:1800])
