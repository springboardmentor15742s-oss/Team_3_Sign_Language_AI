import React from 'react';
import { render, screen } from '@testing-library/react';
import { ClassTrendsPanel } from './ClassTrendsPanel';
import { ClassTrendsResponse } from '../types/classTrends';

function makeTrends(overrides: Partial<ClassTrendsResponse> = {}): ClassTrendsResponse {
  return {
    accuracy_trend: [
      { date: '2026-08-18', attempts: 4, scored_attempts: 4, accuracy_percent: 75 },
      { date: '2026-08-19', attempts: 2, scored_attempts: 2, accuracy_percent: 100 },
    ],
    course_completion: [
      {
        course_id: 'alphabet-fundamentals',
        course_title: 'ASL Alphabet Fundamentals',
        learner_count: 4,
        not_started_count: 1,
        in_progress_count: 2,
        completed_count: 1,
        certified_count: 1,
      },
      {
        course_id: 'common-signs',
        course_title: 'Common Signs',
        learner_count: 4,
        not_started_count: 0,
        in_progress_count: 4,
        completed_count: 0,
        // Not a certifiable course — the service reports this as null,
        // not 0, so the panel must not print a "0 certified" badge that
        // would misleadingly imply certification is possible here.
        certified_count: null,
      },
    ],
    ...overrides,
  };
}

test('shows the empty state when there is no scored practice yet', () => {
  render(<ClassTrendsPanel trends={makeTrends({ accuracy_trend: [] })} />);
  expect(screen.getByText(/no scored practice yet/i)).toBeInTheDocument();
});

test('renders one bar per day with its real accuracy percentage', () => {
  render(<ClassTrendsPanel trends={makeTrends()} />);
  expect(screen.getByText('75%')).toBeInTheDocument();
  expect(screen.getByText('100%')).toBeInTheDocument();
  expect(screen.getByText(/last 2 active days/i)).toBeInTheDocument();
});

test('renders a certified badge only for a certifiable course', () => {
  render(<ClassTrendsPanel trends={makeTrends()} />);
  expect(screen.getByText('1 certified')).toBeInTheDocument();
  // Common Signs isn't certifiable (certified_count: null) — no badge for it.
  expect(screen.queryByText('0 certified')).not.toBeInTheDocument();
});

test('shows the empty roster state when no course has any learners', () => {
  const trends = makeTrends({
    course_completion: [
      {
        course_id: 'alphabet-fundamentals',
        course_title: 'ASL Alphabet Fundamentals',
        learner_count: 0,
        not_started_count: 0,
        in_progress_count: 0,
        completed_count: 0,
        certified_count: 0,
      },
    ],
  });
  render(<ClassTrendsPanel trends={trends} />);
  expect(screen.getByText(/no learners in this group yet/i)).toBeInTheDocument();
});
