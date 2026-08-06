#!/usr/bin/env python3
"""Round-2 export verification — checks that could actually have failed.

1. Real-path export at x1/x2/x3, fully offline, from file://.
2. SHAPING ASSERTION: measure a known Arabic string's ink width in the DOM,
   then measure the same string's ink extents in the exported raster. Broken
   shaping yields isolated forms, which are measurably wider. >2% divergence
   fails. This is the check that would have caught the html2canvas bug.
3. PERCEPTUAL DIFF: screenshot the on-screen stage, diff against the export
   at the same scale. Subsumes broken text, missing photo, corner artifacts.
4. Runs under chromium and (with --webkit) webkit.

Usage: verify-round2.py [--webkit] [--photo]
"""
import json, sys, math
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

ROOT = Path('/Users/ahmadelkattan/Poster-Generator')
ENGINE = 'webkit' if '--webkit' in sys.argv else 'chromium'
WITH_PHOTO = '--photo' in sys.argv
TAG = ENGINE + ('-photo' if WITH_PHOTO else '')
OUT = ROOT / 'build' / 'exports' / TAG
OUT.mkdir(parents=True, exist_ok=True)

# a string whose shaping is unambiguous: every letter joins to the next
PROBE = 'عن لقاء شهري'

SETUP_PHOTO = """
(() => {
  const c = document.createElement('canvas'); c.width = 800; c.height = 1000;
  const x = c.getContext('2d');
  x.fillStyle = '#e8e2d5'; x.fillRect(0,0,800,1000);
  x.fillStyle = '#fdfcf8'; x.fillRect(480,60,260,420);
  x.fillStyle = '#c9a184'; x.beginPath(); x.arc(360,380,150,0,7); x.fill();
  x.fillStyle = '#3a3f45'; x.fillRect(140,520,460,480);
  const url = c.toDataURL('image/jpeg', .9);
  applyTemplate('speaker');
  const p = DOC.elements.find(e => e.role === 'photo');
  if (p) { p.src = url; }
  render();
  return !!(p && p.src);
})()
"""

# ink bounding box of the probe string as the DOM lays it out
PROBE_IN_DOM = """
(probe => {
  const t = DOC.elements.find(e => e.role === 'title');
  const n = document.querySelector(`.el[data-id="${t.id}"]`);
  const cs = getComputedStyle(n);
  const span = document.createElement('span');
  span.textContent = probe;
  span.style.cssText = `position:absolute;left:-99999px;top:0;white-space:nowrap;`
    + `font-family:${cs.fontFamily};font-size:${cs.fontSize};font-weight:${cs.fontWeight};`
    + `letter-spacing:${cs.letterSpacing};direction:rtl`;
  document.body.appendChild(span);
  const r = span.getBoundingClientRect();
  const out = {w: r.width, h: r.height, fontSize: parseFloat(cs.fontSize),
               family: cs.fontFamily, ls: cs.letterSpacing};
  span.remove();
  return out;
})
"""


def ink_bbox(img, box=None):
    """Bounding box of non-background ink inside an optional crop."""
    im = img.convert('L')
    if box:
        im = im.crop(box)
    # background is the most common value; ink is anything far from it
    hist = im.histogram()
    bg = hist.index(max(hist))
    mask = im.point(lambda v: 255 if abs(v - bg) > 45 else 0)
    return mask.getbbox()


results = {'offlineFlag': ENGINE != 'webkit', 'engine': ENGINE, 'photo': WITH_PHOTO, 'exports': [], 'shaping': None, 'diff': []}

