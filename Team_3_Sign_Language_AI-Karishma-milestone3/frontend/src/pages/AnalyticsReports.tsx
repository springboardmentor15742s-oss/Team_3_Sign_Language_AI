import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Topbar } from '../components/Topbar';
import { LearnerAnalytics, LearningAnalyticsWorkflow } from '../types/analytics';
import './AnalyticsReports.css';

const TOPIC_LABEL: Record<string, string> = { letter: 'letter', motion_sign: 'motion sign' };

export function AnalyticsReports() {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<LearnerAnalytics | null>(null);
  const [workflow, setWorkflow] = useState<LearningAnalyticsWorkflow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!user) return;
    try {
      const [analyticsRes, workflowRes] = await Promise.all([
        client.get<LearnerAnalytics>(`/api/learner/${user.id}/analytics`),
        client.get<LearningAnalyticsWorkflow>(`/api/learner/${user.id}/analytics-workflow`),
      ]);
      setAnalytics(analyticsRes.data);
      setWorkflow(workflowRes.data);
    }
    catch { setError('Could not load analytics.'); }
  }, [user]);
  useEffect(() => { load(); }, [load]);
  if (error) return <div className="page analytics-reports"><Topbar title="Analytics & Reports" /><p className="status-message status-message--error">{error}</p></div>;
  if (!analytics || !workflow) return <div className="page analytics-reports"><Topbar title="Analytics & Reports" /><p className="status-message">Loading analytics…</p></div>;
  const maxAttempts = Math.max(1, ...analytics.accuracy_trend.map((point) => point.attempts));
  const scored = Object.entries(analytics.per_letter).filter(([, value]) => value.accuracy_percent !== null);
  const comparison = workflow.performance_comparison;
  return <div className="page analytics-reports"><Topbar title="Analytics & Reports" />
    <section className="analytics-reports__intro"><span>Real learner data</span><h2>Learning Analytics</h2><p>Activity, assessed accuracy, and sign mastery based on your recorded practice.</p></section>
    <section className="analytics-reports__grid">
      <article className="analytics-card"><h3>Learning activity over time</h3><p>Assessed practice attempts by day</p><div className="bar-chart">{analytics.accuracy_trend.map((point) => <div key={point.date} className="bar-chart__column"><span>{point.attempts}</span><i style={{ height: `${(point.attempts / maxAttempts) * 160}px` }} /><small>{point.date.slice(5)}</small></div>)}</div></article>
      <article className="analytics-card"><h3>Accuracy trend over time</h3><p>Daily verified practice accuracy</p><div className="trend-list">{analytics.accuracy_trend.map((point) => <div key={point.date}><span>{point.date}</span><b>{point.accuracy_percent === null ? '—' : `${point.accuracy_percent}%`}</b><i><em style={{ width: `${point.accuracy_percent ?? 0}%` }} /></i></div>)}</div></article>
    </section>
    <section className="analytics-card"><h3>Sign mastery breakdown</h3><p>{scored.length} signs have assessed results. Focus areas are based on at least three scored attempts below 70%.</p><div className="mastery-grid">{scored.map(([letter, value]) => <div key={letter}><span>{letter}</span><i><em style={{ width: `${value.accuracy_percent}%` }} /></i><b>{value.accuracy_percent}%</b></div>)}</div></section>

    <section className="analytics-reports__intro" style={{ marginTop: 'var(--space-6)' }}><span>Learning analytics workflow</span><h2>Coverage, frequency, and trends</h2><p>Completion rate, how often you practice, what gets missed most, and how this period compares to the last.</p></section>
    <section className="analytics-reports__grid">
      <article className="analytics-card">
        <h3>Completion rate</h3>
        <p>Share of each course's letters/signs you've attempted at least once.</p>
        <div className="mastery-grid">
          {workflow.completion_rate.by_course.filter((c) => c.completion_percent !== null).map((c) => (
            <div key={c.course_id}><span title={c.title}>{c.title.split(' ')[0]}</span><i><em style={{ width: `${c.completion_percent}%` }} /></i><b>{c.completion_percent}%</b></div>
          ))}
        </div>
      </article>
      <article className="analytics-card">
        <h3>Activity frequency</h3>
        <p>How often and how recently you've been practicing.</p>
        <div className="kv-list">
          <div><span>Active days (last 7)</span><span>{workflow.frequency_patterns.days_active_last_7}</span></div>
          <div><span>Active days (last 30)</span><span>{workflow.frequency_patterns.days_active_last_30}</span></div>
          <div><span>Avg. attempts / active day</span><span>{workflow.frequency_patterns.avg_attempts_per_active_day ?? '—'}</span></div>
          <div><span>Last active</span><span>{workflow.frequency_patterns.last_active_date ?? 'Never'}</span></div>
          <div><span>Most active day</span><span>{workflow.frequency_patterns.most_active_weekday ?? '—'}</span></div>
        </div>
      </article>
    </section>
    <section className="analytics-reports__grid">
      <article className="analytics-card">
        <h3>Commonly missed topics</h3>
        <p>Ranked by how many times each has actually been missed.</p>
        {workflow.commonly_missed.length > 0 ? (
          <ul className="missed-list">
            {workflow.commonly_missed.map((item) => (
              <li key={`${item.topic_type}-${item.topic}`}><span>{item.topic} <small>({TOPIC_LABEL[item.topic_type]})</small></span><b>{item.incorrect_count} missed</b></li>
            ))}
          </ul>
        ) : <p className="panel__empty">No missed topics recorded yet.</p>}
        {workflow.avoided_topics.length > 0 && (
          <>
            <h3 style={{ marginTop: 'var(--space-4)' }}>Never attempted</h3>
            <div className="avoided-chips">
              {workflow.avoided_topics.map((t) => <span key={`${t.topic_type}-${t.topic}`}>{t.topic}</span>)}
            </div>
          </>
        )}
      </article>
      <article className="analytics-card">
        <h3>Current vs. previous performance</h3>
        <p>Last 7 days compared to the 7 days before that.</p>
        {comparison.available ? (
          <div className="comparison-row">
            <div><b>{comparison.previous_period.accuracy_percent}%</b><span>Previous period</span></div>
            <div><b>{comparison.current_period.accuracy_percent}%</b><span>Current period</span></div>
            <div>
              <b className={`comparison-delta comparison-delta--${comparison.trend}`}>
                {comparison.accuracy_delta_percent! > 0 ? '+' : ''}{comparison.accuracy_delta_percent}pp
              </b>
              <span>{comparison.trend}</span>
            </div>
          </div>
        ) : <p className="panel__empty">{comparison.reason}</p>}
      </article>
    </section>
  </div>;
}
