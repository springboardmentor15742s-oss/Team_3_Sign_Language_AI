// Mirrors backend/app/schemas/instructor.py

export interface LearnerRosterEntry {
  learner_id: string;
  name: string;
  email: string;
  total_attempts: number;
  overall_accuracy_percent: number | null;
  letters_scored: number;
  total_letters: number;
  weak_area_count: number;
}

export interface LearnerRosterResponse {
  learners: LearnerRosterEntry[];
}

export interface WeakLetterCount {
  letter: string;
  learner_count: number;
}

export interface ClassAnalytics {
  learner_count: number;
  active_learner_count: number;
  average_accuracy_percent: number | null;
  weak_letter_distribution: WeakLetterCount[];
  outstanding_assignment_count: number;
  completed_assignment_count: number;
}
