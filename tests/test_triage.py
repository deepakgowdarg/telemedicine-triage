import unittest
from triage.rules import assess


class TestTriageRules(unittest.TestCase):

    def test_emergency_sign_always_wins(self):
        result = assess(["chest_pain_severe", "cough"], "1 to 2 days")
        self.assertEqual(result["urgency"], "emergency")

    def test_urgent_symptom(self):
        result = assess(["high_fever"], "3 days or more")
        self.assertEqual(result["urgency"], "urgent")

    def test_routine_symptoms(self):
        result = assess(["cough", "runny_nose"], "Less than 1 day")
        self.assertEqual(result["urgency"], "routine")

    def test_routine_never_says_safe(self):
        result = assess(["cough"], "Less than 1 day")
        self.assertIn("not a guarantee", result["recommendation"])

    def test_unknown_codes_are_ignored(self):
        result = assess(["made_up_symptom"], "1 to 2 days")
        self.assertEqual(result["urgency"], "routine")


if __name__ == "__main__":
    unittest.main()