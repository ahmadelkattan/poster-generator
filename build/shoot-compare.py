#!/usr/bin/env python3
"""Before/after evidence shots: content step panel + whole app."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/Users/ahmadelkattan/Poster-Generator')
OUT = ROOT / 'build' / 'shots'
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # ── BEFORE (needs network for Google Fonts) ──────────────────────────
    ctx = browser.new_context(locale='ar', viewport={'width': 1600, 'height': 1000})
    page = ctx.new_page()
    page.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    page.goto('http://localhost:8123/build/index-before.html')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)
    page.click('.step[data-step="3"]')
    page.wait_for_timeout(400)
    page.locator('#left').screenshot(path=str(OUT / 'content-before.png'))
    page.screenshot(path=str(OUT / 'app-before.png'))
    ctx.close()

    # ── AFTER (offline, file://) ─────────────────────────────────────────
    ctx = browser.new_context(locale='ar', viewport={'width': 1600, 'height': 1000})
    ctx.set_offline(True)
    page = ctx.new_page()
    page.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    page.goto((ROOT / 'index.html').as_uri() + '?step=3')
    page.wait_for_load_state('load')
    page.wait_for_timeout(1500)
    page.locator('#left').screenshot(path=str(OUT / 'content-after.png'))
    page.screenshot(path=str(OUT / 'app-after.png'))
    ctx.close()
    browser.close()

# side-by-side composite (after on the right, before on the left)
from PIL import Image, ImageDraw
a = Image.open(OUT / 'content-before.png')
b = Image.open(OUT / 'content-after.png')
h = max(a.height, b.height)
gap = 40
canvas = Image.new('RGB', (a.width + b.width + gap * 3, h + 90), '#EDEAE3')
d = ImageDraw.Draw(canvas)
canvas.paste(a, (gap, 70))
canvas.paste(b, (a.width + gap * 2, 70))
d.text((gap + a.width // 2 - 30, 25), 'BEFORE', fill='#8C2914')
d.text((a.width + gap * 2 + b.width // 2 - 25, 25), 'AFTER', fill='#0A4530')
canvas.save(OUT / 'content-step-compare.png')
print('saved', OUT / 'content-step-compare.png', canvas.size)
