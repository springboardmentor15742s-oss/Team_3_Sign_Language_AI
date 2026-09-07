import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InstructorNotesPanel } from './InstructorNotesPanel';
import { InstructorNote } from '../types/instructorNote';

function makeNote(overrides: Partial<InstructorNote> = {}): InstructorNote {
  return {
    id: 'note-1',
    learner_id: 'learner-1',
    instructor_id: 'instructor-1',
    instructor_name: 'Ms. Rivera',
    note: 'Doing well with fingerspelling.',
    created_at: '2026-08-01T12:00:00Z',
    ...overrides,
  };
}

test('shows the empty state when there are no notes', () => {
  render(<InstructorNotesPanel notes={[]} onAdd={jest.fn()} />);
  expect(screen.getByText(/no notes yet/i)).toBeInTheDocument();
});

test('lists existing notes with their author', () => {
  render(<InstructorNotesPanel notes={[makeNote()]} onAdd={jest.fn()} />);
  expect(screen.getByText('Doing well with fingerspelling.')).toBeInTheDocument();
  expect(screen.getByText(/Ms\. Rivera/)).toBeInTheDocument();
});

test('the submit button stays disabled until there is real (non-whitespace) text', async () => {
  render(<InstructorNotesPanel notes={[]} onAdd={jest.fn()} />);
  const submit = screen.getByRole('button', { name: /add note/i });
  expect(submit).toBeDisabled();

  await userEvent.type(screen.getByPlaceholderText(/add a note/i), '   ');
  expect(submit).toBeDisabled();

  await userEvent.type(screen.getByPlaceholderText(/add a note/i), 'Great progress today');
  expect(submit).toBeEnabled();
});

test('submitting calls onAdd with the trimmed note and clears the draft', async () => {
  const onAdd = jest.fn().mockResolvedValue(undefined);
  render(<InstructorNotesPanel notes={[]} onAdd={onAdd} />);

  const textarea = screen.getByPlaceholderText(/add a note/i);
  await userEvent.type(textarea, '  Needs more practice with motion signs  ');
  await userEvent.click(screen.getByRole('button', { name: /add note/i }));

  expect(onAdd).toHaveBeenCalledWith('Needs more practice with motion signs');
  await waitFor(() => expect(textarea).toHaveValue(''));
});

test('shows an error message and keeps the draft when saving fails', async () => {
  const onAdd = jest.fn().mockRejectedValue(new Error('network down'));
  render(<InstructorNotesPanel notes={[]} onAdd={onAdd} />);

  const textarea = screen.getByPlaceholderText(/add a note/i);
  await userEvent.type(textarea, 'This will fail to save');
  await userEvent.click(screen.getByRole('button', { name: /add note/i }));

  expect(await screen.findByText(/could not save that note/i)).toBeInTheDocument();
  expect(textarea).toHaveValue('This will fail to save');
});

test('the textarea enforces the same length cap the backend does', () => {
  render(<InstructorNotesPanel notes={[]} onAdd={jest.fn()} />);
  const textarea = screen.getByPlaceholderText(/add a note/i);
  // Mirrors backend/app/schemas/instructor_note.py's MAX_NOTE_LENGTH.
  expect(textarea).toHaveAttribute('maxLength', '4000');
});
