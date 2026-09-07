// Mirrors backend/app/schemas/class_trends.py

export interface RosterAccuracyTrendPoint {
  date: string;
  attempts: number;
  scored_attempts: number;
  accuracy_percent: number | null;
}

export interface RosterCourseCompletion {
  course_id: string;
  course_title: string;
  learner_count: number;
  not_started_count: number;
  in_progress_count: number;
  completed_count: number;
  certified_count: number | null;
}

export interface ClassTrendsResponse {
  accuracy_trend: RosterAccuracyTrendPoint[];
  course_completion: RosterCourseCompletion[];
}
