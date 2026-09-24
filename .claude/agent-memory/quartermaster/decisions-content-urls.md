---
name: decisions-content-urls
description: Decisions taken on repeated URLs/emails in flow/flow_data.py, and which project artefacts are frozen records that are never edited
metadata:
  type: project
---

Repeated-link policy in `flow/flow_data.py`, settled 2026-09-24 when the client
replaced the Microsoft enquiry form (forms.office.com -> forms.cloud.microsoft):

- The enquiry-form URL is hoisted to a module-level `ENQUIRY_FORM_URL` constant
  above `FLOW`, spliced back with f-strings so each node still shows a URL alone
  on its own line. Trigger for hoisting is "this link has now changed twice in
  three places", not the repetition count alone.
- `info@glftt.org` and `https://www.glftt.org/19/events` were deliberately NOT
  hoisted: ~16 occurrences between them, neither has ever changed, and bundling
  them would swamp a client copy change. Rule adopted: hoist a repeated link the
  first time it *changes*, not the first time it repeats.

**Why:** CLAUDE.md sanctions hoisting repeated URLs but forbids refactoring
prose; the cost of a missed site is a wrong public link in the conversion funnel.
**How to apply:** when the next repeated URL or address changes, hoist it then
and add it to the constants block at the top of `flow_data.py`.

Frozen artefacts — read, never edited, even when they hold a stale URL:

- `design_handoff_eligibility_checker/Eligibility Checker.dc.html` — received
  design prototype with its own duplicated copy of `FLOW`. Its README (line 16)
  names `flow/flow_data.py` the source of truth for content, so nobody
  re-transcribes copy out of the prototype.
- `tools/flow_doc_extract.txt` — the extract of what the client actually sent.
  Editing it falsifies the record and destroys the value of diffing the next
  extract against it.

**Why:** both are evidence of what was received, not code.
**How to apply:** when a link or a line of copy changes, change `flow_data.py`
only, and expect greps to keep returning stale hits in those two files.

Django `urlize` note that is load-bearing after this change: the new form host
ends in `.microsoft`, which is outside the small TLD set Django's bare-domain
fallback recognises. The explicit `https://` prefix is what makes the link
linkify at all now. Never transcribe this URL without its scheme.
