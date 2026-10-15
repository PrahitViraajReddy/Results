from django.test import Client, SimpleTestCase
from django.urls import reverse

from academic_analytics import load_academic_data
from results.views import dataset


class ResultsRouteTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        dataset.cache_clear()
        cls.frame = load_academic_data("results.xlsx")
        cls.rolls = cls.frame["rollNumber"].dropna().astype(str).drop_duplicates().tolist()
        if not cls.rolls:
            raise AssertionError("results.xlsx loaded but contains no student records")
        cls.roll = cls.rolls[0]
        cls.second_roll = next((roll for roll in cls.rolls if roll != cls.rolls[0]), None)

    @classmethod
    def tearDownClass(cls):
        dataset.cache_clear()
        super().tearDownClass()

    def test_home_page_loads_with_workbook(self):
        response = self.client.get(reverse("results:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Results")

    def test_results_lookup_renders_academic_records(self):
        response = self.client.post(
            reverse("results:home"),
            {"page": "Results", "roll_number": self.roll},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semester overview")
        self.assertContains(response, "Semester-wise subject results")

    def test_analytics_page_renders(self):
        response = self.client.post(
            reverse("results:home"),
            {"page": "My Analytics", "roll_number": self.roll},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Performance insights")
        self.assertContains(response, "Semester SGPA")

    def test_comparison_page_renders_for_two_students(self):
        if self.second_roll is None:
            self.skipTest("Workbook contains fewer than two distinct students")
        response = self.client.post(
            reverse("results:home"),
            {
                "page": "Comparison",
                "roll_a": self.roll,
                "roll_b": self.second_roll,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Common-subject comparison")
        self.assertContains(response, "Semester performance comparison")

    def test_pdf_and_csv_exports(self):
        pdf = self.client.get(
            reverse("results:export", args=["pdf"]), {"roll": self.roll}
        )
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

        csv = self.client.get(
            reverse("results:export", args=["csv"]), {"roll": self.roll}
        )
        self.assertEqual(csv.status_code, 200)
        self.assertIn("text/csv", csv["Content-Type"])
        self.assertIn(b"subjectCode", csv.content)

    def test_unknown_export_type_is_not_found(self):
        response = self.client.get("/export/unknown/?roll=TEST123")
        self.assertEqual(response.status_code, 404)

    def test_post_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("results:home"),
            {"page": "Results", "roll_number": self.roll},
        )
        self.assertEqual(response.status_code, 403)
