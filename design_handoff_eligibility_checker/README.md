# Handoff: Eligibility Checker — visual refresh + animated progress figure

## Overview
This is a restyled version of the GLF Teacher Training eligibility checker (`philchurch77/teach_first`, Django app, `flow` app). It keeps the existing flow logic and content exactly as-is and changes two things:

1. **Visual refresh** of the page: two-column layout (progress rail + question card), new type system, refined option buttons, long statement text parsed into paragraphs / bullets / sub-headings / links, and a **Back** control alongside "Start again".
2. **An animated progress figure** — a compact ring (arc) in a small card in the left rail that fills and shifts colour green → gold as the candidate advances, with a travelling head dot, milestone ticks at stage boundaries, stage number inside the ring, and a stage label + "N% complete" line beneath it.

A second figure variant (a growing tree) is also implemented in the prototype behind a toggle. **The ring is the chosen design.** The tree is optional/not required — implement the ring.

## About the Design Files
`Eligibility Checker.dc.html` in this bundle is a **design reference created in HTML** — a working prototype showing intended look and behaviour, not production code to copy verbatim. It is a self-contained React-ish component file with inline styles and the full `FLOW` tree duplicated in JavaScript.

The task is to **recreate this design in the existing Django codebase** using its established patterns:
- `flow/templates/flow/flow.html` — the single template (server-rendered, one node per request, POST → redirect → GET).
- `flow/flow_data.py` — the `FLOW` dict (source of truth for content; do not rewrite copy).
- `flow/views.py` — `flow_view`, session-backed `node_id`.
- `flow/static/flow/` — static assets (`TSH.jpg` logo).

Do **not** introduce a JS framework. Everything here can be done with the existing template plus a `<style>` block (or a static CSS file) and ~30 lines of vanilla JS for the animation. Keep server-side flow logic authoritative.

## Fidelity
**High fidelity.** Colours, type, spacing, radii, shadows, SVG geometry and animation timings below are final — match them. Where the prototype and this README disagree, this README wins.

---

## Screens / Views

There is one screen, rendered for every node in `FLOW`.

### Page shell
- `body`: background `#f4efe6`, colour `#211e19`, font `Newsreader, Georgia, serif`, margin 0.
- Page wrapper: `min-height: 100vh`, `padding: 34px 26px 60px`, background:
  ```css
  radial-gradient(1200px 600px at 12% -10%, rgba(31,95,91,.13), transparent 60%),
  radial-gradient(900px 520px at 108% 112%, rgba(180,133,67,.16), transparent 60%),
  linear-gradient(180deg, #f8f4ed 0%, #f2ece1 100%)
  ```
- Inner container: `max-width: 1180px; margin: 0 auto; display: flex; flex-direction: column; gap: 26px`.

### Header (centred, above both columns)
- Eyebrow: "GLF TEACHER TRAINING" — IBM Plex Sans, 11px, 600, `letter-spacing: .22em`, uppercase, `#655d51`.
- H1: "Are you eligible for teacher training?" — Newsreader, `font-size: clamp(2rem, 4.4vw, 3.1rem)`, weight 500, `line-height: 1.02`, `letter-spacing: -.015em`, colour `#123f3c`, `text-wrap: balance`. Sentence case (not uppercase — this is a change from the current page).
- Sub-line: "Answer a few questions and we will point you to the route, the paperwork and the people who can help." — 1.02rem, `line-height: 1.5`, `#6b6255`, `max-width: 46ch`.

### Two-column body
`display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start`
- Left rail `<aside>`: `flex: 1 1 250px; max-width: 320px; position: sticky; top: 24px; display: flex; flex-direction: column; gap: 18px`.
- Right `<main>`: `flex: 1 1 520px; min-width: 0`.
On narrow viewports the rail wraps above the card automatically (no media query needed).

---

### Component 1 — Progress figure card (left rail, top)
Container:
- `background: linear-gradient(180deg,#fffdf8 0%,#fff 100%)`, `border: 1px solid #e0d4c1`, `border-radius: 22px`, `box-shadow: 0 14px 34px rgba(49,37,17,.09)`, `padding: 12px 14px 14px`, `display: flex; flex-direction: column; gap: 8px`.
- Everything must stay **inside** this box — the SVG viewBox is sized so the glow never overflows. Do not use `overflow: visible` on the SVG.

