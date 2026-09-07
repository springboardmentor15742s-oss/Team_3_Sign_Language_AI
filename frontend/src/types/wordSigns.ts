// Mirrors backend/app/schemas/word_signs.py

export type WordAssessmentStatus = 'pass' | 'fail' | 'no_attempt_detected';

export interface SupportedWordSigns {
  words: string[];
  // The trained classifier's own measured test accuracy, as a 0-1
  // fraction straight from sklearn's accuracy_score (NOT 0-100 — scale
  // by 100 when displaying a percentage). Shown to the learner so this
  // isn't presented as more reliable than the alphabet classifier. Null
  // only if the model bundle is missing it.
  model_test_accuracy: number | null;
  // word -> reference photo URL (relative, e.g. "/media/word-signs/think.jpg"),
  // for words that have a generated reference image. See
  // word_sign_service.get_reference_image_urls.
  reference_images: Record<string, string>;
}

// Response of the non-scoring POST /api/word-signs/recognize — what Live
// mode polls repeatedly with short rolling windows of frames. word is null
// either when no pose was tracked (detected=false) or when a pose was
// tracked but the classifier didn't land on one of the supported words
// with enough confidence (detected=true, word=null).
export interface WordSignRecognizeResult {
  detected: boolean;
  word: string | null;
  confidence: number | null;
  frame_count: number;
}

export interface WordSignFeedback {
  // Null when status is no_attempt_detected — that outcome isn't logged
  // as a WordSignAttempt, same convention as MotionSignFeedback.
  attempt_id: string | null;
  status: WordAssessmentStatus;
  correct: boolean | null;
  target_sign: string;
  predicted_sign: string | null;
  confidence: number | null;
  feedback: string;
  learner_level: string | null;
  error: string | null;
  improvement_tip: string | null;
  created_at: string | null;
}
