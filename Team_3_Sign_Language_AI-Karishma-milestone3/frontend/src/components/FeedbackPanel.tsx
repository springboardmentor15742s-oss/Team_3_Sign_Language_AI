import React from 'react';
import { LearnerFeedback } from '../types/analytics';
import './Panel.css';

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
};

export function FeedbackPanel({ feedback }: { feedback: LearnerFeedback }) {
  if (feedback.generated_from_attempts === 0) {
    return (
      <div className="panel feedback-panel">
        <div className="feedback-panel__header">
          <h2 className="panel__title">Your feedback</h2>
          <span className={`adaptive-plan__level adaptive-plan__level--${feedback.learner_level}`}>
            {LEVEL_LABEL[feedback.learner_level]}
          </span>
        </div>
        <p className="panel__empty">{feedback.performance.summary}</p>
      </div>
    );
  }

  return (
    <div className="panel feedback-panel">
      <div className="feedback-panel__header">
        <h2 className="panel__title">Your feedback</h2>
        <span className={`adaptive-plan__level adaptive-plan__level--${feedback.learner_level}`}>
          {LEVEL_LABEL[feedback.learner_level]}
        </span>
      </div>

      <p className="feedback-panel__summary">{feedback.performance.summary}</p>

      {feedback.errors.length > 0 && (
        <div className="feedback-panel__section">
          <h3 className="feedback-panel__section-title">Errors</h3>
          <ul className="feedback-panel__list">
            {feedback.errors.map((err, i) => (
              <li key={`${err.topic_type}-${err.topic}-${i}`}>{err.detail}</li>
            ))}
          </ul>
        </div>
      )}

      {feedback.areas_for_improvement.length > 0 && (
        <div className="feedback-panel__section">
          <h3 className="feedback-panel__section-title">Areas for improvement</h3>
          <ul className="feedback-panel__list">
            {feedback.areas_for_improvement.map((area) => (
              <li key={`${area.topic_type}-${area.topic}`}>
                <strong>{area.topic}</strong>
                {area.accuracy_percent !== null && ` — ${area.accuracy_percent}% accuracy`}
                {area.suggested_activities[0] && (
                  <span className="feedback-panel__activity-hint"> · {area.suggested_activities[0].instruction}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