SVG: `viewBox="0 0 200 152"`, `width: 100%; max-height: 190px; height: auto; display: block`.

Geometry (centre `(100,104)`, radius `76`, arc spans 220° from 200° to −20°, total length **291.8**):
```html
<!-- track -->
<path d="M28.6 130 A76 76 0 1 1 171.4 130" fill="none" stroke="#e6dccb"
      stroke-width="10" stroke-linecap="round"/>
<!-- progress -->
<path d="M28.6 130 A76 76 0 1 1 171.4 130" fill="none" stroke="url(#arcGrad)"
      stroke-width="10" stroke-linecap="round"
      stroke-dasharray="291.8" stroke-dashoffset="<291.8*(1-p)>"/>
```
Gradient (`userSpaceOnUse`, `x1="24" y1="104" x2="176" y2="104"`): stop 0 `#1f5f5b`, stop .55 `#3f7d63`, stop 1 `#c08a3e`.

Point on the arc for a progress fraction `p` (0–1):
```
theta = (200 - 220 * p) * PI / 180
x = 100 + 76 * cos(theta)
y = 104 - 76 * sin(theta)
```

- **Milestone ticks**: `<circle r="2.4">` at `p = 0.2, 0.4, 0.6, 0.8` using the formula above. Fill `#fffdf8` when `p >= tick`, else `#cfc2ad`.
- **Head marker**: a `<g transform="translate(x y)">` at the current `p` containing three circles:
  - `r="12"`, fill = head colour, `opacity: .26`, animation `headPulse 2.4s ease-out infinite`, **`transform-box: fill-box; transform-origin: center`** (required — without `fill-box` the scale animation resolves against the SVG view-box and the glow flies out of the card; this was a real bug).
  - `r="8"`, fill `#fffdf8`.
  - `r="5"`, fill = head colour.
  - The `<g>` carries `transition: transform 980ms cubic-bezier(.34,1.56,.64,1)`.
  - Head colour interpolates with progress: `oklch(calc(0.42 + 0.16p) calc(0.07 + 0.05p) calc(178 - 100p))` — i.e. `oklch(0.42 0.07 178)` at 0% → `oklch(0.58 0.12 78)` at 100%. A fixed pair (`#1f5f5b` → `#c08a3e`) interpolated in oklch is fine.
- **Stage number** inside the ring: `<text x="100" y="112" text-anchor="middle">` — Newsreader, 40px, weight 400, fill `#123f3c`, content `01`–`05` (zero-padded).

Below the SVG, one row (`display: flex; align-items: baseline; justify-content: space-between; gap: 10px; padding: 0 4px`):
- Stage label — IBM Plex Sans 11px/600, `letter-spacing: .14em`, uppercase, `#6b6255`.
- "N% complete" — IBM Plex Sans 12px/500, `#655d51`.

Keyframes:
```css
@keyframes headPulse { 0% { transform: scale(1); opacity: .5 } 70%,100% { transform: scale(2.6); opacity: 0 } }
```

### Component 2 — Stage list (left rail, middle)
`display: flex; flex-direction: column; gap: 2px; padding: 4px 6px`. Five rows, one per stage (see Stage model below). Each row: `display: flex; align-items: center; gap: 12px; padding: 9px 8px; border-radius: 12px`.
- Dot: 9×9px circle.
  - past stage: `#c08a3e`
  - current stage: `#1f5f5b` plus `box-shadow: 0 0 0 4px rgba(31,95,91,.16)`
  - future stage: `#d9ccb8`
- Label: IBM Plex Sans 13px/500. Current `#123f3c`; past `#5b5347`; future `#7d7466`.
- Current row background: `rgba(255,253,248,.9)`; others transparent.

### Component 3 — Answer trail (left rail, bottom; only when at least one question answered)
`padding: 16px 18px; border: 1px solid #e6dccb; border-radius: 20px; background: rgba(255,253,248,.7); display: flex; flex-direction: column; gap: 10px`.
- Heading "YOUR ANSWERS" — IBM Plex Sans 10px/600, `letter-spacing: .2em`, uppercase, `#655d51`.
- Up to the **6 most recent** answered questions, **newest first**. Each entry: question title at `.84rem`, `#655d51`, `line-height: 1.3`; chosen answer label at `.98rem`, `#123f3c`, `line-height: 1.35`.

