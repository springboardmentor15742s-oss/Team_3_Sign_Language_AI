// Mirrors backend/app/schemas/admin.py

export interface AdminUserEntry {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
  total_attempts: number | null; // null for non-learner roles, never 0
}

export interface AdminOverviewResponse {
  total_users: number;
  role_counts: Record<string, number>;
  total_practice_attempts: number;
  overall_accuracy_percent: number | null;
  users: AdminUserEntry[];
}
