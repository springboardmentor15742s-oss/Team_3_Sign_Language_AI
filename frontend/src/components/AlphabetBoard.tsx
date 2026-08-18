import React from 'react';
import { LetterStats } from '../types/analytics';
import './AlphabetBoard.css';

const WEAK_THRESHOLD = 70;
const WEAK_MIN_SCORED = 3;

interface AlphabetBoardProps {
  perLetter: Record<string, LetterStats>;
}

export function AlphabetBoard({ perLetter }: AlphabetBoardProps) {
  const letters = Object.keys(perLetter);

  return (
    <div className="alphabet-board">
      {letters.map((letter) => {
        const stats = perLetter[letter];
        const untried = stats.accuracy_percent === null;
        const scored = stats.correct + stats.incorrect;
        const isWeak = !untried && (stats.accuracy_percent as number) < WEAK_THRESHOLD && scored >= WEAK_MIN_SCORED;

        const tooltip = untried
          ? 'Not yet attempted'
          : `${stats.accuracy_percent}% accuracy · ${stats.attempts} attempt${stats.attempts === 1 ? '' : 's'}`;

        return (
          <div
            key={letter}
            className={`board-cell${untried ? ' board-cell--untried' : ''}${isWeak ? ' board-cell--weak' : ''}`}
          >
            {!untried && (
              <div className="board-cell__fill" style={{ height: `${stats.accuracy_percent}%` }} />
            )}
            <span className="board-cell__letter">{letter}</span>
            <div className="board-cell__tooltip">{tooltip}</div>
          </div>
        );
      })}
    </div>
  );
}
