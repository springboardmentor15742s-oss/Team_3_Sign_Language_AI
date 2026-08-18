import React from 'react';
import { Link } from 'react-router-dom';
import { RecommendationItem } from '../types/analytics';
import './Panel.css';

interface PracticeNextPanelProps {
  recommendations: RecommendationItem[];
}

export function PracticeNextPanel({ recommendations }: PracticeNextPanelProps) {
  return (
    <div className="panel">
      <h2 className="panel__title">Practice next</h2>
      <ol className="rank-list">
        {recommendations.map((rec, i) => (
          <li key={rec.letter}>
            <Link to={`/practice?letter=${rec.letter}`} className="rank-list__item">
              <span className="rank-list__rank">{i + 1}</span>
              <span className="rank-list__letter">{rec.letter}</span>
              <span className="rank-list__reason">{rec.reason}</span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}
