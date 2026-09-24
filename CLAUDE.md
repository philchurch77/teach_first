# CLAUDE.md — GLF Teacher Training eligibility chatbot

A single-page Django app that walks prospective teacher-training candidates
through an eligibility and routes-into-teaching funnel. It is embedded on the
client's public website (glftt.org).

The Ship's Articles apply. This file records what they cannot infer.

## Data classification

```
Sensitive apps: none
Sensitive models: none
```

There are still **no models, no migrations, no login and no form that saves.**
No answer is written to a table of our own, and nothing is transmitted to any
third party. Article 1 (permission filtering) has nothing to bite on: no
queryset, no owner field, no PK in any URL. **The Gauntlet does not apply.**

**But this app is no longer free of personal data.** That changed when the
answer trail was added. The session now holds four keys:

| Key | What it is |
|---|---|
| `node_id` | the screen the visitor is on |
| `history` | up to 40 `{"id", "trailed"}` steps, for the Back control |
| `trail` | up to 40 `{"question", "answer"}` pairs — the visitor's own answers. Six are ever displayed; the rest exist so Back can unwind the whole journey |
| `prev_p` | the progress fraction last rendered, for the ring animation |
| `timed_out` | a one-shot flag, popped on the next render, so an expired session can say so |

`trail` is the one that matters. Both of its values are strings taken from
`FLOW`, but *the pairing is the visitor's answer* — so a session can record that
this device's owner has no confirmed right to work in the UK, no degree-level
comparability statement, or missing GCSE equivalence.

Sessions are database-backed, so those pairs sit in `django_session` on the
server. That makes them personal data under UK GDPR: a `sessionid` is an
identifier that singles out a device, and identifier plus answers is personal
data even with no name and no account. It is **not** Article 9 special category
data — nationality and immigration status are not in that list, and no question
asks about health, disability, ethnicity or religion — and it is **not**
children's data. Treat immigration status as sensitive in practice regardless.

Consequences, so nobody rediscovers them:

- **Retention is bounded deliberately, and half of it lives outside the code.**
  `SESSION_COOKIE_AGE` is one hour and `SESSION_EXPIRE_AT_BROWSER_CLOSE` is on,
  but Django never deletes expired rows by itself — **`manage.py clearsessions`
  must be scheduled** or the answers accumulate for the life of the deployment.
  That is step 7 of `DEPLOYMENT.md`. If you find it is not scheduled, that is a
  live finding, not a tidy-up.
- **No cookie is set until the visitor answers something.** `_render` skips the
  session write while they are still on `start` with no history, so merely
  landing on the page — or crawling it — creates neither a cookie nor a row.
  Keep that property; it is what makes the cookie defensible as necessary.
- **Never put an answer in a URL, a log line or a redirect.** Navigation is
  POST-then-redirect for exactly this reason.
- **Never send an answer to a third-party API.** Nothing does, and nothing
  should start.
- Adding a question about health, disability, ethnicity, religion, or age under
  18 would make this Article 9 data and change every answer above. Come back
  here first.

The honest line for the client is "no name, no contact detail, session-only,
nothing shared" — **not** "we collect no personal data", which was true before
the answer trail and is not true now.

If a saved enquiry form or a captured email address ever appears, this stops
being a session-only app and Article 0 applies properly. Update this section
before writing that code.

## Shape of the thing

There are **no models and no app migrations.** `flow/models.py` is empty and
`flow/migrations/` holds only `__init__.py`. Do not go looking for ORM problems,
`select_related` opportunities or `on_delete` decisions; there are none.

| File | What it is |
|---|---|
| `flow/flow_data.py` | **All the content.** One module-level `FLOW` dict, ~36 nodes, ~40KB of client-written prose. Nothing but content. |
| `flow/progress.py` | The progress model: `NODE_PROGRESS` (a fraction 0–1 per node), the five stages, the ring's arc geometry, and pure functions over them. No Django imports. |
| `flow/textblocks.py` | `parse_blocks(text)` — classifies each line of client prose as a sub-heading, a bullet run, a numbered point or a paragraph. |
| `flow/views.py` | One view plus session bookkeeping: Back history, the answer trail, progress context. POST-redirect-GET. |
| `flow/templates/flow/flow.html` | Page shell, question card, option forms, and the ~30-line inline ring animation. |
| `flow/templates/flow/_progress_figure.html` | The inline SVG ring. Its geometry pairs with `flow/progress.py`. |
| `flow/templates/flow/_stage_list.html`, `_answer_trail.html` | Left-rail components. |
| `flow/static/flow/flow.css` | The whole stylesheet. Design tokens live at the top as custom properties. |
| `flow/tests.py` | View, navigation, graph-integrity, progress-model and text-parsing tests. |
| `tools/extract_docx.py` | Turns a client Word document into plain text with hyperlinks made explicit. |
| `design_handoff_eligibility_checker/` | The design spec the current look implements. `README.md` is authoritative over the prototype beside it. |

