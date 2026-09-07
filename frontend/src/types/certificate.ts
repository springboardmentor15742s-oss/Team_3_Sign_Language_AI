// Mirrors backend/app/schemas/certificate.py

export interface Certificate {
  id: string;
  learner_id: string;
  course_id: string;
  course_title: string;
  verification_code: string;
  issued_at: string;
  issued_by: string;
  issued_by_name: string;
  revoked: boolean;
  revoked_at: string | null;
  revoked_reason: string | null;
}

export interface CertificateListResponse {
  certificates: Certificate[];
}

export interface CourseCertificationStatus {
  course_id: string;
  course_title: string;
  items_total: number;
  items_passed: number;
  eligible: boolean;
  already_issued: boolean;
  certificate_id: string | null;
}

export interface CertificationStatusResponse {
  courses: CourseCertificationStatus[];
}

export interface CertificateVerificationResponse {
  valid: boolean;
  learner_name: string | null;
  course_title: string | null;
  issued_at: string | null;
  revoked: boolean;
  revoked_at: string | null;
}
