import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import client from '../api/client';
import { AlphabetBoard } from '../components/AlphabetBoard';
import { PracticeNextPanel } from '../components/PracticeNextPanel';
import { ConfusionPanel } from '../components/ConfusionPanel';
import { AssignedFocusPanel } from '../components/AssignedFocusPanel';
import { AssignmentForm, AssignmentFormFields } from '../components/AssignmentForm';
import { InstructorNotesPanel } from '../components/InstructorNotesPanel';
import { WeakAreasPanel } from '../components/WeakAreasPanel';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { AchievementsPanel } from '../components/AchievementsPanel';
import { ActivityTimelinePanel } from '../components/ActivityTimelinePanel';
import { ForecastPanel } from '../components/ForecastPanel';
import { AdaptiveLearningPanel } from '../components/AdaptiveLearningPanel';
import { FeedbackPanel } from '../components/FeedbackPanel';
import { LearningPlanPanel } from '../components/LearningPlanPanel';
import { StatsRow, StatTile } from '../components/StatsRow';
import { Topbar } from '../components/Topbar';
import {
  AdaptiveLearningPlan,
  ConfusionPair,
  LearnerAnalytics,
  LearnerFeedback,
  LearningPlan,
  RecommendationItem,
} from '../types/analytics';
import { LearnerRosterEntry, LearnerRosterResponse } from '../types/instructor';
import { Assignment, AssignmentListResponse, AssignmentTopicType } from '../types/instructorAssignment';
import { InstructorNote, NoteListResponse } from '../types/instructorNote';
import { SupportedMotionSigns } from '../types/motionSigns';
import { SupportedWordSigns } from '../types/wordSigns';
import { LearnerProgress } from '../types/progress';
import '../pages/Dashboard.css';
import './InstructorLearnerDetail.css';

