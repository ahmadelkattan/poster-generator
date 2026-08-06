# DESIGN.md — مِرسام / Mirsam
### Arabic poster studio for the mosque committee, Gezira Sporting Club

Written before the build, per the two-pass process: **plan → critique → resolution**. Section 10 is
the critique of sections 3–9 and it changed several of them. Section 11 is filled in after the
acceptance test.

---

## 1. The one-line brief

A committee of non-designers has to produce a dignified Arabic announcement poster roughly twice a
month, forever, and the current method — asking an image model — breaks the Arabic, can't be edited,
and looks machine-made. Replace it with an HTML renderer they can actually drive.

## 2. What is actually wrong with the four references

These are named so they can be designed *against*, not carried forward.

| # | Problem | Where | Fix adopted |
|---|---|---|---|
| 1 | **Three accents competing.** Green, navy and gold all at full strength with no ranking. | all four | **Navy is demoted to ink.** Green is the single dominant accent, gold is subordinate and mostly hairline. A palette is now `deep` (dominant) + `gold` (subordinate) + `ink` (text) + `paper`, with `alt` reserved for *one* secondary block per poster, never a third shout. |
| 2 | **Clipart ornament.** The gold flourishes are stock dingbats. | 1, 2, 3 | All six dividers are **constructed** — girih strapwork, an 8-fold compass rosette, a kufic square, a muqarnas step, a two-centre arch cap, a plain rule with knot. Every path is generated from geometry in code, so it rescales and recolours honestly. |
| 3 | **Fake metal.** Bevelled, embossed, drop-shadowed gold — the `7,000` in poster 4. | 4, 3 | **No gradients on gold anywhere.** Gold is flat fill or a 1.5–3px hairline. There is no bevel, emboss, inner glow or metallic gradient anywhere in the codebase. Value numerals get scale and a flat badge instead. |
| 4 | **Text shadows and outlines** propping up contrast the layout should have given. | 2, 4 | No `text-shadow` on poster text. Contrast is solved structurally: dark type on paper, or a solid scrim panel behind type on photography. A WCAG AA checker warns when it isn't. |
| 5 | **Inconsistent margins.** Poster 4's four edges disagree. | 4, 2 | Every background function **publishes a safe-area rect**; every layout positions against that rect, not against the canvas. One margin token (8.9% = 96px at 1080) unless a background genuinely needs to intrude. |
| 6 | **Photo with no tonal relationship** to the paper — a stock headshot dropped in an arch. | 2 | Photo elements get a **duotone** option (`feColorMatrix` → palette `deep`/`paper`), a multiply blend option, and a gradient scrim. Default for the side-photo layout is duotone on, so it belongs. |
| 7 | **Bottom-heavy clutter** — stacked bars, numbers and footnote strips fighting at the base. | 3, 4 | Layouts allow **one** footer object. The contact bar is a single row; a second one has to be a deliberate act. Meta rows move up into the content column where they read as information, not as sediment. |
| 8 | **Decoration that carries no information.** Mosque silhouettes because mosque. | 3, 4 | Ornament policy (§7): every ornament must **separate, frame, anchor or direct**. The skyline background survives only because it anchors to a baseline rule and defines the safe area's bottom edge. |

## 3. The governing idea — *printed, not generated*

Every one of those eight problems is a tell of screen-origin: bevels, glows, soft shadows, stock
vectors, drifting bleed. So the constraint for the whole system is:

> **Nothing on the poster may be anything a two- or three-plate print job couldn't do.**

Flat colour, hairlines, real registration, knockout white, honest overprint. No gradient may exist
except a deliberate one-stop scrim over photography. This single rule kills all eight failure modes
at once and — more usefully — it gives a committee with no design training a look that stays
coherent even when they push things around, because the ingredient list is short enough to be
non-toxic in any combination.

The house it belongs to is Egyptian institutional print: Awqaf notices, club bulletins, mosque
boards. Confident, plain, generous margins, one strong colour.

## 4. Colour

Tokens, never hex, in the document model: `deep · alt · gold · paper · ink`. Palette swap recolours
the whole poster. Sampled from the references, then corrected for print honesty.

