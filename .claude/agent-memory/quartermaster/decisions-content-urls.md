---
name: decisions-content-urls
description: Decisions taken on repeated URLs/emails in flow/flow_data.py (the hoisted EOI link, its guard tests, expiry), and which project artefacts are frozen records that are never edited
metadata:
  type: project
---

Repeated-link policy in `flow/flow_data.py`, settled 2026-09-24 when the client
replaced the Microsoft enquiry form (forms.office.com -> forms.cloud.microsoft):

- The enquiry-form URL is hoisted to a module-level constant above `FLOW`,
  spliced back with f-strings so each node still shows a URL alone on its own
  line. Trigger for hoisting is "this link has now changed twice in three
  places", not the repetition count alone.
- `info@glftt.org` and `https://www.glftt.org/19/events` were deliberately NOT
  hoisted: ~16 occurrences between them, neither has ever changed. Rule: hoist a
  repeated link the first time it *changes*, not the first time it repeats.

**Why:** CLAUDE.md sanctions hoisting repeated URLs but forbids refactoring
prose; the cost of a missed site is a wrong public link in the conversion funnel.
**How to apply:** when the next repeated URL or address changes, hoist it then.

2026-09-29 plan: the EOI moved from Microsoft Forms to an Eteach job advert
(`eteach.com/careers/glfschools/job/trainee-teacher-<id>/?lang=en-GB`, expires
2027-06-30). Decisions in that plan:

- Constant renamed `ENQUIRY_FORM_URL` -> `EXPRESSION_OF_INTEREST_URL` (client's
  own term is "EOI"; churn is flow_data.py, tests.py, CLAUDE.md only). URL
  transcribed verbatim, scheme and `?lang=en-GB` kept.
- The old test's self-check (constant must match the Microsoft regex) was
  vendor-pinned and broke on the host change. Replaced by: (a) no node links to
  ANY Microsoft Forms URL (all superseded; copy-back source is the frozen
  artefacts); (b) every `eteach.com/careers/glfschools/job/...` URL in FLOW is
  the constant, constant self-matches that pattern, and the constant appears in
  at least one node. No node ids named, no URL literal hard-coded. The plain
  vacancies listing `eteach.com/careers/glfschools/` (employment_routes_2) is a
  different link and must not match - the `/job/` segment separates them.
- No date-based test for the expiry (a calendar time bomb breaks unrelated
  deploys); expiry recorded in the constant's comment and CLAUDE.md known issues.
- "Enquiry form" copy on the three screens flagged to the client, not changed.
- Privacy: no SECURE_REFERRER_POLICY override, so Django's default `same-origin`
  sends no Referer to Eteach; no answer in any URL. Data section unchanged.

Frozen artefacts - read, never edited, even when they hold a stale URL:

- `design_handoff_eligibility_checker/Eligibility Checker.dc.html` - received
  design prototype with its own duplicated copy of `FLOW`.
- `tools/flow_doc_extract.txt` - the extract of what the client actually sent.
  Editing it falsifies the record and the next diff.

**Why:** both are evidence of what was received, not code.
**How to apply:** change `flow_data.py` only; expect greps to keep returning
stale forms.office hits in those two files.

`urlize` note: bare domains only linkify for com/edu/gov/int/mil/net/org or
`www.`. Always keep the `https://` on a hoisted URL whatever its host.
