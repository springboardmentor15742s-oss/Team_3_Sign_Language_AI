"""
Quiz / Knowledge-Check module routes (roadmap: "Quiz generation" + "Skill
evaluation" under the Assessment & Certification Module).

    GET  /api/quiz/questions?level=Beginner&count=5   random question set (no answer key)
    POST /api/quiz/submit                             grade answers, log the attempt
    GET  /api/quiz/my-attempts                         this learner's quiz history

Grading always happens server-side against quiz_questions.correct_option —
the answer key is never sent to the client in /questions.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from config import LEARNING_LEVELS
from database import db
from deps import get_current_user
from schemas.models import QuizQuestionOut, QuizSubmitRequest

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

DEFAULT_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 20


@router.get("/questions", response_model=List[QuizQuestionOut])
def get_quiz_questions(
    level: str = Query(..., description="Beginner | Intermediate | Advanced | Professional"),
    count: int = Query(DEFAULT_QUESTION_COUNT, ge=1, le=MAX_QUESTION_COUNT),
    current_user=Depends(get_current_user),
):
    if level not in LEARNING_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid level. Choose one of: {', '.join(LEARNING_LEVELS)}")
    questions = db.list_quiz_questions_for_taking(level, limit=count)
    if not questions:
        raise HTTPException(status_code=404, detail=f"No quiz questions available for {level} yet.")
    return questions


@router.post("/submit")
def submit_quiz(payload: QuizSubmitRequest, current_user=Depends(get_current_user)):
    if payload.level not in LEARNING_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid level. Choose one of: {', '.join(LEARNING_LEVELS)}")
    if not payload.answers:
        raise HTTPException(status_code=400, detail="Submit at least one answer.")

    question_ids = [a.question_id for a in payload.answers]
    questions_by_id = {q["id"]: q for q in db.get_quiz_questions_by_ids(question_ids)}

    results = []
    score = 0
    for answer in payload.answers:
        question = questions_by_id.get(answer.question_id)
        if not question:
            continue  # ignore a stale/unknown question id rather than fail the whole submission
        is_correct = answer.selected_option == question["correct_option"]
        if is_correct:
            score += 1
        results.append(
            {
                "question_id": question["id"],
                "question_text": question["question_text"],
                "your_answer": answer.selected_option,
                "correct_option": question["correct_option"],
                "correct": is_correct,
                "explanation": question["explanation"],
            }
        )

    total = len(results)
    attempt = db.create_quiz_attempt(current_user["id"], payload.level, score, total)
    return {
        "attempt_id": attempt["id"],
        "level": payload.level,
        "score": score,
        "total": total,
        "percent": round((score / total) * 100, 1) if total else 0.0,
        "results": results,
    }


@router.get("/my-attempts")
def my_quiz_attempts(current_user=Depends(get_current_user)):
    return db.get_quiz_attempts(current_user["id"])