**`p` lives in `flow/progress.py`, not in `flow_data.py`.** A progress fraction
is not content, and a developer transcribing prose out of a Word document has no
prompt to invent one. A node added without a `p` would read as 0.0 and snap the
ring back to empty mid-flow — silent, and visible only to whoever clicks through
that branch. `ProgressModelTests` fails loudly instead, naming every node that
is missing one.

A node is:

```python
"node_id": {
    "type": "question" | "statement",
    "title": str,
    "text": str,                                   # plain text, \n\n between paragraphs
    "options": [{"label": str, "next": "node_id"}],
}
```

`start` is the entry node. The view resolves an unknown or stale id to `start`
before storing it — keep that guard if you touch `views.py`, or a deleted node
sitting in someone's session silently diverges from what renders.

**Keep `FLOW` a flat dict in one file.** It is data, not logic: no branching, no
imports, nothing to factor out. Section banner comments do the job a file split
would. Revisit only if a *second* flow appears.

## How content changes actually arrive

This is the part that is not guessable from the code.

The client sends an updated **Word document**. A developer transcribes it. The
document is not a clean spec — it mixes new copy with **inline editorial
instructions addressed to the developer**, e.g.:

> `Equivalency Testing- remove`
> `4. Flexibility Remove this`
> `Change this to this: ...`
> `Add a question- Are you interested in training full-time...`

Those instruction fragments must **not** be transcribed into `FLOW`.

The client also **highlights** their changes: **yellow** marks edited or new
content, **magenta/pink** marks sections to move or delete. Recover that map —
it is the client's own diff and it is far more reliable than eyeballing:

```bash
.venv/Scripts/python.exe tools/extract_docx.py "Flow for Chat bot updated 26-27.docx"
```

For the highlight colours, parse `w:rPr/w:highlight` out of `word/document.xml`
in the `.docx` zip. Diffing the new extract against the previous document's
extract is also worth the thirty seconds.

### Rules for transcribing

- **Do not silently fix the client's copy.** If their text contradicts itself,
  quotes a suspect figure, or names another provider, **flag it and ask**. Faithful
  transcription plus a question beats a confident guess in public-facing copy about
  fees, visas and course length.
- **Do not refactor prose. Do de-duplicate bare facts.** Repeated paragraphs
  between two route descriptions are the client's deliberate copy and should stay
  duplicated — the client's edit unit is "a page of Word prose", and hoisting a
  shared paragraph into a constant makes the next transcription harder. Repeated
  *URLs and email addresses* are a different matter and are worth hoisting. The
  working rule is **hoist a repeated link the first time it changes, not the
  first time it repeats.** Only `ENQUIRY_FORM_URL` qualifies so far — the client
  replaced that form for 2027/28 and it appeared in three nodes, so a fourth
  change would have been three edits with one silently missable. `info@glftt.org`
  and the events link are repeated far more often, have never moved, and stay
  inline where a transcriber can see them.
  **Keep the `https://` on a hoisted URL.** `urlize` only linkifies a bare domain
  for a short TLD list (`com`, `edu`, `gov`, `int`, `mil`, `net`, `org`, or a
  `www.` prefix), and the enquiry form host now ends in `.microsoft` — so without
  the scheme the link renders as unclickable grey text on all three screens, with
  nothing failing anywhere. Tested, not assumed.
  The superseded `forms.office.com` URL deliberately survives in
  `design_handoff_eligibility_checker/` and `tools/flow_doc_extract.txt`: the
  first is a non-authoritative received artefact, the second is the record of what
  the client actually sent, and editing it would make the next document diff lie.
  A grep for `forms.office` will keep returning those hits forever and they are
  correct. `test_no_node_links_to_a_superseded_enquiry_form` is what stops one
  being copied back into `FLOW`.
- Content is plain text and the template autoescapes. **HTML in a `text` value
  renders as visible literal markup.** You cannot add markup from the content
  side — but you no longer need to for headings and bullets, because
  `flow/textblocks.py` infers them from the shape of each line. See below.
- URLs go bare on their own line — `urlize` links them. Avoid leaving a bare
  domain in a *label* (`"Educations.com: https://..."`), or `urlize` will turn
  the label into a second, broken `http://Educations.com` link.
