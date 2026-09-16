import os

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .flow_data import FLOW
from .progress import (
	ARC_LEN,
	NODE_PROGRESS,
	STAGE_STARTS,
	STAGES,
	point_at,
	progress_for,
	ring_context,
	stage_index,
)
from .textblocks import parse_blocks
from .views import (
	HISTORY_LIMIT,
	TRAIL_DISPLAY,
	TRAIL_LIMIT,
	_history_entry,
	_options,
)


class FlowViewTests(TestCase):
	def test_root_route_renders_start_node(self):
		response = self.client.get(reverse("flow"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Eligibility Checker 1")
		self.assertContains(response, "Did you have the right to work in the UK confirmed?")

	def test_post_advances_to_next_node(self):
		response = self.client.post(reverse("flow"), {"next": "eligibility_2"}, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Eligibility Checker 2")

	# Renamed from test_invalid_next_resets_to_start, because that is no longer
	# what happens and the old test could not tell the difference: it posted from
	# a fresh session, which is already at "start", so "reset to start" and
	# "stayed put" look identical. An unknown target is now a no-op — see the
	# companion test in FlowNavigationTests for why that matters mid-journey.
	def test_invalid_next_leaves_the_visitor_on_the_current_node(self):
		response = self.client.post(reverse("flow"), {"next": "not-a-real-node"}, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Eligibility Checker 1")


class FlowGraphIntegrityTests(SimpleTestCase):
	"""Structure-only checks on the FLOW graph. No copy, wording or content is asserted."""

	# Catches a dangling option target: a button the user clicks that leads to a node
	# that does not exist, so the view falls back to start or raises KeyError.
	def test_every_option_points_at_a_real_node(self):
		broken = []

		for node_id, node in FLOW.items():
			for index, option in enumerate(node.get("options") or []):
				target = option.get("next")
				if target not in FLOW:
					broken.append(
						"node {!r} option {} (label {!r}) points at {!r}, which is not a node id".format(
							node_id, index, option.get("label"), target
						)
					)

		self.assertEqual(
			broken,
			[],
			"Options pointing at non-existent nodes:\n" + "\n".join(broken),
		)

	# Catches an orphaned node: content the client paid for that no path from "start"
	# can ever reach, so it is invisible in the running app.
	def test_every_node_is_reachable_from_start(self):
		self.assertIn("start", FLOW, "FLOW has no 'start' node, so nothing is reachable.")

		visited = set()
		queue = ["start"]

		while queue:
			node_id = queue.pop(0)
			if node_id in visited or node_id not in FLOW:
				continue
			visited.add(node_id)
			for option in FLOW[node_id].get("options") or []:
				target = option.get("next")
				if target in FLOW and target not in visited:
					queue.append(target)

		unreachable = sorted(set(FLOW) - visited)

		self.assertEqual(
			visited,
			set(FLOW),
			"Nodes unreachable from 'start': " + ", ".join(unreachable),
		)

	# Catches a dead end: a node with no options renders a page the user cannot leave
	# without using the browser back button.
	def test_every_node_offers_at_least_one_option(self):
		dead_ends = sorted(
			node_id for node_id, node in FLOW.items() if not node.get("options")
		)

		self.assertEqual(
			dead_ends,
			[],
			"Nodes with no options (dead ends the user cannot leave): "
			+ ", ".join(dead_ends),
		)

	# Catches a malformed node: a missing or empty type/title/text/options, or an option
	# with no label or no target, which renders as a blank page or a blank button.
	def test_every_node_has_required_shape(self):
		valid_types = {"question", "statement"}
		problems = []

		for node_id in sorted(FLOW):
			node = FLOW[node_id]

			if not isinstance(node, dict):
				problems.append("node {!r}: is {}, not a dict".format(node_id, type(node).__name__))
				continue

			node_type = node.get("type")
			if node_type not in valid_types:
				problems.append(
					"node {!r}: field 'type' is {!r}, expected one of {}".format(
						node_id, node_type, sorted(valid_types)
					)
				)

			for field in ("title", "text", "options"):
				if field not in node:
					problems.append("node {!r}: field {!r} is missing".format(node_id, field))
				elif not node[field]:
					problems.append("node {!r}: field {!r} is empty".format(node_id, field))

			for index, option in enumerate(node.get("options") or []):
				if not isinstance(option, dict):
					problems.append(
						"node {!r} option {}: is {}, not a dict".format(
							node_id, index, type(option).__name__
						)
					)
					continue
				for field in ("label", "next"):
					if not option.get(field):
						problems.append(
							"node {!r} option {}: field {!r} is missing or empty".format(
								node_id, index, field
							)
						)

		self.assertEqual(
			problems,
			[],
			"Malformed nodes:\n" + "\n".join(problems),
		)


class ProgressModelTests(SimpleTestCase):
	"""NODE_PROGRESS against FLOW. Structure only; no fraction is asserted by value.

	progress.py and views.py both name this class as what stops the progress map
	drifting out of step with the content. Nothing here asserts a node's position
	on the ring, only that every node has one and that all five stage rows stay
	reachable.
	"""

	# Catches a node transcribed into FLOW without a progress fraction: it renders
	# with the ring frozen at the previous node's value, invisible to anyone who
	# does not click through that branch.
	def test_every_flow_node_has_a_progress_fraction(self):
		missing = sorted(set(FLOW) - set(NODE_PROGRESS))

		self.assertEqual(
			missing,
			[],
			"Nodes in FLOW with no NODE_PROGRESS entry (add them to flow/progress.py): "
			+ ", ".join(missing),
		)

	# Catches a stale entry left behind when a node is deleted from FLOW: dead
	# weight that hides the fact its fraction is no longer used by anything.
	def test_every_progress_entry_is_a_real_node(self):
		stale = sorted(set(NODE_PROGRESS) - set(FLOW))

		self.assertEqual(
			stale,
			[],
			"NODE_PROGRESS keys that are not nodes in FLOW (remove them from "
			"flow/progress.py): " + ", ".join(stale),
		)

	# Catches a fraction outside (0, 1]: 0.0 reads as an empty ring on a screen the
	# visitor has already reached, and above 1.0 pushes the head marker off the end
	# of the arc and the percentage past 100.
	def test_every_progress_fraction_is_within_bounds(self):
		problems = []

		for node_id in sorted(NODE_PROGRESS):
			p = NODE_PROGRESS[node_id]
			if isinstance(p, bool) or not isinstance(p, (int, float)):
				problems.append(
					"node {!r}: progress is {}, not a number".format(
						node_id, type(p).__name__
					)
				)
			elif not 0 < p <= 1:
				problems.append(
					"node {!r}: progress is {!r}, expected 0 < p <= 1".format(node_id, p)
				)

		self.assertEqual(
			problems,
			[],
			"Progress fractions out of range in flow/progress.py:\n" + "\n".join(problems),
		)

	# Catches a stage row no node can ever light up, after an edit to STAGE_STARTS
	# or to the fractions: the stage list would show a step the visitor is never
	# told they are on.
	def test_every_stage_is_reachable_from_some_node(self):
		reached = {stage_index(p) for p in NODE_PROGRESS.values()}
		unreachable = sorted(set(range(len(STAGES))) - reached)

		self.assertEqual(
			unreachable,
			[],
			"Stages that no node's progress fraction falls in (adjust STAGE_STARTS or "
			"the fractions in flow/progress.py): "
			+ ", ".join("{} ({!r})".format(i, STAGES[i]) for i in unreachable),
		)


class FlowNavigationTests(TestCase):
	"""Session behaviour: the answer trail, Back, and the ring's animation state.

	There is no model layer here, so the session is the only place state lives and
	these are the only tests that can catch it being written wrongly.
	"""

	def _seed(self, node_id, **session_values):
		"""Put the visitor on ``node_id`` without walking there first."""
		self.client.get(reverse("flow"))
		session = self.client.session
		session["node_id"] = node_id
		session.update(session_values)
		session.save()

	def _post(self, next_id, choice=None, came_from=None):
		data = {"next": next_id}
		if choice is not None:
			data["choice"] = str(choice)
		data["from"] = (
			self.client.session.get("node_id") if came_from is None else came_from
		)
		return self.client.post(reverse("flow"), data)

	def _back_index(self, node_id, target_id):
		for index, option in enumerate(FLOW[node_id]["options"]):
			if option["next"] == target_id:
				return index
		self.fail("{!r} no longer offers a route back to {!r}".format(node_id, target_id))

	# The realistic trigger is this project's own content workflow: nodes are
	# added and removed every time a client document is transcribed, so a visitor
	# holding a page open across a deploy can click an option whose target has
	# since gone. That used to discard their answers and their Back history.
	def test_unknown_next_mid_journey_preserves_the_answer_trail(self):
		self.client.get(reverse("flow"))
		self._post("eligibility_2", choice=0, came_from="start")
		self.client.get(reverse("flow"))

		trail_before = list(self.client.session["trail"])
		history_before = list(self.client.session["history"])
		self.assertEqual(len(trail_before), 1, "precondition: one answer recorded")

		self._post("a_node_removed_by_a_content_deploy", choice=0)
		self.client.get(reverse("flow"))

		self.assertEqual(self.client.session["node_id"], "eligibility_2")
		self.assertEqual(self.client.session["trail"], trail_before)
		self.assertEqual(self.client.session["history"], history_before)

	# Eleven nodes carry a real "Start over" content option. That one still wipes,
	# because clearing the journey is exactly what the visitor asked for.
	def test_start_over_option_still_clears_the_journey(self):
		self.client.get(reverse("flow"))
		self._post("eligibility_2", choice=0, came_from="start")
		self.client.get(reverse("flow"))
		self.assertEqual(len(self.client.session["trail"]), 1)

		self._post("start", choice=0)
		self.client.get(reverse("flow"))

		self.assertEqual(self.client.session["node_id"], "start")
		self.assertEqual(self.client.session["trail"], [])
		self.assertEqual(self.client.session["history"], [])

	# "Start again" in the footer must not be reachable by a GET: a link prefetch,
	# a chat link preview or a browser restoring tabs would then silently destroy
	# the journey without the visitor deciding anything.
	def test_start_again_is_a_post_and_is_not_a_link_in_the_page(self):
		self.client.get(reverse("flow"))
		self._post("eligibility_2", choice=0, came_from="start")
		response = self.client.get(reverse("flow"))

		self.assertNotContains(response, "?node=start")
		self.assertContains(response, 'name="reset"')

		self.client.post(reverse("flow"), {"reset": "1"})
		self.client.get(reverse("flow"))

		self.assertEqual(self.client.session["node_id"], "start")
		self.assertEqual(self.client.session["trail"], [])
		self.assertEqual(self.client.session["history"], [])

	# Catches a backwards option rendering the design's forward arrow. Eight nodes
	# carry their own "Back" option, and "Back to Routes ->" a few lines above the
	# footer's "<- Back" gives the candidate two controls with the same word
	# pointing opposite ways.
	def test_no_backward_option_is_flagged_as_going_forward(self):
		wrong = []

		for node_id, node in FLOW.items():
			for option in _options(node_id, node):
				label = (option["label"] or "").strip().lower()
				if label.startswith("back") and not option["goes_back"]:
					wrong.append(
						"node {!r} option {!r} points back to {!r} but would "
						"render a forward arrow".format(
							node_id, option["label"], option["next"]
						)
					)

		self.assertEqual(
			wrong,
			[],
			"Backward options rendering a forward arrow:\n" + "\n".join(wrong),
		)

	# Catches the trail inventing an answer. Without a trustworthy index there is
	# no way to tell which of two same-target options was clicked, and naming the
	# first would put a sentence in the rail the visitor never chose.
	def test_ambiguous_target_without_an_index_records_nothing(self):
		ambiguous = "training_locations"
		target = FLOW[ambiguous]["options"][0]["next"]
		self.assertEqual(
			FLOW[ambiguous]["options"][1]["next"],
			target,
			"precondition: both options must still share a target",
		)

		self._seed(ambiguous, history=[], trail=[])
		self.client.post(
			reverse("flow"), {"next": target, "from": ambiguous}
		)

		self.assertEqual(self.client.session["trail"], [])

	# Catches ?node= being honoured as a deep link again. It is a GET that clears
	# state, so a prefetch or a stale bookmark could drop a visitor mid-flow at a
	# percentage they never earned.
	def test_node_query_parameter_always_lands_on_start(self):
		response = self.client.get(reverse("flow") + "?node=employment_routes_2")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(self.client.session["node_id"], "start")

	# Catches the rail silently emptying. The session lasts an hour of inactivity
	# and one screen in this flow is 5,300 characters of reading.
	def test_session_expiry_mid_flow_is_announced_once(self):
		self.client.get(reverse("flow"))
		self._post("eligibility_2", choice=0, came_from="start")
		self.client.get(reverse("flow"))

		del self.client.cookies["sessionid"]

		response = self.client.post(
			reverse("flow"),
			{"next": "overseas_eligibility_3", "choice": "1", "from": "eligibility_2"},
			follow=True,
		)

		self.assertContains(response, 'class="notice"')
		self.assertEqual(self.client.session["node_id"], "overseas_eligibility_3")
		self.assertNotContains(self.client.get(reverse("flow")), 'class="notice"')

	# A first answer arrives with no session too, because nothing is written while
	# the visitor is still on start. It must not be mistaken for an expiry.
	def test_first_answer_is_not_mistaken_for_an_expired_session(self):
		self.client.get(reverse("flow"))

		response = self.client.post(
			reverse("flow"),
			{"next": "eligibility_2", "choice": "0", "from": "start"},
			follow=True,
		)

		self.assertNotContains(response, 'class="notice"')

	# A deleted node sitting in the Back history costs one step, not the journey.
	def test_back_walks_past_a_history_step_whose_node_was_deleted(self):
		self.client.get(reverse("flow"))
		self._post("eligibility_2", choice=0, came_from="start")
		self.client.get(reverse("flow"))

		session = self.client.session
		session["history"] = [
			{"id": "start", "trailed": False},
			{"id": "a_node_removed_by_a_content_deploy", "trailed": False},
		]
		session.save()

		self.client.post(reverse("flow"), {"back": "1"})
		self.client.get(reverse("flow"))

		self.assertEqual(self.client.session["node_id"], "start")

	# Catches the answer trail recording the wrong option. subject_phase_2,
	# subject_phase_3 and training_locations each offer two differently labelled
	# options with the same target, so a label looked up by target alone always
	# returns the first of the pair -- telling a candidate they chose Oxford/Reading
	# when they clicked Banstead.
	def test_trail_records_the_option_clicked_not_the_first_with_that_target(self):
		options = FLOW["training_locations"]["options"]
		self.assertEqual(
			options[0]["next"],
			options[1]["next"],
			"training_locations no longer has two options sharing one target, so this "
			"test no longer exercises the index-versus-target lookup.",
		)
		self.assertNotEqual(options[0]["label"], options[1]["label"])

		self._seed("training_locations", history=[], trail=[])
		self._post(options[1]["next"], choice=1)

		trail = self.client.session["trail"]
		self.assertEqual(len(trail), 1)
		self.assertEqual(trail[0]["answer"], options[1]["label"])

	# Catches Back popping the wrong answer. A step that recorded no trail entry
	# must not make Back remove a different question's answer; from then on every
	# entry in the trail is attributed to the wrong question.
	def test_back_removes_only_the_trail_entry_its_own_step_created(self):
		untrailed_target = "contact_us"
		self.assertNotIn(
			untrailed_target,
			[option["next"] for option in FLOW["eligibility_2"]["options"]],
			"{!r} is now an option of eligibility_2, so posting it records a trail "
			"entry and this test no longer covers the asymmetric case.".format(
				untrailed_target
			),
		)

		self._seed("start", history=[], trail=[])
		self._post("eligibility_2", choice=0)
		answered = self.client.session["trail"]
		self.assertEqual(len(answered), 1)

		# A target that is a real node but not an option of the current one: the
		# label lookup finds nothing, so the step is pushed with trailed=False.
		self._post(untrailed_target)
		session = self.client.session
		self.assertEqual(session["node_id"], untrailed_target)
		self.assertEqual(session["trail"], answered)
		self.assertEqual(len(session["history"]), 2)
		self.assertIs(session["history"][-1]["trailed"], False)

		self.client.post(reverse("flow"), {"back": "1"})
		session = self.client.session
		self.assertEqual(session["node_id"], "eligibility_2")
		self.assertEqual(
			session["trail"],
			answered,
			"Back over a step that recorded no answer removed another question's answer.",
		)

		self.client.post(reverse("flow"), {"back": "1"})
		session = self.client.session
		self.assertEqual(session["node_id"], "start")
		self.assertEqual(session["trail"], [])

	# Catches Back on the first screen crashing, or silently resetting the journey,
	# when there is nothing to go back to.
	def test_back_with_empty_history_is_a_no_op(self):
		answered = [{"question": "Q", "answer": "A"}]
		self._seed("eligibility_2", history=[], trail=list(answered))

		response = self.client.post(reverse("flow"), {"back": "1"}, follow=True)

		session = self.client.session
		self.assertEqual(response.status_code, 200)
		self.assertEqual(session["node_id"], "eligibility_2")
		self.assertEqual(session["trail"], answered)
		self.assertEqual(session["history"], [])

	# Catches an answer being attributed to whichever question is current now when
	# the form came from a different one -- a second tab, or a page the browser
	# restored from its cache.
	def test_post_from_a_stale_screen_navigates_without_recording_anything(self):
		self._seed("start", history=[], trail=[])

		self._post("eligibility_2", choice=0, came_from="training_locations")

		session = self.client.session
		self.assertEqual(session["node_id"], "eligibility_2")
		self.assertEqual(session["trail"], [])
		self.assertEqual(session["history"], [])

	# Catches a tampered or stale option index being trusted: each of these must
	# fall back to the by-target lookup rather than record an answer for a route
	# the visitor was never offered.
	def test_untrustworthy_choice_falls_back_to_the_target_lookup(self):
		options = FLOW["start"]["options"]
		target = options[0]["next"]
		expected = options[0]["label"]
		self.assertNotEqual(options[1]["next"], target)

		offenders = []
		for choice in (None, "", "banana", "-1", "99", "0.5", "1"):
			self._seed("start", history=[], trail=[])
			self._post(target, choice=choice)
			trail = self.client.session["trail"]
			answer = trail[-1]["answer"] if trail else None
			if answer != expected:
				offenders.append(
					"choice={!r} recorded {!r}, expected {!r}".format(
						choice, answer, expected
					)
				)

		self.assertEqual(
			offenders,
			[],
			"Option indexes trusted when they should not have been:\n"
			+ "\n".join(offenders),
		)

	# Catches "Start again" leaving the previous journey's history and answer trail
	# behind, so the page describes a path this visitor never walked and the ring
	# animates in from wherever they had got to.
	def test_node_query_parameter_clears_history_trail_and_animation(self):
		self._seed("start", history=[], trail=[])
		self._post("eligibility_2", choice=0)
		self._post("domestic_eligibility_1", choice=0)
		self.assertTrue(self.client.session["trail"])

		response = self.client.get(reverse("flow") + "?node=start")

		session = self.client.session
		self.assertEqual(session["history"], [])
		self.assertEqual(session["trail"], [])
		self.assertEqual(
			response.context["prev_dash_offset"],
			"{:.2f}".format(ARC_LEN),
			"prev_p was not reset, so the ring animates in from the abandoned journey.",
		)

	# Catches a session written by the previous version of the view -- history as a
	# list of bare node ids -- raising on the first Back after a deploy.
	def test_legacy_string_history_entry_does_not_raise_or_pop_an_answer(self):
		self.assertEqual(_history_entry("eligibility_2"), ("eligibility_2", False))

		answered = [{"question": "Q", "answer": "A"}]
		self._seed(
			"domestic_eligibility_1", history=["eligibility_2"], trail=list(answered)
		)

		response = self.client.post(reverse("flow"), {"back": "1"}, follow=True)

		session = self.client.session
		self.assertEqual(response.status_code, 200)
		self.assertEqual(session["node_id"], "eligibility_2")
		self.assertEqual(session["trail"], answered)
		self.assertEqual(session["history"], [])

	# Catches an unbounded session: the flow contains loops, so a long enough visit
	# grows history and trail without limit and rewrites both on every request.
	#
	# Only one of the two nodes in this loop is a question, so a round trip adds
	# two history steps and one trail entry. The loop therefore has to run past
	# TRAIL_LIMIT round trips for the trail cap to be exercised at all -- at
	# fewer, this test passed while asserting nothing about the trail.
	def test_history_and_trail_are_capped(self):
		question = "routes_into_teaching_1"
		statement = FLOW[question]["options"][0]["next"]
		back = self._back_index(statement, question)

		self.assertEqual(
			FLOW[question]["type"],
			"question",
			"the loop's trail entries come from this node being a question",
		)
		self.assertEqual(
			FLOW[statement]["type"],
			"statement",
			"if this became a question the round-trip arithmetic below changes",
		)

		self._seed(question, history=[], trail=[])
		for _ in range(TRAIL_LIMIT + 2):
			self._post(statement, choice=0, came_from=question)
			self._post(question, choice=back, came_from=statement)

		session = self.client.session
		self.assertEqual(len(session["history"]), HISTORY_LIMIT)
		self.assertEqual(len(session["trail"]), TRAIL_LIMIT)

	# Catches the answer trail rendering oldest-first, or spilling past the
	# TRAIL_DISPLAY entries the panel is designed to hold.
	def test_only_the_newest_trail_entries_reach_the_template_newest_first(self):
		question = "routes_into_teaching_1"
		options = FLOW[question]["options"]

		self._seed(question, history=[], trail=[])
		for step in range(TRAIL_DISPLAY + 1):
			index = step % 2
			statement = options[index]["next"]
			self._post(statement, choice=index, came_from=question)
			self._post(
				question,
				choice=self._back_index(statement, question),
				came_from=statement,
			)

		response = self.client.get(reverse("flow"))
		trail = self.client.session["trail"]
		shown = response.context["trail"]

		self.assertEqual(len(trail), TRAIL_DISPLAY + 1)
		self.assertEqual(len(shown), TRAIL_DISPLAY)
		self.assertEqual(list(shown), list(reversed(trail[-TRAIL_DISPLAY:])))
		self.assertEqual(shown[0]["answer"], options[TRAIL_DISPLAY % 2]["label"])
		self.assertEqual(shown[1]["answer"], options[(TRAIL_DISPLAY + 1) % 2]["label"])

	# Catches prev_p drifting from "the p last rendered": a forward step would not
	# animate the ring, or a reload would animate it again from the wrong place.
	#
	# The landing page is deliberately excluded: _render writes no session there,
	# so prev_p stays 0.0 and the ring fills in from empty on every visit to
	# start. See test_landing_page_get_writes_no_session below.
	def test_prev_p_is_the_p_last_rendered(self):
		self.client.get(reverse("flow"))
		self._post("eligibility_2", choice=0, came_from="start")

		moved = self.client.get(reverse("flow"))

		self.assertEqual(self.client.session["prev_p"], progress_for("eligibility_2"))
		self.assertLess(
			float(moved.context["dash_offset"]),
			float(moved.context["prev_dash_offset"]),
			"A forward step did not move the ring: prev_p is not behind p.",
		)

		reloaded = self.client.get(reverse("flow"))

		self.assertEqual(self.client.session["prev_p"], progress_for("eligibility_2"))
		self.assertEqual(
			reloaded.context["dash_offset"],
			reloaded.context["prev_dash_offset"],
			"A reload animates the ring, because prev_p is not the p last rendered.",
		)

	# Catches a session cookie being created by arrival alone. This page is embedded
	# on the client's public site behind a cookie notice: a cookie set before the
	# visitor clicks anything is one that has to be consented to, and every crawler
	# would leave a django_session row behind.
	def test_landing_page_get_writes_no_session(self):
		response = self.client.get(reverse("flow"))

		self.assertEqual(response.status_code, 200)
		self.assertNotIn(
			settings.SESSION_COOKIE_NAME,
			self.client.cookies,
			"A bare GET of the landing page set a session cookie.",
		)

		self._post("eligibility_2", choice=0, came_from="start")

		self.assertIn(settings.SESSION_COOKIE_NAME, self.client.cookies)
		self.assertEqual(self.client.session["node_id"], "eligibility_2")


class TextBlockTests(SimpleTestCase):
	"""parse_blocks, on lines written here rather than drawn from FLOW.

	The heuristic is what gives plain client prose its structure, so it is tested
	against shapes of line. The one check that does read FLOW asserts a rule, not
	any wording.
	"""

	# Catches consecutive bullet lines rendering as separate one-item lists, which
	# look identical on screen but are not a list to a screen reader.
	def test_consecutive_bullet_lines_collapse_into_one_block(self):
		blocks = parse_blocks("Requirements\n• GCSE maths\n• GCSE English\n• A degree")

		self.assertEqual(
			[block["kind"] for block in blocks],
			["heading", "bullets"],
		)
		self.assertEqual(
			blocks[1]["items"], ["GCSE maths", "GCSE English", "A degree"]
		)

	# Catches a numbered point being renumbered or grouped into an <ol>: the marker
	# shown must be the client's own text, and a run of points must not swallow the
	# line that follows it.
	def test_numbered_lines_keep_the_clients_marker_and_stay_ungrouped(self):
		blocks = parse_blocks(
			"2) Flexibility\nThis point runs on for a second line.\n"
			"4) Fees\nUniversity guides you may find useful:"
		)

		self.assertEqual(
			[block["kind"] for block in blocks],
			["numbered", "body", "numbered", "body"],
		)
		self.assertEqual(
			[(block["marker"], block["text"]) for block in blocks if block["kind"] == "numbered"],
			[("2)", "Flexibility"), ("4)", "Fees")],
		)

	# Catches blank lines between paragraphs becoming empty blocks, which the
	# template then renders as stray vertical gaps.
	def test_blank_lines_are_dropped(self):
		blocks = parse_blocks("\n\nFirst paragraph here.\n\n   \n\nSecond one here.\n\n")

		self.assertEqual(
			blocks,
			[
				{"kind": "body", "text": "First paragraph here."},
				{"kind": "body", "text": "Second one here."},
			],
		)

	# Catches the heading heuristic in both directions: a route name losing its
	# heading styling, and a fee line, an email address, a URL, a question or a
	# numbered item being promoted to a heading it was never meant to be.
	def test_heading_heuristic_classifies_lines_by_shape(self):
		expected = [
			("Salaried Route", "heading"),
			("Assessment Only Route", "heading"),
			("Are you ready?", "body"),
			("It is short.", "body"),
			("Primary or Secondary:", "body"),
			("hello@glftt.org", "body"),
			("https://www.glftt.org/apply", "body"),
			("The fee is £10,050", "body"),
			("2) Flexibility", "numbered"),
			(
				"A line of ordinary prose that runs on well past the heading length "
				"limit and is plainly a paragraph",
				"body",
			),
		]

		offenders = []
		for line, kind in expected:
			blocks = parse_blocks(line)
			actual = blocks[0]["kind"] if blocks else None
			if actual != kind:
				offenders.append(
					"{!r} classified as {!r}, expected {!r}".format(line, actual, kind)
				)

		self.assertEqual(
			offenders,
			[],
			"Lines the heading heuristic in flow/textblocks.py gets wrong:\n"
			+ "\n".join(offenders),
		)

	# Catches a fee, an email address or a link in the client's copy rendering as a
	# route heading -- a silent visual bug that only shows on the one screen that
	# happens to carry that line.
	def test_no_heading_in_flow_carries_a_url_email_or_currency_figure(self):
		offenders = []

		for node_id in sorted(FLOW):
			for block in parse_blocks(FLOW[node_id].get("text")):
				if block["kind"] != "heading":
					continue
				text = block["text"]
				if "http" in text.lower() or "@" in text or any(
					symbol in text for symbol in "£$€"
				):
					offenders.append("node {!r}: heading {!r}".format(node_id, text))

		self.assertEqual(
			offenders,
			[],
			"Lines rendering as sub-headings that are facts, not headings (tighten the "
			"heuristic in flow/textblocks.py, or ask the client to reword):\n"
			+ "\n".join(offenders),
		)


class TemplateCommentSyntaxTests(SimpleTestCase):
	"""Static scan of the templates. A render test cannot catch either of these,
	because the page renders fine in both cases.
	"""

	def _template_files(self):
		root = os.path.join(settings.BASE_DIR, "flow", "templates")
		found = []

		for directory, _subdirs, filenames in os.walk(root):
			for filename in filenames:
				if filename.endswith(".html"):
					found.append(os.path.join(directory, filename))

		self.assertTrue(
			found,
			"No *.html files under {} -- this test is not looking at anything.".format(
				root
			),
		)
		return sorted(found)

	def _lines(self, path):
		with open(path, encoding="utf-8") as handle:
			return handle.read().split("\n")

	# Catches a {# ... #} comment split across a newline. Django's comment syntax is
	# single-line only, so the whole block stops being a comment and renders as
	# visible page text -- notes addressed to a developer, read by a visitor.
	def test_no_django_comment_is_left_open_at_the_end_of_a_line(self):
		offenders = []

		for path in self._template_files():
			for number, line in enumerate(self._lines(path), start=1):
				remainder = line
				while "{#" in remainder:
					remainder = remainder.split("{#", 1)[1]
					if "#}" not in remainder:
						offenders.append(
							"{}:{}: {{# with no closing #}} on the same line".format(
								os.path.relpath(path, settings.BASE_DIR), number
							)
						)
						break
					remainder = remainder.split("#}", 1)[1]

		self.assertEqual(
			offenders,
			[],
			"Unclosed Django comments (close them on the same line, or use "
			"{% comment %} ... {% endcomment %}):\n" + "\n".join(offenders),
		)

	# Catches an HTML comment: invisible on screen but delivered to every browser
	# and readable in view-source, so a developer note ships to the public site.
	def test_no_html_comments_in_templates(self):
		offenders = []

		for path in self._template_files():
			for number, line in enumerate(self._lines(path), start=1):
				if "<!--" in line or "-->" in line:
					offenders.append(
						"{}:{}: {}".format(
							os.path.relpath(path, settings.BASE_DIR), number, line.strip()
						)
					)

		self.assertEqual(
			offenders,
			[],
			"HTML comments in templates (use {# ... #} or {% comment %} instead):\n"
			+ "\n".join(offenders),
		)


class RingGeometryTests(SimpleTestCase):
	"""The arc maths in progress.py against the SVG path in _progress_figure.html.

	That path is hard-coded: M28.6 130 A76 76 0 1 1 171.4 130. If the constants
	here and the path there stop describing the same curve, the head marker walks
	off the stroke and nothing errors.
	"""

	# Catches the constants and the hard-coded <path d="..."> drifting apart, which
	# puts the head marker and the milestone ticks beside the arc instead of on it.
	def test_arc_endpoints_match_the_hard_coded_svg_path(self):
		start_x, start_y = point_at(0)
		end_x, end_y = point_at(1)

		self.assertAlmostEqual(start_x, 28.6, places=1)
		self.assertAlmostEqual(start_y, 130.0, places=1)
		self.assertAlmostEqual(end_x, 171.4, places=1)
		self.assertAlmostEqual(end_y, 130.0, places=1)

	# Catches a float reaching the template: Django localises floats when USE_L10N
	# is on, and a decimal comma in an SVG transform or stroke-dashoffset breaks the
	# figure silently, in some locales only.
	def test_ring_context_returns_geometry_as_strings(self):
		context = ring_context(0.5, 0.2)
		offenders = []

		keys = (
			"arc_len",
			"dash_offset",
			"prev_dash_offset",
			"head_x",
			"head_y",
			"prev_head_x",
			"prev_head_y",
		)
		for key in keys:
			if not isinstance(context[key], str):
				offenders.append(
					"{}: {} ({!r})".format(key, type(context[key]).__name__, context[key])
				)

		for index, tick in enumerate(context["ticks"]):
			for key in ("x", "y"):
				if not isinstance(tick[key], str):
					offenders.append(
						"ticks[{}][{!r}]: {}".format(
							index, key, type(tick[key]).__name__
						)
					)

		self.assertEqual(
			offenders,
			[],
			"ring_context values that are not pre-formatted strings:\n"
			+ "\n".join(offenders),
		)

	# Catches the progress stroke not spanning the whole arc: an empty ring would
	# show some fill at the start, or a finished one would stop short of the end.
	def test_dash_offset_spans_the_whole_arc(self):
		self.assertAlmostEqual(float(ring_context(0, 0)["dash_offset"]), ARC_LEN, places=2)
		self.assertEqual(ring_context(1, 1)["dash_offset"], "0.00")
		self.assertEqual(ring_context(0, 0)["arc_len"], "{:.1f}".format(ARC_LEN))

	# Catches an off-by-one at a stage boundary: the visitor is shown the previous
	# stage's name on the first screen of the next one, including exactly on the
	# boundary value itself.
	def test_stage_index_at_every_boundary(self):
		problems = []

		for index, start in enumerate(STAGE_STARTS):
			actual = stage_index(start)
			if actual != index:
				problems.append(
					"p={!r} (start of stage {}) gave index {}".format(
						start, index, actual
					)
				)
			if index:
				below = stage_index(start - 0.001)
				if below != index - 1:
					problems.append(
						"p={!r} (just below stage {}) gave index {}, expected {}".format(
							start - 0.001, index, below, index - 1
						)
					)

		if stage_index(1.0) != len(STAGES) - 1:
			problems.append(
				"p=1.0 gave index {}, expected the last stage".format(stage_index(1.0))
			)

		self.assertEqual(
			problems,
			[],
			"Stage boundaries that map to the wrong stage:\n" + "\n".join(problems),
		)
