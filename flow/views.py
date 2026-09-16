from django.shortcuts import redirect, render

from .flow_data import FLOW
from .progress import progress_for, ring_context
from .textblocks import parse_blocks

# A visitor can loop: several nodes offer a content-level "Back" option that
# posts forward to a fixed node, so both lists below can grow without bound on
# a long enough session. Sessions here are database-backed, so this is write
# amplification rather than a cookie-size limit, but it is capped either way.
HISTORY_LIMIT = 40
# Matched to HISTORY_LIMIT so the trail can always unwind as far as Back can.
# At 12 it was one short of the longest walkable path (13 questions), so the
# first answer was dropped from storage and a visitor who then pressed Back all
# the way out found the trail empty where their first answer should have been.
# Only TRAIL_DISPLAY of these are ever rendered.
TRAIL_LIMIT = 40
TRAIL_DISPLAY = 6


def flow_view(request):
    if request.method == "POST":
        _apply_post(request)
        return redirect("flow")

    if request.GET.get("node"):
        # Always a fresh start, whatever id is asked for.
        #
        # Nothing in the page emits one of these any more -- "Start again" is a
        # POST -- so this only ever arrives from an old bookmark or a stale link
        # on the client's site. Honouring an arbitrary id would drop a visitor
        # mid-flow at a percentage they had not earned, having answered nothing,
        # and being a GET it can be fired by a link prefetch or a tab restore.
        _reset(request, "start")

    return _render(request, _current_id(request))


def _resolve(node_id):
    """An unknown, stale or missing node id becomes ``start``.

    CLAUDE.md names this guard as load-bearing: it is what stops a node deleted
    between two visits leaving a session pointing at something that no longer
    renders. Every path into the view goes through here, and nothing
    re-implements it -- there is one copy of this rule on purpose.
    """
    return node_id if node_id in FLOW else "start"


def _current_id(request):
    return _resolve(request.session.get("node_id"))


def _reset(request, node_id="start"):
    request.session["node_id"] = _resolve(node_id)
    request.session["history"] = []
    request.session["trail"] = []
    request.session["prev_p"] = 0.0


def _apply_post(request):
    # A form posted from a node the session no longer knows about, when the
    # session holds nothing at all, means it expired between the page being
    # rendered and the option being clicked -- an hour of inactivity, and one
    # screen in this flow is 5,300 characters of reading. The click still works;
    # what is gone is their trail and their Back history, and saying so is
    # kinder than silently emptying the rail.
    #
    # A first answer from the landing page looks the same from here, because
    # nothing is written while the visitor is still on start, so "start" is
    # excluded -- there is nothing to have lost.
    came_from = request.POST.get("from")
    expired = bool(came_from) and came_from != "start" and not request.session.get("node_id")

    if request.POST.get("back"):
        _go_back(request)
        return

    # "Start again" in the footer. A POST, not a link: it destroys the journey,
    # and a destructive GET can be fired by a link prefetch, a chat or social
    # link preview, or a browser restoring tabs on start-up -- none of which is
    # the visitor deciding to begin again.
    if request.POST.get("reset"):
        _reset(request, "start")
        return

    next_id = request.POST.get("next")

    # A deliberate "Start over" clears everything, because that is what the
    # visitor asked for. Eleven nodes carry one as a real content option.
    if next_id == "start":
        _reset(request, "start")
        return

    # An unknown target is an error, not a request to start again, so it is no
    # longer treated as one. The realistic cause is this project's own content
    # workflow: nodes are added and removed every time a client document is
    # transcribed, so a visitor holding a page open across a content deploy can
    # click an option whose target has since gone. Discarding their answers for
    # that would be the worst outcome available. Stay put instead -- another
    # option is one click away and nothing is lost.
    if next_id not in FLOW:
        return

    _advance(
        request,
        next_id,
        request.POST.get("choice"),
        came_from,
    )

    if expired:
        request.session["timed_out"] = True


def _advance(request, next_id, choice, came_from):
    current_id = _current_id(request)
    history = request.session.get("history") or []
    trail = request.session.get("trail") or []

    # A form rendered against a different node -- a second tab, or a page
    # restored from the browser's cache -- would otherwise record its answer
    # against whichever question is current now. Honour the navigation, because
    # the visitor did click a real option, but do not write a trail entry or a
    # history step we cannot vouch for.
    if came_from == current_id:
        node = FLOW[current_id]
        trailed = False

        if node.get("type") == "question":
            label = _chosen_label(node, choice, next_id)
            if label:
                entry = {"question": node["title"], "answer": label}
                trail = (trail + [entry])[-TRAIL_LIMIT:]
                trailed = True

        # Each history step records whether it wrote a trail entry, so Back
        # knows exactly what to undo. Inferring it from the node's type -- as
        # the design prototype does -- breaks whenever a question departure
        # records nothing, and then Back pops a *different* question's answer
        # and the trail starts misattributing. Recording the fact is cheap;
        # re-deriving it is wrong.
        history = (history + [{"id": current_id, "trailed": trailed}])[-HISTORY_LIMIT:]

    request.session["history"] = history
    request.session["trail"] = trail
    request.session["node_id"] = next_id


