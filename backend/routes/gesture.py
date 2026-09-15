"""
Gesture Recognition, Hand Tracking & Accuracy Assessment routes — Milestone 2.
"""
import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from database import db
from deps import get_current_user
from gesture.accuracy import assess_gesture
from gesture.classifier import classify_by_fingerstate, get_finger_states
from gesture.landmarks import HAND_CONNECTIONS, detect_hand
from gesture.reference_signs import GESTURE_LIBRARY, list_library

router = APIRouter(prefix="/api/gesture", tags=["gesture"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB


async def _read_image(file: UploadFile) -> bytes:
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Please upload a JPEG, PNG, or WEBP image.")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB).")
    return data


@router.get("/library")
def get_library():
    """Reference gesture library — used by the frontend to show 'how to sign X'."""
    return list_library()

# Connection pairs so the frontend can draw the hand skeleton over the landmarks.
@router.get("/hand-connections")
def get_hand_connections():
    return HAND_CONNECTIONS


@router.post("/detect")
async def detect(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    """
    Hand & Pose Tracking + Gesture Recognition Engine.
    Runs MediaPipe hand-landmark detection on the uploaded frame, then
    classifies the hand shape against the reference gesture library.
    """
    image_bytes = await _read_image(file)
    hand = detect_hand(image_bytes)

    if hand is None:
        return {
            "hand_detected": False,
            "landmarks": None,
            "handedness": None,
            "handedness_confidence": None,
            "predicted_label": None,
            "predicted_display_name": None,
            "confidence": None,
        }

    finger_state = get_finger_states(hand["landmarks"])
    predicted_label, confidence, _scores = classify_by_fingerstate(finger_state)

    return {
        "hand_detected": True,
        "landmarks": hand["landmarks"],
        "handedness": hand["handedness"],
        "handedness_confidence": round(hand["handedness_confidence"], 3),
        "predicted_label": predicted_label,
        "predicted_display_name": GESTURE_LIBRARY[predicted_label]["display_name"] if predicted_label else None,
        "confidence": round(confidence, 3),
    }


@router.post("/assess")
async def assess(
    file: UploadFile = File(...),
    target_label: str = Query(..., description="Key from /api/gesture/library, e.g. 'OPEN_PALM'"),
    current_user=Depends(get_current_user),
):
    """
    Sign Accuracy Assessment Engine.
    Compares the uploaded frame's hand shape against `target_label` and
    returns a scored, per-finger breakdown + corrective feedback. Also logs
    the attempt (Assessment & Certification / Performance Scoring data).
    """
    if target_label not in GESTURE_LIBRARY:
        raise HTTPException(status_code=400, detail=f"Unknown target gesture: {target_label}")

    image_bytes = await _read_image(file)
    hand = detect_hand(image_bytes)
    target_display_name = GESTURE_LIBRARY[target_label]["display_name"]

    if hand is None:
        return {
            "hand_detected": False,
            "target_label": target_label,
            "target_display_name": target_display_name,
            "feedback": ["No hand detected — make sure your hand is clearly visible and well-lit."],
        }

    result = assess_gesture(hand["landmarks"], target_label, hand["handedness_confidence"])
    finger_state = get_finger_states(hand["landmarks"])
    detected_label, _conf, _scores = classify_by_fingerstate(finger_state)

    db.log_gesture_attempt(
        user_id=current_user["id"],
        target_label=target_label,
        detected_label=detected_label,
        matched=result["matched"],
        hand_shape_accuracy=result["hand_shape_accuracy"],
        position_accuracy=result["position_accuracy"],
        overall_accuracy=result["overall_accuracy"],
        feedback_json=json.dumps(result["feedback"]),
    )
    db.log_practice_activity(
        current_user["id"],
        f"Practiced '{target_display_name}' — {result['overall_accuracy']}% accuracy"
        f"{' ✅' if result['matched'] else ''}",
    )

    return {
        "hand_detected": True,
        "target_label": target_label,
        "target_display_name": target_display_name,
        "landmarks": hand["landmarks"],
        **result,
    }


@router.get("/history")
def history(limit: int = 20, current_user=Depends(get_current_user)):
    rows = db.get_gesture_history(current_user["id"], limit=limit)
    for r in rows:
        r["feedback"] = json.loads(r["feedback"]) if r.get("feedback") else []
        r["target_display_name"] = GESTURE_LIBRARY.get(r["target_label"], {}).get("display_name", r["target_label"])
    return rows


@router.get("/stats")
def stats(current_user=Depends(get_current_user)):
    result = db.get_gesture_stats(current_user["id"])
    for row in result["by_gesture"]:
        row["display_name"] = GESTURE_LIBRARY.get(row["target_label"], {}).get("display_name", row["target_label"])
        row["avg_accuracy"] = round(row["avg_accuracy"], 1)
    return result
