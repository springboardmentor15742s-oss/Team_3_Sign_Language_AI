import axios from 'axios';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Topbar } from '../components/Topbar';
import { Recommendations, RecommendationItem } from '../types/analytics';
import { PracticeFeedback } from '../types/practice';
import './Practice.css';

interface CaptureError {
  message: string;
  status?: number;
  detail?: unknown;
}

type CameraState = 'idle' | 'requesting' | 'active' | 'denied' | 'no-device' | 'error';

const CAPTURE_WIDTH = 640;

const FALLBACK_RECOMMENDATION: RecommendationItem = {
  letter: 'A',
  reason: 'Could not load a recommendation — starting from A.',
};

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
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraState, setCameraState] = useState<CameraState>('idle');
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [recommendation, setRecommendation] = useState<RecommendationItem | null>(null);
  const [result, setResult] = useState<PracticeFeedback | null>(null);
  const [captureError, setCaptureError] = useState<CaptureError | null>(null);

  const fetchRecommendation = useCallback(async () => {
    if (!user) return;
    try {
      const response = await client.get<Recommendations>(`/api/learner/${user.id}/recommendations`);
      setRecommendation(response.data.recommendations[0] ?? FALLBACK_RECOMMENDATION);
    } catch (err) {
      console.error('Failed to fetch recommendation:', err);
      setRecommendation((current) => current ?? FALLBACK_RECOMMENDATION);
    }
  }, [user]);

  // Load the first target letter as soon as we know who's practicing.
  useEffect(() => {
    fetchRecommendation();
  }, [fetchRecommendation]);

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

  const handleCapture = useCallback(async () => {
    if (!videoRef.current || submitting || !recommendation) return;

    setSubmitting(true);
    setResult(null);
    setCaptureError(null);
    try {
      const blob = await captureFrame(videoRef.current);

      const formData = new FormData();
      formData.append('target_letter', recommendation.letter);
      formData.append('image', blob, 'capture.jpg');

      const response = await client.post<PracticeFeedback>('/api/practice/feedback', formData);
      console.log('gesture recognition response:', response.data);
      setResult(response.data);

      // no_attempt_detected isn't logged, so the recommendation can't have
      // changed — only refetch when an attempt actually landed in the DB.
      if (response.data.status !== 'no_attempt_detected') {
        fetchRecommendation();
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
  }, [submitting, recommendation, fetchRecommendation]);

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
            <button className="camera-state__action" onClick={requestCamera}>
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
            <button className="camera-state__action" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        {cameraState === 'no-device' && (
          <div className="camera-state camera-state--warn">
            <p className="camera-state__text">No camera was found on this device.</p>
            <p className="camera-state__hint">Connect a webcam and try again.</p>
            <button className="camera-state__action" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        {cameraState === 'error' && (
          <div className="camera-state camera-state--warn">
            <p className="camera-state__text">Something went wrong starting the camera.</p>
            {errorDetail && <p className="camera-state__hint">{errorDetail}</p>}
            <button className="camera-state__action" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        <div className="camera-stage">
          <video
            ref={videoRef}
            className={`camera-video${cameraState === 'active' ? ' camera-video--visible' : ''}`}
            autoPlay
            playsInline
            muted
          />

          {cameraState === 'active' && !result && !recommendation && (
            <div className="capture-controls">
              <span className="capture-controls__target">Loading your next letter&hellip;</span>
            </div>
          )}

          {cameraState === 'active' && !result && recommendation && (
            <div className="capture-controls">
              <span className="capture-controls__target">
                Sign the letter <strong>{recommendation.letter}</strong>
              </span>
              <span className="capture-controls__reason">{recommendation.reason}</span>
              <button className="camera-state__action" onClick={handleCapture} disabled={submitting}>
                {submitting ? 'Checking…' : 'Capture'}
              </button>

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
            <div className={`result result--${result.status}`}>
              {result.status === 'pass' && (
                <>
                  <span className="result__badge">Correct</span>
                  <p className="result__feedback">{result.feedback}</p>
                  <p className="result__meta">
                    Confidence: <strong>{Math.round((result.confidence ?? 0) * 100)}%</strong>
                  </p>
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
                </>
              )}

              {result.status === 'no_attempt_detected' && (
                <>
                  <span className="result__badge">No hand detected</span>
                  <p className="result__feedback">{result.feedback}</p>
                </>
              )}

              <div className="result__actions">
                <button className="camera-state__action camera-state__action--ghost" onClick={handleTryAgain}>
                  Try again
                </button>
                <button className="camera-state__action" onClick={handleNextLetter}>
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
