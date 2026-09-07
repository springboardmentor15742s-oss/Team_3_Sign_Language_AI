// Mirrors backend/app/schemas/practice.py

export type AssessmentStatus = 'pass' | 'fail' | 'no_attempt_detected';

export interface HandLandmarkPoint {
  x: number;
  y: number;
  z: number;
}

export interface SupportedLettersResponse {
  letters: string[];
}

// Response of the non-scoring POST /api/practice/recognize — what Live
// mode polls repeatedly. See PracticeFeedback below for the real, graded
// attempt shape this deliberately does NOT include (no attempt_id,
// feedback text, or created_at — this never becomes a logged attempt).
export interface PracticeRecognizeResult {
  detected: boolean;
  predicted_letter: string | null;
  confidence: number | null;
  landmarks: HandLandmarkPoint[] | null;
}

export interface PracticeFeedback {
  // Null when status is no_attempt_detected — that outcome isn't logged.
  attempt_id: string | null;
  status: AssessmentStatus;
  correct: boolean | null;
  confidence: number | null;
  target_letter: string;
  predicted_letter: string | null;
  feedback: string;
  created_at: string | null;
  // Null whenever no hand was detected, same as predicted_letter.
  landmarks: HandLandmarkPoint[] | null;
}
