// Mirrors backend/app/schemas/instructor_assignment.py

export type AssignmentTopicType = 'letter' | 'motion_sign' | 'word_sign';

export type AssignmentMediaType = 'image' | 'video';

export interface Assignment {
  id: string;
  learner_id: string;
  instructor_id: string;
  instructor_name: string | null;
  topic: string;
  topic_type: AssignmentTopicType;
  notes: string | null;
  due_date: string | null; // "YYYY-MM-DD"
  completed: boolean;
  completed_at: string | null;
  // Set only when the instructor attached a reference photo/video —
  // reference_media_url is a ready-to-fetch /media/... path.
  reference_media_url: string | null;
  reference_media_type: AssignmentMediaType | null;
  created_at: string | null;
}

export interface AssignmentListResponse {
  assignments: Assignment[];
}