- The file is UTF-8 and contains `’`, `–`, `•` and `£`. Write UTF-8 explicitly;
  cp1252 will mangle the fee figures.

#### Structure is inferred from the line, so punctuation now matters

`flow/textblocks.py` decides how each line renders. This is worth understanding
before you transcribe, because it is right today for reasons *the client*
controls and does not know about.

- A line starting `•` becomes a bullet. Consecutive bullets become one list.
- A line starting `1)`, `2)` … becomes an enumerated point with a hanging
  marker. **The marker shown is the client's own text, never a browser-generated
  number**, so nothing is silently renumbered. These are deliberately *not*
  collapsed into an `<ol>`: in the real copy each point is followed by its own
  continuation lines and the run is then interrupted by a line introducing
  something else ("University guides you may find useful…"), so any grouping
  rule either swallows that line or restarts the numbering at 1.
- A line becomes a **sub-heading** if it is not a bullet, not a `N)` item, is
  46 characters or fewer, does **not** end in `. : , ; ! ? )`, is not a URL, and
  contains no `@` and no currency figure.
- Everything else is a paragraph.

Today that yields exactly three sub-headings — the three route names in
`employment_routes_2` — and no false positives. The traps:

- **A question transcribed without its `?` becomes a bold green heading.**
  "Which would you like to know more about?" is 40 characters and is held back
  by its punctuation alone. The client's documents contain instruction fragments
  of exactly that shape (`Add a question- Are you interested in training
  full-time...`).
- **A short unpunctuated fact is the likeliest misfire.** The `£`/`$`/`€` guard
  catches fee lines; a line like `Applications open in October` would not be
  caught and would render as a route name.
- **The reverse fails silently.** Rename a route to `Postgraduate Teacher
  Apprenticeship Route (PGTA)` — 48 characters, ends in `)` — and it quietly
  stops being a heading. Nobody notices for a release.
- **Keep paragraphs as one logical line.** The heuristic works because each
  paragraph is a single long string built by implicit concatenation. If you
  transcribe a paragraph as a `"""…"""` block with hard line wraps, every short
  wrapped line becomes a heading candidate and the page falls apart.

`TextBlockTests` asserts the *rule*, not the copy: no heading may contain a URL,
an `@` or a currency figure.

## Tests

```bash
DJANGO_DEBUG=1 .venv/Scripts/python.exe manage.py test flow
```

43 tests in seven classes — `FlowViewTests` 3, `FlowGraphIntegrityTests` 5,
`ProgressModelTests` 4, `FlowNavigationTests` 20, `TextBlockTests` 5,
`TemplateCommentSyntaxTests` 2, `RingGeometryTests` 4.

The three that matter most for content work:

- **`FlowGraphIntegrityTests`** — a dangling `next`, an unreachable node, a dead
  end, a malformed node.
- **`ProgressModelTests`** — a node with no `p`, a stale `p` for a deleted node,
  an out-of-range value, a stage no node can reach.
- **`TextBlockTests`** — the parser's shape rules, plus one invariant over the
  real `FLOW`: **no sub-heading may contain a URL, an `@` or a currency figure.**
  That is what turns "a fee line started rendering as a route name" from a
  silent visual bug into a red run.

Every one of them reports *all* offenders in one run rather than one per run,
and names the file to fix. **Run the suite before and after any edit to `FLOW`**
— green-before-red-after tells you the breakage is yours.

Also present: `FlowNavigationTests` (the trail, Back, the caps, the stale-tab
guard), `RingGeometryTests` (the arc maths must agree with the hard-coded SVG
path), and `TemplateCommentSyntaxTests` — the Article 7 static check that fails
on a `{#` with no `#}` on the same line, or on any HTML comment, in any
template. A render test cannot catch that, because the page renders fine.

Do not write tests that assert on copy, titles or wording. Content churns every
time a document arrives; those tests would be pure churn. Test shape and graph
structure only. The one deliberate exception is the answer-trail label test,
which reads its expected value out of `FLOW` rather than hard-coding a string —
the assertion is about the index-versus-target logic, not the wording.

## Environment

- Development is **Windows**; the interpreter is `.venv/Scripts/python.exe`.
  Deployment is Linux — keep Windows-only packages out of `requirements.txt`.