### Component 4 — Question / statement card (right column)
- Outer: `background: linear-gradient(180deg,#fffdf8 0%,#fff 62%)`, `border: 1px solid #e0d4c1`, `border-radius: 28px`, `box-shadow: 0 26px 60px rgba(49,37,17,.12)`, `overflow: hidden`.
- Top edge strip: 6px tall, `background: linear-gradient(90deg,#1f5f5b,#c08a3e)`.
- Inner padding: `30px 32px 26px`.
- Header row: `display: flex; align-items: flex-start; gap: 20px; justify-content: space-between`.
  - Left stack (`gap: 10px`): kind eyebrow — "QUESTION" for `type: "question"`, "INFORMATION" for `type: "statement"` — IBM Plex Sans 10px/600, `letter-spacing: .2em`, uppercase, `#655d51`; then `<h2>` with `node.title`: Newsreader, `clamp(1.5rem, 2.8vw, 2.1rem)`, weight 500, `line-height: 1.1`, `letter-spacing: -.01em`, `#211e19`, `text-wrap: pretty`.
  - Right: logo `flow/static/flow/TSH.jpg`, `height: 52px; width: auto; border-radius: 8px`, `alt="GLF Teacher Training"`. (Replaces the absolutely-positioned `.card-logo`.)
- Body text block: `display: flex; flex-direction: column; gap: 12px; margin: 22px 0 26px; max-width: 68ch`.

**Text parsing rules** (replaces `|urlize|linebreaksbr`). Split `node.text` on newlines, trim, drop empties, then per line:
- Lines starting with `•` render as a bullet row: `display: flex; gap: 10px; align-items: baseline`, marker `●` in `#c08a3e` at 1.1rem, and the rest of the line as body text.
- A line is a **sub-heading** if it is not a bullet, not a `N)` numbered item, ≤ 46 characters, does not end in `. : , ; ! ? )`, is not a URL and contains no `@`. Style: 1.16rem, weight 600, `#123f3c`, `line-height: 1.4`, `margin-top: 8px`. (This is what turns "Salaried Route", "Assessment Only Route" etc. into headings.)
- All other lines: body text — 1.06rem, `line-height: 1.62`, `#4b453c`, `overflow-wrap: anywhere`, `text-wrap: pretty`.
- URLs (`https?://…`) and emails become links: `#144643`, weight 500, `text-decoration: underline`, `text-decoration-color: rgba(20,70,67,.35)`, `text-underline-offset: 3px`. Emails get `mailto:`. Trailing `. , ; : )` must be stripped from the matched token and kept as plain text (careful: `…&route=shorturl` URLs must not be truncated).

Note `flow_data.py` currently contains HTML entities (`&amp;`) inside Python strings — with this parsing they will render literally. Either change those to `&` in the data or mark the rendered text safe consistently; do not leave `&amp;` visible.

- Options: `display: grid; gap: 10px`. One `<form method="post">` per option (keep the existing hidden `next` input + `csrf_token`); the button:
  - `display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; font-size: 1.05rem; color: #211e19; background: #fff; border: 1px solid #ded2be; border-radius: 16px; padding: 15px 18px; cursor: pointer`
  - `transition: transform 180ms cubic-bezier(.34,1.5,.64,1), border-color 180ms ease, box-shadow 180ms ease, background 180ms ease`
  - hover/focus-visible: `transform: translateY(-2px); border-color: #1f5f5b; background: #fffdf8; box-shadow: 0 14px 28px rgba(31,95,91,.14)`
  - active: `transform: translateY(1px) scale(.995)`
  - Leading key badge: 26×26 circle, `border: 1px solid #ded2be`, IBM Plex Sans 11px/600, `#6b6255`, content `A`, `B`, `C`… by option index.
  - Middle: option label, `line-height: 1.4`, `text-wrap: pretty`, `flex: 1 1 auto`.
  - Trailing `→` in `#c08a3e`, 1.05rem.
