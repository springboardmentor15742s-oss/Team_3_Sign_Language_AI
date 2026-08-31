import React from 'react';
import { Link } from 'react-router-dom';
import { AdaptiveLearningPlan, AdaptiveRecommendation } from '../types/analytics';
import './Panel.css';

function practiceHref(rec: AdaptiveRecommendation): string {
  return rec.topic_type === 'motion_sign'
    ? `/motion-signs?sign=${rec.topic}`
    : `/practice?letter=${rec.topic}`;
}

export function AdaptiveLearningPanel({ plan }: { plan: AdaptiveLearningPlan }) {
  const primary = plan.recommendations[0];
  if (!primary) return null;

  return (
    <section className="panel adaptive-plan">
      <div className="adaptive-plan__header">
        <div>
          <h2 className="panel__title">Your adaptive learning plan</h2>
          <p className="adaptive-plan__summary">{plan.profile_summary}</p>
          <p className="adaptive-plan__summary">{plan.activity_days} active day{plan.activity_days === 1 ? '' : 's'} · {plan.time_spent_minutes} minutes practised</p>
        </div>
        <span className={`adaptive-plan__level adaptive-plan__level--${plan.learning_level}`}>
          {plan.learning_level}
        </span>
      </div>

      <p className="adaptive-plan__focus">
        Focus #{primary.priority}: <strong>{primary.topic}</strong> — {primary.reason}
      </p>
      <ol className="adaptive-plan__activities">
        {primary.activities.map((activity, index) => (
          <li key={`${activity.type}-${index}`}>
            <span className="adaptive-plan__activity-type">{activity.type}</span>
            <span>{activity.instruction}</span>
          </li>
        ))}
      </ol>

      <p className="adaptive-plan__next">{plan.next_assessment}</p>
      <Link className="btn" to={practiceHref(primary)}>
        Start {primary.topic} practice
      </Link>
    </section>
  );
}
