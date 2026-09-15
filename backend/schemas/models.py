"""Pydantic models used for request validation and response shaping."""
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth ------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str
    is_active: int


# --- Learner profile --------------------------------------------------------
class ProfileUpsertRequest(BaseModel):
    learning_level: str
    preferred_language: str
    learning_goals: List[str] = []
    bio: Optional[str] = ""


class ProfileOut(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    avatar_data: Optional[str] = None
    learning_level: str
    preferred_language: str
    learning_goals: List[str]
    bio: Optional[str] = ""
    updated_at: str


class ProfileIdentityRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=60)
    avatar_data: Optional[str] = None  # base64 data: URL, resized client-side


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


# --- Admin -------------------------------------------------------------------
class RoleUpdateRequest(BaseModel):
    role: str


class ActiveUpdateRequest(BaseModel):
    is_active: bool


class LevelUpdateRequest(BaseModel):
    level: str  # Beginner | Intermediate | Advanced | Professional


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., max_length=120)
    message: str = Field(..., max_length=500)


class CertificateStatusUpdateRequest(BaseModel):
    status: str  # 'Active' | 'Revoked'


# --- Quiz / Knowledge-Check module ------------------------------------------
class QuizQuestionOut(BaseModel):
    id: int
    level: str
    topic: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class QuizAnswerIn(BaseModel):
    question_id: int
    selected_option: str  # 'a' | 'b' | 'c' | 'd'


class QuizSubmitRequest(BaseModel):
    level: str
    answers: List[QuizAnswerIn]


# --- Gesture recognition & assessment (Milestone 2) -------------------------
class LandmarkPoint(BaseModel):
    x: float
    y: float
    z: float


class DetectResponse(BaseModel):
    hand_detected: bool
    landmarks: Optional[List[LandmarkPoint]] = None
    handedness: Optional[str] = None
    handedness_confidence: Optional[float] = None
    predicted_label: Optional[str] = None
    predicted_display_name: Optional[str] = None
    confidence: Optional[float] = None


class FingerStateOut(BaseModel):
    finger: str
    extended: bool


class FingerBreakdownOut(BaseModel):
    finger: str
    expected: bool
    actual: bool
    correct: bool


class AssessResponse(BaseModel):
    hand_detected: bool
    target_label: str
    target_display_name: str
    detected_finger_state: Optional[List[FingerStateOut]] = None
    expected_finger_state: Optional[List[FingerStateOut]] = None
    hand_shape_accuracy: Optional[float] = None
    position_accuracy: Optional[float] = None
    overall_accuracy: Optional[float] = None
    matched: Optional[bool] = None
    feedback: List[str] = []
    finger_breakdown: Optional[List[FingerBreakdownOut]] = None
    landmarks: Optional[List[LandmarkPoint]] = None


TokenResponse.model_rebuild()


# --- Course & Content Service --------------------------------------------
class LessonOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: str
    video_id: str
    duration_seconds: int
    sort_order: int
    watched: bool = False


class CourseOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    level: str
    thumbnail_emoji: str
    created_by: Optional[int] = None
    created_at: str
    lesson_count: int = 0


class CourseDetailOut(CourseOut):
    lessons: List[LessonOut] = []
    is_enrolled: bool = False
    progress_percent: float = 0.0
    watched_lessons: int = 0


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field("", max_length=2000)
    category: str
    level: str
    thumbnail_emoji: Optional[str] = "🤟"


class LessonCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field("", max_length=2000)
    video_id: str = Field(..., min_length=5, max_length=32)
    duration_seconds: int = Field(300, ge=0, le=36000)


class EnrollmentOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    level: str
    thumbnail_emoji: str
    enrolled_at: str
    lesson_count: int
    watched_count: int


class CourseProgressOut(BaseModel):
    course_id: int
    total_lessons: int
    watched_lessons: int
    percent: float
