from django.test import TestCase
from django.urls import reverse


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
