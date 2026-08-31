import React from 'react';
import { PerformanceForecast } from '../types/progress';
import './Panel.css';

interface ForecastPanelProps {
  forecast: PerformanceForecast;
}

// When there isn't enough real data to project a trend from, this says so
// plainly (forecast.reason) rather than showing a number anyway — same
// null-vs-zero discipline as the rest of the dashboard.
export function ForecastPanel({ forecast }: ForecastPanelProps) {
  return (
    <div className="panel forecast-panel">
      <h2 className="panel__title">Performance forecast</h2>
      {!forecast.available ? (
        <p className="panel__empty">{forecast.reason ?? 'Not enough data yet.'}</p>
      ) : (
        <div className="forecast-grid">
          <div className="forecast-cell">
            <span className="forecast-cell__label">Current level</span>
            <span className="forecast-cell__value">{forecast.current_level}</span>
          </div>
          <div className="forecast-cell">
            <span className="forecast-cell__label">Trending toward</span>
            <span className="forecast-cell__value forecast-cell__value--accent">
              {forecast.predicted_next_level ?? 'Top level reached'}
            </span>
          </div>
          <div className="forecast-cell">
            <span className="forecast-cell__label">Accuracy trend</span>
            <span className="forecast-cell__value">
              {forecast.trend_percent_per_day !== null
                ? `${forecast.trend_percent_per_day > 0 ? '+' : ''}${forecast.trend_percent_per_day}%/day`
                : '—'}
            </span>
          </div>
          <div className="forecast-cell">
            <span className="forecast-cell__label">Est. days to next level</span>
            <span className="forecast-cell__value">
              {forecast.estimated_days_to_next_level ?? '—'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
