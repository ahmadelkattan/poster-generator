#!/usr/bin/env python3
"""WebKit (Safari engine) rendering check: content step, format step, inspector."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/Users/ahmadelkattan/Poster-Generator')
OUT = ROOT / 'build' / 'shots'

with sync_playwright() as p:
    browser = p.webkit.launch(headless=True)
    ctx = browser.new_context(locale='ar', viewport={'width': 1600, 'height': 1000})
    page = ctx.new_page()
    page.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    page.goto((ROOT / 'index.html').as_uri() + '?step=3&sel=title')
    page.wait_for_load_state('load')
    page.wait_for_timeout(2500)
    info = page.evaluate("({h2c: typeof window.html2canvas, els: DOC.elements.length,"
                         " fontsLoaded: [...document.fonts].filter(f=>f.status==='loaded').length,"
                         " errs: window.__errs || null})")
    page.screenshot(path=str(OUT / 'webkit-step3.png'))
    page.evaluate("goStep(4)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / 'webkit-step4.png'))
    # export smoke test in WebKit too
    exp = page.evaluate("""posterCanvas(1, groundColor()).then(c => ({w: c.width, h: c.height,
        cov: (() => { const x = c.getContext('2d'); const d = x.getImageData(0,0,c.width,c.height).data;
          let dark = 0, light = 0; for (let i = 0; i < d.length; i += 4000) { const l = d[i]+d[i+1]+d[i+2];
          if (l < 300) dark++; else light++; } return {dark, light}; })()}))""")
    print(json.dumps({'boot': info, 'export': exp}, ensure_ascii=False))
    browser.close()