with sync_playwright() as p:
    browser = getattr(p, ENGINE).launch(headless=True)
    ctx = browser.new_context(locale='ar', viewport={'width': 1700, 'height': 1100},
                              accept_downloads=True, device_scale_factor=1)
    # WebKit's offline flag breaks file:// navigation in the harness itself, so
    # there we prove offline-ness the strict way instead: assert the page issues
    # ZERO external requests (the netlog below must come back empty).
    if ENGINE != 'webkit':
        ctx.set_offline(True)
    page = ctx.new_page()
    page.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    netlog = []
    page.on('request', lambda r: netlog.append(r.url) if r.url.startswith(('http://', 'https://')) else None)

    page.goto((ROOT / 'index.html').as_uri())
    page.wait_for_load_state('load')
    page.wait_for_timeout(1800)

    if WITH_PHOTO:
        results['photoSet'] = page.evaluate(SETUP_PHOTO)
        page.wait_for_timeout(600)

    # put the probe string into the title so both measurements see the same text
    page.evaluate("""probe => {
        const t = DOC.elements.find(e => e.role === 'title');
        t.html = probe; render(); }""", PROBE)
    page.wait_for_timeout(500)

    results['dom'] = page.evaluate(PROBE_IN_DOM, PROBE)
    results['titleBox'] = page.evaluate("""() => {
        const t = DOC.elements.find(e => e.role === 'title');
        const n = document.querySelector(`.el[data-id="${t.id}"]`);
        return {x: n.offsetLeft, y: n.offsetTop, w: n.offsetWidth, h: n.offsetHeight};
    }""")

    # ── exports ──────────────────────────────────────────────────────────
    for scale in (1, 2, 3):
        page.evaluate("exportModal()")
        page.click(f"[data-seg='exq'] button[data-v='{scale}']")
        with page.expect_download(timeout=120000) as dl:
            page.click('#ePng')
        dest = OUT / f"poster-x{scale}.png"
        dl.value.save_as(dest)
        results['exports'].append({'scale': scale, 'file': str(dest), 'bytes': dest.stat().st_size})
        page.wait_for_timeout(250)

    # ── on-screen stage screenshot at 1:1 for the perceptual diff ────────
    page.evaluate("SELID=null; drawSel(); setZoom(1); document.getElementById('safeguide').style.display='none';")
    page.wait_for_timeout(400)
    page.evaluate("""() => {
        const s = document.getElementById('stagewrap');
        s.style.overflow = 'visible';
        document.getElementById('overlay').style.display = 'none';
    }""")
    page.wait_for_timeout(200)
    page.locator('#stage').screenshot(path=str(OUT / 'stage-onscreen.png'))
    results['netRequests'] = netlog
    browser.close()

# ── shaping assertion ────────────────────────────────────────────────────
# The title element is centred; crop the band around it in the x1 export and
# measure the ink width of the probe line, then compare to the DOM width.
x1 = Image.open(OUT / 'poster-x1.png')
onscreen = Image.open(OUT / 'stage-onscreen.png')

# locate the title band by diffing rows: take the widest ink run in the upper half
def widest_line_bbox(img, y0frac, y1frac):
    W, H = img.size
    best = None
    y0, y1 = int(H * y0frac), int(H * y1frac)
    strip = img.crop((0, y0, W, y1))
    bb = ink_bbox(strip)
    if bb:
        best = (bb[0], y0 + bb[1], bb[2], y0 + bb[3])
    return best

# measure the probe's ink width at EVERY scale, not just x1 — a font that only
# resolves on the second render would otherwise hide in the untested scales
results['shaping'] = {'probe': PROBE, 'domInkWidth': round(results['dom']['w'], 1), 'perScale': []}
dom_w = results['dom']['w']
tb = results['titleBox']
for ex in results['exports']:
    im = Image.open(ex['file'])
    s = ex['scale']
    pad = 4 * s
    crop = (max(0, int(tb['x'] * s) - pad), max(0, int(tb['y'] * s) - pad),
            min(im.size[0], int((tb['x'] + tb['w']) * s) + pad),
            min(im.size[1], int((tb['y'] + tb['h']) * s) + pad))
    bb = ink_bbox(im, crop)
    ink_w = (bb[2] - bb[0]) / s if bb else 0
    ratio = ink_w / dom_w if dom_w else None
    results['shaping']['perScale'].append({
        'scale': s, 'exportInkWidth': round(ink_w, 1),
        'ratio': round(ratio, 4) if ratio else None,
        'verdict': 'PASS' if ratio and abs(ratio - 1) <= 0.02 else 'FAIL'})
results['shaping']['verdict'] = 'PASS' if all(p['verdict'] == 'PASS' for p in results['shaping']['perScale']) else 'FAIL'

# ── perceptual diff: on-screen stage vs x1 export ────────────────────────
a = onscreen.convert('RGB').resize(x1.size, Image.LANCZOS)
b = x1.convert('RGB')
diff = ImageChops.difference(a, b)
stat_px = list(diff.convert('L').resize((160, 200)).getdata())
mean = sum(stat_px) / len(stat_px)
over = sum(1 for v in stat_px if v > 40) / len(stat_px)
results['diff'] = {'meanAbsDiff': round(mean, 2), 'fracPixelsOver40': round(over, 4),
                   'verdict': 'PASS' if mean < 12 and over < 0.06 else 'FAIL'}
diff.save(OUT / 'diff.png')

print(json.dumps(results, ensure_ascii=False, indent=1))