- Card footer: `margin-top: 28px; padding-top: 18px; border-top: 1px solid #ece3d4; display: flex; flex-wrap: wrap; gap: 14px 22px; align-items: flex-end; justify-content: space-between`.
  - Left: existing "Web address: www.glftt.org" / "Email address: info@glftt.org" lines — `.95rem`, `#6b6255`; links `#144643`, weight 600, no underline.
  - Right: **Back** (only when there is history) — IBM Plex Sans 13px/500, `#6b6255`, `border: 1px solid #ded2be`, `border-radius: 999px`, `padding: 8px 16px`, transparent background; hover `border-color: #1f5f5b; color: #144643`. Then **Start again** — same font, `#144643`, underlined, `text-underline-offset: 3px`, `padding: 8px 12px`.

### Card content entrance animation
The whole inner content block (eyebrow → options, not the footer) animates in on each node change:
```css
@keyframes swoop { from { opacity: 0; transform: translateY(16px) } to { opacity: 1; transform: none } }
/* applied as: animation: swoop 520ms cubic-bezier(.22,1.3,.36,1) both; */
```
Server-rendered, so it simply runs on page load — no JS needed.

---

## Interactions & Behavior
- **Answering**: unchanged — POST `next`, store in session, redirect, GET renders the next node.
- **Back**: push the current `node_id` onto a session list before navigating; Back pops it. Clear the stack when `next == "start"`. Render the Back control only when the stack is non-empty.
- **Answer trail**: when leaving a node whose `type == "question"`, append `{question: node.title, answer: <chosen option label>}` to a session list (the POST needs the chosen label — add a hidden `label` input, or look it up from `FLOW[current]["options"]` by `next`). Clear on reset/"start". Display last 6, reversed.
- **Arc animation across page loads** (important — the page is server-rendered, so the fill has to animate from the *previous* value):
  1. Keep `prev_p` in the session (the `p` of the node rendered last time; default 0).
  2. Render the progress path with `stroke-dashoffset = 291.8 * (1 - prev_p)` and the head group translated to `pointAt(prev_p)`; put the target values in `data-` attributes.
  3. On `DOMContentLoaded` + one `requestAnimationFrame`, set the offset/transform to the target values so the CSS transitions run: `stroke-dashoffset 980ms cubic-bezier(.34,1.56,.64,1)` and the same for the head `transform`. Also swap tick fills and the head colour at that point.
  4. `prefers-reduced-motion: reduce` → skip step 3's transition (render target values immediately; keep `headPulse` off too).
- **Hover/active states**: as specified per component above. Mirror every `:hover` with `:focus-visible` (keyboard users) — the current template already does this.
- **Responsive**: single flex-wrap breakpointless layout; below ~820px the rail stacks above the card. Keep `padding: 22px 16px 16px` on the wrapper and `padding: 22px` on the card under 640px, as in the current template.

## State Management
Server-side, in `request.session`:
- `node_id` — current node (existing).
- `history` — list of node ids for Back.
- `trail` — list of `{question, answer}` dicts (cap at ~12 stored, display 6).
- `prev_p` — progress fraction of the previously rendered node, for the animation.

Template context to add: `p` (float 0–1), `pct` (int), `stage_index` (0–4), `stage_label`, `stages` (list of `{label, state}` where state ∈ `past|current|future`), `prev_p`, `head_x/head_y`, `prev_head_x/prev_head_y`, `ticks` (list of `{x, y, reached}`), `can_back`, `trail`.

## Progress model
Add a `p` value to each node in `flow_data.py` (this is the only content-file change needed). Values used in the prototype:

| node | p |
| --- | --- |
| start | 0.04 |
| eligibility_2, overseas_candidate_statement | 0.12 |
| overseas_eligibility_3, overseas_3_no_statement, overseas_3_not_enough, domestic_eligibility_1, domestic_1_no_gcse | 0.20 |
| overseas_eligibility_4, overseas_4_no_statement, overseas_4_not_enough, domestic_eligibility_2, domestic_2_no_degree | 0.28 |
| overseas_eligibility_5 | 0.36 |
| routes_into_teaching_1 | 0.44 |
| routes_into_teaching_salary_info, routes_into_teaching_fee_info | 0.50 |
| employment_routes_1, employment_routes_no_experience, fee_funded_routes_1 | 0.56 |
| employment_routes_2, fee_funded_full_time, fee_funded_flexible | 0.62 |
| subject_phase_1 | 0.70 |
| subject_phase_2, subject_phase_3 | 0.76 |
| training_locations | 0.84 |
| next_steps_1 | 0.90 |
| next_steps_2 | 0.93 |
| next_steps_3 | 0.95 |
| events, contact_us | 0.98 |
| closing_statement_1–4 | 1.00 |

