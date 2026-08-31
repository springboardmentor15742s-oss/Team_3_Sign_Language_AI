import React from 'react';
import { ConfusionPair } from '../types/analytics';
import './Panel.css';

interface ConfusionPanelProps {
  pairs: ConfusionPair[];
}

// pairs comes from GET /api/learner/{id}/confusion-pairs — grouped/counted
// target-vs-predicted pairs from failed attempts, top 5 by count descending.
export function ConfusionPanel({ pairs }: ConfusionPanelProps) {
  return (
    <div className="panel">
      <h2 className="panel__title">Where it slips</h2>
      {pairs.length === 0 ? (
        <p className="panel__empty">No repeated mix-ups yet.</p>
      ) : (
        <ul className="confusion-list">
          {pairs.map((pair) => (
            <li key={`${pair.target_letter}-${pair.predicted_letter}`} className="confusion-list__item">
              <span className="confusion-list__pair">
                {pair.target_letter} <span className="confusion-list__arrow">&rarr;</span> {pair.predicted_letter}
              </span>
              <span className="confusion-list__count">&times;{pair.count}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
