"""Progress model for the eligibility flow: how far along the ring is, and where.

Why this is not in ``flow_data.py``
-----------------------------------
``flow_data.py`` is a hand transcription of the client's Word document and is
re-transcribed every time they send a new one. A developer copying prose out of
that document has no prompt to think about a progress fraction, and a node added
without one would read as 0.0 and snap the ring back to empty mid-flow --
silent, and only visible to whoever happens to click through that branch.

Keeping the fractions here means ``flow_data.py`` stays what it claims to be:
client content, nothing else. The cost is that this map can drift out of step
with ``FLOW``; ``ProgressModelTests`` in ``tests.py`` is what stops that, and it
names every missing or stale node id in one run.

Everything below is a pure function of one or two floats. No Django imports, no
node lookups beyond ``NODE_PROGRESS``.
"""

import math

# --- Arc geometry -----------------------------------------------------------
# The ring is a 220-degree arc of radius 76 centred at (100, 104) in a
# 200x152 viewBox, sweeping from 200 degrees round to -20. ARC_LEN is that
# arc's path length and is the stroke-dasharray the template renders.
#
# These five numbers and the two <path d="..."> values in
# templates/flow/_progress_figure.html describe the same curve. Change one and
# you must change the other.
ARC_LEN = 291.8
CX = 100.0
CY = 104.0
R = 76.0
ANGLE_START = 200.0
ANGLE_SWEEP = 220.0

# Fractions at which a milestone tick sits on the arc.
TICKS = (0.2, 0.4, 0.6, 0.8)

# --- Stages -----------------------------------------------------------------
STAGES = (
    "Eligibility",
    "Training route",
    "Subject & phase",
    "Location",
    "Next steps",
)

# Lower bound of each stage, aligned with STAGES by index.
STAGE_STARTS = (0.0, 0.4, 0.68, 0.8, 0.86)

# Endpoints of the head-marker colour ramp, used as the no-oklch fallback.
HEAD_FROM_RGB = (0x1F, 0x5F, 0x5B)  # brand green #1f5f5b
HEAD_TO_RGB = (0xC0, 0x8A, 0x3E)  # gold #c08a3e

# --- Progress per node ------------------------------------------------------
# Every id here must exist in FLOW, and every id in FLOW must appear here.
# ProgressModelTests enforces both directions.
NODE_PROGRESS = {
    # Stage 1 -- Eligibility
    "start": 0.04,
    "eligibility_2": 0.12,
    "overseas_candidate_statement": 0.12,
    "overseas_eligibility_3": 0.20,
    "overseas_3_no_statement": 0.20,
    "overseas_3_not_enough": 0.20,
    "domestic_eligibility_1": 0.20,
    "domestic_1_no_gcse": 0.20,
    "overseas_eligibility_4": 0.28,
    "overseas_4_no_statement": 0.28,
    "overseas_4_not_enough": 0.28,
    "domestic_eligibility_2": 0.28,
    "domestic_2_no_degree": 0.28,
    "overseas_eligibility_5": 0.36,
    # Stage 2 -- Training route
    "routes_into_teaching_1": 0.44,
    "routes_into_teaching_salary_info": 0.50,
    "routes_into_teaching_fee_info": 0.50,
    "employment_routes_1": 0.56,
    "employment_routes_no_experience": 0.56,
    "fee_funded_routes_1": 0.56,
    "employment_routes_2": 0.62,
    "fee_funded_full_time": 0.62,
    "fee_funded_flexible": 0.62,
    # Stage 3 -- Subject & phase
    "subject_phase_1": 0.70,
    "subject_phase_2": 0.76,
    "subject_phase_3": 0.76,
    # Stage 4 -- Location
    "training_locations": 0.84,
    # Stage 5 -- Next steps
    "next_steps_1": 0.90,
    "next_steps_2": 0.93,
    "next_steps_3": 0.95,
    "events": 0.98,
    "contact_us": 0.98,
    "closing_statement_1": 1.00,
    "closing_statement_2": 1.00,
    "closing_statement_3": 1.00,
    "closing_statement_4": 1.00,
}


