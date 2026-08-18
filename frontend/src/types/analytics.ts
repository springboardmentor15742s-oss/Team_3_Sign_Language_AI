// Mirrors backend/app/schemas/analytics.py

export interface LetterStats {
  attempts: number;
  correct: number;
  incorrect: number;
  no_attempt: number;
  accuracy_percent: number | null;
}

export interface AccuracyTrendPoint {
  date: string;
  attempts: number;
  scored_attempts: number;
  correct: number;
  accuracy_percent: number | null;
}

export interface LetterCount {
  letter: string;
  attempts: number;
}

export interface WeakArea {
  letter: string;
  accuracy_percent: number;
  scored_attempts: number;
}

export interface LearnerAnalytics {
  learner_id: string;
  total_attempts: number;
  correct_count: number;
  incorrect_count: number;
  no_attempt_count: number;
  scored_attempts: number;
  overall_accuracy_percent: number | null;
  accuracy_trend: AccuracyTrendPoint[];
  per_letter: Record<string, LetterStats>;
  most_practiced_letters: LetterCount[];
  least_practiced_letters: LetterCount[];
  weak_areas: WeakArea[];
}

// Mirrors backend/app/schemas/recommendation.py

export interface RecommendationItem {
  letter: string;
  reason: string;
}

export interface Recommendations {
  learner_id: string;
  recommendations: RecommendationItem[];
}

// Mirrors backend/app/schemas/confusion.py

export interface ConfusionPair {
  target_letter: string;
  predicted_letter: string;
  count: number;
}