| palette | deep | alt | gold | paper | ink | note |
|---|---|---|---|---|---|---|
| `gsc` | `#0C4A2E` | `#12395F` | `#B4862B` | `#F1E7DD` | `#16283C` | club green/navy/gold/cream. Default, always first. Sampled: green `#0E452C`, navy `#0E2861`, gold `#B77F11`, paper `#F1E7DD`. |
| `navy` | `#12395F` | `#0C4A2E` | `#B4862B` | `#F1E7DD` | `#101E2E` | the club's own two colours, swapped |
| `emerald` | `#0A5540` | `#1B4D3E` | `#C09135` | `#F3EDE2` | `#122A24` | brighter, for Eid |
| `maroon` | `#6B1F2A` | `#3A2320` | `#B08A3E` | `#F4EBE0` | `#2A1417` | Muharram / Ashura register |
| `teal` | `#0B4A52` | `#123A63` | `#B08C3C` | `#EEEAE0` | `#10262B` | |
| `charcoal` | `#22282B` | `#3E4A4E` | `#B08D42` | `#EFEBE3` | `#171B1D` | |
| `royal` | `#1E3A8A` → `#20386F` | `#0C4A2E` | `#BC9134` | `#F2EDE4` | `#14203A` | |
| `sand` | `#8A6A2F` | `#4A3C22` | `#7A5C1E` | `#F5EFE1` | `#2A2415` | tone-on-tone, quiet |
| `bone` ★ | `#141414` | `#2E2C28` | `#9C8248` | `#EDE8DC` | `#141414` | **near-black / bone.** They would never pick it. It is the most contemporary thing in the set. |
| `olive` ★ | `#3D4A24` | `#8C4A2F` | `#A98A3E` | `#F0E9DA` | `#22281A` | **deep olive / terracotta.** Warm, earthy, un-corporate. |

★ = the two the brief asked for that extend past what they know.

**Ranking rule, enforced by the layouts:** `deep` may cover large areas. `gold` may not exceed roughly
5% of the canvas and is hairline by default. `alt` is allowed on at most one block. `ink` does the
reading.

## 5. Typography

Ten Arabic families load from the starter. The working pairs:

| pairing | display / head | body | when |
|---|---|---|---|
| **house** (default) | **Reem Kufi** — geometric kufic, flat terminals, no swashes. It is the closest thing in the Google library to a drawn institutional letter. | **Cairo** — neutral, high legibility at small sizes, huge weight range. | lectures, notices — the workhorse |
| **formal** | **Aref Ruqaa** | **Amiri** | Eid greetings, Qur'anic occasions |
| **modern** | **Noto Kufi Arabic** | **Tajawal** | the Tier-2 dark and Swiss directions |
| **warm** | **El Messiri** | **Almarai** | social / family events |

Type scale, in design-px against the 1080 reference (scaled by `W/1080`):

```
kicker    40 / 1.5     title   118 / 1.12    connector 46
name     108 / 1.2     desc     33 / 1.75    meta      38 / 1.4
footer    30 / 1.4     micro    26
```

Ratio ≈ 1.33 between steps, deliberately with a **big** jump from body to title. The references are
timid in the middle and shouty at the top; a wide gap with nothing in it is what makes a poster
read from across a courtyard.

**Arabic-specific:** `letter-spacing` defaults to `0` on every text element and is labelled as risky
in the inspector, because positive tracking breaks Arabic joining. `dir="rtl"` +
`unicode-bidi: plaintext` on every text box so phone numbers, URLs and "6:30" sit correctly with no
fiddling. Line-height floors at 1.1 for display sizes so descenders and the *hamza* stack don't
collide.

## 6. Grid and safe area

Canvas 1080 wide (design reference). **Margin token = 96px = 8.9%.** Everything is stored in
percentages so the four canvas sizes share one layout.

Every background exposes `safe: {x, y, w, h}` in percent. A background with a header band pushes
`safe.y` down; a side-band background narrows `safe.w`. Layouts *only* place inside the safe rect.
This is the single mechanic that fixes problem #5, and it is why backgrounds are functions, not
images.

## 7. Ornament policy

An ornament ships only if it does one of four jobs:

- **separate** — divider between content blocks
- **frame** — border that contains and dignifies
- **anchor** — weight at an edge that stops the composition floating
- **direct** — leads the eye from one block to the next

