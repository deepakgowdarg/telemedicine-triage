# Each symptom has a short code (saved in the database) and a label (shown to the user)
SYMPTOMS = [
    ("chest_pain_severe", "Severe chest pain or pressure"),
    ("breathing_severe", "Severe difficulty breathing"),
    ("unresponsive", "Collapsed or not responding"),
    ("stroke_signs", "Face drooping, arm weakness or slurred speech"),
    ("severe_bleeding", "Bleeding that will not stop"),
    ("high_fever", "High fever"),
    ("persistent_vomiting", "Vomiting that will not stop"),
    ("moderate_pain", "Moderate pain that is getting worse"),
    ("cough", "Cough"),
    ("runny_nose", "Runny nose or sore throat"),
    ("mild_headache", "Mild headache"),
    ("fatigue", "Tiredness"),
]

LABELS = dict(SYMPTOMS)
CODES = set(LABELS)

DURATIONS = ["Less than 1 day", "1 to 2 days", "3 days or more"]

EMERGENCY_SYMPTOMS = {
    "chest_pain_severe",
    "breathing_severe",
    "unresponsive",
    "stroke_signs",
    "severe_bleeding",
}

URGENT_SYMPTOMS = {
    "high_fever",
    "persistent_vomiting",
    "moderate_pain",
}


def assess(selected, duration):
    """Return the urgency, the rules that fired, and a recommendation."""
    selected = {s for s in selected if s in CODES}

    # Rule 1: any emergency warning sign always wins
    emergency_hits = sorted(selected & EMERGENCY_SYMPTOMS)
    if emergency_hits:
        return {
            "urgency": "emergency",
            "matched_rules": [f"R1: emergency warning sign ({', '.join(emergency_hits)})"],
            "recommendation": "Possible emergency warning signs. Call 112 now. Do not wait to finish this form.",
        }

    # Rule 2: any urgent symptom
    urgent_hits = sorted(selected & URGENT_SYMPTOMS)
    if urgent_hits:
        return {
            "urgency": "urgent",
            "matched_rules": [f"R2: urgent symptom ({', '.join(urgent_hits)})"],
            "recommendation": "A doctor should review this soon, ideally today. If symptoms get worse, call 112.",
        }

    # Rule 3: everything else is routine, but never described as 'safe'
    listed = ", ".join(sorted(selected))
    return {
        "urgency": "routine",
        "matched_rules": [f"R3: no emergency or urgent symptom selected ({listed})"],
        "recommendation": (
            "Routine review is suggested. This is not a guarantee that you are safe. "
            "Seek care sooner if symptoms get worse or new warning signs appear."
        ),
    }