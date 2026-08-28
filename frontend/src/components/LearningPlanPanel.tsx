import React from 'react';
import { Link } from 'react-router-dom';
import { LearningPlan } from '../types/analytics';
import './Panel.css';

export function LearningPlanPanel({ plan }: { plan: LearningPlan }) {
  const { summary, practice_session, motivational_note } = plan;
  const hasSession = practice_session.letters.length > 0;

  return (
    <section className="panel learning-plan-panel">
      <h2 className="panel__title">Your personalized learning plan</h2>
      <p className="learning-plan-panel__note">{motivational_note}</p>

      {(summary.strongest_area || summary.weakest_area) && (
        <p className="learning-plan-panel__summary">
          {summary.strongest_area && (
            <>
              Strongest: <strong>{summary.strongest_area.letter}</strong> ({summary.strongest_area.accuracy_percent}%)
            </>
          )}
          {summary.strongest_area && summary.weakest_area && ' · '}
          {summary.weakest_area && (
            <>
              Needs work: <strong>{summary.weakest_area.letter}</strong> ({summary.weakest_area.accuracy_percent}%)
            </>
          )}
        </p>
      )}

      {hasSession ? (
        <ol className="learning-plan-panel__session">
          {practice_session.letters.map((item) => (
            <li key={`${item.order}-${item.letter}`}>
              <span className="learning-plan-panel__letter">{item.letter}</span>
              <span className="learning-plan-panel__reason">
                {item.reason} · {item.target_attempts} attempts
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="panel__empty">No practice session to show yet — keep practicing to build one up.</p>
      )}

      {hasSession && (
        <Link className="btn" to={`/practice?letter=${practice_session.letters[0].letter}`}>
          Start your next session
        </Link>
      )}
    </section>
  );
}
