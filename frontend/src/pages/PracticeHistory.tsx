import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import '../components/DataTable.css';
import { StatsRow, StatTile } from '../components/StatsRow';
import { Topbar } from '../components/Topbar';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { HistoryEntry, PracticeHistory as PracticeHistoryData } from '../types/history';
import { TopicType } from '../types/analytics';
import './PracticeHistory.css';

type TopicFilter = 'all' | TopicType;
type StatusFilter = 'all' | 'pass' | 'fail' | 'no_attempt_detected';

const STATUS_LABEL: Record<HistoryEntry['status'], string> = {
  pass: 'Pass',
  fail: 'Fail',
  no_attempt_detected: 'No attempt',
};

const TOPIC_TYPE_LABEL: Record<TopicType, string> = {
  letter: 'Letter',
  motion_sign: 'Motion sign',
};

export function PracticeHistory() {
  const { user } = useAuth();
  const [history, setHistory] = useState<PracticeHistoryData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [topicFilter, setTopicFilter] = useState<TopicFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const loadHistory = useCallback(async () => {
    if (!user) return;
    setLoadError(null);
    try {
      const params: Record<string, string> = {};
      if (topicFilter !== 'all') params.topic_type = topicFilter;
      if (statusFilter !== 'all') params.status = statusFilter;
      const response = await client.get<PracticeHistoryData>(
        `/api/learner/${user.id}/practice-history`,
        { params }
      );
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to load practice history:', err);
      setLoadError('Could not load your practice history.');
    }
  }, [user, topicFilter, statusFilter]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return (
    <div className="page practice-history">
      <Topbar title="Practice History" />

      {history && (
        <StatsRow>
          <StatTile value={<AnimatedNumber value={history.total_sessions} />} label="Total sessions" />
          <StatTile value={<AnimatedNumber value={history.scored_sessions} />} label="Scored sessions" />
          <StatTile
            variant="accent"
            value={
              history.accuracy_percent !== null ? (
                <>
                  <AnimatedNumber
                    value={history.accuracy_percent}
                    decimals={Number.isInteger(history.accuracy_percent) ? 0 : 1}
                  />
                  <span className="stat-tile__unit">%</span>
                </>
              ) : (
                '—'
              )
            }
            label="Overall accuracy"
          />
        </StatsRow>
      )}

      <div className="history-filters">
        <div className="history-filters__group">
          {(['all', 'letter', 'motion_sign'] as TopicFilter[]).map((value) => (
            <button
              key={value}
              type="button"
              className={`history-filters__tab${topicFilter === value ? ' history-filters__tab--active' : ''}`}
              onClick={() => setTopicFilter(value)}
            >
              {value === 'all' ? 'All topics' : TOPIC_TYPE_LABEL[value]}
            </button>
          ))}
        </div>
        <div className="history-filters__group">
          {(['all', 'pass', 'fail'] as StatusFilter[]).map((value) => (
            <button
              key={value}
              type="button"
              className={`history-filters__tab${statusFilter === value ? ' history-filters__tab--active' : ''}`}
              onClick={() => setStatusFilter(value)}
            >
              {value === 'all' ? 'All results' : STATUS_LABEL[value]}
            </button>
          ))}
        </div>
      </div>

      {loadError && <p className="status-message status-message--error">{loadError}</p>}

      {!loadError && history === null && (
        <div className="content-loading">
          <p className="status-message">Loading your history&hellip;</p>
        </div>
      )}

      {!loadError && history !== null && history.entries.length === 0 && (
        <p className="status-message">No sessions match this filter yet.</p>
      )}

      {!loadError && history !== null && history.entries.length > 0 && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Topic</th>
                <th>Type</th>
                <th>Result</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {history.entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'}</td>
                  <td className="data-table__numeric">{entry.topic}</td>
                  <td>{TOPIC_TYPE_LABEL[entry.topic_type]}</td>
                  <td>
                    <span className={`history-status-pill history-status-pill--${entry.status}`}>
                      {STATUS_LABEL[entry.status]}
                    </span>
                  </td>
                  <td className="data-table__numeric">
                    {entry.confidence !== null ? `${Math.round(entry.confidence * 100)}%` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