def _chosen_label(node, choice, next_id):
    """The label of the option the visitor actually clicked.

    The option index is posted alongside the target because three nodes offer
    two differently labelled options that lead to the same place --
    subject_phase_2, subject_phase_3 and training_locations. Looking the label
    up by target alone always returns the first of the pair, which would tell a
    candidate they chose Oxford/Reading when they chose Banstead.

    The index is only trusted when its target matches the posted one, so a
    stale or hand-edited form falls back to the lookup rather than recording an
    answer for a route the visitor was never offered.
    """
    options = node.get("options") or []

    try:
        index = int(choice)
    except (TypeError, ValueError):
        index = -1

    if 0 <= index < len(options) and options[index].get("next") == next_id:
        return options[index].get("label")

    # No trustworthy index. Fall back to the target, but only when it is
    # unambiguous. On the three nodes that offer two differently labelled
    # options with the same target, naming the first of the pair would write a
    # sentence into the trail that the visitor never chose. Recording nothing is
    # more honest than guessing, and the trail is allowed to be incomplete.
    matches = [
        option for option in options if option.get("next") == next_id
    ]
    if len(matches) == 1:
        return matches[0].get("label")

    return None


def _go_back(request):
    history = list(request.session.get("history") or [])
    trail = list(request.session.get("trail") or [])

    # Back undoes exactly one departure. History records the path actually
    # walked and whether that step wrote a trail entry, so a node with several
    # parents never confuses this and neither does a step that recorded nothing.
    #
    # Steps whose node has since been deleted are walked past rather than
    # reset over -- content deploys remove nodes, and skipping a dead step
    # costs the visitor one screen where a reset would cost them everything.
    while history:
        previous_id, trailed = _history_entry(history.pop())
        if trailed and trail:
            trail = trail[:-1]

        if previous_id in FLOW:
            request.session["history"] = history
            request.session["trail"] = trail
            request.session["node_id"] = previous_id
            return

    # Nothing left that still resolves. Leave the visitor where they are rather
    # than throwing them back to the beginning; the Back control simply stops
    # being offered.
    request.session["history"] = []
    request.session["trail"] = trail


def _history_entry(entry):
    """(node_id, trailed) for one history step.

    Tolerates the bare-string entries written by an earlier version of this
    view, so a session held open across a deploy still navigates -- it just
    does not pop a trail entry, since a bare string does not record whether
    that step wrote one.
    """
    if isinstance(entry, dict):
        return entry.get("id"), bool(entry.get("trailed"))
    return entry, False


def _options(node_id, node):
    """The node's options, each with the index the form posts and its key badge.

    The A/B/C badges are decoration -- there are no keyboard shortcuts behind
    them -- so the template marks them aria-hidden. The index is what makes the
    answer trail truthful; see _chosen_label.

    ``goes_back`` picks the arrow. Eight nodes carry their own "Back" option as
    real content, and the design's forward arrow on those produced
    "Back to Routes ->" a few lines above the footer's "<- Back": two controls
    carrying the same word and pointing opposite ways, one of them wrong.

    Two signals, because neither covers all eight on its own. A target earlier
    in the flow catches the six that go back a stage; the label catches the two
    that return within the same stage, where the progress fraction is equal. If
    a future transcription renames one, the worst case is a forward arrow on a
    backward option -- no worse than before, and never a wrong destination.
    """
    here = progress_for(node_id)
    options = []

    for index, option in enumerate(node.get("options") or []):
        label = option.get("label") or ""
        target = option.get("next")
        options.append(
            {
                "label": option.get("label"),
                "next": target,
                "index": index,
                "key": chr(ord("A") + index) if index < 26 else "",
                "goes_back": (
                    progress_for(target, here) < here
                    or label.strip().lower().startswith("back")
                ),
            }
        )

    return options


def _render(request, node_id):
    node = FLOW[node_id]

    prev_p = request.session.get("prev_p")
    if not isinstance(prev_p, (int, float)):
        prev_p = 0.0
    # An unmapped node freezes the ring where it was rather than snapping it to
    # empty in front of a candidate. ProgressModelTests is what makes that loud.
    p = progress_for(node_id, prev_p)

    trail = request.session.get("trail") or []
    timed_out = bool(request.session.pop("timed_out", False))

    context = {
        "timed_out": timed_out,
        "node": node,
        "node_id": node_id,
        "blocks": parse_blocks(node["text"]),
        "options": _options(node_id, node),
        "trail": list(reversed(trail[-TRAIL_DISPLAY:])),
        "can_back": bool(request.session.get("history")),
    }
    context.update(ring_context(p, prev_p))

    # Only touch the session once there is something worth remembering.
    #
    # Writing on every GET meant a bare visit to the landing page created a
    # session cookie and a django_session row before the visitor had clicked
    # anything -- including for crawlers and for anyone who merely arrived. On
    # an embedded page with a cookie notice, a cookie set on arrival is one that
    # has to be consented to; a cookie set once someone starts answering is
    # doing a job they asked for. Nothing is lost by waiting: an absent node_id
    # resolves to start, and an absent prev_p reads as 0.0.
    if node_id != "start" or request.session.get("history"):
        request.session["node_id"] = node_id
        # "The p last rendered." Read on the next GET so the arc animates from
        # where the visitor last saw it: forwards on an answer, backwards on
        # Back, and not at all on a reload of an answered screen, where
        # prev_p == p.
        #
        # The landing page is the one exception, and it follows from the skip
        # above rather than being arranged: nothing is written while the visitor
        # is still on start, so prev_p stays absent and the ring fills in from
        # empty on every visit to start. That is the right first impression.
        request.session["prev_p"] = p

    return render(request, "flow/flow.html", context)
