import React, { useCallback, useState } from 'react';
import client from '../api/client';
import { Certificate, CourseCertificationStatus } from '../types/certificate';
import './Panel.css';
import './CertificatesPanel.css';

interface CertificatesPanelProps {
  learnerId: string;
  certificates: Certificate[];
  status: CourseCertificationStatus[];
  // Staff (instructor/admin) get manual issue + revoke controls; a
  // learner viewing their own certificates on Dashboard.tsx only gets
  // the earned list, the in-progress bars, and downloads — never a way
  // to certify or revoke themselves.
  isStaff?: boolean;
  onIssue?: (courseId: string) => Promise<void>;
  onRevoke?: (certificateId: string) => Promise<void>;
}

// Certification workflow's learner-facing (and, with isStaff, instructor/
// admin-facing) panel — earned certificates with PDF download + a
// verification code, plus honest in-progress bars for every certifiable
// course not yet earned (same "show real progress, never hide it"
// discipline as AchievementsPanel). Data is fetched by the parent
// (Dashboard.tsx / InstructorLearnerDetail.tsx), same convention as
// ClassOverviewPanel/AssignmentReportPanel — this component owns only
// its own per-certificate PDF download and, for staff, the issue/revoke
// actions via the callback props above.
export function CertificatesPanel({ learnerId, certificates, status, isStaff = false, onIssue, onRevoke }: CertificatesPanelProps) {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [issuingCourseId, setIssuingCourseId] = useState<string | null>(null);
  const [issueError, setIssueError] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const handleDownload = useCallback(async (certificate: Certificate) => {
    setDownloadingId(certificate.id);
    setDownloadError(null);
    try {
      const response = await client.get(
        `/api/certificates/learner/${learnerId}/${certificate.id}/pdf`,
        { responseType: 'blob' }
      );
      const disposition = response.headers['content-disposition'] as string | undefined;
      const filename = disposition?.match(/filename="?([^"]+)"?/)?.[1] ?? 'certificate.pdf';

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download certificate:', err);
      setDownloadError('Could not download this certificate.');
    } finally {
      setDownloadingId(null);
    }
  }, [learnerId]);

  const handleIssue = useCallback(async (courseId: string) => {
    if (!onIssue) return;
    setIssuingCourseId(courseId);
    setIssueError(null);
    try {
      await onIssue(courseId);
    } catch (err) {
      console.error('Failed to issue certificate:', err);
      setIssueError('Could not issue this certificate.');
    } finally {
      setIssuingCourseId(null);
    }
  }, [onIssue]);

  const handleRevoke = useCallback(async (certificateId: string) => {
    if (!onRevoke) return;
    if (!window.confirm('Revoke this certificate? This keeps a record but marks it invalid.')) return;
    setRevokingId(certificateId);
    try {
      await onRevoke(certificateId);
    } catch (err) {
      console.error('Failed to revoke certificate:', err);
    } finally {
      setRevokingId(null);
    }
  }, [onRevoke]);

  const inProgress = status.filter((s) => !s.already_issued);
  const activeCertificates = certificates.filter((c) => !c.revoked);
  const revokedCertificates = certificates.filter((c) => c.revoked);

  return (
    <div className="panel certificates-panel">
      <h2 className="panel__title">Certificates</h2>

      {activeCertificates.length === 0 ? (
        <p className="panel__empty">No certificates earned yet.</p>
      ) : (
        <ul className="certificate-list">
          {activeCertificates.map((certificate) => (
            <li key={certificate.id} className="certificate-list__item">
              <div className="certificate-list__body">
                <span className="certificate-list__title">{certificate.course_title}</span>
                <span className="certificate-list__meta">
                  Issued {new Date(certificate.issued_at).toLocaleDateString()} &middot; {certificate.issued_by_name}
                </span>
                <span className="certificate-list__code">Code: {certificate.verification_code}</span>
              </div>
              <div className="certificate-list__actions">
                <button
                  type="button"
                  className="btn btn--ghost certificates-panel__download-btn"
                  onClick={() => handleDownload(certificate)}
                  disabled={downloadingId === certificate.id}
                >
                  {downloadingId === certificate.id ? 'Generating…' : 'Download PDF'}
                </button>
                {isStaff && onRevoke && (
                  <button
                    type="button"
                    className="certificates-panel__revoke-btn"
                    onClick={() => handleRevoke(certificate.id)}
                    disabled={revokingId === certificate.id}
                  >
                    {revokingId === certificate.id ? '…' : 'Revoke'}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {downloadError && <p className="status-message status-message--error">{downloadError}</p>}

      {revokedCertificates.length > 0 && (
        <div className="certificates-panel__revoked">
          <h3 className="certificates-panel__subtitle">Revoked</h3>
          <ul className="certificate-list certificate-list--revoked">
            {revokedCertificates.map((certificate) => (
              <li key={certificate.id} className="certificate-list__item certificate-list__item--revoked">
                <div className="certificate-list__body">
                  <span className="certificate-list__title">{certificate.course_title}</span>
                  <span className="certificate-list__meta">
                    {certificate.revoked_reason ?? 'Revoked'}
                    {certificate.revoked_at ? ` · ${new Date(certificate.revoked_at).toLocaleDateString()}` : ''}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {inProgress.length > 0 && (
        <div className="certificates-panel__progress">
          <h3 className="certificates-panel__subtitle">In progress</h3>
          <ul className="certificates-panel__progress-list">
            {inProgress.map((course) => {
              const percent = course.items_total > 0 ? Math.round((course.items_passed / course.items_total) * 100) : 0;
              return (
                <li key={course.course_id} className="certificates-panel__progress-item">
                  <div className="certificates-panel__progress-header">
                    <span>{course.course_title}</span>
                    <span className="certificates-panel__progress-count">
                      {course.items_passed}/{course.items_total} passed
                    </span>
                  </div>
                  <div className="certificates-panel__progress-track">
                    <div className="certificates-panel__progress-fill" style={{ width: `${percent}%` }} />
                  </div>
                  {isStaff && onIssue && (
                    <button
                      type="button"
                      className="btn btn--ghost certificates-panel__issue-btn"
                      onClick={() => handleIssue(course.course_id)}
                      disabled={issuingCourseId === course.course_id}
                    >
                      {issuingCourseId === course.course_id
                        ? 'Issuing…'
                        : course.eligible
                        ? 'Issue certificate'
                        : 'Issue anyway'}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
          {issueError && <p className="status-message status-message--error">{issueError}</p>}
        </div>
      )}
    </div>
  );
}
