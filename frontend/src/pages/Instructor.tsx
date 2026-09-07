import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import { BulkAssignPanel } from '../components/BulkAssignPanel';
import { AssignmentFormFields } from '../components/AssignmentForm';
import { ClassOverviewPanel } from '../components/ClassOverviewPanel';
import { AssignmentReportPanel } from '../components/AssignmentReportPanel';
import { ClassTrendsPanel } from '../components/ClassTrendsPanel';
import '../components/DataTable.css';
import { Topbar } from '../components/Topbar';
import { ClassAnalytics, LearnerRosterEntry, LearnerRosterResponse } from '../types/instructor';
import { AssignmentListResponse, AssignmentTopicType } from '../types/instructorAssignment';
import { SupportedMotionSigns } from '../types/motionSigns';
import { SupportedLettersResponse } from '../types/practice';
import { SupportedWordSigns } from '../types/wordSigns';
import { AssignmentReportResponse } from '../types/reporting';
import { ClassTrendsResponse } from '../types/classTrends';
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
  const [classAnalytics, setClassAnalytics] = useState<ClassAnalytics | null>(null);
  const [assignmentReport, setAssignmentReport] = useState<AssignmentReportResponse | null>(null);
  const [classTrends, setClassTrends] = useState<ClassTrendsResponse | null>(null);
  const [letters, setLetters] = useState<string[]>([]);
  const [motionSigns, setMotionSigns] = useState<string[]>([]);
  const [wordSigns, setWordSigns] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Per-row state, keyed by learner_id — several instructors could in
  // principle click different rows in quick succession, so a single
  // shared boolean/error (like Dashboard's own report button uses for
  // its one learner) isn't enough here.
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [downloadErrors, setDownloadErrors] = useState<Record<string, string>>({});
  const [removingIds, setRemovingIds] = useState<Set<string>>(new Set());
  const [newLearnerEmail, setNewLearnerEmail] = useState('');
  const [addingLearner, setAddingLearner] = useState(false);
  const [addLearnerError, setAddLearnerError] = useState<string | null>(null);

  const loadRoster = useCallback(async () => {
    setLoadError(null);
    try {
      const [rosterRes, analyticsRes, assignmentReportRes, classTrendsRes, lettersRes, motionSignsRes, wordSignsRes] = await Promise.all([
        client.get<LearnerRosterResponse>('/api/instructor/learners'),
        client.get<ClassAnalytics>('/api/instructor/class-analytics'),
        client.get<AssignmentReportResponse>('/api/instructor/reports/assignments'),
        client.get<ClassTrendsResponse>('/api/instructor/class-trends'),
        client.get<SupportedLettersResponse>('/api/practice/supported-letters'),
        client.get<SupportedMotionSigns>('/api/motion-signs/supported'),
        client.get<SupportedWordSigns>('/api/word-signs/supported'),
      ]);
      setLearners(sortByAccuracyAscending(rosterRes.data.learners));
      setClassAnalytics(analyticsRes.data);
      setAssignmentReport(assignmentReportRes.data);
      setClassTrends(classTrendsRes.data);
      setLetters(lettersRes.data.letters);
      setMotionSigns(motionSignsRes.data.signs);
      setWordSigns(wordSignsRes.data.words);
    } catch (err) {
      console.error('Failed to load learner roster:', err);
      setLoadError('Could not load the learner roster.');
    }
  }, []);

  useEffect(() => {
    loadRoster();
  }, [loadRoster]);

  const handleAddLearner = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLearnerEmail.trim()) return;
    setAddingLearner(true);
    setAddLearnerError(null);
    try {
      const response = await client.post<LearnerRosterResponse>('/api/instructor/learners', {
        learner_email: newLearnerEmail.trim(),
      });
      setLearners(sortByAccuracyAscending(response.data.learners));
      setNewLearnerEmail('');
      // The roster changed, so the class-wide numbers above it need a refresh too.
      const analyticsRes = await client.get<ClassAnalytics>('/api/instructor/class-analytics');
      setClassAnalytics(analyticsRes.data);
    } catch (err) {
      console.error('Failed to add learner to roster:', err);
      setAddLearnerError('Could not find a learner with that email.');
    } finally {
      setAddingLearner(false);
    }
  }, [newLearnerEmail]);

  const handleRemoveLearner = useCallback(async (learnerId: string) => {
    setRemovingIds((current) => new Set(current).add(learnerId));
    try {
      await client.delete(`/api/instructor/learners/${learnerId}`);
      setLearners((current) => (current ? current.filter((l) => l.learner_id !== learnerId) : current));
      const analyticsRes = await client.get<ClassAnalytics>('/api/instructor/class-analytics');
      setClassAnalytics(analyticsRes.data);
      const assignmentReportRes = await client.get<AssignmentReportResponse>('/api/instructor/reports/assignments');
      setAssignmentReport(assignmentReportRes.data);
    } catch (err) {
      console.error('Failed to remove learner from roster:', err);
    } finally {
      setRemovingIds((current) => {
        const next = new Set(current);
        next.delete(learnerId);
        return next;
      });
    }
  }, []);

  const handleBulkAssign = useCallback(
    async (learnerIds: string[], topic: string, topicType: AssignmentTopicType, fields: AssignmentFormFields) => {
      const formData = new FormData();
      learnerIds.forEach((id) => formData.append('learner_ids', id));
      formData.append('topic', topic);
      formData.append('topic_type', topicType);
      if (fields.notes) formData.append('notes', fields.notes);
      if (fields.dueDate) formData.append('due_date', fields.dueDate);
      if (fields.referenceMedia) formData.append('reference_media', fields.referenceMedia);
      await client.post<AssignmentListResponse>('/api/instructor/assignments', formData);
      // Assignment counts changed; refresh the class overview numbers and the assignment report.
      const analyticsRes = await client.get<ClassAnalytics>('/api/instructor/class-analytics');
      setClassAnalytics(analyticsRes.data);
      const assignmentReportRes = await client.get<AssignmentReportResponse>('/api/instructor/reports/assignments');
      setAssignmentReport(assignmentReportRes.data);
    },
    []
  );

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

      {classAnalytics && <ClassOverviewPanel analytics={classAnalytics} />}
      {classTrends && <ClassTrendsPanel trends={classTrends} />}
      {assignmentReport && <AssignmentReportPanel report={assignmentReport} />}

      <section className="roster-section">
        <form className="roster-section__add-learner" onSubmit={handleAddLearner}>
          <label className="roster-section__add-learner-field">
            Add a learner to your roster
            <input
              type="email"
              value={newLearnerEmail}
              onChange={(e) => setNewLearnerEmail(e.target.value)}
              placeholder="learner@example.com"
            />
          </label>
          <button type="submit" className="btn roster-section__add-learner-btn" disabled={addingLearner || !newLearnerEmail.trim()}>
            {addingLearner ? 'Adding…' : 'Add learner'}
          </button>
        </form>
        {addLearnerError && <p className="status-message status-message--error">{addLearnerError}</p>}

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
          <p className="status-message">No learners on your roster yet — add one by email above.</p>
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
                  <th>Roster</th>
                </tr>
              </thead>
              <tbody>
                {learners.map((learner) => {
                  const isWeakAccuracy =
                    learner.overall_accuracy_percent !== null &&
                    learner.overall_accuracy_percent < WEAK_ACCURACY_THRESHOLD;
                  const isDownloading = downloadingIds.has(learner.learner_id);
                  const downloadError = downloadErrors[learner.learner_id];
                  const isRemoving = removingIds.has(learner.learner_id);

                  return (
                    <tr key={learner.learner_id}>
                      <td>
                        <Link to={`/instructor/learners/${learner.learner_id}`}>{learner.name}</Link>
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
                      <td className="data-table__numeric">
                        <button
                          type="button"
                          className="btn btn--ghost roster-section__remove-btn"
                          onClick={() => handleRemoveLearner(learner.learner_id)}
                          disabled={isRemoving}
                          aria-label={`Remove ${learner.name} from your roster`}
                        >
                          {isRemoving ? '…' : 'Remove'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {learners && learners.length > 0 && (
        <BulkAssignPanel learners={learners} letters={letters} motionSigns={motionSigns} wordSigns={wordSigns} onAssign={handleBulkAssign} />
      )}
    </div>
  );
}
