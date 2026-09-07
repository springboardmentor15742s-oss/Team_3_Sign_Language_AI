import React from 'react';
import { render, screen } from '@testing-library/react';
import { AchievementsPanel } from './AchievementsPanel';
import { Achievement } from '../types/progress';

function makeAchievement(overrides: Partial<Achievement> = {}): Achievement {
  return {
    id: 'streak',
    label: 'On a Roll',
    description: 'Practice on 3 different days.',
    unlocked: false,
    progress_current: 1,
    progress_target: 3,
    ...overrides,
  };
}

test('shows the empty state when there are no achievements', () => {
  render(<AchievementsPanel achievements={[]} />);
  expect(screen.getByText(/no achievements yet/i)).toBeInTheDocument();
});

test('renders real progress for a locked badge without hiding it', () => {
  render(<AchievementsPanel achievements={[makeAchievement({ unlocked: false, progress_current: 12, progress_target: 28 })]} />);
  expect(screen.getByText('12 / 28')).toBeInTheDocument();
  expect(screen.queryByText('Unlocked')).not.toBeInTheDocument();
});

test('marks an unlocked badge as Unlocked', () => {
  render(
    <AchievementsPanel
      achievements={[makeAchievement({ id: 'century_club', unlocked: true, progress_current: 100, progress_target: 100 })]}
    />
  );
  expect(screen.getByText('Unlocked')).toBeInTheDocument();
  expect(screen.getByText('100 / 100')).toBeInTheDocument();
});

test('formats a fractional progress value to one decimal place', () => {
  render(<AchievementsPanel achievements={[makeAchievement({ progress_current: 2.5, progress_target: 5 })]} />);
  expect(screen.getByText('2.5 / 5')).toBeInTheDocument();
});
