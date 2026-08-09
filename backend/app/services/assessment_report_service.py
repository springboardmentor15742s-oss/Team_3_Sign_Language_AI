def generate_session_report(results: list[dict]) -> dict:
    """
    Summarizes a practice session from a list of sign_assessment_service
    results (each with a "status" of "pass", "fail", or
    "no_attempt_detected", and a "target_letter").

    overall_accuracy_percent and each letter's accuracy_percent are
    computed over scored attempts only (pass + fail) — no-attempt
    results reflect a missing read, not a wrong answer, so including
    them in the accuracy denominator would unfairly penalize the
    learner. scored_attempts is included so consumers can see that
    denominator explicitly.
    """
    total_attempts = len(results)
    correct_count = sum(1 for r in results if r["status"] == "pass")
    incorrect_count = sum(1 for r in results if r["status"] == "fail")
    no_attempt_count = sum(1 for r in results if r["status"] == "no_attempt_detected")
    scored_attempts = correct_count + incorrect_count
    overall_accuracy_percent = (
        round(correct_count / scored_attempts * 100, 1) if scored_attempts else None
    )

    per_letter: dict[str, dict] = {}
    for r in results:
        stats = per_letter.setdefault(
            r["target_letter"], {"attempts": 0, "correct": 0, "incorrect": 0, "no_attempt": 0}
        )
        stats["attempts"] += 1
        if r["status"] == "pass":
            stats["correct"] += 1
        elif r["status"] == "fail":
            stats["incorrect"] += 1
        else:
            stats["no_attempt"] += 1

    for stats in per_letter.values():
        scored = stats["correct"] + stats["incorrect"]
        stats["accuracy_percent"] = round(stats["correct"] / scored * 100, 1) if scored else None

    return {
        "total_attempts": total_attempts,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "no_attempt_count": no_attempt_count,
        "scored_attempts": scored_attempts,
        "overall_accuracy_percent": overall_accuracy_percent,
        "per_letter": dict(sorted(per_letter.items())),
    }
