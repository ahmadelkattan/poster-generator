---
name: arabic-poster-design
description: Conventions for building or extending Arabic Islamic institutional poster renderers — background generators, palette tokens, safe areas, RTL typography, layout flow, and export. Use when adding a background, palette, layout, ornament or template to the Mirsam poster studio (index.html), or when starting a similar Arabic poster/announcement tool. Triggers on "add a background", "new palette", "new layout", "Arabic poster", "RTL poster", "mosque committee poster", "poster template".
---

# Arabic poster design — house conventions

These are the rules the Mirsam poster studio is built on. Follow them when extending
`index.html` so new work stays consistent with what is already there. Full rationale is
in `DESIGN.md`; this file is the operating manual.

## The governing rule

> **Nothing on the poster may be anything a two- or three-plate print job couldn't do.**

Flat colour, hairlines, knockout white, honest overprint. No bevel, emboss, drop shadow,
inner glow, metallic gradient or text-shadow — anywhere. The only permitted gradient is a
single-stop scrim over photography. This one constraint is what keeps the output from
looking machine-generated, and it is why the reference posters looked dated.

## Colour: tokens, never hex

Elements store `'deep' | 'alt' | 'gold' | 'paper' | 'ink'`, resolved at render time by
`C(token, palette, use)`. Never write a hex value into an element or a layout.

- `deep` — the one dominant accent; may cover large areas
- `gold` — subordinate; **hairline by default**, never more than ~5% of the canvas, never
  used for body text (it fails WCAG AA on cream)
- `ink` — what does the reading. On this palette family navy is ink, not a third brand colour
- `alt` — at most one secondary block per poster
- `paper` — "the light one". It is *not* the ground; the ground is `groundColor()`

**Inversion is cross-cutting.** `DOC.bgOpts.inverted` toggles, and backgrounds listed in
`DARK_BG` are dark by construction; `invActive()` XORs the two. Under inversion a token
resolves differently depending on use:

```js
C('deep')                  // → lifted deep   (a panel behind type)
C('deep', null, 'text')    // → the light one (type itself)
```

`styleEl` passes `'text'` for `color`. If you add a new place that paints type, pass it too,
or headings will disappear into a dark field.

## Backgrounds are functions, not images

```js
bgDef(id, arabicName, tier, (P, o, W, H) => ({ svg, safe }))
```

- Pure SVG strings. Never bitmaps — they must recolour and re-proportion at any canvas size.
- `o` is `{ scale, placement, intensity, weight, inverted }`. Honour as many as make sense;
  one motif should yield many usable grounds.
- Derive colours from `tones(P, o)`, never from `P` directly, so `inverted` works for free.
- **Every background must publish a `safe` rect in percent.** This is the mechanic that
  fixes drifting margins. Layouts position only inside it.
- Add the id to `BG_ORDER` and give it a `LAYOUT_FIT` entry.

### Safe areas that follow curved frames

If the frame narrows (arch, negative-arch), measure the available width **slightly below**
the top of the content area, not at it — the first line is short and centred and can live in
the narrow part, while the body needs a usable column. Measuring at the very top produces a
column so narrow the title wraps.

### Geometry helpers

- `archPath(cx, halfW, springY, sharp)` — two-centre pointed arch. Derive the spring line
  **from the desired apex** (`spring = apexY + sqrt(R²−d²)`), never the reverse, or the apex
  goes off-canvas on tall formats. `sharp ≈ 0.22` is Cairene; 0.34 reads Gothic.
- `archD(w, h)` — the same arch as an absolute-size mask path. Do **not** express a mask as a
  0..1 path plus `transform="scale(w,h)"`: the transform also scales `stroke-width` and dash
  arrays out of unit space and you get a stroke hundreds of pixels wide.
- `rosettePath(cx, cy, R, n, inner)` — 2n-fold compass rosette.
- `girihUnit(u)`, `kuficField(cols, rows, u)` — tessellation units. `kuficField` must stay
  **deterministic**; randomised cells read as noise, not as square Kufic.

## Ornament policy

An ornament ships only if it **separates, frames, anchors or directs**. Decoration that is
there because the subject is a mosque does not qualify — the skyline background survives only
because it sets the bottom of the safe area.

Six constructed dividers only (`rule · girih · rosette · kufic · muqarnas · diamond`). All
paths generated from geometry. No dingbats, no swashes, no gradient metal. At poster scale a
dense repeat collapses into asterisks — three units at a readable size beat seven small ones.

## Layouts

A layout is a function `S => [elementSpec]`, positioned relative to the safe rect via
`SP(S, fractionX, fractionW)`.

- **`role` is the join key** across layouts, templates, the content form and the inspector.
  Switching layout REBUILDS the element list from the new layout's slot specs (positions and
  sizes always come from the spec — no residue), pours content back in by role, and parks
  content whose role has no slot in `DOC.tray` — the visible «عناصر غير مستخدمة» shelf in the
  layers panel. Never park content on the canvas, never drop it silently. A later layout that
  has the role pours the trayed content straight back in. Starter `DEFAULT_TEXT` fills a slot
  only when the document has never had that role — a deliberately emptied role stays empty.
- **`ord` is a row number, not a sequence.** Elements sharing an `ord` flow side by side
  (the two venue boxes, the two description columns). Never stack columns independently from
  the top of the safe area — they collide with the title.
