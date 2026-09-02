import React, { useMemo, useRef, useState } from 'react';
import { AssignmentTopicType } from '../types/instructorAssignment';
import './AssignedFocusPanel.css';

export interface AssignmentFormFields {
  notes: string | null;
  dueDate: string | null;
  referenceMedia: File | null;
}

interface AssignmentFormProps {
  letters: string[];
  motionSigns: string[];
  wordSigns: string[];
  onCreate: (topic: string, topicType: AssignmentTopicType, fields: AssignmentFormFields) => Promise<void>;
}

const TOPIC_TYPE_LABELS: Record<AssignmentTopicType, string> = {
  letter: 'Letter',
  motion_sign: 'Motion sign',
  word_sign: 'Word sign',
};

// Mirrors backend/app/services/media_upload_service.MAX_MEDIA_BYTES — a
// client-side check so a too-large file fails immediately with a clear
// message instead of only after a slow upload hits the server's limit.
const MAX_MEDIA_BYTES = 20 * 1024 * 1024;

export function AssignmentForm({ letters, motionSigns, wordSigns, onCreate }: AssignmentFormProps) {
  const [topicType, setTopicType] = useState<AssignmentTopicType>('letter');
  const [notes, setNotes] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [referenceMedia, setReferenceMedia] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const optionsByType: Record<AssignmentTopicType, string[]> = useMemo(
    () => ({ letter: letters, motion_sign: motionSigns, word_sign: wordSigns }),
    [letters, motionSigns, wordSigns]
  );

  const options = optionsByType[topicType];
  const [topic, setTopic] = useState(options[0] ?? '');

  const handleTopicTypeChange = (nextType: AssignmentTopicType) => {
    setTopicType(nextType);
    setTopic(optionsByType[nextType][0] ?? '');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    if (file && file.size > MAX_MEDIA_BYTES) {
      setError(`That file is too large (${(file.size / 1_000_000).toFixed(1)}MB) — the limit is 20MB.`);
      setReferenceMedia(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setError(null);
    setReferenceMedia(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic) return;
    setSubmitting(true);
    setError(null);
    try {
      await onCreate(topic, topicType, {
        notes: notes.trim() ? notes.trim() : null,
        dueDate: dueDate || null,
        referenceMedia,
      });
      setNotes('');
      setDueDate('');
      setReferenceMedia(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error('Failed to create assignment:', err);
      setError('Could not assign that focus. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="assignment-form" onSubmit={handleSubmit}>
      <label className="assignment-form__field">
        Type
        <select value={topicType} onChange={(e) => handleTopicTypeChange(e.target.value as AssignmentTopicType)}>
          {(Object.keys(TOPIC_TYPE_LABELS) as AssignmentTopicType[]).map((t) => (
            <option key={t} value={t}>
              {TOPIC_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </label>

      <label className="assignment-form__field">
        Topic
        <select value={topic} onChange={(e) => setTopic(e.target.value)} disabled={options.length === 0}>
          {options.length === 0 && <option value="">None available</option>}
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </label>

      <label className="assignment-form__field assignment-form__field--wide">
        Notes / instructions (optional)
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g. focus on hand orientation, not speed"
          rows={2}
        />
      </label>

      <label className="assignment-form__field">
        Due date (optional)
        <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
      </label>

      <label className="assignment-form__field">
        Reference photo/video (optional)
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp,video/mp4,video/webm,video/quicktime"
          onChange={handleFileChange}
        />
      </label>

      <button type="submit" className="btn assignment-form__submit" disabled={submitting || !topic}>
        {submitting ? 'Assigning…' : 'Assign focus'}
      </button>

      {error && <p className="status-message status-message--error">{error}</p>}
    </form>
  );
}
