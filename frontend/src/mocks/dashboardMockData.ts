import { ConfusionPair, LearnerAnalytics, LetterStats, Recommendations } from '../types/analytics';

const WEAK_THRESHOLD = 70;
const WEAK_MIN_SCORED = 3;

// [letter, attempts, correct, incorrect, no_attempt]
const RAW_LETTER_DATA: [string, number, number, number, number][] = [
  ['A', 12, 11, 1, 0],
  ['B', 9, 8, 1, 0],
  ['C', 0, 0, 0, 0],
  ['D', 5, 2, 3, 0],
  ['E', 6, 6, 0, 0],
  ['F', 3, 3, 0, 0],
  ['G', 0, 0, 0, 0],
  ['H', 7, 5, 1, 1],
  ['I', 4, 4, 0, 0],
  ['J', 0, 0, 0, 0],
  ['K', 8, 6, 2, 0],
  ['L', 2, 1, 1, 0],
  ['M', 6, 2, 4, 0],
  ['N', 0, 0, 0, 0],
  ['O', 5, 4, 1, 0],
  ['P', 3, 1, 2, 0],
  ['Q', 0, 0, 0, 0],
  ['R', 9, 8, 1, 0],
  ['S', 10, 10, 0, 0],
  ['T', 4, 3, 1, 0],
  ['U', 0, 0, 0, 0],
  ['V', 3, 1, 2, 0],
  ['W', 5, 4, 1, 0],
  ['X', 0, 0, 0, 0],
  ['Y', 6, 5, 1, 0],
  ['Z', 0, 0, 0, 0],
  ['del', 4, 4, 0, 0],
  ['space', 0, 0, 0, 0],
];

function buildPerLetter(): Record<string, LetterStats> {
  const perLetter: Record<string, LetterStats> = {};
  for (const [letter, attempts, correct, incorrect, no_attempt] of RAW_LETTER_DATA) {
    const scored = correct + incorrect;
    perLetter[letter] = {
      attempts,
      correct,
      incorrect,
      no_attempt,
      accuracy_percent: scored > 0 ? Math.round((correct / scored) * 1000) / 10 : null,
    };
  }
  return perLetter;
}

const perLetter = buildPerLetter();

function buildAnalytics(): LearnerAnalytics {
  const entries = Object.entries(perLetter);

  const total_attempts = entries.reduce((sum, [, s]) => sum + s.attempts, 0);
  const correct_count = entries.reduce((sum, [, s]) => sum + s.correct, 0);
  const incorrect_count = entries.reduce((sum, [, s]) => sum + s.incorrect, 0);
  const no_attempt_count = entries.reduce((sum, [, s]) => sum + s.no_attempt, 0);
  const scored_attempts = correct_count + incorrect_count;
  const overall_accuracy_percent =
    scored_attempts > 0 ? Math.round((correct_count / scored_attempts) * 1000) / 10 : null;

  const weak_areas = entries
    .filter(([, s]) => {
      const scored = s.correct + s.incorrect;
      return s.accuracy_percent !== null && s.accuracy_percent < WEAK_THRESHOLD && scored >= WEAK_MIN_SCORED;
    })
    .map(([letter, s]) => ({
      letter,
      accuracy_percent: s.accuracy_percent as number,
      scored_attempts: s.correct + s.incorrect,
    }))
    .sort((a, b) => a.accuracy_percent - b.accuracy_percent);

  const byAttempts = [...entries].sort((a, b) => b[1].attempts - a[1].attempts);
  const most_practiced_letters = byAttempts.slice(0, 5).map(([letter, s]) => ({ letter, attempts: s.attempts }));
  const least_practiced_letters = byAttempts
    .slice(-5)
    .reverse()
    .map(([letter, s]) => ({ letter, attempts: s.attempts }));

  return {
    learner_id: 'mock-learner',
    total_attempts,
    correct_count,
    incorrect_count,
    no_attempt_count,
    scored_attempts,
    overall_accuracy_percent,
    accuracy_trend: [
      { date: '2026-08-08', attempts: 34, scored_attempts: 30, correct: 20, accuracy_percent: 66.7 },
      { date: '2026-08-09', attempts: 41, scored_attempts: 38, correct: 29, accuracy_percent: 76.3 },
      { date: '2026-08-10', attempts: 36, scored_attempts: 33, correct: 27, accuracy_percent: 81.8 },
    ],
    per_letter: perLetter,
    most_practiced_letters,
    least_practiced_letters,
    weak_areas,
  };
}

export const mockAnalytics: LearnerAnalytics = buildAnalytics();

export const mockRecommendations: Recommendations = {
  learner_id: 'mock-learner',
  recommendations: [
    { letter: 'M', reason: 'weak area — 33.3% accuracy over 6 attempts' },
    { letter: 'D', reason: 'weak area — 40.0% accuracy over 5 attempts' },
    { letter: 'P', reason: 'weak area — 33.3% accuracy over 3 attempts' },
    { letter: 'V', reason: 'weak area — 33.3% accuracy over 3 attempts' },
    { letter: 'C', reason: 'not yet practiced' },
  ],
};

// No backend endpoint returns per-attempt target/predicted pairs yet —
// this shape is what ConfusionPanel expects once that endpoint exists.
export const mockConfusionPairs: ConfusionPair[] = [
  { target_letter: 'M', predicted_letter: 'N', count: 4 },
  { target_letter: 'D', predicted_letter: 'O', count: 3 },
  { target_letter: 'P', predicted_letter: 'B', count: 2 },
  { target_letter: 'V', predicted_letter: 'W', count: 2 },
  { target_letter: 'K', predicted_letter: 'R', count: 2 },
];