- Django 6.0.1, WhiteNoise, Gunicorn. SQLite locally.
- **`DJANGO_DEBUG=1` is required for local work.** `DEBUG` now defaults to
  `False` so a deploy that forgets the variable fails closed, and outside
  `DEBUG` a missing `DJANGO_SECRET_KEY` raises `ImproperlyConfigured` at
  startup. Without the variable, `manage.py` — including `manage.py test` —
  refuses to start. That is intended, not a broken checkout.

  ```bash
  DJANGO_DEBUG=1 .venv/Scripts/python.exe manage.py test flow
  ```

  **Never set it on the server.** Debug mode is the one input that disables
  secure cookies, HSTS and the SSL redirect, publishes tracebacks, and swaps the
  secret key for a throwaway — and the site comes up looking perfectly healthy
  while it does. It also skips building the static manifest that `DEBUG=False`
  then requires. Settings refuse to start with debug on when a hosting marker
  (`WEBSITE_HOSTNAME`, `WEBSITE_SITE_NAME`, `DYNO`, `K_SERVICE`) is present, but
  do not lean on that catching every platform. There is no committed secret key
  to fall back on any more: in debug a random one is generated per process.
- Deployment steps and required env vars: `DEPLOYMENT.md` and `.env.example`.
- `collectstatic` **has** now been run locally, so `staticfiles/` exists with a
  populated manifest. Be careful what you conclude from that: it means a local
  `DEBUG=False` run resolves `{% static %}` happily and therefore proves nothing
  about the server, where a missed `collectstatic` 500s every request. See step
  5 of `DEPLOYMENT.md`. (On a fresh clone the suite emits a harmless
  `No directory at: ...staticfiles\` warning instead. Also not a failure.)

## Behaviour worth knowing

Decisions, not defects. Each of these looks like a bug until you know why.

- **A POST with an unknown `next` is a no-op.** It used to reset to `start`,
  which was deliberate and harmless when the session held one string. It is not
  harmless now: the session holds the visitor's answers and their Back history,
  and the realistic trigger is this project's own content workflow — a visitor
  holding a page open across a transcription deploy clicks an option whose
  target has since been removed. They stay where they are instead.
  `test_unknown_next_mid_journey_preserves_the_answer_trail` pins this.
- **A `next` of `"start"` still clears everything**, because eleven nodes carry
  a real "Start over" option and that is what the visitor asked for.
- **`_go_back` walks past history steps whose node no longer exists** rather
  than resetting, for the same reason. Losing a step is proportionate; losing
  the journey is not.
- **"Start again" is a POST, not a link**, and **`?node=<anything>` always lands
  on `start`** — the id is ignored. Both follow from one rule: a GET that
  destroys state can be fired by a link prefetch, a chat or social link preview,
  or a browser restoring tabs, with nobody deciding anything. Honouring an
  arbitrary `?node=` would also drop a visitor mid-flow at a percentage they had
  not earned, having answered nothing. Nothing in the page emits one.
- **Option arrows are direction-aware.** `_options()` sets `goes_back` and the
  template renders a left arrow instead of a right one. Eight nodes carry their
  own "Back" option as content, and a forward arrow on those produced
  "Back to Routes →" a few lines above the footer's "← Back". Two signals decide
  it, because neither covers all eight alone: a target earlier in the flow, or a
  label beginning "back". Worst case after a content rename is a forward arrow
  on a backward option — never a wrong destination.
  `test_no_backward_option_is_flagged_as_going_forward` guards it.
- **An expired session is announced.** The cookie lasts an hour of inactivity
  and one screen is 5,300 characters of reading, so a visitor can click an
  option after their session has gone. The click still works; the trail and the
  Back history do not survive it, and `timed_out` renders a one-line note rather
  than letting the rail empty silently. A *first* answer from the landing page
  looks identical from the server's side — nothing is written while the visitor
  is still on `start` — so `start` is excluded, and a test covers that.
- **Each node renders its own `<title>`.** All 36 screens are served at `/`, so
  a single fixed title made every browser-history entry identical.

## Known issues (open)

### Ours to fix, once the client decides

- **Eight nodes carry their own content-level "Back" option** — a forward POST to
  a fixed node — *and* the footer has a real Back control that pops the history
  stack. Seven of the eight send both Backs to the same node, so that redundancy
  is mostly harmless; only `employment_routes_2` genuinely differs (content
  "Back to Routes" goes to `routes_into_teaching_1`, footer Back to
  `employment_routes_1`). Removing the content ones is a flow change and
  therefore the client's call.
- **The ring reads "100% complete / Next steps" on the three rejection
  closings** (`closing_statement_1`, `_2`, `_3`, reached from
  `overseas_4_not_enough`, `overseas_eligibility_5` and `domestic_2_no_degree`).
  A candidate who has just been told they need a different qualification, and
  who never saw a route, subject or location, gets a full gold ring. The 1.00
  values are the design handoff's own, so lowering them — or hiding the figure
  on those screens — is a design decision, not a bug to fix unilaterally.
- **Nine forward clicks leave the percentage unchanged**, because both nodes
  share a fraction: the `overseas_3_*`, `overseas_4_*`, `domestic_1_*` and
  `domestic_2_*` detours, and the `employment_routes_no_experience` pair. With
  no ring this did not matter; now the visitor answers, watches an animated
  figure, and nothing moves — which reads as a click that did not register, on
  the branches where the news is already bad. Small offsets would fix it. Also
  the handoff's numbers, so also the client's call.
- **`overseas_eligibility_5` is worse than it was, without its copy changing.**
  It still tells candidates "it appears from the answers you have provided that
  you have… a statement of comparability… an equivalent to a BA Honours Degree"
  when they have just said they have neither. The answer trail now prints their
  actual answers in the left rail, on the same screen, beside that sentence. A
  candidate who reads both stops trusting the tool. The client's document
  explicitly asks for that Continue path, so the reword needs their approval —
  but this is the one to put in front of them first.
- `employment_routes_2` is still ~5,300 characters on one screen (~7 phone
  screens of scrolling). Its three route names now render as real sub-headings
  rather than body text, which was the worst of it — so **the three-way node
  split may no longer be needed.** Confirm before doing it.
- Several nodes still carry pre-2021 visa terminology ("Tier 2", "Tier 4") and
  future-tense references to January 2021. The client has not revised them.

### Accepted, with the reason

- **A bullet ending in a colon has its payload fall outside the list.** In
  `overseas_4_not_enough`, a bullet ending "…send your comparability statement…:"
  is followed by a bare `info@glftt.org` line, which per the URL convention is
  its own line and so becomes a paragraph after the `</ul>`. Attaching it would
  need a heuristic guessing which bare URLs belong to the bullet above, and that
  would misfire on the other thirty.
- **Numbered points do not become an `<ol>`.** Each `N)` point is followed by its
  own continuation lines, and the run is interrupted by a line introducing
  something else, so any grouping rule either swallows that line or restarts the
  numbering at 1. They get a hanging inline marker instead, showing the client's
  own text.
- **The A/B/C badges on option buttons are decoration** — no keyboard shortcuts
  sit behind them. They are `aria-hidden`, so they promise nothing to a screen
  reader; a sighted keyboard user may still expect them to work. Implementing
  shortcuts would mean un-hiding them, because they would then be information.
- **A short unpunctuated line holding a bare figure with no currency symbol
  still reads as a sub-heading.** "Applications open in October" would render as
  a route name. The currency guard catches fee lines; a bare number is genuinely
  ambiguous, and the transcription note above is the mitigation.

### Recommended, not done — needs a decision outside the code

- **`/admin/` is mounted** (`teachflow/urls.py`) with no models to administer: a
  public Django login form on the trust's domain, no rate limiting, nothing
  behind it. Removing the URL pattern and `django.contrib.admin` is a two-line
  change with no downside anyone has named.
- **SQLite in production.** Article 9 wants Postgres. Every visitor now writes
  to the database on every request, SQLite serialises writes, and on an
  ephemeral filesystem the file — and every in-flight journey — vanishes on
  restart. `DEPLOYMENT.md` section 3 already advises Postgres; nothing enforces
  it.
- **Cookie-based sessions would remove the retention problem entirely.**
  `SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"` was
  measured at roughly 340 bytes for a full history and trail, well inside the
  4KB limit. No `django_session` table, no `clearsessions` schedule, nothing to
  disclose in a subject access request. The trade-off, stated plainly: signed
  cookies are signed, not encrypted, so a visitor can read their own answers —
  fine here, but it should be a decision rather than an accident.
- **Google Fonts are loaded from Google.** Chosen deliberately, for fidelity,
  but every visitor's IP reaches Google before first paint on a page embedded in
  a school trust's site. Self-hosting into `flow/static/flow/fonts/` is
  sanctioned by the handoff and removes two render-blocking third-party
  requests.
- **How the page is actually embedded is unconfirmed.** This file's first line
  says "embedded on the client's public website", but `X_FRAME_OPTIONS` is
  Django's default `DENY` and `SESSION_COOKIE_SAMESITE` is `Lax` — so a
  cross-origin iframe cannot work today, and it is presumably linked or
  same-origin. If it ever must be framed cross-site it needs CSP
  `frame-ancestors` in place of `X-Frame-Options`, `SameSite=None`, and a
  partitioned-cookie plan — and a third-party cookie carrying immigration-status
  answers is a materially worse privacy story. Confirm before assuming.