// The instructor-facing counterpart to Dashboard.tsx — same panels, same
// endpoints, just pointed at :learnerId instead of the logged-in user's
// own id. Every /api/learner/{id}/... route already allows staff roles
// via require_self_or_staff (see auth_dependency.py), so this is a
// frontend-only addition: no new backend endpoints, no second
// aggregation logic, no risk of ever disagreeing with what the learner
// sees on their own Dashboard.
//
// The roster entry (name/email/summary stats) is fetched from the same
// /api/instructor/learners the roster page already uses, rather than a
// new by-id endpoint, so this page works correctly on a direct link or
// refresh, not just when navigated to from a roster row click.
export function InstructorLearnerDetail() {
  const { learnerId } = useParams<{ learnerId: string }>();
  const [rosterEntry, setRosterEntry] = useState<LearnerRosterEntry | null>(null);
  const [rosterNotFound, setRosterNotFound] = useState(false);
  const [analytics, setAnalytics] = useState<LearnerAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [confusionPairs, setConfusionPairs] = useState<ConfusionPair[]>([]);
  const [progress, setProgress] = useState<LearnerProgress | null>(null);
  const [adaptivePlan, setAdaptivePlan] = useState<AdaptiveLearningPlan | null>(null);
  const [feedback, setFeedback] = useState<LearnerFeedback | null>(null);
  const [learningPlan, setLearningPlan] = useState<LearningPlan | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [notes, setNotes] = useState<InstructorNote[]>([]);
  const [motionSigns, setMotionSigns] = useState<string[]>([]);
  const [wordSigns, setWordSigns] = useState<string[]>([]);
  const [removingAssignmentId, setRemovingAssignmentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [addingToRoster, setAddingToRoster] = useState(false);
  const [addToRosterError, setAddToRosterError] = useState<string | null>(null);

  const loadLearnerDetail = useCallback(async () => {
    if (!learnerId) return;
    setLoading(true);
    setLoadError(null);
    try {
      const [
        rosterRes,
        analyticsRes,
        recommendationsRes,
        confusionRes,
        progressRes,
        adaptivePlanRes,
        feedbackRes,
        learningPlanRes,
        assignmentsRes,
        notesRes,
        motionSignsRes,
        wordSignsRes,
      ] = await Promise.all([
        client.get<LearnerRosterResponse>('/api/instructor/learners'),
        client.get<LearnerAnalytics>(`/api/learner/${learnerId}/analytics`),
        client.get<{ recommendations: RecommendationItem[] }>(`/api/learner/${learnerId}/recommendations`),
        client.get<{ pairs: ConfusionPair[] }>(`/api/learner/${learnerId}/confusion-pairs`),
        client.get<LearnerProgress>(`/api/learner/${learnerId}/progress`),
        client.get<AdaptiveLearningPlan>(`/api/learner/${learnerId}/adaptive-learning-plan`),
        client.get<LearnerFeedback>(`/api/learner/${learnerId}/feedback`),
        client.get<LearningPlan>(`/api/learner/${learnerId}/learning-plan`),
        client.get<AssignmentListResponse>(`/api/instructor/learners/${learnerId}/assignments`),
        client.get<NoteListResponse>(`/api/instructor/learners/${learnerId}/notes`),
        client.get<SupportedMotionSigns>('/api/motion-signs/supported'),
        client.get<SupportedWordSigns>('/api/word-signs/supported'),
      ]);

      const match = rosterRes.data.learners.find((l) => l.learner_id === learnerId) ?? null;
      setRosterEntry(match);
      setRosterNotFound(match === null);
      setAnalytics(analyticsRes.data);
      setRecommendations(recommendationsRes.data.recommendations);
      setConfusionPairs(confusionRes.data.pairs);
      setProgress(progressRes.data);
      setAdaptivePlan(adaptivePlanRes.data);
      setFeedback(feedbackRes.data);
      setLearningPlan(learningPlanRes.data);
      setAssignments(assignmentsRes.data.assignments);
      setNotes(notesRes.data.notes);
      setMotionSigns(motionSignsRes.data.signs);
      setWordSigns(wordSignsRes.data.words);
    } catch (err) {
      console.error('Failed to load learner detail:', err);
      setLoadError('Could not load this learner’s data.');
    } finally {
      setLoading(false);
    }
  }, [learnerId]);

  const handleCreateAssignment = useCallback(
    async (topic: string, topicType: AssignmentTopicType, fields: AssignmentFormFields = { notes: null, dueDate: null, referenceMedia: null }) => {
      if (!learnerId) return;
      const formData = new FormData();
      formData.append('topic', topic);
      formData.append('topic_type', topicType);
      if (fields.notes) formData.append('notes', fields.notes);
      if (fields.dueDate) formData.append('due_date', fields.dueDate);
      if (fields.referenceMedia) {
        formData.append('reference_media', fields.referenceMedia);
      }
      // No explicit Content-Type here — axios sets multipart/form-data with
      // the correct boundary itself when the body is a FormData instance.
      const response = await client.post<Assignment>(`/api/instructor/learners/${learnerId}/assignments`, formData);
      setAssignments((current) => [response.data, ...current]);
    },
    [learnerId]
  );

  const handleAssignWeakArea = useCallback(
    (letter: string) => handleCreateAssignment(letter, 'letter'),
    [handleCreateAssignment]
  );

  const handleRemoveAssignment = useCallback(async (assignmentId: string) => {
    setRemovingAssignmentId(assignmentId);
    try {
      await client.delete(`/api/instructor/assignments/${assignmentId}`);
      setAssignments((current) => current.filter((a) => a.id !== assignmentId));
    } catch (err) {
      console.error('Failed to remove assignment:', err);
    } finally {
      setRemovingAssignmentId(null);
    }
  }, []);

  const handleAddNote = useCallback(
    async (note: string) => {
      if (!learnerId) return;
      const response = await client.post<InstructorNote>(`/api/instructor/learners/${learnerId}/notes`, { note });
      setNotes((current) => [response.data, ...current]);
    },
    [learnerId]
  );

  const handleAddToRoster = useCallback(async () => {
    if (!learnerId) return;
    setAddingToRoster(true);
    setAddToRosterError(null);
    try {
      await client.post(`/api/instructor/learners/${learnerId}/roster`);
      // Refreshes rosterEntry/rosterNotFound (and everything else) from
      // scratch so the page reflects the now-owned learner immediately.
      await loadLearnerDetail();
    } catch (err) {
      console.error('Failed to add learner to roster:', err);
      setAddToRosterError('Could not add this learner to your roster.');
    } finally {
      setAddingToRoster(false);
    }
  }, [learnerId, loadLearnerDetail]);

  useEffect(() => {
    loadLearnerDetail();
  }, [loadLearnerDetail]);

  const handleDownloadReport = useCallback(async () => {
    if (!learnerId) return;
    setDownloadingReport(true);
    setDownloadError(null);
    try {
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
      console.error('Failed to download report:', err);
      setDownloadError('Could not generate the report. Please try again.');
    } finally {
      setDownloadingReport(false);
    }
  }, [learnerId]);

  const headerTitle = rosterEntry ? `${rosterEntry.name}’s Progress` : 'Learner Detail';

  if (loading && !analytics) {
    return (
      <div className="page instructor-learner-detail">
        <Topbar title="Learner Detail" />
        <div className="content-loading">
          <p className="status-message">Loading learner data&hellip;</p>
        </div>
      </div>
    );
  }

  if (loadError && !analytics) {
    return (
      <div className="page instructor-learner-detail">
        <Topbar title="Learner Detail" />
        <Link to="/instructor" className="instructor-learner-detail__back">
          &larr; Back to roster
        </Link>
        <p className="status-message status-message--error">{loadError}</p>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  const letterCount = Object.keys(analytics.per_letter).length;
  const scoredLetterCount = Object.values(analytics.per_letter).filter(
    (s) => s.accuracy_percent !== null
  ).length;

  return (
    <div className="page instructor-learner-detail">
      <Topbar title={headerTitle} />

      <Link to="/instructor" className="instructor-learner-detail__back">
        &larr; Back to roster
      </Link>

      {rosterNotFound && (
        <div className="instructor-learner-detail__not-on-roster">
          <p className="status-message status-message--error">
            This learner isn&rsquo;t on your roster yet — you can still view their data, but you&rsquo;ll need to add
            them before assigning a new focus or leaving a note.
          </p>
          <button className="btn btn--ghost" onClick={handleAddToRoster} disabled={addingToRoster}>
            {addingToRoster ? 'Adding…' : 'Add to my roster'}
          </button>
          {addToRosterError && <p className="status-message status-message--error">{addToRosterError}</p>}
        </div>
      )}

      {rosterEntry && (
        <p className="instructor-learner-detail__email">{rosterEntry.email}</p>
      )}

      <div className="dashboard__actions">
        <button className="btn btn--ghost" onClick={handleDownloadReport} disabled={downloadingReport}>
          {downloadingReport ? 'Generating report…' : 'Download progress report (PDF)'}
        </button>
        {downloadError && <p className="status-message status-message--error">{downloadError}</p>}
      </div>

      <StatsRow>
        <StatTile
          variant="accent"
          value={
            <>
              {analytics.overall_accuracy_percent !== null ? (
                <AnimatedNumber
                  value={analytics.overall_accuracy_percent}
                  decimals={Number.isInteger(analytics.overall_accuracy_percent) ? 0 : 1}
                />
              ) : (
                '—'
              )}
              {analytics.overall_accuracy_percent !== null && <span className="stat-tile__unit">%</span>}
            </>
          }
          label="Lifetime accuracy"
        />
        <StatTile value={<AnimatedNumber value={analytics.total_attempts} />} label="Attempts" />
        <StatTile
          value={
            <>
              <AnimatedNumber value={scoredLetterCount} />
              <span className="stat-tile__unit">/{letterCount}</span>
            </>
          }
          label="Letters scored"
        />
        <StatTile
          variant="warn"
          value={<AnimatedNumber value={analytics.weak_areas.length} />}
          label="Weak areas"
        />
        {progress && (
          <StatTile
            variant={progress.current_streak_days > 0 ? 'accent' : 'default'}
            value={<AnimatedNumber value={progress.current_streak_days} />}
            label="Day streak"
          />
        )}
      </StatsRow>

      <section className="board-section">
        <AlphabetBoard perLetter={analytics.per_letter} />
      </section>

      <section className="panels-row">
        <PracticeNextPanel recommendations={recommendations} />
        <ConfusionPanel pairs={confusionPairs} />
      </section>

      <WeakAreasPanel weakAreas={analytics.weak_areas} assignments={assignments} onAssign={handleAssignWeakArea} />

      <AssignedFocusPanel assignments={assignments} onRemove={handleRemoveAssignment} removingId={removingAssignmentId}>
        <AssignmentForm
          letters={Object.keys(analytics.per_letter)}
          motionSigns={motionSigns}
          wordSigns={wordSigns}
          onCreate={handleCreateAssignment}
        />
      </AssignedFocusPanel>

      <InstructorNotesPanel notes={notes} onAdd={handleAddNote} />

      {adaptivePlan && <AdaptiveLearningPanel plan={adaptivePlan} />}
      {feedback && <FeedbackPanel feedback={feedback} />}
      {learningPlan && <LearningPlanPanel plan={learningPlan} />}

      {progress && (
        <>
          <section className="panels-row">
            <AchievementsPanel achievements={progress.achievements} />
            <ActivityTimelinePanel activity={progress.recent_activity} />
          </section>

          <ForecastPanel forecast={progress.forecast} />
        </>
      )}
    </div>
  );
}