def progress_for(node_id, fallback=0.0):
    """Progress fraction for a node.

    An unmapped node freezes the ring at ``fallback`` (the last value rendered)
    rather than resetting it to zero, so the failure is graceful in front of a
    candidate. ProgressModelTests makes it loud for the developer.
    """
    return NODE_PROGRESS.get(node_id, fallback)


def point_at(p):
    """(x, y) on the arc at progress fraction ``p``."""
    radians = math.radians(ANGLE_START - ANGLE_SWEEP * p)
    return CX + R * math.cos(radians), CY - R * math.sin(radians)


def stage_index(p):
    """Index into STAGES for progress fraction ``p``."""
    index = 0
    for i, start in enumerate(STAGE_STARTS):
        if p >= start:
            index = i
    return index


def head_colour(p):
    """The head marker's colour at ``p``, as an oklch() string.

    Ramps green -> gold: oklch(0.42 0.07 178) at 0 to oklch(0.58 0.12 78) at 1.
    """
    return "oklch({:.3f} {:.3f} {:.1f})".format(
        0.42 + 0.16 * p, 0.07 + 0.05 * p, 178.0 - 100.0 * p
    )


def head_colour_hex(p):
    """The same ramp as a hex sRGB value, for browsers without oklch().

    An unsupported colour in an SVG ``fill`` renders black rather than falling
    back, so the template ships this in the attribute and the stylesheet swaps
    in oklch() behind an @supports check.
    """
    channels = [
        round(start + (end - start) * p)
        for start, end in zip(HEAD_FROM_RGB, HEAD_TO_RGB)
    ]
    return "#{:02x}{:02x}{:02x}".format(*channels)


def ring_context(p, prev_p):
    """Everything the progress figure needs, for ``p`` now and ``prev_p`` before.

    Coordinates and offsets are returned pre-formatted as strings on purpose:
    Django localises floats when USE_L10N is on, and a decimal comma in an SVG
    path or a stroke-dashoffset silently breaks the figure in any locale that
    uses one.

    Colour is left to the stylesheet wherever it can be -- ticks and stage rows
    carry a state, not a hex value. The head ramp is continuous, so it cannot be
    a class and is the one colour computed here.
    """
    index = stage_index(p)
    head_x, head_y = point_at(p)
    prev_head_x, prev_head_y = point_at(prev_p)

    ticks = []
    for tick in TICKS:
        tick_x, tick_y = point_at(tick)
        ticks.append(
            {
                "x": "{:.2f}".format(tick_x),
                "y": "{:.2f}".format(tick_y),
                "reached": p >= tick,
                "was_reached": prev_p >= tick,
            }
        )

    return {
        "p": p,
        "pct": int(round(p * 100)),
        "stage_index": index,
        "stage_number": "{:02d}".format(index + 1),
        "stage_label": STAGES[index],
        "stage_position": index + 1,
        "stage_count": len(STAGES),
        "stages": [
            {
                "label": label,
                "state": (
                    "current" if i == index else "past" if i < index else "future"
                ),
            }
            for i, label in enumerate(STAGES)
        ],
        "arc_len": "{:.1f}".format(ARC_LEN),
        "dash_offset": "{:.2f}".format(ARC_LEN * (1 - p)),
        "prev_dash_offset": "{:.2f}".format(ARC_LEN * (1 - prev_p)),
        "head_x": "{:.2f}".format(head_x),
        "head_y": "{:.2f}".format(head_y),
        "prev_head_x": "{:.2f}".format(prev_head_x),
        "prev_head_y": "{:.2f}".format(prev_head_y),
        "head_colour": head_colour(p),
        "head_colour_hex": head_colour_hex(p),
        "prev_head_colour": head_colour(prev_p),
        "prev_head_colour_hex": head_colour_hex(prev_p),
        "ticks": ticks,
    }
