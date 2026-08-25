// Mirrors backend/app/schemas/practice.py

export type AssessmentStatus = 'pass' | 'fail' | 'no_attempt_detected';

export interface HandLandmarkPoint {
  x: number;
  y: number;
  z: number;
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
