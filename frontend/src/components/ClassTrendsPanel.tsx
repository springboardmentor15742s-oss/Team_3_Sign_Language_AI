import React from 'react';
import { ClassTrendsResponse } from '../types/classTrends';
import './Panel.css';
import './ClassTrendsPanel.css';

interface ClassTrendsPanelProps {
  trends: ClassTrendsResponse;
}

// The one thing ClassOverviewPanel's snapshot numbers and the reporting
// module's PDFs don't show: how the roster/platform is trending over
// time, and how learners are actually distributed across each course
// (not started / in progress / completed / certified) rather than a
// single averaged number. See class_trends_service.py for why the
// accuracy trend is alphabet-scoped (same as every other "accuracy"
// figure already shown elsewhere in this app) and why completed vs.
// certified are reported separately rather than collapsed into one.
export function ClassTrendsPanel({ trends }: ClassTrendsPanelProps) {
  const { accuracy_trend: accuracyTrend, course_completion: courseCompletion } = trends;
  const maxAttempts = Math.max(1, ...accuracyTrend.map((p) => p.attempts));

  return (
    <div className="panel class-trends-panel">
      <h2 className="panel__title">Trends over time</h2>

      {accuracyTrend.length === 0 ? (
        <p className="panel__empty">No scored practice yet — a trend needs at least one day of real attempts.</p>
      ) : (
        <>
          <p className="class-trends-panel__caption">
            Daily practice volume and accuracy across everyone in scope, last {accuracyTrend.length} active day
            {accuracyTrend.length === 1 ? '' : 's'}.
          </p>
          <div className="class-trends-panel__chart">
            {accuracyTrend.map((point) => (
              <div key={point.date} className="class-trends-panel__bar-column">
                <span className="class-trends-panel__bar-value">
                  {point.accuracy_percent === null ? '—' : `${point.accuracy_percent}%`}
                </span>
                <i
                  className="class-trends-panel__bar"
                  style={{ height: `${(point.attempts / maxAttempts) * 140}px` }}
                  title={`${point.attempts} attempts, ${point.scored_attempts} scored`}
                />
                <small className="class-trends-panel__bar-label">{point.date.slice(5)}</small>
              </div>
            ))}
          </div>
        </>
      )}

      <h3 className="class-trends-panel__subtitle">Course completion</h3>
      {courseCompletion.every((c) => c.learner_count === 0) ? (
        <p className="panel__empty">No learners in this group yet.</p>
      ) : (
        <ul className="class-trends-panel__course-list">
          {courseCompletion.map((course) => {
            const total = course.learner_count || 1;
            return (
              <li key={course.course_id} className="class-trends-panel__course-item">
                <div className="class-trends-panel__course-header">
                  <span>{course.course_title}</span>
                  {course.certified_count !== null && (
                    <span className="class-trends-panel__certified-badge">{course.certified_count} certified</span>
                  )}
                </div>
                <div className="class-trends-panel__stacked-bar">
                  <i
                    className="class-trends-panel__segment class-trends-panel__segment--completed"
                    style={{ width: `${(course.completed_count / total) * 100}%` }}
                    title={`${course.completed_count} completed`}
                  />
                  <i
                    className="class-trends-panel__segment class-trends-panel__segment--in-progress"
                    style={{ width: `${(course.in_progress_count / total) * 100}%` }}
                    title={`${course.in_progress_count} in progress`}
                  />
                  <i
                    className="class-trends-panel__segment class-trends-panel__segment--not-started"
                    style={{ width: `${(course.not_started_count / total) * 100}%` }}
                    title={`${course.not_started_count} not started`}
                  />
                </div>
                <div className="class-trends-panel__course-counts">
                  <span><i className="class-trends-panel__dot class-trends-panel__dot--completed" />{course.completed_count} completed</span>
                  <span><i className="class-trends-panel__dot class-trends-panel__dot--in-progress" />{course.in_progress_count} in progress</span>
                  <span><i className="class-trends-panel__dot class-trends-panel__dot--not-started" />{course.not_started_count} not started</span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
