import React from 'react';
import { Achievement } from '../types/progress';
import { AnimatedProgressBar } from './AnimatedProgressBar';
import './Panel.css';

interface AchievementsPanelProps {
  achievements: Achievement[];
}

// Every badge shows its real progress_current/progress_target from the
// backend, whether unlocked or not — never hidden or replaced with a
// vague "locked" state, so a not-yet-earned badge still reads honestly
// as "12/28 letters" rather than looking broken or fake.
export function AchievementsPanel({ achievements }: AchievementsPanelProps) {
  return (
    <div className="panel">
      <h2 className="panel__title">Achievements</h2>
      {achievements.length === 0 ? (
        <p className="panel__empty">No achievements yet.</p>
      ) : (
        <ul className="achievement-list">
          {achievements.map((badge) => {
            const percent =
              badge.progress_target > 0
                ? Math.min(100, Math.round((badge.progress_current / badge.progress_target) * 100))
                : 0;
            return (
              <li
                key={badge.id}
                className={`achievement-item${badge.unlocked ? ' achievement-item--unlocked' : ''}`}
              >
                <div className="achievement-item__header">
                  <span className="achievement-item__label">{badge.label}</span>
                  {badge.unlocked && <span className="achievement-item__badge">Unlocked</span>}
                </div>
                <p className="achievement-item__description">{badge.description}</p>
                <div className="achievement-item__track">
                  <AnimatedProgressBar percent={percent} className="achievement-item__fill" />
                </div>
                <span className="achievement-item__progress">
                  {Number.isInteger(badge.progress_current) ? badge.progress_current : badge.progress_current.toFixed(1)}
                  {' / '}
                  {Number.isInteger(badge.progress_target) ? badge.progress_target : badge.progress_target.toFixed(1)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
