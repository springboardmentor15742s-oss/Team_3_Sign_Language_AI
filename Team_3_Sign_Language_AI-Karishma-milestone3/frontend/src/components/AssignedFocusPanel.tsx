import React from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import { Assignment } from '../types/instructorAssignment';
import './Panel.css';
import './AssignedFocusPanel.css';

// reference_media_url from the backend is a relative /media/... path (see
// instructor_assignment_service.media_url); <img>/<video> tags fetch
// directly rather than through the axios client, so it needs the API's
// origin prepended — reusing the same baseURL the app already talks to
// rather than hardcoding it a second time.
function mediaSrc(relativeUrl: string): string {
  return `${client.defaults.baseURL}${relativeUrl}`;
}

interface AssignedFocusPanelProps {
  assignments: Assignment[];
  // Read-only on the learner's own Dashboard. On the instructor's learner
  // detail page, onRemove is supplied and a remove control is shown.
  onRemove?: (assignmentId: string) => void;
  removingId?: string | null;
  // The instructor's assignment-creation form, rendered inside this same
  // card below the list rather than as a separate bordered box.
  children?: React.ReactNode;
}

// A second, clearly-labeled source alongside PracticeNextPanel's
// auto-generated recommendations — not merged into that ranked list, so
// it's always obvious which suggestions are the instructor's and which
// are the platform's own weak-area/not-yet-tried logic.
function assignmentHref(assignment: Assignment): string {
  switch (assignment.topic_type) {
    case 'motion_sign':
      return `/motion-signs?sign=${assignment.topic}`;
    case 'word_sign':
      return `/conversational-fluency?word=${assignment.topic}`;
    case 'letter':
    default:
      return `/practice?letter=${assignment.topic}`;
  }
}

function topicTypeLabel(topicType: Assignment['topic_type']): string {
  switch (topicType) {
    case 'motion_sign':
      return 'Motion sign';
    case 'word_sign':
      return 'Word sign';
    case 'letter':
    default:
      return 'Letter';
  }
}

export function AssignedFocusPanel({ assignments, onRemove, removingId, children }: AssignedFocusPanelProps) {
  return (
    <div className="panel assigned-focus-panel">
      <h2 className="panel__title">Assigned focus</h2>
      {assignments.length === 0 ? (
        <p className="panel__empty">
          {onRemove ? 'No assignments for this learner yet.' : 'Your instructor hasn’t assigned a practice focus yet.'}
        </p>
      ) : (
        <ul className="assigned-focus-list">
          {assignments.map((assignment) => (
            <li key={assignment.id} className="assigned-focus-list__item">
              <div className="assigned-focus-list__body">
                <Link to={assignmentHref(assignment)} className="assigned-focus-list__link">
                  <span className="assigned-focus-list__topic-type">{topicTypeLabel(assignment.topic_type)}</span>
                  <span className="assigned-focus-list__topic">{assignment.topic}</span>
                  {assignment.instructor_name && (
                    <span className="assigned-focus-list__by">assigned by {assignment.instructor_name}</span>
                  )}
                </Link>
                {assignment.reference_media_url && assignment.reference_media_type === 'image' && (
                  <img
                    src={mediaSrc(assignment.reference_media_url)}
                    alt={`Reference for ${assignment.topic}`}
                    className="assigned-focus-list__media assigned-focus-list__media--image"
                  />
                )}
                {assignment.reference_media_url && assignment.reference_media_type === 'video' && (
                  <video
                    src={mediaSrc(assignment.reference_media_url)}
                    controls
                    className="assigned-focus-list__media assigned-focus-list__media--video"
                  />
                )}
              </div>
              {onRemove && (
                <button
                  type="button"
                  className="assigned-focus-list__remove"
                  onClick={() => onRemove(assignment.id)}
                  disabled={removingId === assignment.id}
                  aria-label={`Remove assignment: ${assignment.topic}`}
                >
                  {removingId === assignment.id ? '…' : '✕'}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {children}
    </div>
  );
}