- `ord >= 99` pins to the bottom of the safe area.
- `flow: false` opts out of flow entirely (crest, photo, QR).
- In RTL the **primary item takes the right column**.

### Flow runs on structural change only

`flow()` is called on layout switch, template load, add/remove, canvas resize and font change
— **never on a keystroke**. That is what makes "change the date without anything else moving"
true. When content does not fit, compress the gaps (floor ~0.28) rather than let blocks
overlap, then let `checkOverflow()` warn.

Reserve space for a non-flowing masthead crest inside `flow()` on a local copy of the safe
rect — `render()` recomputes `DOC.safe` from the background on every pass, so writing to it
there is lost.

## Arabic typography

- `dir="rtl"` + `unicode-bidi: plaintext` on every text box, so phone numbers, URLs and
  "6:30" sit correctly with no manual fiddling.
- `letter-spacing` defaults to **0** and is labelled as risky. Positive tracking breaks
  Arabic joining. Expose it; never apply it by default.
- Display line-height floors at ~1.24. Arabic descenders (ي ج ح خ) hang well below the
  baseline and clip inside a filled box at 1.1–1.2.
- Sizes are design-px against a 1080 reference, scaled by `W/1080`. Inline spans written by
  the sub-selection toolbar use **`em`**, never `px`, so they survive box scaling and canvas
  changes.
- Inline colour is stored as `data-tok="<token>"` and re-resolved at render, so a palette
  swap recolours it with everything else.
- A visible gap after `أ` `د` `ر` `و` `ز` is correct — those letters do not join forwards.
  Do not "fix" it.
- Day and month names come from `AR_DAYS` / `AR_MONTHS` lookups, never from
  `toLocaleDateString` guesswork.

## Export

`posterCanvas(scale, bg)` composites in three passes: flat ground → background SVG
rasterised via `svgToImage` → element layer rasterised through an SVG `<foreignObject>`.

**Never use a rasteriser that re-implements text layout.** html2canvas and friends walk
text nodes, split them into runs and `fillText` each run at coordinates they compute
themselves. For Latin that is roughly fine; for Arabic it is fatal, because splitting a
word destroys the glyph joining that shaping produced — each fragment re-shapes in
isolation and medial forms collapse to isolated ones, so `عن لقاء شهري` exports as
`عن لق اش هري`. This shipped once. Print → PDF never had the bug, because it uses the
real renderer. `foreignObject` hands the markup back to the browser's own layout and
shaping engine, so the export *is* the preview.

Four rules the route imposes, all load-bearing:

1. **Every stylesheet inlined.** An SVG image resolves nothing external.
2. **`@font-face` as base64 data: URIs**, and the `<style>` must be an **SVG-level**
   `<style>` wrapped in `CDATA`, not an XHTML `<style>` inside the `foreignObject`.
   CDATA also keeps CSS combinators like `>` out of XML escaping.
3. **Every image a `data:` URI before serialising** — no blob:, no paths.
4. **Serialise with `XMLSerializer`**, never `innerHTML`; XML parsing is strict, which is
   also why every generated inline `<svg>` must carry `xmlns`.

**An SVG-as-image is its own document with its own font and resource caches.** Warming
them from the parent page does nothing, and the FIRST render paints before embedded
fonts and images resolve — producing an export that is correctly shaped but in a system
fallback face, or silently missing a photo at one scale and not another. Both were real
bugs. `primeExportResources()` renders a 16×16 SVG carrying the identical `@font-face`
rules and the same image `data:` URIs first; it costs ~100ms and makes the real render
deterministic. Rasterising the whole poster twice also works and costs seconds at ×3.

Verify exports with checks that can actually fail: measure a known Arabic string's ink
width in the DOM and in the raster (broken shaping is measurably wider — >2% fails), and
perceptually diff the on-screen stage against the export. File size and pixel dimensions
prove nothing; the broken build passed both.

Always offer Print → Save as PDF as the secondary path.

## QR

Self-contained byte-mode encoder, EC level M, versions 1–10. If you touch it, **re-verify
against an independent reference encoder** (`pip install segno`) and compare matrices
module-for-module. A transposed format-information block produces a symbol that looks
perfectly plausible and that no scanner can read. Expect one pad codeword to differ from
segno when the bit stream lands on a codeword boundary; both decode identically.

## Copy

Quick-insert phrases come from the committee's own previous posters and are editable and
persisted. This is the single most effective fix for copy that "sounds AI-written" — do not
replace them with generated alternatives.

## Checklist for a new background

- [ ] pure SVG, no bitmap, no gradient except a photo scrim
- [ ] derives colour from `tones(P, o)`
- [ ] honours `scale` / `placement` / `intensity` / `weight`
- [ ] publishes a `safe` rect that content actually fits in
- [ ] added to `BG_ORDER` and `LAYOUT_FIT`
- [ ] every inline `<svg>` has `xmlns`
- [ ] ids namespaced (handled by `buildBG`, don't bypass it)
- [ ] renders at 1080×1080, 1080×1350, 1080×1920 and 1240×1754
- [ ] `checkOverflow()` returns 0 and `contrastReport()` is empty with its first-fit layout
- [ ] looks right with `inverted` on as well as off
