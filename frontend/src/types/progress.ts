// Mirrors backend/app/schemas/progress.py

export interface Achievement {
  id: string;
  label: string;
  description: string;
  unlocked: boolean;
  progress_current: number;
  progress_target: number;
}

export interface RecentActivityItem {
  letter: string;
  status: 'pass' | 'fail' | 'no_attempt_detected';
  confidence: number | null;
  created_at: string | null;
}

export interface PerformanceForecast {
  available: boolean;
  // Set only when available is false, explaining what's missing — never
  // paired with fabricated numbers below it.
  reason: string | null;
  current_level: string | null;
  predicted_next_level: string | null;
  trend_percent_per_day: number | null;
  estimated_days_to_next_level: number | null;
}

export interface LearnerProgress {
  learner_id: string;
  current_streak_days: number;
  achievements: Achievement[];
  recent_activity: RecentActivityItem[];
  forecast: PerformanceForecast;
}
