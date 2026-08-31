import axios from 'axios';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Topbar } from '../components/Topbar';
import { HandLandmarkOverlay } from '../components/HandLandmarkOverlay';
import { LearnerAnalytics, Recommendations, RecommendationItem } from '../types/analytics';
import { PracticeFeedback } from '../types/practice';
import './Practice.css';

interface CaptureError {
  message: string;
  status?: number;
  detail?: unknown;
}

type CameraState = 'idle' | 'requesting' | 'active' | 'denied' | 'no-device' | 'error';

const CAPTURE_WIDTH = 640;
const COUNTDOWN_START = 3;
const COUNTDOWN_TICK_MS = 1000;

const EXPLICIT_REASON = 'Chosen from your dashboard';

const FALLBACK_RECOMMENDATION: RecommendationItem = {
  topic: 'A',
  topic_type: 'letter',
  reason: 'Could not load a recommendation — starting from A.',
};

interface AccuracySnapshot {
  letter: string;
  accuracy: number | null;
}

function ConfidenceMeter({ value, variant }: { value: number; variant: 'pass' | 'fail' }) {
  const percent = Math.round(value * 100);
  return (
    <div className="confidence-meter">
      <div className="confidence-meter__track">
        <div
          className={`confidence-meter__fill confidence-meter__fill--${variant}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="confidence-meter__value">{percent}%</span>
    </div>
  );
}

// Draws the current video frame to an off-DOM canvas, downscaled to
// CAPTURE_WIDTH wide (aspect ratio preserved), and exports it as a JPEG
// blob. Deliberately does NOT apply the CSS mirror — that's display-only,
// and the model was trained on unmirrored images, so the captured frame
// must match what the camera actually saw.
function captureFrame(video: HTMLVideoElement): Promise<Blob> {
  const scale = CAPTURE_WIDTH / video.videoWidth;
  const width = CAPTURE_WIDTH;
  const height = Math.round(video.videoHeight * scale);

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return Promise.reject(new Error('Could not get canvas context'));
  }
  ctx.drawImage(video, 0, 0, width, height);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('Failed to encode capture as JPEG'))),
      'image/jpeg',
      0.8
    );
  });
}

export function Practice() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const explicitLetter = searchParams.get('letter');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraState, setCameraState] = useState<CameraState>('idle');
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [recommendation, setRecommendation] = useState<RecommendationItem | null>(null);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [result, setResult] = useState<PracticeFeedback | null>(null);
  const [captureError, setCaptureError] = useState<CaptureError | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [beforeAccuracy, setBeforeAccuracy] = useState<AccuracySnapshot | null>(null);
  const [afterAccuracy, setAfterAccuracy] = useState<AccuracySnapshot | null>(null);
  const [capturedImageUrl, setCapturedImageUrl] = useState<string | null>(null);
  // Display-only — never read by captureFrame, which always draws from the
  // video element's intrinsic pixels, not its rendered/CSS-transformed box.
  const [zoomed, setZoomed] = useState(false);
  const practiceStartedAt = useRef<number>(Date.now());

  // Revokes the previous object URL whenever it's replaced, and the final
  // one on unmount — capturedImageUrl is only ever used for the landmark
  // overlay below, never persisted past the component's lifetime.
  useEffect(() => {
    return () => {
      if (capturedImageUrl) URL.revokeObjectURL(capturedImageUrl);
    };
  }, [capturedImageUrl]);

  const fetchLetterAccuracy = useCallback(
    async (letter: string): Promise<number | null> => {
      if (!user) return null;
      try {
        const response = await client.get<LearnerAnalytics>(`/api/learner/${user.id}/analytics`);
        return response.data.per_letter[letter]?.accuracy_percent ?? null;
      } catch (err) {
        console.error('Failed to fetch letter accuracy:', err);
        return null;
      }
    },
    [user]
  );

  const fetchRecommendation = useCallback(async () => {
    if (!user) return;
    try {
      const response = await client.get<Recommendations>(`/api/learner/${user.id}/recommendations?topic_type=letter`);
      setRecommendation(response.data.recommendations[0] ?? FALLBACK_RECOMMENDATION);
      setRecommendationError(null);
    } catch (err) {
      console.error('Failed to fetch recommendation:', err);
      // Degrade gracefully rather than block practice entirely — capture
      // still works against the fallback letter — but say so visibly
      // instead of silently substituting it.
      setRecommendationError('Could not load your personalized recommendation — using a default letter.');
      setRecommendation((current) => current ?? FALLBACK_RECOMMENDATION);
    }
  }, [user]);

  // Load the first target letter as soon as we know who's practicing —
  // honour an explicit ?letter= from the dashboard instead of asking the
  // recommendation endpoint. Once this attempt is logged, performCapture's
  // post-capture refetch naturally replaces this with a real, algorithm
  // -driven pick for whatever comes next.
  useEffect(() => {
    if (explicitLetter) {
      setRecommendation({ topic: explicitLetter, topic_type: 'letter', reason: EXPLICIT_REASON });
      return;
    }
    fetchRecommendation();
  }, [explicitLetter, fetchRecommendation]);

  // Snapshots this letter's accuracy right before each capture opportunity
  // (initial load, and again after Try Again / Next Letter clear the prior
  // result) so the result card can show the before -> after change once
  // this attempt is logged, without a second round trip at display time.
  useEffect(() => {
    if (result || !recommendation) return;
    const letter = recommendation.topic;
    let cancelled = false;
    fetchLetterAccuracy(letter).then((accuracy) => {
      if (!cancelled) setBeforeAccuracy({ letter, accuracy });
    });
    return () => {
      cancelled = true;
    };
  }, [result, recommendation, fetchLetterAccuracy]);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const requestCamera = useCallback(async () => {
    setCameraState('requesting');
    setErrorDetail(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraState('active');
    } catch (err) {
      const name = err instanceof DOMException ? err.name : '';
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError' || name === 'SecurityError') {
        setCameraState('denied');
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        setCameraState('no-device');
      } else {
        setCameraState('error');
        setErrorDetail(err instanceof Error ? err.message : 'Unknown error');
      }
    }
  }, []);

  // Stop tracks on unmount so the camera light turns off when navigating away.
  useEffect(() => {
    return () => stopStream();
  }, [stopStream]);

  // The actual frame-grab + POST — runs once the countdown reaches zero,
  // not directly on trigger (see triggerCapture below).
  const performCapture = useCallback(async () => {
    if (!videoRef.current || submitting || !recommendation) return;

    setSubmitting(true);
    setResult(null);
    setCaptureError(null);
    try {
      const blob = await captureFrame(videoRef.current);
      setCapturedImageUrl(URL.createObjectURL(blob));

      const formData = new FormData();
      formData.append('target_letter', recommendation.topic);
      formData.append('practice_seconds', String(Math.round((Date.now() - practiceStartedAt.current) / 1000)));
      formData.append('image', blob, 'capture.jpg');

      const response = await client.post<PracticeFeedback>('/api/practice/feedback', formData);
      console.log('gesture recognition response:', response.data);
      setResult(response.data);

      // no_attempt_detected isn't logged, so the recommendation — and this
      // letter's accuracy — can't have changed; only refetch when an
      // attempt actually landed in the DB.
      if (response.data.status !== 'no_attempt_detected') {
        practiceStartedAt.current = Date.now();
        fetchRecommendation();
        const capturedLetter = response.data.target_letter;
        fetchLetterAccuracy(capturedLetter).then((accuracy) => {
          setAfterAccuracy({ letter: capturedLetter, accuracy });
        });
      }
    } catch (err) {
      console.error('Capture/send failed:', err);
      if (axios.isAxiosError(err)) {
        if (err.response) {
          // Server responded with a non-2xx status (e.g. 401, 400, 500).
          setCaptureError({
            message: `Request failed with status ${err.response.status}`,
            status: err.response.status,
            detail: err.response.data,
          });
        } else if (err.request) {
          // Request was sent but no response ever came back — network
          // failure, CORS block, or the configured timeout was hit.
          setCaptureError({
            message:
              err.code === 'ECONNABORTED'
                ? 'Request timed out — the server did not respond in time.'
                : 'No response received from the server (network error or CORS block).',
          });
        } else {
          setCaptureError({ message: err.message });
        }
      } else {
        setCaptureError({ message: err instanceof Error ? err.message : 'Unknown error' });
      }
    } finally {
      setSubmitting(false);
    }
  }, [submitting, recommendation, fetchRecommendation, fetchLetterAccuracy]);

  // Starts the 3-2-1 countdown; the actual capture fires when it elapses.
  // Guarded the same way for both the button click and the spacebar
  // shortcut, so neither can double-trigger or interrupt an in-progress
  // countdown/submission.
  const triggerCapture = useCallback(() => {
    if (submitting || !recommendation || result || countdown !== null) return;
    setCountdown(COUNTDOWN_START);
  }, [submitting, recommendation, result, countdown]);

  useEffect(() => {
    if (countdown === null) return;

    const timer = setTimeout(() => {
      if (countdown <= 1) {
        setCountdown(null);
        performCapture();
      } else {
        setCountdown(countdown - 1);
      }
    }, COUNTDOWN_TICK_MS);

    return () => clearTimeout(timer);
  }, [countdown, performCapture]);

  // Spacebar triggers capture too — signing one-handed while clicking with
  // the other is awkward. preventDefault only when we're actually going to
  // act on it, so Space still behaves normally (e.g. activating a focused
  // "Try again" button) in every other state.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.code !== 'Space') return;
      if (cameraState !== 'active' || result || !recommendation || submitting || countdown !== null) return;
      event.preventDefault();
      triggerCapture();
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cameraState, result, recommendation, submitting, countdown, triggerCapture]);

  const handleTryAgain = useCallback(() => {
    setResult(null);
    setCaptureError(null);
  }, []);

  const handleNextLetter = useCallback(() => {
    // recommendation is already fresh (refetched right after the last
    // logged attempt) — this may legitimately show the same letter again
    // if it's still the top-priority pick.
    setResult(null);
    setCaptureError(null);
  }, []);

  return (
    <div className="page practice">
      <Topbar title="Practice" />

      <section className="camera-panel">
        {cameraState === 'idle' && (
          <div className="camera-state">
            <p className="camera-state__text">
              Practice sessions use your camera to check your hand shape against the target letter.
            </p>
            <button className="btn" onClick={requestCamera}>
              Turn on camera
            </button>
          </div>
        )}

        {cameraState === 'requesting' && (
          <div className="camera-state">
            <p className="camera-state__text">Requesting camera access&hellip;</p>
          </div>
        )}

        {cameraState === 'denied' && (
          <div className="camera-state camera-state--warn">
            <p className="camera-state__text">
              Camera access was denied. This practice view needs your camera to check your signing.
            </p>
            <p className="camera-state__hint">
              Click the camera icon in your browser's address bar, allow access, then try again.
            </p>
            <button className="btn" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        {cameraState === 'no-device' && (
          <div className="camera-state camera-state--warn">
            <p className="camera-state__text">No camera was found on this device.</p>
            <p className="camera-state__hint">Connect a webcam and try again.</p>
            <button className="btn" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        {cameraState === 'error' && (
          <div className="camera-state camera-state--warn">
            <p className="camera-state__text">Something went wrong starting the camera.</p>
            {errorDetail && <p className="camera-state__hint">{errorDetail}</p>}
            <button className="btn" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        <div className="camera-stage">
          <div className="camera-video-wrap">
            <video
              ref={videoRef}
              className={`camera-video${cameraState === 'active' ? ' camera-video--visible' : ''}${zoomed ? ' camera-video--zoomed' : ''}`}
              autoPlay
              playsInline
              muted
            />
            {countdown !== null && (
              <div className="countdown-badge" aria-live="assertive">
                {countdown}
              </div>
            )}
            {cameraState === 'active' && !result && countdown === null && (
              <div className="live-indicator">
                <span className="live-indicator__dot" />
                LIVE
              </div>
            )}
          </div>

          {cameraState === 'active' && (
            <button type="button" className="btn btn--ghost" onClick={() => setZoomed((current) => !current)}>
              {zoomed ? 'Normal view' : 'Zoom to hand'}
            </button>
          )}

          {cameraState === 'active' && !result && !recommendation && (
            <div className="capture-controls">
              <span className="capture-controls__target">Loading your next letter&hellip;</span>
            </div>
          )}

          {cameraState === 'active' && !result && recommendation && (
            <div className="capture-controls">
              <span className="capture-controls__target">
                Sign the letter <strong>{recommendation.topic}</strong>
              </span>
              <span className="capture-controls__reason">{recommendation.reason}</span>

              {recommendationError && (
                <p className="status-message status-message--error">{recommendationError}</p>
              )}

              <button
                className="btn"
                onClick={triggerCapture}
                disabled={submitting || countdown !== null}
              >
                {submitting ? 'Checking…' : countdown !== null ? `Capturing in ${countdown}…` : 'Capture'}
              </button>

              <p className="capture-controls__hint">
                or press <kbd>Space</kbd> to capture
              </p>

              {captureError && (
                <pre className="debug-output debug-output--error">
                  {`Error: ${captureError.message}` +
                    (captureError.status ? ` (HTTP ${captureError.status})` : '') +
                    (captureError.detail ? `\n\n${JSON.stringify(captureError.detail, null, 2)}` : '')}
                </pre>
              )}
            </div>
          )}

          {cameraState === 'active' && result && (
            <div key={result.attempt_id ?? `${result.status}-${result.target_letter}`} className={`result result--${result.status}`}>
              {result.status === 'pass' && (
                <>
                  <span className="result__badge">Correct</span>
                  <p className="result__feedback">{result.feedback}</p>
                  {result.confidence !== null && <ConfidenceMeter value={result.confidence} variant="pass" />}
                </>
              )}

              {result.status === 'fail' && (
                <>
                  <span className="result__badge">Not quite</span>
                  <p className="result__feedback">{result.feedback}</p>
                  <p className="result__meta">
                    Target: <strong>{result.target_letter}</strong> &middot; You signed:{' '}
                    <strong>{result.predicted_letter ?? '—'}</strong>
                  </p>
                  {result.confidence !== null && <ConfidenceMeter value={result.confidence} variant="fail" />}
                </>
              )}

              {result.status === 'no_attempt_detected' && (
                <>
                  <span className="result__badge">No hand detected</span>
                  <p className="result__feedback">{result.feedback}</p>
                </>
              )}

              {(result.status === 'pass' || result.status === 'fail') &&
                capturedImageUrl &&
                result.landmarks &&
                result.landmarks.length === 21 && (
                  <HandLandmarkOverlay
                    imageUrl={capturedImageUrl}
                    landmarks={result.landmarks}
                    variant={result.status === 'pass' ? 'pass' : 'fail'}
                  />
                )}

              {(result.status === 'pass' || result.status === 'fail') &&
                beforeAccuracy?.letter === result.target_letter &&
                afterAccuracy?.letter === result.target_letter && (
                  <p className="result__progress">
                    {result.target_letter}:{' '}
                    <strong>{beforeAccuracy.accuracy !== null ? `${beforeAccuracy.accuracy}%` : '—'}</strong>
                    {' → '}
                    <strong>{afterAccuracy.accuracy !== null ? `${afterAccuracy.accuracy}%` : '—'}</strong>
                  </p>
                )}

              <div className="result__actions">
                <button className="btn btn--ghost" onClick={handleTryAgain}>
                  Try again
                </button>
                <button className="btn" onClick={handleNextLetter}>
                  Next letter
                </button>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
