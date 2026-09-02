import React, { useMemo, useRef, useState } from 'react';
import { LearnerRosterEntry } from '../types/instructor';
import { AssignmentTopicType } from '../types/instructorAssignment';
import { AssignmentFormFields } from './AssignmentForm';
import './AssignedFocusPanel.css';
import './BulkAssignPanel.css';

interface BulkAssignPanelProps {
  learners: LearnerRosterEntry[];
  letters: string[];
  motionSigns: string[];
  wordSigns: string[];
  onAssign: (learnerIds: string[], topic: string, topicType: AssignmentTopicType, fields: AssignmentFormFields) => Promise<void>;
}

const TOPIC_TYPE_LABELS: Record<AssignmentTopicType, string> = {
  letter: 'Letter',
  motion_sign: 'Motion sign',
  word_sign: 'Word sign',
};

const MAX_MEDIA_BYTES = 20 * 1024 * 1024;

// The roster-page counterpart to AssignmentForm: same topic/notes/due-
// date/media fields, but fans one assignment out to several learners at
// once instead of being scoped to a single learner's page. Deliberately
// a separate component rather than a "multi" mode bolted onto
// AssignmentForm — the learner-selection checklist has no equivalent on
// the single-learner page, and keeping them separate avoids a prop-flag
// branching through the whole form.
export function BulkAssignPanel({ learners, letters, motionSigns, wordSigns, onAssign }: BulkAssignPanelProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [topicType, setTopicType] = useState<AssignmentTopicType>('letter');
  const [notes, setNotes] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [referenceMedia, setReferenceMedia] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
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

  const toggleLearner = (learnerId: string) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(learnerId)) next.delete(learnerId);
      else next.add(learnerId);
      return next;
    });
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
    if (!topic || selectedIds.size === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await onAssign(Array.from(selectedIds), topic, topicType, {
        notes: notes.trim() ? notes.trim() : null,
        dueDate: dueDate || null,
        referenceMedia,
      });
      setSelectedIds(new Set());
      setNotes('');
      setDueDate('');
      setReferenceMedia(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error('Failed to bulk-assign:', err);
      setError('Could not assign that focus to the selected learners. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (learners.length === 0) return null;

  return (
    <div className="panel bulk-assign-panel">
      <button type="button" className="bulk-assign-panel__toggle" onClick={() => setExpanded((v) => !v)}>
        <h2 className="panel__title">Assign to multiple learners{expanded ? '' : ` (${learners.length} on your roster)`}</h2>
        <span className="bulk-assign-panel__chevron">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <form className="bulk-assign-panel__form" onSubmit={handleSubmit}>
          <div className="bulk-assign-panel__learners">
            {learners.map((learner) => (
              <label key={learner.learner_id} className="bulk-assign-panel__learner">
                <input
                  type="checkbox"
                  checked={selectedIds.has(learner.learner_id)}
                  onChange={() => toggleLearner(learner.learner_id)}
                />
                {learner.name}
              </label>
            ))}
          </div>

          <div className="assignment-form">
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
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
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

            <button
              type="submit"
              className="btn assignment-form__submit"
              disabled={submitting || !topic || selectedIds.size === 0}
            >
              {submitting ? 'Assigning…' : `Assign to ${selectedIds.size || ''} learner${selectedIds.size === 1 ? '' : 's'}`}
            </button>
          </div>

          {error && <p className="status-message status-message--error">{error}</p>}
        </form>
      )}
    </div>
  );
}
