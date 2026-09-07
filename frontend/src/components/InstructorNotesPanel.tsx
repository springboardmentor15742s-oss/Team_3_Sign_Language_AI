import React, { useState } from 'react';
import { InstructorNote } from '../types/instructorNote';
import './Panel.css';
import './InstructorNotesPanel.css';

// Mirrors backend/app/schemas/instructor_note.py's MAX_NOTE_LENGTH — a
// client-side cap so typing past the limit is simply not possible, instead
// of only failing with a 422 after "Add note" is clicked.
const MAX_NOTE_LENGTH = 4000;

interface InstructorNotesPanelProps {
  notes: InstructorNote[];
  onAdd: (note: string) => Promise<void>;
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return '';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString();
}

// Instructor-only — deliberately never rendered on the learner's own
// Dashboard.tsx (see InstructorNote's model docstring for the
// visibility contract). Lives on InstructorLearnerDetail.tsx only.
export function InstructorNotesPanel({ notes, onAdd }: InstructorNotesPanelProps) {
  const [draft, setDraft] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await onAdd(draft.trim());
      setDraft('');
    } catch (err) {
      console.error('Failed to add note:', err);
      setError('Could not save that note. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="panel instructor-notes-panel">
      <h2 className="panel__title">Private notes</h2>
      <p className="instructor-notes-panel__hint">Visible to instructors only — never shown to the learner.</p>

      {notes.length === 0 ? (
        <p className="panel__empty">No notes yet.</p>
      ) : (
        <ul className="instructor-notes-panel__list">
          {notes.map((note) => (
            <li key={note.id} className="instructor-notes-panel__item">
              <p className="instructor-notes-panel__text">{note.note}</p>
              <p className="instructor-notes-panel__meta">
                {note.instructor_name ?? 'Instructor'} · {formatTimestamp(note.created_at)}
              </p>
            </li>
          ))}
        </ul>
      )}

      <form className="instructor-notes-panel__form" onSubmit={handleSubmit}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add a note about this learner…"
          rows={2}
          maxLength={MAX_NOTE_LENGTH}
        />
        <button type="submit" className="btn instructor-notes-panel__submit" disabled={submitting || !draft.trim()}>
          {submitting ? 'Saving…' : 'Add note'}
        </button>
      </form>
      {error && <p className="status-message status-message--error">{error}</p>}
    </div>
  );
}
