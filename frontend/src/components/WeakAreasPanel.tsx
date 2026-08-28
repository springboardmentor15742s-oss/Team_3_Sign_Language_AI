import React, { useState } from 'react';
import { WeakArea } from '../types/analytics';
import { Assignment } from '../types/instructorAssignment';
import './Panel.css';
import './WeakAreasPanel.css';

interface WeakAreasPanelProps {
  weakAreas: WeakArea[];
  // Used only to grey out letters already assigned, so the instructor
  // never fires off a second identical assignment by accident — reads
  // straight from the same assignments list AssignedFocusPanel shows,
  // not a separate tracked state.
  assignments: Assignment[];
  onAssign: (letter: string) => Promise<void>;
}

// Turns the learner's real weak-area data (accuracy < 70% over >=3 scored
// attempts — see learning_analytics_service.WEAK_AREA_ACCURACY_THRESHOLD)
// into a one-click path to assigning that exact letter as a practice
// focus, instead of the instructor having to find it in the general
// assignment form's dropdown.
export function WeakAreasPanel({ weakAreas, assignments, onAssign }: WeakAreasPanelProps) {
  const [assigningLetter, setAssigningLetter] = useState<string | null>(null);

  const assignedLetters = new Set(
    assignments.filter((a) => a.topic_type === 'letter').map((a) => a.topic)
  );

  const handleAssign = async (letter: string) => {
    setAssigningLetter(letter);
    try {
      await onAssign(letter);
    } finally {
      setAssigningLetter(null);
    }
  };

  return (
    <div className="panel weak-areas-panel">
      <h2 className="panel__title">Weak areas</h2>
      {weakAreas.length === 0 ? (
        <p className="panel__empty">
          No weak areas right now — accuracy is holding up, or there aren&rsquo;t enough scored attempts yet to tell.
        </p>
      ) : (
        <ul className="weak-areas-list">
          {weakAreas.map((area) => {
            const alreadyAssigned = assignedLetters.has(area.letter);
            const isAssigning = assigningLetter === area.letter;
            return (
              <li key={area.letter} className="weak-areas-list__item">
                <span className="weak-areas-list__letter">{area.letter}</span>
                <span className="weak-areas-list__stats">
                  {area.accuracy_percent}% accuracy &middot; {area.scored_attempts} attempt
                  {area.scored_attempts === 1 ? '' : 's'}
                </span>
                <button
                  type="button"
                  className="btn btn--ghost weak-areas-list__assign"
                  onClick={() => handleAssign(area.letter)}
                  disabled={alreadyAssigned || isAssigning}
                >
                  {alreadyAssigned ? 'Assigned' : isAssigning ? 'Assigning…' : 'Assign'}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
