import React, { useCallback, useState } from 'react';
import client from '../api/client';
import { AssignmentReportResponse } from '../types/reporting';
import { StatsRow, StatTile } from './StatsRow';
import { AnimatedNumber } from './AnimatedNumber';
import './Panel.css';
import './AssignmentReportPanel.css';

interface AssignmentReportPanelProps {
  report: AssignmentReportResponse;
}

function statusLabel(row: { completed: boolean; overdue: boolean }): 'Completed' | 'Overdue' | 'Open' {
  if (row.completed) return 'Completed';
  if (row.overdue) return 'Overdue';
  return 'Open';
}

// The assignment/completion report — every InstructorAssignment across
// the caller's roster (or, for an admin, the whole platform), same
// scoping as ClassOverviewPanel. Reads the report as a prop (fetched by
// the parent page, same convention as ClassOverviewPanel's `analytics`)
// and owns its own "Download PDF" button, hitting the sibling PDF
// endpoint directly.
export function AssignmentReportPanel({ report }: AssignmentReportPanelProps) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPdf = useCallback(async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const response = await client.get('/api/instructor/reports/assignments/pdf', { responseType: 'blob' });
      const disposition = response.headers['content-disposition'] as string | undefined;
      const filename = disposition?.match(/filename="?([^"]+)"?/)?.[1] ?? 'assignment-report.pdf';

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download assignment report:', err);
      setDownloadError('Could not generate this report.');
    } finally {
      setDownloading(false);
    }
  }, []);

  return (
    <div className="panel assignment-report-panel">
      <div className="assignment-report-panel__header">
        <h2 className="panel__title">Assignment report</h2>
        <div className="assignment-report-panel__download">
          <button
            type="button"
            className="btn btn--ghost assignment-report-panel__download-btn"
            onClick={handleDownloadPdf}
            disabled={downloading}
          >
            {downloading ? 'Generating…' : 'Download PDF'}
          </button>
          {downloadError && (
            <p className="status-message status-message--error assignment-report-panel__download-error">
              {downloadError}
            </p>
          )}
        </div>
      </div>

      <StatsRow>
        <StatTile value={<AnimatedNumber value={report.total_count} />} label="Total assignments" />
        <StatTile value={<AnimatedNumber value={report.completed_count} />} label="Completed" />
        <StatTile
          variant="warn"
          value={<AnimatedNumber value={report.outstanding_count} />}
          label="Outstanding"
        />
        <StatTile
          variant="warn"
          value={<AnimatedNumber value={report.overdue_count} />}
          label="Overdue"
        />
      </StatsRow>

      {report.rows.length === 0 ? (
        <p className="panel__empty">No assignments in this group yet.</p>
      ) : (
        <div className="data-table-wrap assignment-report-panel__table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Learner</th>
                <th>Topic</th>
                <th>Due</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {report.rows.map((row, index) => {
                const status = statusLabel(row);
                return (
                  // No stable row id in the payload (assignment id isn't carried
                  // through the report schema) — the tuple below is unique per
                  // row for this report's lifetime, which is all a React key needs.
                  <tr key={`${row.learner_id}-${row.topic}-${row.created_at}-${index}`}>
                    <td>{row.learner_name}</td>
                    <td>{row.topic}</td>
                    <td className="data-table__numeric">{row.due_date ?? '—'}</td>
                    <td>
                      <span
                        className={`assignment-report-panel__badge assignment-report-panel__badge--${status.toLowerCase()}`}
                      >
                        {status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
