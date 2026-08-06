/* Mirsam transition regression — run inside the live app page.
   Cycles template → background → layout transitions and asserts after every
   transition: zero out-of-canvas elements, zero collisions, zero orphans
   (every roled element belongs to the active layout), tray integrity.
   Usage:  await cycleTest()            — full sweep (~912 states)
           await cycleTest({quick:1})   — 2 templates only
           await cycleTest({shuffle:N}) — N extra random-order transitions */
async function cycleTest(opts) {
  opts = opts || {};
  const fails = [];
  const repro = [];
  const seq = [];
  let states = 0;
  const layoutRoles = id => new Set((LAYOUTS[id].els(DOC.safe) || []).map(s => s.role));
  const check = (where) => {
    states++;
    seq.push(where); if (seq.length > 6) seq.shift();
    const iss = checkIssues();
    const bad = [];
    if (iss.over) bad.push(`${iss.over} out-of-bounds`);
    if (iss.collide) bad.push(`${iss.collide} colliding`);
    const roles = layoutRoles(DOC.layout);
    DOC.elements.forEach(e => {
      if (e.role && !roles.has(e.role) && !e.pinned) bad.push(`orphan on canvas: ${e.role}`);
      if (e.orphan) bad.push(`legacy orphan flag: ${e.role}`);
    });
    if (!Array.isArray(DOC.tray)) bad.push('tray missing');
    if (bad.length) {
      fails.push(`${where} :: ${bad.join(' + ')}`);
      const cols = [...document.querySelectorAll('.el.colliding,.el.overflowing')]
        .map(n => { const e = DOC.elements.find(x => x.id === n.dataset.id); return e && (e.role || e.type); });
      repro.push({ where, tpl: DOC.template, bg: DOC.bg, lay: DOC.layout, fs: FITSCALE.s,
                   bad, roles: cols, seq: seq.slice() });
    }
  };
  const setBg = (bg) => setBackground(bg, DOC.bgOpts);   /* the real click path */
  const tpls = Object.keys(TEMPLATES).slice(0, opts.quick ? 2 : 99);
  const bgs = BG_ORDER.slice();
  const lays = Object.keys(LAYOUTS);
  if (opts.onlyShuffle) { /* random pass only, over ALL templates */ }
  else for (const tp of tpls) {
    applyTemplate(tp);
    check(`tpl:${tp}`);
    for (const bg of bgs) {
      setBg(bg);
      check(`tpl:${tp} bg:${bg}`);
      for (const ly of lays) {
        applyLayout(ly, true);
        check(`tpl:${tp} bg:${bg} lay:${ly}`);
      }
    }
    await new Promise(r => setTimeout(r, 0));
  }
  /* random-order pass: transitions in arbitrary interleaving */
  const rnd = a => a[Math.floor(Math.random() * a.length)];
  for (let i = 0; i < (opts.shuffle || 0); i++) {
    const k = Math.random();
    let where;
    if (k < .25) { const tp = rnd(tpls); applyTemplate(tp); where = `rnd tpl:${tp}`; }
    else if (k < .6) { const bg = rnd(bgs); setBg(bg); where = `rnd bg:${bg}`; }
    else { const ly = rnd(lays); applyLayout(ly, true); where = `rnd lay:${ly}`; }
    check(where + ` #${i}`);
    if (i % 40 === 39) await new Promise(r => setTimeout(r, 0));
  }
  const uniq = [...new Set(fails)];
  window.__CYCLE = { states, fails: uniq, repro };
  return { states, failCount: uniq.length, fails: uniq.slice(0, 40), repro: repro.slice(0, 10) };
}
window.cycleTest = cycleTest;
