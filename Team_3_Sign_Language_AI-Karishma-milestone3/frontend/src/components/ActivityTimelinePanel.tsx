import React from 'react';
import { RecentActivityItem } from '../types/progress';
import './Panel.css';

interface ActivityTimelinePanelProps {
  activity: RecentActivityItem[];
}

const STATUS_LABEL: Record<RecentActivityItem['status'], string> = {
  pass: 'Correct',
  fail: 'Not quite',
  no_attempt_detected: 'No hand detected',
};

function timeAgo(isoDate: string | null): string {
  if (!isoDate) return '—';
  const then = new Date(isoDate).getTime();
  const diffMs = Date.now() - then;
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// Reflects real logged PracticeAttempt rows — not "lessons completed" or
// "assessments finished", since this platform has no course/lesson data
// model. What actually happened is what's shown.
export function ActivityTimelinePanel({ activity }: ActivityTimelinePanelProps) {
  return (
    <div className="panel">
      <h2 className="panel__title">Recent activity</h2>
      {activity.length === 0 ? (
        <p className="panel__empty">No practice attempts logged yet.</p>
      ) : (
        <ul className="activity-list">
          {activity.map((item, index) => (
            <li key={index} className={`activity-list__item activity-list__item--${item.status}`}>
              <span className="activity-list__dot" />
              <span className="activity-list__text">
                Practiced <strong>{item.letter}</strong> &mdash; {STATUS_LABEL[item.status]}
              </span>
              <span className="activity-list__time">{timeAgo(item.created_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
