// Mirrors backend/app/schemas/reporting.py

export type ReportScope = 'roster' | 'platform';

export interface ClassReportRosterEntry {
  learner_id: string;
  name: string;
  email: string;
  total_attempts: number;
  overall_accuracy_percent: number | null;
}

export interface AssignmentReportRow {
  learner_id: string;
  learner_name: string;
  learner_email: string;
  topic: string;
  topic_type: string;
  notes: string | null;
  due_date: string | null;
  completed: boolean;
  completed_at: string | null;
  overdue: boolean;
  created_at: string;
}

export interface AssignmentReportResponse {
  scope: ReportScope;
  generated_at: string;
  total_count: number;
  completed_count: number;
  outstanding_count: number;
  overdue_count: number;
  rows: AssignmentReportRow[];
}
