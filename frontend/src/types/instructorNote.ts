// Mirrors backend/app/schemas/instructor_note.py

export interface InstructorNote {
  id: string;
  learner_id: string;
  instructor_id: string;
  instructor_name: string | null;
  note: string;
  created_at: string | null;
}

export interface NoteListResponse {
  notes: InstructorNote[];
}