Stages (labels in order): `Eligibility`, `Training route`, `Subject & phase`, `Location`, `Next steps`.
Derive the stage from `p`: `p < 0.4 → 0`, `< 0.68 → 1`, `< 0.8 → 2`, `< 0.86 → 3`, else `4`.

## Design Tokens
Colours
- Page background `#f4efe6`; gradient stops `#f8f4ed`, `#f2ece1`
- Panel `#fffdf8` → `#fff`; borders `#e0d4c1`, `#ded2be`, `#e6dccb`, `#ece3d4`
- Ink `#211e19`; body text `#4b453c`; muted `#6b6255` / `#655d51`; future/disabled `#7d7466`
- Brand green `#1f5f5b`; deep green `#123f3c`; link green `#144643`; mid green `#3f7d63`
- Gold `#c08a3e`; track `#e6dccb`; tick unreached `#cfc2ad`; stage dot future `#d9ccb8`
- Head colour ramp: `oklch(0.42 0.07 178)` → `oklch(0.58 0.12 78)`

Typography
- Display/body: **Newsreader** (Google Fonts, weights 300–700, opsz 6–72) with `Georgia, serif` fallback
- UI/meta: **IBM Plex Sans** (400/500/600)
- Scale: h1 `clamp(2rem,4.4vw,3.1rem)`/500; h2 `clamp(1.5rem,2.8vw,2.1rem)`/500; body 1.06rem/1.62; option 1.05rem; sub-head 1.16rem/600; meta 13px, 12px, 11px, 10px (IBM Plex Sans, tracked uppercase)

Spacing: 2, 4, 6, 8, 10, 12, 14, 18, 22, 24, 26, 28, 30, 32, 34px
Radii: 12 (stage row), 16 (option), 20 (trail), 22 (figure card), 26/28 (main card), 999 (pill)
Shadows: figure card `0 14px 34px rgba(49,37,17,.09)`; main card `0 26px 60px rgba(49,37,17,.12)`; option hover `0 14px 28px rgba(31,95,91,.14)`
Motion: arc `980ms cubic-bezier(.34,1.56,.64,1)`; card entrance `520ms cubic-bezier(.22,1.3,.36,1)`; option hover `180ms cubic-bezier(.34,1.5,.64,1)`; leaf/colour fades `500–600ms ease`

## Assets
- `flow/static/flow/TSH.jpg` — existing logo in the repo, used top-right of the card at 52px tall. No new assets. All other graphics are inline SVG (circles, arcs, ellipses) — nothing to export.
- Fonts via Google Fonts: `https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..500&family=IBM+Plex+Sans:wght@400;500;600&display=swap`. If the deployment must avoid third-party requests, self-host both families in `flow/static/flow/fonts/`.

## Files
- `Eligibility Checker.dc.html` (in this bundle) — the full working prototype. The template markup is at the top; the `Component` class at the bottom holds `FLOW`, the arc/stage maths (`pointAt`, `STAGES`, `MOTION`), and the text parser (`parseText`, `splitParts`) — port those three pieces to Python/template/JS as appropriate.
- Target files to change: `flow/templates/flow/flow.html` (layout + styles + inline SVG + animation script), `flow/views.py` (history, trail, prev_p, stage context), `flow/flow_data.py` (add `p` per node; fix `&amp;` entities).

## Out of scope
- The tree variant (`isTree` branch in the prototype) — reference only, not part of the build.
- Any change to question wording, option labels, or flow routing. Content is verbatim from `flow_data.py`.

## Screenshots
`screenshots/01-state.png` … `04-state.png` — the same page at four points in the flow (20%, 76%, 93%, 100%), showing the ring filling and shifting green → gold, the stage list updating, and long statement text with sub-headings and links.

Note: the capture tool drops the stage number that sits inside the ring (`01`–`05`, Newsreader 2.3rem, `#123f3c`, centred on the ring). It is present in the prototype and is part of the design — see the Progress figure section above.
