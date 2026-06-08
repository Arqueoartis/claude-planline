import unittest

from claude_planline.cli import render


class RenderTest(unittest.TestCase):
    def test_five_hour_usage(self):
        payload = {
            "rate_limits": {
                "five_hour": {
                    "used_percentage": 42,
                    "resets_at": "2:10am (Europe/Madrid)",
                }
            }
        }

        output = render(payload, lang="es", style="cute", color=False)

        self.assertIn("5h", output)
        self.assertIn("42% usado", output)
        self.assertIn("queda 58%", output)

    def test_five_hour_one_percent_is_not_treated_as_fraction(self):
        payload = {
            "rate_limits": {
                "five_hour": {
                    "used_percentage": 1,
                    "resets_at": "2:10am (Europe/Madrid)",
                }
            }
        }

        output = render(payload, lang="es", style="cute", color=False)

        self.assertIn("1% usado", output)
        self.assertIn("queda 99%", output)

    def test_five_hour_explicit_fraction_field(self):
        payload = {
            "rate_limits": {
                "five_hour": {
                    "used_fraction": 0.42,
                }
            }
        }

        output = render(payload, lang="es", style="cute", color=False)

        self.assertIn("42% usado", output)

    def test_usage_credits_structured(self):
        payload = {
            "usage_credits": {
                "spent": 25.14,
                "limit": 30,
                "currency": "EUR",
                "resets_at": "Jul 1",
            }
        }

        output = render(payload, lang="es", style="cute", color=False)

        self.assertIn("extra", output)
        self.assertIn("€25.14/€30 mes", output)

    def test_usage_credits_text_fallback(self):
        payload = {
            "usage_credits": {
                "used_percentage": "83%",
                "summary": "€25.14 / €30.00 spent · Resets Jul 1 (Europe/Madrid)",
            }
        }

        output = render(payload, lang="es", style="cute", color=False)

        self.assertIn("extra", output)
        self.assertIn("€25.14/€30 mes", output)

    def test_no_data(self):
        output = render({}, lang="es", style="cute", color=False)

        self.assertEqual(output, "(-_-) sin datos")


if __name__ == "__main__":
    unittest.main()
