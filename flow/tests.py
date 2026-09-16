from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .flow_data import FLOW


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

	def test_invalid_next_resets_to_start(self):
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
