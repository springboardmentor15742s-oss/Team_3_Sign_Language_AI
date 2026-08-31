// Mirrors backend/app/schemas/history.py — the raw, session-by-session
// practice log behind the Practice History page, distinct from
// LearnerAnalytics' aggregated per-letter/per-day view.

import { TopicType } from './analytics';

export type PracticeStatus = 'pass' | 'fail' | 'no_attempt_detected';

export interface HistoryEntry {
  id: string;
  topic: string;
  topic_type: TopicType;
  status: PracticeStatus;
  correct: boolean | null;
  confidence: number | null;
  created_at: string | null;
}

export interface PracticeHistory {
  learner_id: string;
  total_sessions: number;
  scored_sessions: number;
  accuracy_percent: number | null;
  entries: HistoryEntry[];
}
