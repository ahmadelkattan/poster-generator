# Session prompt — Arabic poster studio for the GSC mosque committee

> Paste this whole file as your first message in a fresh Claude Code session.
> Attach the 4 reference posters (`IMG_6349–6352.jpg`) to that same message.
> `starter-shell.html` in this folder is a partially built shell — read it before you start.

---

## 0. Before you write any code

1. Run `/skills` (or list your available skills) and read every SKILL.md that could apply. At minimum:
   - **frontend-design** — read it first. This is a design-led build; the whole complaint about the current process is that output "looks AI generated". Follow its two-pass process: write a design plan (palette / type / layout / signature element), critique it against the brief, then build.
   - **web-artifacts-builder** — skim it for component patterns, but note this app ships as a **standalone file**, not a claude.ai artifact. Do not adopt its build tooling.
   - **skill-creator** — at the *end* of the build, use it to author a reusable `arabic-poster-design` skill that captures the background/layout/typography conventions you settled on, so future sessions can extend the app without rediscovering them.
   - If you have a browser-automation or screenshot skill available, use it to actually load the page and look at your own output after each phase. Do not ship a poster generator you have never seen render.
2. Look at the four reference posters carefully — then read §5 before you form any opinion about them. **They are the floor, not the target.** They establish the idiom the committee's audience expects (Arabic Islamic institutional announcement: cream paper, deep green, navy, gold, arch forms, ornamental dividers, icon meta rows). Your job is to hit that idiom at a much higher level of craft, and to add directions they have never had access to.
3. Write the design plan to `DESIGN.md` in the repo before coding.

---

## 1. Who this is for and why

The mosque committee at **Gezira Sporting Club (GSC), Zamalek** produces event posters — monthly lectures, Eid prayer announcements, Awqaf sacrifice-voucher notices. They currently make them by asking ChatGPT to generate an image. Three things are broken:

- **Arabic renders broken.** Image models mangle Arabic glyph shaping and letter joining. They burn many attempts getting legible text.
- **Editing is hopeless.** They never had a design file, so every correction goes back through chat, and each fix breaks something else or drops quality.
- **It looks AI-made.** Both the design and the copy.

The fix is to stop generating images and start **rendering HTML**. The browser does Arabic shaping natively and perfectly. Text stays text. Every edit is instant, local, and non-destructive.

**The committee members are not designers.** Assume an older, non-technical Arabic-speaking user on a laptop or an iPad. Every control must be obvious with zero training.

---

## 2. Hard constraints

- **One self-contained `index.html`.** Vanilla HTML/CSS/JS. No framework, no build step, no npm. It must work when opened directly from `file://` after being emailed to someone.
- **No backend, no login, no accounts, no server storage.**
- Only external dependencies allowed: Google Fonts, and `html2canvas` from a CDN — both with graceful degradation if offline/blocked.
- Ship a `fonts/` fallback path: document how to drop `.woff2` files in and switch to `@font-face` for fully offline use.
- Persistence = **last draft only**, in `localStorage`, plus manual JSON export/import so drafts can be shared between committee members. No poster library.
- RTL-first. UI in Arabic, with an AR/EN toggle.
- Must work with touch (iPad) as well as mouse.

---

## 3. The flow

A light stepper on the left panel, but **never modal** — the live poster is always visible and the user can jump between steps freely.

```
1  القالب      Template: event type (lecture / Eid greeting / prayer times /
                voucher notice / free) + canvas size
2  الخلفية      Background pattern + colour palette + optional texture
3  التخطيط      Layout: element arrangement presets for the chosen background
4  المحتوى      Content: form fields for every text slot
5  التنسيق      Fonts, then free-form direct editing on the canvas
   ↓
   تنزيل        PNG / JPG / print-to-PDF
```

---

## 4. Architecture

### Canvas
Render the poster as **absolutely-positioned DOM inside a fixed-size `#stage`** (design width 1080px), with a wrapper transform for zoom-to-fit. Never scale the stage itself — export depends on its untransformed geometry.

