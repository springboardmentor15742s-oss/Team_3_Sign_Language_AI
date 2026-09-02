import React from 'react';
import { ClassAnalytics } from '../types/instructor';
import { StatsRow, StatTile } from './StatsRow';
import { AnimatedNumber } from './AnimatedNumber';
import './Panel.css';
import './ClassOverviewPanel.css';

interface ClassOverviewPanelProps {
  analytics: ClassAnalytics;
}

// The one place that aggregates across an instructor's whole roster
// rather than repeating single-learner numbers per row — sits above the
// roster table on Instructor.tsx. See class_analytics_service for the
// aggregation itself; this component only renders what it's given.
export function ClassOverviewPanel({ analytics }: ClassOverviewPanelProps) {
  if (analytics.learner_count === 0) return null;

  return (
    <div className="panel class-overview-panel">
      <h2 className="panel__title">Class overview</h2>

      <StatsRow>
        <StatTile value={<AnimatedNumber value={analytics.learner_count} />} label="Learners" />
        <StatTile
          value={<AnimatedNumber value={analytics.active_learner_count} />}
          label="Have practiced"
        />
        <StatTile
          variant="accent"
          value={
            <>
              {analytics.average_accuracy_percent !== null ? (
                <AnimatedNumber
                  value={analytics.average_accuracy_percent}
                  decimals={Number.isInteger(analytics.average_accuracy_percent) ? 0 : 1}
                />
              ) : (
                '—'
              )}
              {analytics.average_accuracy_percent !== null && <span className="stat-tile__unit">%</span>}
            </>
          }
          label="Avg. class accuracy"
        />
        <StatTile
          variant="warn"
          value={<AnimatedNumber value={analytics.outstanding_assignment_count} />}
          label="Open assignments"
        />
        <StatTile
          value={<AnimatedNumber value={analytics.completed_assignment_count} />}
          label="Completed assignments"
        />
      </StatsRow>

      {analytics.weak_letter_distribution.length > 0 && (
        <div className="class-overview-panel__weak-letters">
          <h3 className="class-overview-panel__subtitle">Most common weak letters across your roster</h3>
          <ul className="class-overview-panel__letters">
            {analytics.weak_letter_distribution.map((entry) => (
              <li key={entry.letter} className="class-overview-panel__letter">
                <span className="class-overview-panel__letter-value">{entry.letter}</span>
                <span className="class-overview-panel__letter-count">
                  {entry.learner_count} learner{entry.learner_count === 1 ? '' : 's'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
