"""Scenario tests for the adaptive recommendation engine's pure core (no DB)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.adaptive_learning_service import build_adaptive_plan_from_data


def make_outcomes(count: int, accuracy: float) -> list[bool]:
    correct = round(count * accuracy / 100)
    return [True] * correct + [False] * (count - correct)


def make_topic(topic: str, topic_type: str, accuracy: float | None, scored: int) -> dict:
    outcomes = make_outcomes(scored, accuracy) if accuracy is not None else []
    return {
        "topic": topic, "topic_type": topic_type,
        "accuracy_percent": accuracy, "scored_attempts": scored,
        "outcomes": outcomes,
    }


def _overall(topics: list[dict]) -> tuple[float | None, int]:
    scored = sum(t["scored_attempts"] for t in topics)
    if scored == 0:
        return None, 0
    correct = sum(round(t["scored_attempts"] * (t["accuracy_percent"] or 0) / 100) for t in topics)
    return round(correct / scored * 100, 1), scored


def main() -> None:
    high_topics = [make_topic("A", "letter", 90, 10), make_topic("B", "letter", None, 0)]
    high_acc, high_scored = _overall(high_topics)
    high = build_adaptive_plan_from_data("high", high_topics, high_acc, high_scored)

    average_topics = [make_topic("A", "letter", 70, 10), make_topic("B", "letter", None, 0)]
    average_acc, average_scored = _overall(average_topics)
    average = build_adaptive_plan_from_data("average", average_topics, average_acc, average_scored)

    struggling_topics = [make_topic("A", "letter", 50, 10), make_topic("B", "letter", None, 0)]
    struggling_acc, struggling_scored = _overall(struggling_topics)
    struggling = build_adaptive_plan_from_data("struggling", struggling_topics, struggling_acc, struggling_scored)

    beginner_topics = [make_topic("A", "letter", 30, 10), make_topic("B", "letter", None, 0)]
    beginner_acc, beginner_scored = _overall(beginner_topics)
    beginner = build_adaptive_plan_from_data("beginner", beginner_topics, beginner_acc, beginner_scored)

    # Mixed topic types: strong at the letter, weak at the motion sign —
    # checks that a motion_sign topic is prioritised and phrased correctly
    # (no "handshape" language) when it's the actual weak point.
    mixed_topics = [make_topic("A", "letter", 92, 10), make_topic("Wave", "motion_sign", 40, 10)]
    mixed_acc, mixed_scored = _overall(mixed_topics)
    mixed = build_adaptive_plan_from_data("mixed", mixed_topics, mixed_acc, mixed_scored)

    assert high["learning_level"] == "advanced"
    assert average["learning_level"] == "intermediate"
    assert struggling["learning_level"] == "beginner"
    assert beginner["recommendations"][0]["activities"][0]["type"] == "lesson"
    assert struggling["recommendations"][0]["activities"][0]["type"] == "lesson"
    assert high["completed_topics"] == ["A"]

    assert mixed["recommendations"][0]["topic"] == "Wave"
    assert mixed["recommendations"][0]["topic_type"] == "motion_sign"
    assert "handshape" not in mixed["recommendations"][0]["activities"][0]["instruction"]
    assert "motion" in mixed["recommendations"][0]["activities"][0]["instruction"]

    print("Adaptive engine scenarios passed: high, average, struggling, beginner, and mixed-topic-type learners.")


if __name__ == "__main__":
    main()
