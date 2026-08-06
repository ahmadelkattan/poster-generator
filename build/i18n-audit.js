/* i18n completeness audit — run in the page with LANG='en'.
   Walks every panel, tab, modal and inspector state and reports any visible
   UI text still containing Arabic. The poster (#stage) is excluded on
   purpose: poster CONTENT never translates, only the interface does. */
async function i18nAudit() {
  const AR = /[؀-ۿ]/;
  const leaks = [];
  const seen = new Set();
  const scan = (where) => {
    const root = document.body;
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        if (!n.nodeValue || !AR.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
        let p = n.parentElement;
        while (p) {
          if (p.id === 'stage' || p.id === 'toast') return NodeFilter.FILTER_REJECT;  /* poster + transient */
          if (p.id === 'bLang') return NodeFilter.FILTER_REJECT;   /* deliberately names the OTHER language */
          /* background preview cards mirror the poster's own ground word */
          if (p.classList && p.classList.contains('bgcard') && DOC.groundWord && n.nodeValue.includes(DOC.groundWord)) return NodeFilter.FILTER_REJECT;
          if (p.tagName === 'STYLE' || p.tagName === 'SCRIPT') return NodeFilter.FILTER_REJECT;
          if (p.classList && (p.classList.contains('chip') && p.dataset && p.dataset.ph !== undefined)) return NodeFilter.FILTER_REJECT; /* committee's own phrases = content */
          if (p.classList && p.classList.contains('chip') && p.dataset && p.dataset.pray !== undefined) return NodeFilter.FILTER_REJECT;
          if (p.matches && p.matches('textarea, input, option, .layeritem .nm, .fld textarea')) return NodeFilter.FILTER_REJECT; /* user content */
          /* the arNum switch shows «١٢٣» as a live sample of what it toggles */
          if (p.classList && p.classList.contains('switch') && /١٢٣/.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
          p = p.parentElement;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    let n;
    while ((n = walk.nextNode())) {
      const el = n.parentElement;
      if (el && el.offsetParent === null && el.tagName !== 'OPTION') continue;   /* not visible */
      const txt = n.nodeValue.trim().slice(0, 70);
      const key = where + '|' + txt;
      if (txt && !seen.has(key)) { seen.add(key); leaks.push({ where, text: txt, sel: el ? (el.tagName + '.' + el.className).slice(0, 50) : '?' }); }
    }
    /* attributes users can see */
    document.querySelectorAll('[title],[placeholder],[aria-label]').forEach(el => {
      if (el.closest('#stage') || el.id === 'bLang') return;
      /* the arNum label shows «١٢٣» as a live sample of what it does */
      if (el.closest('.switch') && /١٢٣/.test(el.textContent || '')) return;
      ['title', 'placeholder', 'aria-label'].forEach(a => {
        const v = el.getAttribute(a);
        if (v && AR.test(v)) {
          const key = where + '|@' + a + '|' + v;
          if (!seen.has(key)) { seen.add(key); leaks.push({ where, attr: a, text: v.slice(0, 70), sel: el.tagName + '.' + el.className }); }
        }
      });
    });
  };

  for (const tpl of Object.keys(TEMPLATES)) {
    applyTemplate(tpl);
    for (let s = 0; s <= 4; s++) { goStep(s); scan(`tpl:${tpl} step:${s}`); }
    /* inspector for every element type present */
    for (const e of DOC.elements.slice()) {
      select(e.id);
      document.querySelectorAll('#right .tab')[0].click();
      scan(`tpl:${tpl} inspector:${e.type}/${e.role}`);
    }
    document.querySelectorAll('#right .tab')[1].click(); buildLayers();
    scan(`tpl:${tpl} layers`);
    SELID = null; buildInspector(); scan(`tpl:${tpl} no-selection`);
  }
  /* modals */
  exportModal(); scan('modal:export'); closeModal();
  helpModal();   scan('modal:help');   closeModal();
  /* tray state */
  applyTemplate('voucher'); applyLayout('classic', true);
  document.querySelectorAll('#right .tab')[1].click(); buildLayers();
  scan('layers:with-tray');
  /* warning states */
  const ttl = DOC.elements.find(e => e.role === 'title');
  if (ttl) { ttl.html = 'x'.repeat(400); render(); checkIssues(); goStep(2); scan('overflow-warning'); }

  const byText = new Map();
  leaks.forEach(l => { if (!byText.has(l.text)) byText.set(l.text, l); });
  const distinct = [...byText.values()];
  return { leakCount: leaks.length, distinctCount: distinct.length, distinct };
}
window.i18nAudit = i18nAudit;
