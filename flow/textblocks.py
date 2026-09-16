"""Turn a node's ``text`` into typed blocks: sub-headings, bullets and body.

The content side of this app cannot express structure. ``flow_data.py`` holds
plain text and the template autoescapes, so HTML in a ``text`` value renders as
visible literal markup. Everything a page needs -- a route name as a heading, a
list of requirements as bullets -- therefore has to be *inferred* from the shape
of the line. That inference lives here and nowhere else.

Linkification is deliberately not done here. Django's ``urlize`` already strips
trailing punctuation, balances brackets and adds ``mailto:``, and it is applied
per block in the template. Re-implementing it was the design prototype's
approach and it carried a hand-written special case for one Office Forms URL;
there is no reason to inherit that.

The heading heuristic is right for today's content but it is right for reasons
the *client* controls -- see ``HEADING_MAX_LENGTH`` below and the transcription
note in CLAUDE.md.
"""

import re

# A line this long or shorter may be a sub-heading. Longer lines are prose.
HEADING_MAX_LENGTH = 46

# A line ending in any of these is a sentence or a clause, not a heading.
# The question mark is doing more work than it looks: several client questions
# ("Which would you like to know more about?", "Do you want to teach Primary or
# Secondary?") are short enough to pass every other test and are kept out of
# heading styling by their punctuation alone.
SENTENCE_ENDINGS = ".:,;!?)"

_BULLET = re.compile(r"^•\s*")
# Captures the client's own marker so it is shown verbatim rather than
# renumbered. See the note on the "numbered" kind in parse_blocks.
_NUMBERED = re.compile(r"^(\d+\))\s+(.+)$")
_URL = re.compile(r"https?:", re.IGNORECASE)
# A bare figure in a short line is a fact, not a heading: "For 2027/28 the fee
# is £10,050" would otherwise pass every test above and render as a route name.
_MONEY = re.compile(r"[£$€]\s?\d")


def _is_heading(text, is_bullet):
    if is_bullet or not text:
        return False
    if _NUMBERED.match(text):
        return False
    if len(text) > HEADING_MAX_LENGTH:
        return False
    if text[-1] in SENTENCE_ENDINGS:
        return False
    # search, not match: anchoring this to the start of the line meant
    # "Apply at https://www.glftt.org" -- short, unpunctuated, no @ -- classified
    # as a sub-heading with a link inside it. A heading should not contain a URL
    # wherever it sits, which is also the invariant TextBlockTests asserts.
    if _URL.search(text) or "@" in text:
        return False
    if _MONEY.search(text):
        return False
    return True


def parse_blocks(text):
    """Split ``text`` into a list of typed blocks.

    Each block is a dict with a ``kind`` of:

    ``heading``   a sub-heading    -- carries ``text``
    ``body``      a paragraph      -- carries ``text``
    ``bullets``   a list           -- carries ``items``, a list of strings
    ``numbered``  an enumerated point -- carries ``marker`` and ``text``

    Runs of consecutive bullet lines are collected into one ``bullets`` block so
    the template can render a real ``<ul>``. The design draws each item as a
    flex row with its own marker, which looks identical either way, but a list
    of paragraphs is not a list to a screen reader.

    **Numbered lines are deliberately NOT grouped into an ``<ol>``.** In the
    client's copy a ``N)`` point is followed by its own continuation lines -- an
    email address, a URL, an extra sentence -- and the run is then interrupted by
    a line that introduces something else entirely ("University guides you may
    find useful as a starting point:"). Grouping by "everything until the next
    number" swallows that line into the previous point; grouping only
    consecutive numbers puts each one in a single-item list that restarts at 1.
    So each numbered line becomes its own block with a hanging marker, which
    gives it the visual rank its content deserves without inventing structure
    the prose does not have. The marker is the client's own text, never a
    browser-generated number, so nothing is silently renumbered.

    Blank lines are dropped; the template supplies the spacing between blocks.
    """
    blocks = []

    for raw_line in str(text or "").split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        is_bullet = bool(_BULLET.match(line))
        if is_bullet:
            line = _BULLET.sub("", line).strip()
            if not line:
                continue

            if blocks and blocks[-1]["kind"] == "bullets":
                blocks[-1]["items"].append(line)
            else:
                blocks.append({"kind": "bullets", "items": [line]})
            continue

        numbered = _NUMBERED.match(line)
        if numbered:
            blocks.append(
                {
                    "kind": "numbered",
                    "marker": numbered.group(1),
                    "text": numbered.group(2).strip(),
                }
            )
            continue

        kind = "heading" if _is_heading(line, is_bullet) else "body"
        blocks.append({"kind": kind, "text": line})

    return blocks
