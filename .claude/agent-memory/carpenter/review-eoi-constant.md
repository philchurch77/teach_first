---
name: review-eoi-constant
description: 2026-09-29 review of the EOI constant rename (ENQUIRY_FORM_URL -> EXPRESSION_OF_INTEREST_URL) and its two guard tests; what was found and accepted
metadata:
  type: project
---

EOI link lives once in flow/flow_data.py (EXPRESSION_OF_INTEREST_URL); guard tests are in FlowGraphIntegrityTests in flow/tests.py. No stale ENQUIRY_FORM refs remain outside the quartermaster memory note (historical, fine).

Findings left open (all Low): the Microsoft-form test has no positive control (regex could rot and pass vacuously); the Eteach test regex is https-only and `\S+` swallows trailing punctuation; CLAUDE.md says the link moved "to 2027/28" then "September 2026", which reads backwards.

**Why:** avoid re-raising. **How to apply:** only re-raise if the code has changed since.