Six dividers, all constructed: `rule` (hairline + centre knot), `girih` (8-point strapwork band),
`rosette` (16-fold compass construction, hairline), `kufic` (square-kufic bar), `muqarnas` (stepped
profile), `diamond` (nested lozenges). No dingbat, no swash, no gradient, no metal.

## 8. Backgrounds as a parametric system

`bg(id, palette, opts, W, H) → { svg, safe }`. Pure SVG strings, no bitmaps, so they recolour and
re-proportion cleanly at any canvas size.

**Tier 1 (8)** — their vocabulary, done properly: `wave · arch · skyline · frame · banner · geo ·
split · minimal`.
**Tier 2 (10)** — directions they have never had: `mashrabiya · kufic · inverted ·
calligraphic-ground · zellige · negative-arch · rule-grid · edge-wash · duotone-photo ·
radial-rosette`. Plus upload-your-own with scrim + duotone.

Options — `scale · placement · intensity · weight · inverted` — so 18 motifs yield hundreds of
usable grounds. **Shuffle** samples the option space six at a time, because non-designers choose far
better from options than from sliders.

## 9. App chrome

Kept the starter's direction — dark warm-slate workbench, brass accent — for one reason that
survives scrutiny: **the poster is cream, so the chrome must be dark or the paper stops reading as
paper.** A light UI would make the poster look like a `<div>`.

Changed from the starter:
- Brass pulled back to selection, focus and the primary button only. In the starter it was also on
  card captions and switches, which put a third accent in the *tool* — the exact mistake the posters
  make.
- Warmed the neutrals (a green-grey cast rather than blue-grey) so the chrome and the cream poster
  sit in the same light rather than reading as two screenshots.
- Panel type down to 12.5–13px with more line-height. The committee reads Arabic UI labels; Arabic
  at small sizes needs air.
- Added a persistent **poster-first** rule: at any viewport the stage never goes below 45% of the
  window width, and under 940px the panels become bottom sheets over a full-bleed stage.

---

## 10. Critique pass

Read back against the brief. What was wrong with sections 3–9 on first pass, and what changed.

**C1 — "printed, not generated" risked becoming "beige and boring."**
The rule bans effects, and a committee poster with no effects and timid colour is just a memo. The
answer isn't to re-admit gradients, it's to spend the saved energy on **scale and void**: the type
ramp in §5 got a much wider gap between body and title, and `minimal`, `rule-grid` and `inverted`
were given the largest safe-area margins in the set rather than the smallest. Nerve is the
substitute for decoration.

**C2 — the palette table originally had `royal` at `#1E3A8A`.**
That is Tailwind's blue-800. It is the single most recognisable "AI made this" colour on the web and
it has no business next to sampled Egyptian print colours. Corrected to `#20386F`, which is a
printed royal blue, not a screen one. *(This is exactly the class of default the brief is asking to
be beaten, so it is worth naming.)*

**C3 — nine of the ten palettes were dark-on-cream.**
The set claimed range it didn't have. `bone` and `olive` were added as required, but more
importantly `inverted` was promoted from "a background" to a **cross-cutting option on every
background**, so any of the eighteen can go dark. That is where the real range comes from.

**C4 — the ornament policy had no teeth.**
"Must earn its place" is a slogan unless something enforces it. Made concrete: the divider set is
capped at six, dividers are elements with roles so they can be deleted like anything else, and no
background emits a decorative element that isn't also defining the safe area. The mosque skyline
survives *only* because it sets `safe.h`.

**C5 — the type scale was specified in px against 1080 but the sub-selection toolbar sizes in `em`.**
These two systems have to agree or a box scale corrupts inline spans. Resolved: element `size` is
design-px, every inline span written by the mini-toolbar is `em` and therefore relative to it.
Nothing writes inline `px`. Stated here because it is the kind of thing that silently rots.

**C6 — "layout switching preserves text" is not free.**
Preserving by array index breaks the moment two layouts have different element counts. Resolved:
**preserve by `role`**. Text migrates from old `title` to new `title`; a role with no home is kept
as a free element rather than dropped. Roles are the join key throughout the app — layouts,
templates, inspector labels and the content form all key off them.

