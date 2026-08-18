// Roles that land on the instructor roster (/instructor) instead of the
// learner dashboard (/dashboard). Matches the backend's
// require_role("instructor", "admin") on GET /api/instructor/learners —
// deliberately excludes accessibility_trainer, which has no defined home
// route yet.
export const INSTRUCTOR_ROLES = ['instructor', 'admin'];
