import React from 'react';
import { Link } from 'react-router-dom';
import { RecommendationItem } from '../types/analytics';
import './Panel.css';

interface PracticeNextPanelProps {
  recommendations: RecommendationItem[];
}

function practiceHref(rec: RecommendationItem): string {
  return rec.topic_type === 'motion_sign'
    ? `/motion-signs?sign=${rec.topic}`
    : `/practice?letter=${rec.topic}`;
}

export function PracticeNextPanel({ recommendations }: PracticeNextPanelProps) {
  return (
    <div className="panel">
      <h2 className="panel__title">Practice next</h2>
      <ol className="rank-list">
        {recommendations.map((rec, i) => (
          <li key={`${rec.topic_type}-${rec.topic}`}>
            <Link to={practiceHref(rec)} className="rank-list__item">
              <span className="rank-list__rank">{i + 1}</span>
              <span className="rank-list__letter">{rec.topic}</span>
              <span className="rank-list__reason">{rec.reason}</span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}
