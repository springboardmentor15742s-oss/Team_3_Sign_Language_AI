"""
Personalized Learning Plan — Milestone 3.

The last step in the Milestone 3 flow:

    Assessment Results -> Store -> Learning Analytics -> Weak Areas ->
    Feedback Engine -> Recommendation Engine -> Personalized Learning Plan
    -> Learner Dashboard

Takes the ordered list from recommendations.generate_recommendations() (already
weakest-first) and packages it as "today's plan" — a numbered list the
learner can work through, with a one-line headline naming their top
priority. Purely a presentation/ordering step: no new numbers are invented
here, everything traces back to analytics.compute_analytics().
"""


def build_learning_plan(recommendations: list) -> dict:
    """
    Returns:
        {
            "title": "Today's Learning Plan",
            "headline": str,
            "items": [
                {"order": 1, "gesture": ..., "display_name": ..., "practice_count": ..., "reason": ...},
                ...
            ],
        }
    """
    if not recommendations:
        return {
            "title": "Today's Learning Plan",
            "headline": "No recommendations yet — complete a few practice attempts to unlock your plan.",
            "items": [],
        }

    items = [
        {
            "order": i,
            "gesture": r["gesture"],
            "display_name": r["display_name"],
            "practice_count": r["practice_count"],
            "reason": r["reason"],
            "level": r["level"],
        }
        for i, r in enumerate(recommendations, start=1)
    ]

    top = items[0]
    headline = f"Practice {top['display_name']} and {items[1]['display_name']} today." if len(items) > 1 \
        else f"Practice {top['display_name']} today."

    return {
        "title": "Today's Learning Plan",
        "headline": headline,
        "items": items,
    }