Sizes: `1080×1350` (4:5, default), `1080×1080`, `1080×1920` (story), `1240×1754` (A4 @150dpi → export ×2 = 300dpi A4).

Positions and sizes stored as **percentages of canvas width/height**; font sizes stored in design-px against a 1080 reference and scaled by `W/1080`. Switching canvas size must not destroy a layout.

### Document model

```js
DOC = {
  size, W, H,
  bg: 'wave', palette: 'gsc', texture: true, bgImage: null,
  fonts: { head: 'Reem Kufi', body: 'Cairo' },
  elements: [ Element, ... ]
}

Element = {
  id, type: 'text'|'meta'|'divider'|'image'|'qr'|'panel',
  role: 'kicker'|'title'|'name'|'subtitle'|'desc'|'meta'|'footer'|null,
  x, y, w, h,                      // % of canvas; h auto for text
  html,                            // rich innerHTML for text
  rows: [{icon, text}],            // for meta
  font, size, weight, color, align, lineHeight, letterSpacing, dir,
  fill, radius, padding, borderColor,   // gives you pill / ribbon / boxed styles free
  rotation, opacity, z, locked
}
```

**Colours are palette tokens, not hex** — store `'deep' | 'alt' | 'gold' | 'paper' | 'ink'` and resolve at render time, with a custom-hex escape hatch. Changing palette must recolour the whole poster instantly.

### Rendering
Full re-render of `#ellayer` on any change, **except** the element currently being inline-edited (re-rendering it kills the caret). `render(skipId)`.

---

## 5. Backgrounds — refine, then extend

Build every background as a **parametric SVG function** — `bg(id, palette, opts, W, H) → svg string`. Never bitmaps. They must recolour, resize and re-proportion cleanly.

### 5.1 What is actually wrong with the references

Name these problems in `DESIGN.md` and fix them. Do not carry them forward:

- **Three or four accents competing at once.** Green, navy and gold all shouting on the same poster, with no clear hierarchy between them. Pick a dominant and a subordinate; navy should mostly be ink, not a third brand colour.
- **Clipart ornament.** The gold flourishes are generic stock dingbats, not drawn geometry. Replace them with real constructed forms — girih strapwork, kufic squares, rosette compass constructions — built from paths you generate.
- **Fake metal.** Gradient-bevelled gold with emboss and drop shadow (the `7,000` in poster 4) is the single most dated element in the set. Flat gold, or gold as a hairline, always.
- **Text shadows and outlines** used to force contrast that the layout should have provided.
- **Inconsistent margins.** Poster 4's edges don't agree with each other. Every background must publish a **safe-area rectangle** that layouts respect, and it must be consistent across the set.
- **The photo cut-out** in poster 2 is a stock image dropped into an arch with no tonal relationship to the paper. Any photo treatment must include a duotone/multiply option so it belongs to the palette.
- **Bottom-heavy clutter** — stacked bars, phone numbers, footnote strips all fighting at the base.
- **Decoration that carries no information.** Mosque silhouettes appear because it's a mosque poster, not because they organise anything. Every ornament you keep must earn its place structurally: separating, framing, anchoring, or directing the eye.

### 5.2 Tier 1 — their motifs, done properly (8)

Same vocabulary, real craft. These make the committee feel at home immediately.

| id | what changes vs. the reference |
|---|---|
| `wave` | the corner sweep becomes a single confident curve with **one** trailing hairline, not three; the curve resolves against the safe area instead of colliding with the title |
| `arch` | a *constructed* pointed arch (proper two-centre geometry, correct spring line) instead of a traced blob; frame weight varies with canvas size |
| `skyline` | mosque silhouette redrawn as clean flat geometry — domes and minarets as circles, arcs and tapers — anchored to a baseline rule, not floating |
| `frame` | double rule with **drawn** corner rosettes derived from an 8-fold compass construction |
| `banner` | header band whose lower edge is a true muqarnas step profile rather than a decorative scallop |
| `geo` | full-bleed girih tessellation, tone-on-tone at 4–7%, with the scale tied to canvas width so it never looks like wallpaper |
| `split` | flat two-tone division on a considered ratio, one gold rule at the seam, nothing else |
| `minimal` | paper, one rule, one drawn ornament, and a lot of nerve |

