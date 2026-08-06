#!/usr/bin/env python3
"""iPad-viewport touch interaction test: select, drag, halo-resize, edit.
Uses CDP Input.dispatchTouchEvent so the app receives genuine touch-derived
pointer events (pointerType: touch), not mouse simulation."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/Users/ahmadelkattan/Poster-Generator')
OUT = ROOT / 'build' / 'shots'

def touch(cdp, kind, points):
    cdp.send('Input.dispatchTouchEvent', {
        'type': kind,
        'touchPoints': [{'x': x, 'y': y, 'radiusX': 11, 'radiusY': 11, 'force': .8, 'id': 1} for x, y in points]})

def drag(cdp, x1, y1, x2, y2, steps=14):
    touch(cdp, 'touchStart', [(x1, y1)])
    for i in range(1, steps + 1):
        touch(cdp, 'touchMove', [(x1 + (x2 - x1) * i / steps, y1 + (y2 - y1) * i / steps)])
        time.sleep(.02)
    touch(cdp, 'touchEnd', [])

res = {}
with sync_playwright() as p:
    ipad = p.devices['iPad Pro 11 landscape']
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(**ipad, locale='ar')
    ctx.set_offline(True)
    page = ctx.new_page()
    page.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    page.goto((ROOT / 'index.html').as_uri())
    page.wait_for_load_state('load')
    page.wait_for_timeout(1500)
    cdp = ctx.new_cdp_session(page)
    res['viewport'] = page.evaluate('({w: innerWidth, h: innerHeight, touch: navigator.maxTouchPoints})')

    def elBox(role):
        return page.evaluate(f"""(() => {{
          const e = DOC.elements.find(x => x.role === '{role}');
          const n = document.querySelector(`.el[data-id="${{e.id}}"]`);
          const r = n.getBoundingClientRect();
          return {{id: e.id, x: e.x, y: e.y, w: e.w, cx: r.left + r.width/2, cy: r.top + r.height/2,
                   left: r.left, right: r.right, top: r.top}};
        }})()""")

    # 1 · tap the title → selected?
    t = elBox('title')
    touch(cdp, 'touchStart', [(t['cx'], t['cy'])]); touch(cdp, 'touchEnd', [])
    page.wait_for_timeout(300)
    res['tapSelects'] = page.evaluate("selEl() && selEl().role")

    # 2 · touch-drag the title down-left by ~80,60 css px
    before = elBox('title')
    drag(cdp, before['cx'], before['cy'], before['cx'] - 80, before['cy'] + 60)
    page.wait_for_timeout(300)
    after = elBox('title')
    res['drag'] = {'before': [before['x'], before['y']], 'after': [after['x'], after['y']],
                   'moved': abs(after['x'] - before['x']) > 1 and abs(after['y'] - before['y']) > 1}

    # 3 · resize via the LEFT edge handle — deliberately 8px OUTSIDE the visible
    #     20px handle, inside the 44px halo (tests the invisible hit area)
    sel = page.evaluate("""(() => { const h = document.querySelector('#sel .h.e');
      const r = h.getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2}; })()""")
    wBefore = page.evaluate("selEl().w")
    drag(cdp, sel['x'] - 8, sel['y'], sel['x'] - 68, sel['y'])
    page.wait_for_timeout(300)
    wAfter = page.evaluate("selEl().w")
    res['haloResize'] = {'wBefore': wBefore, 'wAfter': wAfter, 'resized': abs(wAfter - wBefore) > 1}

    # 4 · double-tap → inline edit; type; escape
    t = elBox('title')
    touch(cdp, 'touchStart', [(t['cx'], t['cy'])]); touch(cdp, 'touchEnd', [])
    time.sleep(.09)
    touch(cdp, 'touchStart', [(t['cx'], t['cy'])]); touch(cdp, 'touchEnd', [])
    page.wait_for_timeout(400)
    res['dblTapEdits'] = page.evaluate("EDITING === true")
    if res['dblTapEdits']:
        page.keyboard.type(' تجربة')
        page.wait_for_timeout(200)
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        res['typed'] = page.evaluate("htmlToText(DOC.elements.find(x=>x.role==='title').html)")

    # 5 · mobile layout sanity: bottom tab bar visible? panes toggle?
    res['mobtabsVisible'] = page.evaluate("getComputedStyle(document.getElementById('mobtabs')).display")
    page.screenshot(path=str(OUT / 'ipad-touch.png'))
    browser.close()

print(json.dumps(res, ensure_ascii=False, indent=1))
