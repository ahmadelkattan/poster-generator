#!/usr/bin/env python3
"""Offline export verification for Mirsam.

Loads index.html from file:// in a FULLY OFFLINE browser context, drives the
real export modal (quality segment + PNG/JPG buttons), captures the actual
downloaded files, and checks each one: correct pixel size, non-blank, has
both dark and light regions (i.e. content rendered), reasonable byte size.
Also re-runs the full transition cycle test and the UI contrast audit in the
same offline session.
"""
import json, sys, statistics
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/Users/ahmadelkattan/Poster-Generator')
OUT = ROOT / 'build' / 'exports'
OUT.mkdir(parents=True, exist_ok=True)

results = {"exports": [], "cycle": None, "contrast": None, "netRequests": []}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(locale='ar', viewport={'width': 1600, 'height': 1000},
                              accept_downloads=True)
    ctx.set_offline(True)                       # no network, full stop
    page = ctx.new_page()
    page.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    netlog = []
    page.on('request', lambda r: netlog.append(r.url) if r.url.startswith(('http://', 'https://')) else None)

    page.goto((ROOT / 'index.html').as_uri())
    page.wait_for_load_state('load')
    page.evaluate("document.fonts.ready.then(()=>1)")
    page.wait_for_timeout(1200)

    # sanity: app booted, fonts embedded, h2c present
    boot = page.evaluate("({h2c: typeof window.html2canvas, els: DOC.elements.length, "
                         "fonts: [...document.fonts].filter(f=>f.status==='loaded').length})")
    results['boot'] = boot

    # ── real-path exports: ×1 ×2 ×3 PNG + ×2 JPG ─────────────────────────
    for scale, fmt in [(1, 'png'), (2, 'png'), (3, 'png'), (2, 'jpg')]:
        page.evaluate("exportModal()")
        page.click(f"[data-seg='exq'] button[data-v='{scale}']")
        with page.expect_download(timeout=90000) as dl:
            page.click('#ePng' if fmt == 'png' else '#eJpg')
        d = dl.value
        dest = OUT / f"poster-x{scale}.{fmt}"
        d.save_as(dest)
        results['exports'].append({"file": str(dest), "scale": scale, "fmt": fmt,
                                   "bytes": dest.stat().st_size})
        page.wait_for_timeout(300)

    # ── full transition cycle in the same offline session ────────────────
    page.add_script_tag(path=str(ROOT / 'build' / 'cycle-test.js'))
    results['cycle'] = page.evaluate("cycleTest({shuffle: 300})")

    # ── UI contrast audit over computed styles ────────────────────────────
    page.evaluate("applyTemplate('lecture'); goStep(3); buildInspector(); buildLayers();")
    page.wait_for_timeout(300)
    results['contrast'] = page.evaluate("""
(() => {
  const toRGB = s => { const m = s.match(/rgba?\\(([\\d.]+),\\s*([\\d.]+),\\s*([\\d.]+)(?:,\\s*([\\d.]+))?\\)/);
    return m ? [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]] : null; };
  const lum2 = ([r,g,b]) => { const f = v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055,2.4); };
    return .2126*f(r)+.7152*f(g)+.0722*f(b); };
  const ratio = (a,b) => { const l1=lum2(a), l2=lum2(b); return (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05); };
  const bgOf = el => { let n = el;
    while (n && n !== document.documentElement) {
      const c = toRGB(getComputedStyle(n).backgroundColor);
      if (c && c[3] > .9) return c;
      n = n.parentElement; }
    return [250,248,244,1]; };
  const SELS = [
    ['body base', 'body'], ['section header', '.sec-t'], ['field label', '.fld .lbl > span:nth-child(2)'],
    ['hint text', '.hint'], ['button', '.btn:not(.pri):not(.ghost)'], ['primary button', '.btn.pri'],
    ['step label (on)', '.step.on b'], ['step label (off)', '.step:not(.on) b'], ['step number (on)', '.step.on i'],
    ['tab (on)', '.tab.on'], ['tab (off)', '.tab:not(.on)'], ['chip', '.chip'],
    ['card caption', '.card .cap'], ['zoom value', '#zoomval'], ['zoom button', '#zoombar button'],
    ['switch label', '.switch span'], ['fit chip ok', '.fitdot.ok'], ['field badge', '.fbadge'],
    ['group heading', '.grp h5'], ['textarea text', '#pane3 textarea'], ['topbar ghost button', '.btn.ghost span'],
    ['layer name', '.layeritem .nm'], ['layer type badge', '.layeritem .rl'], ['empty-state text', '.empty'],
  ];
  const rows = [];
  for (const [name, sel] of SELS) {
    const el = document.querySelector(sel);
    if (!el) { rows.push({name, sel, missing: true}); continue; }
    const cs = getComputedStyle(el);
    const fg = toRGB(cs.color), bg = bgOf(el);
    const px = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
    const large = px >= 24 || (px >= 18.66 && bold);
    rows.push({name, px, bold, large, ratio: Math.round(ratio(fg, bg)*100)/100,
               fg: cs.color, bg: `rgb(${bg.slice(0,3).join(',')})`});
  }
  const worst = rows.filter(r=>!r.missing).sort((a,b)=>a.ratio-b.ratio)[0];
  const minPx = Math.min(...rows.filter(r=>!r.missing).map(r=>r.px));
  return {rows, worst, minPx};
})()""")

    results['netRequests'] = netlog
    # inspect exported files for blankness + size
    browser.close()

# pixel checks with PIL
from PIL import Image
for ex in results['exports']:
    im = Image.open(ex['file']).convert('L')
    w, h = im.size
    px = list(im.resize((80, 100)).getdata())
    ex['size'] = f"{w}x{h}"
    ex['minLum'] = min(px); ex['maxLum'] = max(px)
    ex['stdev'] = round(statistics.pstdev(px), 1)
    ex['verdict'] = 'OK' if (ex['maxLum'] - ex['minLum'] > 100 and ex['stdev'] > 20 and ex['bytes'] > 100000) else 'SUSPECT'

print(json.dumps(results, ensure_ascii=False, indent=1))
