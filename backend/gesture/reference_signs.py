"""
Reference sign/gesture library — Milestone 2.

Milestone 1's Dataset Explorer integrated the ASL Alphabet / Sign-MNIST /
WLASL datasets for *future* CNN/LSTM model training (per the tech stack:
TensorFlow, PyTorch, CNN, LSTM, Transformer models). Training an accurate
full-alphabet classifier needs that real dataset + a GPU training run, which
is out of scope for this offline Milestone-2 slice.

Instead, this milestone ships a genuinely-working **rule-based / geometric**
gesture recognition engine: it reads real hand landmarks from MediaPipe and
classifies based on which fingers are extended vs. curled. This only
reliably distinguishes hand shapes that differ in their finger up/down
pattern, so we use a small set of clearly-distinguishable static gestures
(closely related to common ASL handshapes) rather than the full 26-letter
alphabet, which contains several letters (e.g. C vs E vs O) that a
finger-up/down heuristic cannot reliably tell apart.

Upgrade path (Milestone 3+): swap `classify_by_fingerstate()` in
classifier.py for a trained CNN (image-based) or landmark-sequence
LSTM/Transformer model using the datasets already wired up in Milestone 1,
without changing the API contract below.
"""

# Each pattern is [thumb, index, middle, ring, pinky] where 1 = extended, 0 = curled.
#
# Coverage note: this heuristic can only tell fingers apart by
# extended-vs-curled, not by curl *degree*, finger crossing, or hand
# rotation. That means a true, unique static ASL handshape exists for every
# entry below, but several real ASL letters are NOT included because they
# are not distinguishable this way even in principle:
#   - C / O / E differ from a fist (and each other) only by *how much* the
#     fingers are curled, not whether they're curled — indistinguishable here.
#   - U / V / H / K differ from each other by finger *spread/orientation*
#     at the same extension pattern — this heuristic can't measure that.
#   - M / N / T / S differ from a fist only by thumb *position between*
#     specific fingers, not extension — indistinguishable from FIST here.
#   - R (crossed fingers), X (hooked index) — need curl/cross detection,
#     not just extension.
#   - J and Z are motion signs (drawn in the air) — impossible to represent
#     as a single static frame at all.
# Where two real signs share an identical extension pattern (e.g. "3" vs
# "K", or "V" already covering "U"/"H" in spirit), the entry documents both
# rather than silently picking one. This is exactly the limitation flagged
# in the module docstring above, and the reason Milestone 3+'s upgrade path
# is a trained CNN/LSTM model over the full alphabet datasets already wired
# up in Milestone 1.
GESTURE_LIBRARY = {
    "OPEN_PALM": {
        "display_name": "Open Palm",
        "related_sign": "ASL 'B' / Number 5",
        "pattern": [1, 1, 1, 1, 1],
        "description": "All five fingers extended and spread, palm facing the camera.",
    },
    "FIST": {
        "display_name": "Closed Fist",
        "related_sign": "ASL 'A' / ASL 'S'",
        "pattern": [0, 0, 0, 0, 0],
        "description": "All fingers curled into the palm, thumb resting alongside.",
    },
    "POINTING": {
        "display_name": "Pointing (Index Up)",
        "related_sign": "ASL 'D' / Number 1",
        "pattern": [0, 1, 0, 0, 0],
        "description": "Only the index finger extended upward; other fingers curled.",
    },
    "PEACE": {
        "display_name": "Peace / Victory Sign",
        "related_sign": "ASL 'V' / Number 2",
        "pattern": [0, 1, 1, 0, 0],
        "description": "Index and middle fingers extended in a V shape; others curled.",
    },
    "THUMBS_UP": {
        "display_name": "Thumbs Up",
        "related_sign": "ASL 'A' variant (approval sign)",
        "pattern": [1, 0, 0, 0, 0],
        "description": "Only the thumb extended upward; all other fingers curled into a fist.",
    },
    "LETTER_L": {
        "display_name": "Letter L",
        "related_sign": "ASL 'L'",
        "pattern": [1, 1, 0, 0, 0],
        "description": "Thumb and index finger extended to form an L shape; other fingers curled.",
    },
    "LETTER_Y": {
        "display_name": "Letter Y",
        "related_sign": "ASL 'Y'",
        "pattern": [1, 0, 0, 0, 1],
        "description": "Thumb and pinky extended outward ('hang loose'); other fingers curled.",
    },
    "LETTER_I": {
        "display_name": "Letter I",
        "related_sign": "ASL 'I'",
        "pattern": [0, 0, 0, 0, 1],
        "description": "Only the pinky finger extended upward; other fingers curled.",
    },
    "LETTER_W": {
        "display_name": "Letter W",
        "related_sign": "ASL 'W'",
        "pattern": [0, 1, 1, 1, 0],
        "description": "Index, middle, and ring fingers extended and spread; thumb and pinky curled together.",
    },
    "LETTER_F": {
        "display_name": "Letter F (approx.)",
        "related_sign": "ASL 'F'",
        "pattern": [0, 0, 1, 1, 1],
        "description": "Middle, ring, and pinky extended; thumb and index curled together (approximates the F pinch).",
    },
    "THREE_K": {
        "display_name": "Number Three",
        "related_sign": "Number '3' / ASL 'K'",
        "pattern": [1, 1, 1, 0, 0],
        "description": "Thumb, index, and middle fingers extended; ring and pinky curled.",
    },
    "FOUR": {
        "display_name": "Number Four",
        "related_sign": "Number '4'",
        "pattern": [0, 1, 1, 1, 1],
        "description": "Four fingers extended and spread, thumb curled across the palm.",
    },
    "ILY": {
        "display_name": "I Love You",
        "related_sign": "ASL 'ILY' handshape",
        "pattern": [1, 1, 0, 0, 1],
        "description": "Thumb, index, and pinky extended (middle and ring curled) — the well-known ASL 'I Love You' sign.",
    },
}

FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]


def get_reference(label: str) -> dict:
    return GESTURE_LIBRARY.get(label)


def list_library() -> list:
    return [
        {"key": key, **{k: v for k, v in info.items()}}
        for key, info in GESTURE_LIBRARY.items()
    ]
