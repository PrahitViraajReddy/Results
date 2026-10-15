from django.test import SimpleTestCase
from django.urls import reverse

class ResultsRouteTests(SimpleTestCase):
    def test_home_page_responds(self):
        response = self.client.get(reverse("results:home"))
        # No private workbook: show a friendly 503, never a traceback.
        self.assertIn(response.status_code, (200, 503))

    def test_unknown_export_type_is_not_found(self):
        response = self.client.get("/export/unknown/?roll=TEST123")
        self.assertEqual(response.status_code, 404)
