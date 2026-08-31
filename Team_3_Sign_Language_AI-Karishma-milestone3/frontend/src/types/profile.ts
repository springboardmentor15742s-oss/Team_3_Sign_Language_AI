// Mirrors backend/app/schemas/learner_profile.py

export interface LearnerProfile {
  id: string;
  user_id: string;
  learning_level: string;
  preferred_language: string;
  learning_goals: string | null;
}

export interface LearnerProfileUpdate {
  learning_level?: string;
  preferred_language?: string;
  learning_goals?: string;
}
