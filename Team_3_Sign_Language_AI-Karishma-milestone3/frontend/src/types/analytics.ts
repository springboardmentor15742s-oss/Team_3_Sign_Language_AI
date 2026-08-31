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
//
// topic/topic_type cover every practicable thing on the platform, not just
// letters — a recommendation can point at a static-alphabet letter or a
// motion sign (Wave/Clap), and topic_type is what a consumer uses to route
// to the right practice page (/practice?letter=X vs /motion-signs?sign=X).

export type TopicType = 'letter' | 'motion_sign';

export interface RecommendationItem {
  topic: string;
  topic_type: TopicType;
  reason: string;
}

export interface Recommendations {
  learner_id: string;
  recommendations: RecommendationItem[];
}

export type LearningLevel = 'beginner' | 'intermediate' | 'advanced';
export type ActivityType = 'lesson' | 'exercise' | 'quiz' | 'practice' | 'revision' | 'challenge';

export interface AdaptiveActivity {
  type: ActivityType;
  difficulty: LearningLevel;
  topic: string;
  instruction: string;
}

export interface AdaptiveRecommendation {
  topic: string;
  topic_type: TopicType;
  priority: number;
  reason: string;
  activities: AdaptiveActivity[];
}

export interface TopicProgress {
  topic: string;
  topic_type: TopicType;
  accuracy_percent: number | null;
  scored_attempts: number;
  trend: string;
}

export interface AdaptiveLearningPlan {
  learner_id: string;
  learning_level: LearningLevel;
  profile_summary: string;
  overall_accuracy_percent: number | null;
  activity_days: number;
  time_spent_minutes: number;
  completed_topics: string[];
  strong_topics: TopicProgress[];
  weak_topics: TopicProgress[];
  needs_more_practice: TopicProgress[];
  recommendations: AdaptiveRecommendation[];
  next_assessment: string;
}

// Mirrors backend/app/schemas/confusion.py

export interface ConfusionPair {
  target_letter: string;
  predicted_letter: string;
  count: number;
}

// Mirrors backend/app/schemas/feedback.py — Task 1, the AI-based feedback
// engine: errors, performance, and areas for improvement, tiered by the
// learner's current skill level.

export interface ActivityFeedback {
  topic: string;
  topic_type: TopicType;
  status: 'pass' | 'fail' | 'no_attempt_detected';
  learner_level: LearningLevel;
  message: string;
  performance: string;
  error: string | null;
  improvement_tip: string | null;
}

export interface FeedbackErrorItem {
  topic: string;
  topic_type: TopicType;
  accuracy_percent: number | null;
  scored_attempts: number | null;
  detail: string;
}

export interface FeedbackPerformance {
  learning_level: LearningLevel;
  overall_accuracy_percent: number | null;
  scored_attempts: number;
  summary: string;
}

export interface FeedbackImprovementArea {
  topic: string;
  topic_type: TopicType;
  accuracy_percent: number | null;
  suggested_activities: AdaptiveActivity[];
}

export interface LearnerFeedback {
  learner_id: string;
  learner_level: LearningLevel;
  generated_from_attempts: number;
  errors: FeedbackErrorItem[];
  performance: FeedbackPerformance;
  areas_for_improvement: FeedbackImprovementArea[];
}

// Mirrors backend/app/schemas/learning_analytics_workflow.py — Task 2, the
// learning analytics workflow: completion rate, activity frequency
// patterns, commonly-missed/avoided topics, and a current-vs-previous
// performance comparison.

export interface CourseCompletion {
  course_id: string;
  title: string;
  attempted_count: number | null;
  total_count: number | null;
  completion_percent: number | null;
}

export interface CompletionRate {
  overall_percent: number | null;
  attempted_count: number;
  total_count: number;
  by_course: CourseCompletion[];
}

export interface FrequencyPatterns {
  days_active_total: number;
  days_active_last_7: number;
  days_active_last_30: number;
  avg_attempts_per_active_day: number | null;
  last_active_date: string | null;
  days_since_last_active: number | null;
  most_active_weekday: string | null;
}

export interface CommonlyMissedItem {
  topic: string;
  topic_type: TopicType;
  incorrect_count: number;
  accuracy_percent: number | null;
}

export interface AvoidedTopicItem {
  topic: string;
  topic_type: TopicType;
}

export interface PerformanceWindow {
  attempts: number;
  scored_attempts: number;
  accuracy_percent: number | null;
}

export interface PerformanceComparison {
  available: boolean;
  reason: string | null;
  current_period: PerformanceWindow;
  previous_period: PerformanceWindow;
  accuracy_delta_percent: number | null;
  trend: 'improving' | 'steady' | 'declining' | null;
}

export interface LearningAnalyticsWorkflow {
  learner_id: string;
  collected_data_summary: {
    total_letter_attempts: number;
    total_motion_attempts: number;
    total_scored_attempts: number;
  };
  performance_metrics: {
    overall_accuracy_percent: number | null;
    letter_accuracy_percent: number | null;
    motion_sign_accuracy_percent: number | null;
  };
  completion_rate: CompletionRate;
  frequency_patterns: FrequencyPatterns;
  commonly_missed: CommonlyMissedItem[];
  avoided_topics: AvoidedTopicItem[];
  performance_comparison: PerformanceComparison;
}

// Mirrors backend/app/schemas/learning_plan.py — the personalized
// learning path built directly from the current recommendation queue
// (learning_plan_service.generate_learning_plan calls get_recommendations
// internally), distinct from AdaptiveLearningPlan above: this one
// sequences an actual letter-by-letter practice session with per-letter
// attempt targets, plus a data-grounded motivational note. Milestone 3
// integration: this was previously generated by the backend but never
// consumed by the frontend — LearningPlanPanel is what displays it.

export interface PlanAreaStat {
  letter: string;
  accuracy_percent: number;
  scored_attempts: number;
}

export interface PlanSummary {
  overall_accuracy_percent: number | null;
  total_attempts: number;
  scored_attempts: number;
  strongest_area: PlanAreaStat | null;
  weakest_area: PlanAreaStat | null;
}

export interface PracticeSessionLetter {
  order: number;
  letter: string;
  reason: string;
  target_attempts: number;
}

export interface PracticeSession {
  attempts_per_letter: number;
  estimated_total_attempts: number;
  letters: PracticeSessionLetter[];
}

export interface LearningPlan {
  learner_id: string;
  summary: PlanSummary;
  practice_session: PracticeSession;
  motivational_note: string;
}
