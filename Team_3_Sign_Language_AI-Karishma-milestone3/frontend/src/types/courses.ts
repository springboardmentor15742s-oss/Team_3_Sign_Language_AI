// Mirrors backend/app/schemas/courses.py

export interface CourseItem {
  id: string;
  title: string;
  category: string;
  description: string;
  route: string | null;
  built: boolean;
  tracks_progress: boolean;
  // Null whenever progress isn't tracked or computable — never a
  // placeholder number for a course that isn't real yet.
  progress_percent: number | null;
  item_count: number | null;
  locked_reason: string | null;
}

export interface CourseCatalog {
  courses: CourseItem[];
}
