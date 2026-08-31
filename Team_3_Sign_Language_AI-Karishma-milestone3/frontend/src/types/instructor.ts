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
