import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { AlphabetBoard } from '../components/AlphabetBoard';
import { PracticeNextPanel } from '../components/PracticeNextPanel';
import { ConfusionPanel } from '../components/ConfusionPanel';
import { StatsRow, StatTile } from '../components/StatsRow';
import { Topbar } from '../components/Topbar';
import { ConfusionPair, LearnerAnalytics, RecommendationItem } from '../types/analytics';
import './Dashboard.css';

export function Dashboard() {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<LearnerAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [confusionPairs, setConfusionPairs] = useState<ConfusionPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setLoadError(null);
    try {
      const [analyticsRes, recommendationsRes, confusionRes] = await Promise.all([
        client.get<LearnerAnalytics>(`/api/learner/${user.id}/analytics`),
        client.get<{ recommendations: RecommendationItem[] }>(`/api/learner/${user.id}/recommendations`),
        client.get<{ pairs: ConfusionPair[] }>(`/api/learner/${user.id}/confusion-pairs`),
      ]);
      setAnalytics(analyticsRes.data);
      setRecommendations(recommendationsRes.data.recommendations);
      setConfusionPairs(confusionRes.data.pairs);
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
              {analytics.overall_accuracy_percent ?? '—'}
              {analytics.overall_accuracy_percent !== null && <span className="stat-tile__unit">%</span>}
            </>
          }
          label="Lifetime accuracy"
        />
        <StatTile value={analytics.total_attempts} label="Attempts" />
        <StatTile
          value={
            <>
              {scoredLetterCount}
              <span className="stat-tile__unit">/{letterCount}</span>
            </>
          }
          label="Letters scored"
        />
        <StatTile variant="warn" value={analytics.weak_areas.length} label="Weak areas" />
      </StatsRow>

      <section className="board-section">
        <AlphabetBoard perLetter={analytics.per_letter} />
      </section>

      <section className="panels-row">
        <PracticeNextPanel recommendations={recommendations} />
        <ConfusionPanel pairs={confusionPairs} />
      </section>
    </div>
  );
}
