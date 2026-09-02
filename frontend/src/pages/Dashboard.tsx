import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { AlphabetBoard } from '../components/AlphabetBoard';
import { PracticeNextPanel } from '../components/PracticeNextPanel';
import { ConfusionPanel } from '../components/ConfusionPanel';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { AchievementsPanel } from '../components/AchievementsPanel';
import { ActivityTimelinePanel } from '../components/ActivityTimelinePanel';
import { ForecastPanel } from '../components/ForecastPanel';
import { AdaptiveLearningPanel } from '../components/AdaptiveLearningPanel';
import { FeedbackPanel } from '../components/FeedbackPanel';
import { LearningPlanPanel } from '../components/LearningPlanPanel';
import { AssignedFocusPanel } from '../components/AssignedFocusPanel';
import { StatsRow, StatTile } from '../components/StatsRow';
import { Topbar } from '../components/Topbar';
import { AdaptiveLearningPlan, ConfusionPair, LearnerAnalytics, LearnerFeedback, LearningPlan, RecommendationItem } from '../types/analytics';
import { Assignment, AssignmentListResponse } from '../types/instructorAssignment';
import { LearnerProgress } from '../types/progress';
import './Dashboard.css';

export function Dashboard() {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<LearnerAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [confusionPairs, setConfusionPairs] = useState<ConfusionPair[]>([]);
  const [progress, setProgress] = useState<LearnerProgress | null>(null);
  const [adaptivePlan, setAdaptivePlan] = useState<AdaptiveLearningPlan | null>(null);
  const [feedback, setFeedback] = useState<LearnerFeedback | null>(null);
  const [learningPlan, setLearningPlan] = useState<LearningPlan | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [completingAssignmentId, setCompletingAssignmentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setLoadError(null);
    try {
      const [analyticsRes, recommendationsRes, confusionRes, progressRes, adaptivePlanRes, feedbackRes, learningPlanRes, assignmentsRes] = await Promise.all([
        client.get<LearnerAnalytics>(`/api/learner/${user.id}/analytics`),
        client.get<{ recommendations: RecommendationItem[] }>(`/api/learner/${user.id}/recommendations`),
        client.get<{ pairs: ConfusionPair[] }>(`/api/learner/${user.id}/confusion-pairs`),
        client.get<LearnerProgress>(`/api/learner/${user.id}/progress`),
        client.get<AdaptiveLearningPlan>(`/api/learner/${user.id}/adaptive-learning-plan`),
        client.get<LearnerFeedback>(`/api/learner/${user.id}/feedback`),
        client.get<LearningPlan>(`/api/learner/${user.id}/learning-plan`),
        client.get<AssignmentListResponse>(`/api/learner/${user.id}/assignments`),
      ]);
      setAnalytics(analyticsRes.data);
      setRecommendations(recommendationsRes.data.recommendations);
      setConfusionPairs(confusionRes.data.pairs);
      setProgress(progressRes.data);
      setAdaptivePlan(adaptivePlanRes.data);
      setFeedback(feedbackRes.data);
      setLearningPlan(learningPlanRes.data);
      setAssignments(assignmentsRes.data.assignments);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setLoadError('Could not load dashboard data.');
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Re-fetches on every mount, so navigating here fresh from a practice
  // session (a full route change, not a soft update) always shows current data.
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleCompleteAssignment = useCallback(
    async (assignmentId: string, completed: boolean) => {
      if (!user) return;
      setCompletingAssignmentId(assignmentId);
      try {
        const response = await client.patch<Assignment>(
          `/api/learner/${user.id}/assignments/${assignmentId}/complete`,
          { completed }
        );
        setAssignments((current) => current.map((a) => (a.id === assignmentId ? response.data : a)));
      } catch (err) {
        console.error('Failed to update assignment completion:', err);
      } finally {
        setCompletingAssignmentId(null);
      }
    },
    [user]
  );

  const handleDownloadReport = useCallback(async () => {
    if (!user) return;
    setDownloadingReport(true);
    setDownloadError(null);
    try {
      const response = await client.get(`/api/reports/learner/${user.id}/pdf`, { responseType: 'blob' });

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
  }, [user]);

  if (loading && !analytics) {
    return (
      <div className="page dashboard">
        <Topbar title="Learner Dashboard" />
        <div className="content-loading">
          <p className="status-message">Loading your stats&hellip;</p>
        </div>
      </div>
    );
  }

  if (loadError && !analytics) {
    return (
      <div className="page dashboard">
        <Topbar title="Learner Dashboard" />
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
    <div className="page dashboard">
      <Topbar title="Learner Dashboard" />

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

      {assignments.length > 0 && (
        <AssignedFocusPanel
          assignments={assignments}
          onComplete={handleCompleteAssignment}
          completingId={completingAssignmentId}
        />
      )}

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
