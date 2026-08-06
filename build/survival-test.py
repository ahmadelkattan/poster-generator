#!/usr/bin/env python3
"""The scenario from the feedback: edit a poster, move three elements by hand,
then cycle four backgrounds and three layouts. All three manual positions and
the photo must survive. Also checks that each transition is one undo step."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/Users/ahmadelkattan/Poster-Generator')

SCRIPT = """(() => {
  const out = {};
  localStorage.clear();
  applyTemplate('speaker');

  /* a photo the user deliberately added */
  const c = document.createElement('canvas'); c.width = 400; c.height = 500;
  const x = c.getContext('2d'); x.fillStyle = '#c9a184'; x.fillRect(0,0,400,500);
  x.fillStyle = '#2f3a44'; x.fillRect(50,300,300,200);
  DOC.elements.find(e => e.role === 'photo').src = c.toDataURL('image/png');

  /* real edits */
  DOC.elements.find(e => e.role === 'title').html = 'ندوة الثلاثاء';
  DOC.elements.find(e => e.role === 'desc').html = 'وصف من تحرير العضو';
  render(); snap();

  /* three elements placed by hand, exactly as a drag would */
  const placed = ['kicker', 'title', 'name'].map(r => {
    const e = DOC.elements.find(z => z.role === r);
    e.x = r2(e.x - 2.5); e.y = r2(e.y + 3.5);
    markDirty(e, ['x', 'y']);
    return { role: r, x: e.x, y: e.y };
  });
  /* and one resized by hand */
  const nm = DOC.elements.find(z => z.role === 'name');
  nm.size = 64; markDirty(nm, ['size']);
  render(); snap();
  out.placed = placed; out.sizeSet = nm.size;
  const base = checkIssues();
  out.baselineAfterHandPlacement = { overflow: base.over, collisions: base.collide };

  /* PHASE 1 — the curious user tries four backgrounds (the P0-3 complaint).
     The layout is untouched, so nothing should move or clash at all. */
  ['arch', 'skyline', 'zellige', 'minimal'].forEach(b => setBackground(b, DOC.bgOpts));
  const afterBg = ['kicker', 'title', 'name'].map(r => {
    const e = DOC.elements.find(z => z.role === r); return { role: r, x: e.x, y: e.y }; });
  const bgIss = checkIssues();
  out.afterBackgroundsOnly = {
    positionsSurvived: JSON.stringify(afterBg) === JSON.stringify(placed),
    overflow: bgIss.over, collisions: bgIss.collide,
    photo: !!DOC.elements.find(e => e.role === 'photo' && e.src)
  };

  /* PHASE 2 — then three layout changes, through the real click path so each
     one lands in history the way a click would */
  ['boxed-meta', 'two-col', 'classic'].forEach(l => applyLayout(l));

  const after = ['kicker', 'title', 'name'].map(r => {
    const e = DOC.elements.find(z => z.role === r);
    return { role: r, x: e.x, y: e.y };
  });
  const photo = DOC.elements.find(e => e.role === 'photo');
  out.after = after;
  out.positionsSurvived = JSON.stringify(after) === JSON.stringify(placed);
  out.sizeSurvived = DOC.elements.find(z => z.role === 'name').size === 64;
  out.photoSurvived = !!(photo && photo.src);
  out.titleSurvived = htmlToText(DOC.elements.find(e => e.role === 'title').html) === 'ندوة الثلاثاء';
  out.descSurvived  = htmlToText(DOC.elements.find(e => e.role === 'desc').html) === 'وصف من تحرير العضو';
  const iss = checkIssues();
  out.overflow = iss.over; out.collisions = iss.collide;

  /* every transition must be exactly one undo step */
  const sig = () => DOC.bg + '/' + DOC.layout;
  const seen = [sig()];
  for (let i = 0; i < 8; i++) { undo(); seen.push(sig()); }
  out.undoTrail = seen;
  out.undoReachedStart = seen[seen.length - 1] === 'wave/side-photo';
  out.undoDistinctStates = [...new Set(seen)].length;
  return out;
})()"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(locale='ar', viewport={'width': 1600, 'height': 1000})
    ctx.set_offline(True)
    pg = ctx.new_page()
    pg.add_init_script("try{localStorage.clear();localStorage.setItem('mirsam.seen','1')}catch(e){}")
    pg.goto((ROOT / 'index.html').as_uri())
    pg.wait_for_timeout(1800)
    print(json.dumps(pg.evaluate(SCRIPT), ensure_ascii=False, indent=1))
    b.close()
