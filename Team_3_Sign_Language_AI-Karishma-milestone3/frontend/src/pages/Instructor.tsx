import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import '../components/DataTable.css';
import { Topbar } from '../components/Topbar';
import { LearnerRosterEntry, LearnerRosterResponse } from '../types/instructor';
import './Instructor.css';

const WEAK_ACCURACY_THRESHOLD = 70;

// Ascending by accuracy, so the lowest-performing learners lead the table.
// Untried learners (null accuracy) have no measured performance to rank,
// so they sort after every scored learner rather than competing for the
// top slot — the top of the table is reserved for learners who are
// actually struggling, not just learners who haven't started yet.
function sortByAccuracyAscending(learners: LearnerRosterEntry[]): LearnerRosterEntry[] {
  return [...learners].sort((a, b) => {
    if (a.overall_accuracy_percent === null && b.overall_accuracy_percent === null) return 0;
    if (a.overall_accuracy_percent === null) return 1;
    if (b.overall_accuracy_percent === null) return -1;
    return a.overall_accuracy_percent - b.overall_accuracy_percent;
  });
}

export function Instructor() {
  const [learners, setLearners] = useState<LearnerRosterEntry[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Per-row state, keyed by learner_id — several instructors could in
  // principle click different rows in quick succession, so a single
  // shared boolean/error (like Dashboard's own report button uses for
  // its one learner) isn't enough here.
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [downloadErrors, setDownloadErrors] = useState<Record<string, string>>({});

  const loadRoster = useCallback(async () => {
    setLoadError(null);
    try {
      const response = await client.get<LearnerRosterResponse>('/api/instructor/learners');
      setLearners(sortByAccuracyAscending(response.data.learners));
    } catch (err) {
      console.error('Failed to load learner roster:', err);
      setLoadError('Could not load the learner roster.');
    }
  }, []);

  useEffect(() => {
    loadRoster();
  }, [loadRoster]);

  const handleDownloadReport = useCallback(async (learnerId: string) => {
    setDownloadingIds((current) => new Set(current).add(learnerId));
    setDownloadErrors((current) => {
      const next = { ...current };
      delete next[learnerId];
      return next;
    });
    try {
      // Same /api/reports/learner/{id}/pdf endpoint the learner's own
      // Dashboard uses — require_self_or_staff already allows
      // instructor/admin to pull any learner's report, so this is a
      // frontend-only addition, no backend change needed.
      const response = await client.get(`/api/reports/learner/${learnerId}/pdf`, { responseType: 'blob' });

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
      console.error('Failed to download report for learner', learnerId, err);
      setDownloadErrors((current) => ({ ...current, [learnerId]: 'Could not generate this report.' }));
    } finally {
      setDownloadingIds((current) => {
        const next = new Set(current);
        next.delete(learnerId);
        return next;
      });
    }
  }, []);

  return (
    <div className="page instructor">
      <Topbar title="Instructor Dashboard" />

      <section className="roster-section">
        <p className="roster-section__caption">
          Sorted by accuracy, lowest first — learners who need attention are at the top. Learners
          who haven&rsquo;t attempted anything yet are listed at the bottom.
        </p>

        {loadError && <p className="status-message status-message--error">{loadError}</p>}

        {!loadError && learners === null && (
          <div className="content-loading">
            <p className="status-message">Loading roster&hellip;</p>
          </div>
        )}

        {!loadError && learners !== null && learners.length === 0 && (
          <p className="status-message">No learners yet.</p>
        )}

        {!loadError && learners !== null && learners.length > 0 && (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Attempts</th>
                  <th>Accuracy</th>
                  <th>Letters scored</th>
                  <th>Weak areas</th>
                  <th>Report</th>
                </tr>
              </thead>
              <tbody>
                {learners.map((learner) => {
                  const isWeakAccuracy =
                    learner.overall_accuracy_percent !== null &&
                    learner.overall_accuracy_percent < WEAK_ACCURACY_THRESHOLD;
                  const isDownloading = downloadingIds.has(learner.learner_id);
                  const downloadError = downloadErrors[learner.learner_id];

                  return (
                    <tr key={learner.learner_id}>
                      <td>
                        <Link to={`/instructor/learners/${learner.learner_id}`} className="roster-section__learner-link">
                          {learner.name}
                        </Link>
                      </td>
                      <td>{learner.email}</td>
                      <td className="data-table__numeric">{learner.total_attempts}</td>
                      <td
                        className={`data-table__numeric${isWeakAccuracy ? ' data-table__numeric--weak' : ''}`}
                      >
                        {learner.overall_accuracy_percent === null
                          ? '—'
                          : `${learner.overall_accuracy_percent}%`}
                      </td>
                      <td className="data-table__numeric">
                        {learner.letters_scored}/{learner.total_letters}
                      </td>
                      <td
                        className={`data-table__numeric${learner.weak_area_count > 0 ? ' data-table__numeric--weak' : ''}`}
                      >
                        {learner.weak_area_count}
                      </td>
                      <td className="data-table__numeric">
                        <button
                          type="button"
                          className="btn btn--ghost roster-section__report-btn"
                          onClick={() => handleDownloadReport(learner.learner_id)}
                          disabled={isDownloading}
                        >
                          {isDownloading ? 'Generating…' : 'PDF'}
                        </button>
                        {downloadError && (
                          <p className="status-message status-message--error roster-section__report-error">
                            {downloadError}
                          </p>
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
    </div>
  );
}