### 5.3 Tier 2 — directions they have never had (8+)

This is where the app stops looking like the old posters. Take real risks here.

| id | idea |
|---|---|
| `mashrabiya` | a dense wooden lattice screen rendered as a vertical band down one side, text living in the clear field beside it |
| `kufic` | square Kufic (*al-Kufi al-murabba'*) block grid — starkly modern, purely geometric, no floral anything |
| `inverted` | flat deep-green or navy field with cream and gold type. They have **never** made a dark poster; it will read as instantly more considered |
| `calligraphic-ground` | one Arabic word (the event's own key word — عيد, لقاء, صلاة) set enormous at 3–5% opacity behind everything, bleeding off two edges |
| `zellige` | a band of interlocking tile geometry along one edge, high-chroma, drawn from Moroccan zellij ratios |
| `negative-arch` | the arch as *void* — a cream arch punched out of a solid colour field, all content inside it |
| `rule-grid` | Swiss-Arabic: no ornament at all, hairline grid, a single gold rule doing the structural work, everything earned by typography |
| `edge-wash` | soft marbled *ebru* wash confined to one edge, paper elsewhere |
| `duotone-photo` | uploaded photo (club architecture, the mosque itself) mapped to the palette via feColorMatrix duotone, with a gradient scrim |
| `radial-rosette` | a single oversized 16-fold rosette construction bleeding off a corner, hairline only |

Plus **upload your own background** with adjustable scrim and duotone.

### 5.4 Make it a system, not a list

Don't hard-code 18 fixed images. Each background takes options so one motif yields many looks — this is what actually gives them variety over years of monthly posters:

```js
opts = {
  scale:     'tight' | 'normal' | 'grand',   // motif size relative to canvas
  placement: 'corner' | 'edge' | 'band' | 'full' | 'center',
  intensity: 0–100,                          // opacity / weight of the motif
  weight:    'hairline' | 'regular' | 'solid',
  inverted:  bool                            // swap paper and deep
}
```

Give the background picker a **shuffle** button that samples the option space and shows six variants at once. Non-designers choose far better by picking from options than by adjusting sliders.

**Palettes** (each: `deep`, `alt`, `gold`, `paper`, `ink`): `gsc` (club green/navy/gold/cream — default and always first), `navy`, `emerald`, `maroon`, `teal`, `charcoal`, `royal`, `sand`. Add two the committee would never pick themselves but that work — a near-black/bone and a deep olive/terracotta — so the range extends past what they know.

**Ornaments**: 6 dividers, all *constructed* geometry. No dingbats, no swashes, no gradient metal.

---

## 6. Layouts

Each layout is a named set of element specs (position, role, type scale). Offer only the ones that suit the chosen background.

- `classic` — kicker → title → "مع" → speaker name → credentials line → ornament → meta rows → footer link pill *(this is poster 1 exactly)*
- `side-photo` — arch-masked photo right, text left *(poster 2)*
- `greeting` — large centred greeting, highlighted info panel, secondary two-column detail boxes, closing line *(poster 3)*
- `offer` — ribbon title, value in a badge, body paragraph, contact bar *(poster 4)*
- `meta-first` — date/time/place inline at the top, then title and body
- `boxed-meta` — body up top, meta rows inside a bordered panel at the bottom
- `two-col` — description split into two balanced columns
- `centered-minimal` — everything centred, generous air, one ornament

Layout switching must preserve whatever text the user has already typed.

---

## 7. The direct-manipulation editor (this is the heart of the app)

This is the feature that replaces "asking ChatGPT to fix it". Get it right.

- **Click** an element → selection frame with 8 brass handles + a role tag.
- **Drag** to move. **Side handles (e/w)** change box width only — narrowing a box makes the text wrap taller, which is exactly what was asked for. **Corner handles** scale font size and width together. Text height is always auto.
- **Double-click** → inline `contenteditable`. Typing is live. <kbd>Enter</kbd> starts a new line inside the box. <kbd>Esc</kbd> exits.
- **Select part of the text while editing** → floating mini-toolbar appears above the selection: A+ / A− / bold / colour / line break. Implement by wrapping the range in a `<span>` with **`font-size` in `em`, not `px`** — relative sizing survives box scaling and canvas-size changes.
  ```js
  const r = sel.getRangeAt(0); const s = document.createElement('span');
  s.style.fontSize = '1.25em';
  try { r.surroundContents(s); } catch { s.appendChild(r.extractContents()); r.insertNode(s); }
  ```
- **Snapping** while dragging: canvas centre, canvas margins, and other elements' edges within ~6px, with green guide lines.
- **Keyboard**: arrows nudge 1px (<kbd>Shift</kbd> = 10), <kbd>Del</kbd> removes, <kbd>Ctrl/Cmd+D</kbd> duplicates, <kbd>Ctrl/Cmd+Z</kbd> / <kbd>Shift+Z</kbd> undo/redo, <kbd>Esc</kbd> deselects.
- **Undo/redo**: snapshot the whole DOC as JSON on each committed change, cap ~60 states. Non-negotiable — it is what makes them brave enough to experiment.
- **Right panel inspector** for the selected element: font, size, weight, colour, alignment, line height, letter spacing, direction, box fill / radius / padding / border, opacity, rotation, layer order, lock.
- **Layer list** so a text box that ends up behind something is still reachable.
- **Add** free text box / image / ornament / QR / panel at any time.
- **Auto-fit** button per element: shrink font until the text fits its box.

---

## 8. Arabic-specific helpers — these are the time savers

- **Date field**: a native date picker that outputs proper Arabic — `الثلاثاء، ١٨ أغسطس ٢٠٢٦`. Day and month names from a lookup, not `toLocaleDateString` guesswork on the day name.
- **Hijri**: optional second line via `new Intl.DateTimeFormat('ar-EG-u-ca-islamic', {...})`.
- **Arabic-Indic numerals toggle** (`١٢٣` ⇄ `123`) applied across the whole poster.
- **Phrase library** — quick-insert chips using the committee's *own* real wording, lifted from the reference posters. This is the single most effective fix for "the copy sounds AI-written":
  - `تعلن إدارة النادي ولجنة المساجد عن`
  - `استجابة لرغبة العديد من السادة الأعضاء`
  - `تهنئ إدارة النادي ولجنة المساجد السادة الأعضاء بحلول`
  - `بعد صلاة المغرب مباشرة` · `بعد صلاة العشاء مباشرة` · `عقب صلاة الجمعة`
  - `بالمسجد الكبير بنادي الجزيرة الرياضي، الزمالك` · `بمسجد النادي، الزمالك`
  - `الدعوة عامة للسادة الأعضاء` · `وكل عام وأنتم بخير`
  - `وتقام صلاة العيد إن شاء الله` · `ويسبقها تكبيرات العيد`
  - Make the list editable and persisted, so they add their own over time.
- **Prayer-time preset chips** for the time field.
- **Meta rows** with icons matching the references: calendar, clock, mosque, pin, phone, link, person, ticket. Row styles: `rows` (icon + dotted separators, as in poster 1), `boxed`, `inline`.
- **Kashida / letter-spacing warning**: never apply CSS `letter-spacing` to Arabic text by default — it breaks the visual joining. Expose it but default to 0 and label the risk.
- Set `dir="rtl"` and `unicode-bidi: plaintext` on text boxes so mixed Arabic/Latin/numbers (phone numbers, URLs, "6:30") sit correctly without manual fiddling.

---

## 9. Extras worth building

- **QR generator** from a URL (they use Google Forms and WhatsApp links — see posters 1 and 2). `qrcodejs` from CDN; hide the feature if it fails to load.
- **Logo upload** (GSC crest) + **speaker photo upload** with circle / arch / rounded / none masks, plus a zoom-and-pan crop.
- **Event templates** that prefill fields, layout, background and palette in one click, one per poster type in the references.
- **Export**: PNG and JPG at ×1/×2/×3 via html2canvas — clone the stage into an off-screen container with no transform before capture, then remove it. Always also offer **Print → Save as PDF** as a fallback that needs no CDN.
- **Save/load draft**: debounced autosave to `localStorage`, plus "download draft (.json)" / "open draft" so two people can hand a poster back and forth.
- **Legibility check**: warn when text contrast against the background falls below WCAG AA.
- **Overflow warning**: flag any text box whose content spills past the canvas edge before they export.
- **Duplicate for series**: "new poster, same design" keeps background/layout/fonts and clears the text — most of their posters are a monthly series.

---

## 10. Build order

Work in phases and verify each one in a browser before moving on. Commit after each.

1. Shell + stage + zoom-to-fit + DOC model + render loop. *(the starter file already covers most of the chrome)*
2. Backgrounds + palettes, switching live.
3. Layouts + content form, two-way bound to the canvas.
4. Selection, drag, resize, snapping, undo/redo.
5. Inline editing + sub-selection toolbar.
6. Inspector + layer list.
7. Arabic helpers, phrase library, templates.
8. Images, QR, export, drafts.
9. Design pass: re-read `DESIGN.md`, take screenshots, remove one accessory.
10. Write `README-ar.md` — a one-page Arabic guide for the committee — and author the `arabic-poster-design` skill.

---

## 11. Acceptance test

Rebuild **all four reference posters** in the app, from templates, with no manual CSS. This is a test of *coverage*, not fidelity: every piece of information on each original must have a home, and each rebuild should be visibly better designed than the original. Screenshot them side by side and write one line per poster in `DESIGN.md` naming what you improved. If any of them can't be built, the layout or background set is incomplete — fix it, don't rationalise it.

Then produce **two alternate treatments of poster 1** using Tier-2 backgrounds — one `inverted`, one `kufic` or `rule-grid`. If those don't look meaningfully more contemporary than the original, Tier 2 hasn't done its job yet.

Then: hand-check that a user can change the date on a finished poster in **under 10 seconds** without anything else moving.

---

## Appendix — what already exists

`starter-shell.html` (306 lines) in this folder is a working shell you should use as your base. It contains:

- Google Fonts link for 10 Arabic-capable families: Cairo, Tajawal, Almarai, Amiri, Reem Kufi, Aref Ruqaa, El Messiri, Noto Kufi Arabic, Changa, Marhey.
- A full dark "workbench" app theme — deep slate panels with a brass accent, chosen so the cream poster reads as physical paper on a dark table. Design tokens are CSS variables at `:root`.
- Styled primitives: buttons, form fields, segmented controls, toggle switches, preview cards, chips, section headers, layer list, modal, toast.
- Stage + scaler + background layer + element layer structure.
- Complete selection-frame CSS: 8 handles, dashed green editing state, role tag, snap guides, hover box.
- Floating text toolbar, zoom bar, modal scrim, toast.
- Responsive rules — panels collapse to bottom sheets with a tab bar under 940px.
- A `@media print` block that hides all chrome so Print → Save as PDF produces a clean poster.

The `<body>` is empty. Everything from the markup down is still to be built.

**Note on the starter's aesthetic:** it is a defensible direction, not a mandate. Read `frontend-design`, form your own view, and if you think the chrome should be different, change it — but say why in `DESIGN.md`. The one thing that should not change is that the app chrome must stay visually quiet, because the poster is the subject.