**C7 — the brief wants a date change in under 10 seconds.**
That is a layout-stability requirement, not a form requirement. It means the date meta row must not
reflow anything else when its text length changes — so meta rows are their own element with a fixed
box, `h` auto, and the elements below them are positioned absolutely rather than in flow. Already
true of the architecture, but it is the reason for it, so it is written down.

**C8 — `web-artifacts-builder` was reviewed and deliberately not adopted.**
It targets React + Tailwind + shadcn on claude.ai. This ships as one `file://` HTML document with no
build step, so its tooling is inapplicable. What was taken from it: the discipline of a single
source of truth for state and full re-render on change, which is what `DOC` + `render(skipId)` is.

---

## 11. What the build changed

Five things the plan got wrong and the code corrected. Recorded because they are the parts a
future session is most likely to break again.

**B1 — `ord` had to become a row number, not a sequence.** The first flow pass stacked each
`col` independently from the top of the safe area, so `greeting`'s two venue boxes and
`two-col`'s two columns landed on top of the title. Elements sharing an `ord` now flow side
by side on one line. §C6's role-keyed preservation was right; the vertical model wasn't.

**B2 — palette inversion is not one mapping, it is two.** Under a dark ground the same token
has to resolve *light* when it paints type and stay *dark* when it paints a panel behind
type. `C(tok, pal, use)` takes a usage argument for exactly this; without it, `deep` headings
vanished into a `deep` field. Related: three backgrounds (`inverted`, `duotone-photo`,
`upload`) are dark by construction, so inversion is `DARK_BG[bg] XOR opts.inverted`, not the
option alone.

**B3 — gold cannot carry display text.** §4 said gold is subordinate and mostly hairline, but
the `badge`, `closing` and one `kicker` were specified in gold anyway. On cream that is about
2.6:1 — the app's own WCAG check failed its own default templates. Those roles moved to
`deep`. Gold now appears only as rules, ornament and hairline borders, which is what §4
actually claimed. The `sand` palette's `deep` was darkened for the same reason.

**B4 — a two-centre arch must be derived from its apex.** Choosing a spring line directly put
the apex off the top of the canvas on 4:5 and 9:16, and the "arch" read as two vertical
lines. `spring = apexY + √(R²−d²)`. The frame also narrows toward the top, so the safe rect
is measured slightly *below* the content start rather than at it.

**B5 — the RTL stage overflowed leftward.** `#stage` is always 1080 CSS px and `#scaler` is
1080×zoom, so in an RTL document the over-wide child overflowed to the left and sat partly
off-canvas at every zoom below 100%. `#scaler` is now `direction:ltr` with the poster itself
`direction:rtl`.

Two performance/correctness traps are documented in `.claude/skills/arabic-poster-design/`:
inline SVGs need `xmlns` or html2canvas waits out a 15s image timeout on each one, and the
export has to run in a bare iframe because html2canvas clones the whole owner document —
including all nineteen background previews in the side panel.

**On the QR encoder:** it was cross-checked module-for-module against `segno`, an independent
implementation. That found a transposed format-information block — the symbols looked
completely plausible and no scanner could have read one. Anything touching that code should
re-run the comparison.

## 12. Acceptance test

All four references rebuilt from templates with no manual CSS, plus two Tier-2 alternates.
Run `proof.html` to see each rebuild beside its original. Verified at 1080×1350; every
template reports zero overflow and zero WCAG AA failures, as does every background paired
with its first recommended layout, across all ten palettes and with `inverted` both ways.

