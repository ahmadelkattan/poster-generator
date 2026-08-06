/* ═══════════════════════════════════════════════════════════════════
   EXPORT · DRAFTS · MODALS
   ───────────────────────────────────────────────────────────────────
   The poster rasterises through an SVG <foreignObject>: the live element
   layer is serialised to XHTML, handed back to the browser's own layout
   and text engine, and drawn onto a canvas through an <img>.

   This is not a preference. A rasteriser that re-implements text layout —
   html2canvas walks text nodes, splits them into runs and fillText()s each
   run at coordinates it computes itself — destroys Arabic glyph joining:
   a word cut into runs is re-shaped per run, so medial and final forms
   collapse into isolated ones and «عن لقاء شهري» exports as «عن لق اش هري».
   Print → PDF never had the bug precisely because it uses the real
   renderer; foreignObject uses it too, so the export IS the preview.

   What the route requires, all satisfied here:
     · every stylesheet inlined — an SVG image resolves nothing external
     · @font-face as base64 data: URIs (the embedded families already are)
     · every image a data: URI before serialising — no blob:, no paths
     · well-formed XHTML — XMLSerializer, never innerHTML
   ═══════════════════════════════════════════════════════════════════ */
const XHTMLNS = 'http://www.w3.org/1999/xhtml';
const XLINKNS = 'http://www.w3.org/1999/xlink';

