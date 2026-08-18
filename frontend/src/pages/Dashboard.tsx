import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { AlphabetBoard } from '../components/AlphabetBoard';
import { PracticeNextPanel } from '../components/PracticeNextPanel';
import { ConfusionPanel } from '../components/ConfusionPanel';
import { Topbar } from '../components/Topbar';
import { LearnerAnalytics, RecommendationItem } from '../types/analytics';
import { mockConfusionPairs } from '../mocks/dashboardMockData';
import './Dashboard.css';

export function Dashboard() {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<LearnerAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setLoadError(null);
    try {
      const [analyticsRes, recommendationsRes] = await Promise.all([
        client.get<LearnerAnalytics>(`/api/learner/${user.id}/analytics`),
        client.get<{ recommendations: RecommendationItem[] }>(`/api/learner/${user.id}/recommendations`),
      ]);
      setAnalytics(analyticsRes.data);
      setRecommendations(recommendationsRes.data.recommendations);
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

  // Confusion pairs has no backing endpoint yet — see ConfusionPanel.tsx.
  const confusionPairs = mockConfusionPairs;

  if (loading && !analytics) {
    return (
      <div className="page dashboard">
        <Topbar title="Learner Dashboard" />
        <p className="dashboard__status">Loading your stats&hellip;</p>
      </div>
    );
  }

  if (loadError && !analytics) {
    return (
      <div className="page dashboard">
        <Topbar title="Learner Dashboard" />
        <p className="dashboard__status dashboard__status--error">{loadError}</p>
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

      <section className="stats-row">
        <div className="stat-tile">
          <span className="stat-tile__value stat-tile__value--accent">
            {analytics.overall_accuracy_percent ?? '—'}
            {analytics.overall_accuracy_percent !== null && <span className="stat-tile__unit">%</span>}
          </span>
          <span className="stat-tile__label">Lifetime accuracy</span>
        </div>
        <div className="stat-tile">
          <span className="stat-tile__value">{analytics.total_attempts}</span>
          <span className="stat-tile__label">Attempts</span>
        </div>
        <div className="stat-tile">
          <span className="stat-tile__value">
            {scoredLetterCount}
            <span className="stat-tile__unit">/{letterCount}</span>
          </span>
          <span className="stat-tile__label">Letters scored</span>
        </div>
        <div className="stat-tile">
          <span className="stat-tile__value stat-tile__value--warn">{analytics.weak_areas.length}</span>
          <span className="stat-tile__label">Weak areas</span>
        </div>
      </section>

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