- **Poster 1 — اللقاء الشهري (lecture).** `lecture` template · `wave` · `gsc` · `classic`. The corner sweep is one confident curve with a single trailing hairline instead of three stacked bands; the title sits inside a published safe area instead of colliding with the curve; the two stock gold dingbats are replaced by one constructed girih band doing the separating; navy is demoted to ink so green reads as the only accent, and the crest is knocked out of the green field instead of floating on the boundary.
- **Poster 2 — لقاء شهري with speaker photo.** `speaker` · `wave` · `gsc` · `side-photo`. The photo is duotoned into the palette and arch-masked with the same two-centre geometry as the arch background, instead of dropped in as a stock cut-out with its own colour temperature; the whole arrangement is mirrored so the text column starts on the right, which is where RTL reading actually begins; the QR moved into the footer band so the base is one row, not three competing objects.
- **Poster 3 — عيد الأضحى greeting.** `eid` · `arch` · `emerald` · `greeting`. The traced blob is now a constructed pointed arch with a correct spring line and a safe area that follows the curve; the mosque silhouette is gone because it was doing no structural work, and its anchoring job is done by the arch base and one baseline rule; the two venue boxes share one border weight and one radius and are ordered right-to-left by importance; all bevelled gold is flat.
- **Poster 4 — صكوك الأضاحي voucher.** `voucher` · `banner` · `gsc` · `offer`. The embossed metallic `7,000` — the most dated element in the whole set — is flat, much larger, and sits in a hairline badge, which reads louder rather than quieter; the header band's lower edge is a real corbelled muqarnas hood rather than a decorative scallop; the four disagreeing margins are replaced by one published safe area; the stacked bottom bars collapse to a single contact row plus one footer line.
- **Alternate A — poster 1 as `inverted` / `bone` / modern pair.** Near-black ground, bone type, one gold hairline frame and one gold divider. Nothing else. The committee has never issued a dark poster and this is the single biggest jump in apparent contemporaneity in the set.
- **Alternate B — poster 1 as `rule-grid` / `charcoal` / `meta-first`.** No ornament at all: a hairline grid, one gold rule, and the meta row promoted to the top. Everything else earned by type.

**Date-change check.** Step 4 → pick a date → the calendar row rewrites to
`الثلاثاء، ١٨ أغسطس ٢٠٢٦`. Because auto-flow runs only on structural change, nothing else on
the poster moves. Two clicks, well inside ten seconds.

**Accessory removed in the design pass:** the `frame` background drew three concentric
things at each corner — an 8-fold rosette, a second rosette at 52%, and a centre dot. The
inner ring was texture rather than construction, so it went. The outer rosette frames the
corner and the dot marks the compass centre it was struck from; both earn their place under
§7, the middle ring did not.

What survived the same test and why, since "must earn its place" is otherwise just a slogan:
the meta row's vertical rule separates the icon column from the text; the dotted rules
separate one row from the next; they do different jobs, so both stay. The arch's finial is
an architectural terminal, not a dingbat, so it stays too.

- **Poster 1 — اللقاء الشهري (lecture).** Rebuilt from the `lecture` template on `wave`/`gsc`/`classic`. The corner sweep is one confident curve with a single trailing hairline instead of three stacked bands; the title now sits inside a published safe area instead of colliding with the curve; the two stock gold dingbats are replaced by one constructed girih divider doing the separating; navy is demoted to ink so green reads as the only accent. Same information, one accent fewer, wider air between kicker and title.
- **Poster 2 — لقاء شهري with speaker photo.** Rebuilt on `wave`/`gsc`/`side-photo`. The photo is duotoned into the palette and arch-masked with proper two-centre geometry instead of dropped in as a stock cut-out with its own colour temperature; the QR moved into the footer band so the base is one row, not three competing objects; the credentials paragraph is measured to a real column width rather than ragged to the photo edge.
- **Poster 3 — عيد الأضحى greeting.** Rebuilt on `arch`/`emerald`/`greeting`. The traced blob arch is now a constructed pointed arch with a correct spring line; the mosque silhouette is gone because it was doing no structural work, and its anchoring job is done by the arch base and a single baseline rule; the two detail boxes share one border weight and one radius instead of two blues at two weights; all bevelled gold is flat.
- **Poster 4 — صكوك الأضاحي voucher.** Rebuilt on `banner`/`gsc`/`offer`. The embossed metallic `7,000` — the most dated element in the whole set — is flat gold at a much larger scale in a hairline badge, which reads louder, not quieter; the four disagreeing margins are replaced by one published safe area; the stacked bottom bars collapse to a single contact row.
- **Alternate A — poster 1 as `inverted`/`bone`.** Dark ground, bone type, one gold hairline.
- **Alternate B — poster 1 as `rule-grid`/`charcoal`.** No ornament at all; hairline grid and a single gold rule carry the structure, everything else earned by type.