function download(href, name) {
  const a = el('a'); a.href = href; a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
}
const posterName = ext => {
  const ttl = htmlToText((DOC.elements.find(e => e.role === 'title') || {}).html || 'بوستر').slice(0, 28).replace(/[\\/:*?"<>|]/g, '');
  return (ttl || 'poster') + '.' + ext;
};

/* Only the faces this poster actually uses. The embedded set is ~930KB of
   base64 and every byte of it would otherwise ride inside the data: URI. */
function posterFontCSS() {
  const node = $('#fontcss'); if (!node) return '';
  const used = new Set([DOC.fonts.head, DOC.fonts.body]);
  DOC.elements.forEach(e => { if (e.font && e.font !== 'head' && e.font !== 'body') used.add(e.font); });
  const want = [...used].map(f => `font-family: '${f}';`);
  return node.textContent.split('\n').filter(l => want.some(w => l.includes(w))).join('\n');
}
/* the page's own sheet, so poster rules (.el, .mstack, .mrowx…) are identical
   to what the preview used — parity beats a hand-picked subset */
const posterElementCSS = () => $$('style').filter(s => s.id !== 'fontcss').map(s => s.textContent).join('\n');

const imgHref = n => n.getAttribute('src') || n.getAttribute('href') || n.getAttributeNS(XLINKNS, 'href') || '';

/* Everything drawable must be self-contained before serialisation: an SVG
   image resolves no external reference, and a picture still resolving is
   exactly how the ×2 export lost its photo while ×3 kept it. */
async function inlineAllImages(root) {
  const toDataURI = src => new Promise((res, rej) => {
    const im = new Image();
    im.crossOrigin = 'anonymous';
    im.onload = () => {
      try {
        const c = el('canvas');
        c.width = im.naturalWidth || 1; c.height = im.naturalHeight || 1;
        c.getContext('2d').drawImage(im, 0, 0);
        res(c.toDataURL('image/png'));
      } catch (e) { rej(new Error('image-not-inlinable')); }
    };
    im.onerror = () => rej(new Error('image-load-failed'));
    im.src = src;
  });
  const jobs = [];
  $$('img,image', root).forEach(n => {
    const v = imgHref(n);
    if (!v || v.startsWith('data:')) return;
    jobs.push(toDataURI(v).then(d => {
      if (n.hasAttribute('src')) n.setAttribute('src', d); else n.setAttribute('href', d);
      if (n.getAttributeNS(XLINKNS, 'href')) n.setAttributeNS(XLINKNS, 'xlink:href', d);
    }));
  });
  await Promise.all(jobs);
  /* every raster fully decoded — never serialise something still resolving */
  await Promise.all($$('img', root).map(n => (n.decode ? n.decode().catch(() => {}) : Promise.resolve())));
  const bad = $$('img,image', root).filter(n => { const v = imgHref(n); return v && !v.startsWith('data:'); });
  if (bad.length) throw new Error('unresolved-image');
}

/* the element layer, serialised as a standalone SVG document */
async function posterSVGString(W, H) {
  const clone = STAGE.cloneNode(true);
  /* the overlay carries selection frame, guides, hover box and the numbered
     content badges; the safe guide and the background layer are drawn (or
     not) separately. None of them are artwork. */
  ['#overlay', '#safeguide', '#bglayer'].forEach(sel => {
    const n = clone.querySelector(sel); if (n) n.remove();
  });
  /* editing affordances are chrome too — an overflowing element would
     otherwise export with its red warning outline baked in */
  $$('.el', clone).forEach(n => {
    n.classList.remove('overflowing', 'colliding', 'hl', 'selectable', 'locked');
    n.removeAttribute('contenteditable');
  });
  clone.removeAttribute('id');
  clone.setAttribute('style',
    `position:relative;width:${W}px;height:${H}px;overflow:hidden;box-shadow:none;` +
    `background:transparent;direction:rtl;--iz:1;margin:0;padding:0;` +
    `font-family:'${DOC.fonts.body}',serif`);
  await inlineAllImages(clone);

  const wrap = document.createElementNS(XHTMLNS, 'div');
  wrap.setAttribute('style', `width:${W}px;height:${H}px;margin:0;padding:0;overflow:hidden`);
  const style = document.createElementNS(XHTMLNS, 'style');
  style.textContent = posterFontCSS() + '\n' + posterElementCSS();
  wrap.appendChild(style);
  wrap.appendChild(clone);

  const xhtml = new XMLSerializer().serializeToString(wrap);
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="${XLINKNS}" ` +
         `width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
           `<foreignObject x="0" y="0" width="${W}" height="${H}">${xhtml}</foreignObject>` +
         `</svg>`;
}

/* Safari has the weakest foreignObject implementation of the three engines:
   the explicit width/height on the root <svg> above and the decode() retry
   below are both load-bearing there. */
function svgToImage(svgStr, w, h) {
  const src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgStr);
  return new Promise((res, rej) => {
    const img = new Image();
    img.width = w; img.height = h;
    const settle = () => res(img);
    img.onload = () => {
      if (!img.decode) return settle();
      img.decode().then(settle, () => setTimeout(() => img.decode().then(settle, settle), 80));
    };
    img.onerror = () => rej(new Error('svg-raster-failed'));
    img.src = src;
  });
}

async function posterCanvas(scale, bg) {
  /* fonts resolved before anything measures or serialises, or the export
     silently falls back to a system face */
  if (document.fonts) await Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 8000))]);
  const W = DOC.W, H = DOC.H;
  const out = el('canvas');
  out.width = Math.round(W * scale); out.height = Math.round(H * scale);
  const cx = out.getContext('2d');
  cx.fillStyle = bg; cx.fillRect(0, 0, out.width, out.height);

  /* flat ground → background artwork → element layer */
  try {
    const bgSvg = `<svg ${SVGNS} width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${buildBG(DOC.bg, DOC.palette, DOC.bgOpts, W, H).svg}</svg>`;
    cx.drawImage(await svgToImage(bgSvg, W, H), 0, 0, out.width, out.height);
  } catch (e) { console.warn('background raster failed, exporting on flat ground', e); }

  const elImg = await svgToImage(await posterSVGString(W, H), W, H);
  /* onto its own transparent canvas first, so coverage can still tell an
     empty element layer from a poster that merely has a pale ground */
  const elCanvas = el('canvas');
  elCanvas.width = out.width; elCanvas.height = out.height;
  elCanvas.getContext('2d').drawImage(elImg, 0, 0, elCanvas.width, elCanvas.height);
  const wantsContent = DOC.elements.some(e => (e.type === 'text' || e.type === 'meta') ? hasContent(e) : true);
  if (wantsContent && canvasCoverage(elCanvas) < .002) throw new Error('blank-element-layer');
  cx.drawImage(elCanvas, 0, 0);
  return out;
}
/* fraction of pixels that are not fully transparent, sampled on a grid */
function canvasCoverage(canvas) {
  try {
    const cx = canvas.getContext('2d');
    const dat = cx.getImageData(0, 0, canvas.width, canvas.height).data;
    const step = Math.max(4, Math.floor(dat.length / 4 / 20000)) * 4;
    let hit = 0, tot = 0;
    for (let i = 3; i < dat.length; i += step) { tot++; if (dat[i] > 8) hit++; }
    return tot ? hit / tot : 0;
  } catch (e) { return 1; }   /* if sampling itself fails, don't block the export */
}

async function exportImage(fmt, scale) {
  const prevSel = SELID; SELID = null; drawSel();
  toast(t('exporting'));
  const ground = groundColor();
  try {
    const canvas = await posterCanvas(scale, fmt === 'jpg' ? '#ffffff' : ground);
    const url = canvas.toDataURL(fmt === 'jpg' ? 'image/jpeg' : 'image/png', .94);
    /* a real poster never encodes this small */
    if (url.length < 40000) throw new Error('suspiciously-small-file');
    download(url, posterName(fmt));
    toast(t('exportDone').replace('{w}', canvas.width).replace('{h}', canvas.height));
  } catch (err) {
    console.error(err);
    toast(err.message === 'unresolved-image' ? t('exportImgFail')
        : err.message === 'blank-element-layer' ? t('exportBlank')
        : t('exportFail'), true);
  } finally { SELID = prevSel; drawSel(); }
}
