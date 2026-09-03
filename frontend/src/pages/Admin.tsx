import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import '../components/DataTable.css';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { StatsRow, StatTile } from '../components/StatsRow';
import { ClassOverviewPanel } from '../components/ClassOverviewPanel';
import { AssignmentReportPanel } from '../components/AssignmentReportPanel';
import { Topbar } from '../components/Topbar';
import { AdminOverviewResponse } from '../types/admin';
import { ClassAnalytics } from '../types/instructor';
import { AssignmentReportResponse } from '../types/reporting';
import './Admin.css';

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString();
}

export function Admin() {
  const [overview, setOverview] = useState<AdminOverviewResponse | null>(null);
  // Both come from /api/instructor/* — admins are allowed on those
  // endpoints too (require_role("instructor", "admin")), and
  // _roster_scope resolves an admin caller to platform-wide (None)
  // automatically, so these are the exact same platform-scoped numbers
  // an instructor sees for their own roster, just for everyone.
  const [classAnalytics, setClassAnalytics] = useState<ClassAnalytics | null>(null);
  const [assignmentReport, setAssignmentReport] = useState<AssignmentReportResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Per-row, same reasoning as Instructor's roster table — several rows
  // could be downloading independently.
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [downloadErrors, setDownloadErrors] = useState<Record<string, string>>({});

  const loadOverview = useCallback(async () => {
    setLoadError(null);
    try {
      const [overviewRes, analyticsRes, assignmentReportRes] = await Promise.all([
        client.get<AdminOverviewResponse>('/api/admin/overview'),
        client.get<ClassAnalytics>('/api/instructor/class-analytics'),
        client.get<AssignmentReportResponse>('/api/instructor/reports/assignments'),
      ]);
      setOverview(overviewRes.data);
      setClassAnalytics(analyticsRes.data);
      setAssignmentReport(assignmentReportRes.data);
    } catch (err) {
      console.error('Failed to load admin overview:', err);
      setLoadError('Could not load the platform overview.');
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  const handleDownloadReport = useCallback(async (userId: string) => {
    setDownloadingIds((current) => new Set(current).add(userId));
    setDownloadErrors((current) => {
      const next = { ...current };
      delete next[userId];
      return next;
    });
    try {
      const response = await client.get(`/api/reports/learner/${userId}/pdf`, { responseType: 'blob' });

      const disposition = response.headers['content-disposition'] as string | undefined;
      const filename = disposition?.match(/filename="?([^"]+)"?/)?.[1] ?? 'progress-report.pdf';

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download report for user', userId, err);
      setDownloadErrors((current) => ({ ...current, [userId]: 'Could not generate this report.' }));
    } finally {
      setDownloadingIds((current) => {
        const next = new Set(current);
        next.delete(userId);
        return next;
      });
    }
  }, []);

  return (
    <div className="page admin">
      <Topbar title="Admin Overview" />

      {loadError && <p className="status-message status-message--error">{loadError}</p>}

      {!loadError && overview === null && (
        <div className="content-loading">
          <p className="status-message">Loading overview&hellip;</p>
        </div>
      )}

      {!loadError && overview !== null && (
        <>
          <StatsRow>
            <StatTile value={<AnimatedNumber value={overview.total_users} />} label="Total users" />
            <StatTile value={<AnimatedNumber value={overview.role_counts.learner ?? 0} />} label="Learners" />
            <StatTile
              value={<AnimatedNumber value={overview.total_practice_attempts} />}
              label="Practice attempts"
            />
            <StatTile
              variant="accent"
              value={
                <>
                  {overview.overall_accuracy_percent !== null ? (
                    <AnimatedNumber
                      value={overview.overall_accuracy_percent}
                      decimals={Number.isInteger(overview.overall_accuracy_percent) ? 0 : 1}
                    />
                  ) : (
                    '—'
                  )}
                  {overview.overall_accuracy_percent !== null && <span className="stat-tile__unit">%</span>}
                </>
              }
              label="Platform accuracy"
            />
          </StatsRow>

          {classAnalytics && <ClassOverviewPanel analytics={classAnalytics} />}
          {assignmentReport && <AssignmentReportPanel report={assignmentReport} />}

          <section className="admin-users">
            {overview.users.length === 0 ? (
              <p className="status-message">No users yet.</p>
            ) : (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Joined</th>
                      <th>Attempts</th>
                      <th>Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.users.map((user) => {
                      const isDownloading = downloadingIds.has(user.id);
                      const downloadError = downloadErrors[user.id];

                      return (
                        <tr key={user.id}>
                          <td>{user.name}</td>
                          <td>{user.email}</td>
                          <td>{user.role}</td>
                          <td className="data-table__numeric">{formatDate(user.created_at)}</td>
                          <td className="data-table__numeric">
                            {user.total_attempts === null ? '—' : user.total_attempts}
                          </td>
                          <td className="data-table__numeric">
                            {/* Only learners have practice history to report on — staff
                                accounts (instructor/admin) have total_attempts=null and
                                no corresponding report to generate. */}
                            {user.role === 'learner' ? (
                              <>
                                <button
                                  type="button"
                                  className="btn btn--ghost admin-users__report-btn"
                                  onClick={() => handleDownloadReport(user.id)}
                                  disabled={isDownloading}
                                >
                                  {isDownloading ? 'Generating…' : 'PDF'}
                                </button>
                                {downloadError && (
                                  <p className="status-message status-message--error admin-users__report-error">
                                    {downloadError}
                                  </p>
                                )}
                              </>
                            ) : (
                              '—'
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
