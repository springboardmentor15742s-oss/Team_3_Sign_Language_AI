// Mirrors backend/app/schemas/motion_signs.py

export type MotionAssessmentStatus = 'pass' | 'fail' | 'no_attempt_detected';

export interface SupportedMotionSigns {
  signs: string[];
}

export interface MotionSignFeedback {
  // Null when status is no_attempt_detected — that outcome isn't logged
  // as a MotionSignAttempt, same convention as PracticeFeedback.
  attempt_id: string | null;
  status: MotionAssessmentStatus;
  correct: boolean | null;
  target_sign: string;
  predicted_sign: string | null;
  feedback: string;
  created_at: string | null;
}
