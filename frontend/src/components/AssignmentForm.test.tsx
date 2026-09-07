import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssignmentForm } from './AssignmentForm';

const LETTERS = ['A', 'B', 'C'];
const MOTION_SIGNS = ['Wave', 'Clap'];
const WORD_SIGNS = ['Hello', 'Thanks'];

test('defaults to the letter topic type with its first option selected', () => {
  render(<AssignmentForm letters={LETTERS} motionSigns={MOTION_SIGNS} wordSigns={WORD_SIGNS} onCreate={jest.fn()} />);
  expect(screen.getByRole('combobox', { name: /topic$/i })).toHaveValue('A');
});

test('switching topic type re-populates the topic options for that type', async () => {
  render(<AssignmentForm letters={LETTERS} motionSigns={MOTION_SIGNS} wordSigns={WORD_SIGNS} onCreate={jest.fn()} />);

  await userEvent.selectOptions(screen.getByRole('combobox', { name: /^type$/i }), 'motion_sign');
  expect(screen.getByRole('combobox', { name: /topic$/i })).toHaveValue('Wave');
  // Only the current type's options are rendered — "Hello" (a word sign)
  // has no option element in the DOM at all now, not just an unselected one.
  expect(screen.queryByRole('option', { name: 'Hello' })).not.toBeInTheDocument();
});

test('submits the selected topic, type, and trimmed notes', async () => {
  const onCreate = jest.fn().mockResolvedValue(undefined);
  render(<AssignmentForm letters={LETTERS} motionSigns={MOTION_SIGNS} wordSigns={WORD_SIGNS} onCreate={onCreate} />);

  await userEvent.type(screen.getByPlaceholderText(/focus on hand orientation/i), '  Watch your handshape  ');
  await userEvent.click(screen.getByRole('button', { name: /assign focus/i }));

  await waitFor(() =>
    expect(onCreate).toHaveBeenCalledWith('A', 'letter', {
      notes: 'Watch your handshape',
      dueDate: null,
      referenceMedia: null,
    })
  );
});

test('empty notes are submitted as null, not an empty string', async () => {
  const onCreate = jest.fn().mockResolvedValue(undefined);
  render(<AssignmentForm letters={LETTERS} motionSigns={MOTION_SIGNS} wordSigns={WORD_SIGNS} onCreate={onCreate} />);

  await userEvent.click(screen.getByRole('button', { name: /assign focus/i }));

  await waitFor(() =>
    expect(onCreate).toHaveBeenCalledWith('A', 'letter', { notes: null, dueDate: null, referenceMedia: null })
  );
});

test('rejects an oversized reference file client-side, before ever calling onCreate', async () => {
  const onCreate = jest.fn().mockResolvedValue(undefined);
  render(<AssignmentForm letters={LETTERS} motionSigns={MOTION_SIGNS} wordSigns={WORD_SIGNS} onCreate={onCreate} />);

  const oversized = new File([new ArrayBuffer(21 * 1024 * 1024)], 'big.jpg', { type: 'image/jpeg' });
  const fileInput = screen.getByLabelText(/reference photo\/video/i) as HTMLInputElement;
  await userEvent.upload(fileInput, oversized);

  expect(screen.getByText(/too large/i)).toBeInTheDocument();

  // The oversized file must never actually reach onCreate — submitting
  // right after rejection still goes through with referenceMedia: null,
  // not the file that was bounced.
  await userEvent.click(screen.getByRole('button', { name: /assign focus/i }));
  await waitFor(() =>
    expect(onCreate).toHaveBeenCalledWith('A', 'letter', { notes: null, dueDate: null, referenceMedia: null })
  );
});

test('the notes textarea enforces the same length cap the backend does', () => {
  render(<AssignmentForm letters={LETTERS} motionSigns={MOTION_SIGNS} wordSigns={WORD_SIGNS} onCreate={jest.fn()} />);
  // Mirrors backend/app/services/instructor_assignment_service.MAX_NOTES_LENGTH.
  expect(screen.getByPlaceholderText(/focus on hand orientation/i)).toHaveAttribute('maxLength', '2000');
});
