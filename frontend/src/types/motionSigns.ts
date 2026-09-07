// Mirrors backend/app/schemas/motion_signs.py

export type MotionAssessmentStatus = 'pass' | 'fail' | 'no_attempt_detected';

export interface SupportedMotionSigns {
  signs: string[];
}

// Response of the non-scoring POST /api/motion-signs/recognize — what Live
// mode polls repeatedly with short rolling windows of frames. sign is null
// either when no hand was tracked (detected=false) or when motion was
// tracked but didn't match Wave/Clap (detected=true, sign=null) — the UI
// distinguishes those two cases.
export interface MotionSignRecognizeResult {
  detected: boolean;
  sign: string | null;
  frame_count: number;
  hands_detected_frames: number | null;
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
