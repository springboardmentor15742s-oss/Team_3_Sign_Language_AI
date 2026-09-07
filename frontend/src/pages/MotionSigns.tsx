import axios from 'axios';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import client from '../api/client';
import { Topbar } from '../components/Topbar';
import { MotionSignFeedback, MotionSignRecognizeResult, SupportedMotionSigns } from '../types/motionSigns';
import './Practice.css';
import './MotionSigns.css';

interface CaptureError {
  message: string;
  status?: number;
}

type CameraState = 'idle' | 'requesting' | 'active' | 'denied' | 'no-device' | 'error';

const CAPTURE_WIDTH = 480;
const COUNTDOWN_START = 3;
const COUNTDOWN_TICK_MS = 1000;
// A wave or clap needs roughly a second or two to actually happen —
// these bounds match motion_signs.py's MIN_FRAMES/MAX_FRAMES on the
// backend, which rejects a sequence outside [5, 90] frames.
const RECORDING_DURATION_MS = 2400;
const RECORDING_FRAME_INTERVAL_MS = 120; // ~20 frames per recording

// Real-time "Live mode" for motion signs can't classify from a single
// instant like Practice.tsx/CommonSigns.tsx — motion needs a short window.
// Each live window collects LIVE_WINDOW_FRAME_COUNT frames (well within
// motion_signs.py's [MIN_FRAMES=5, MAX_FRAMES=90] bounds), submits them to
// the non-scoring /recognize endpoint, then pauses briefly before starting
// the next window. This is honestly ~1.5s-latency "live", not frame-by-
// frame — the UI copy says so rather than implying instant feedback.
const LIVE_WINDOW_FRAME_COUNT = 8;
const LIVE_WINDOW_FRAME_INTERVAL_MS = 150; // ~1.2s to collect one window
const LIVE_WINDOW_GAP_MS = 250; // pause between windows

function captureFrame(video: HTMLVideoElement): Promise<Blob> {
  const scale = CAPTURE_WIDTH / video.videoWidth;
  const width = CAPTURE_WIDTH;
  const height = Math.round(video.videoHeight * scale);

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) return Promise.reject(new Error('Could not get canvas context'));
  ctx.drawImage(video, 0, 0, width, height);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('Failed to encode frame as JPEG'))),
      'image/jpeg',
      0.75
    );
  });
}

// This is the platform's first MOTION recognizer — every other page
// (Practice, CommonSigns) classifies a single still frame. Here a whole
// short clip (a handful of frames captured over ~2.4s) is sent to the
// backend, which runs rule-based hand-trajectory geometry over the
// sequence (motion_sign_service.py) — not a trained model, and not the
// full ASL vocabulary; see the Courses page for why Intermediate/
// Workplace tiers stay locked while this one is real and working.
export function MotionSigns() {
  const [searchParams] = useSearchParams();
  const explicitSign = searchParams.get('sign');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingFramesRef = useRef<Blob[]>([]);
  const [cameraState, setCameraState] = useState<CameraState>('idle');
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [supportedSigns, setSupportedSigns] = useState<string[]>([]);
  const [targetSign, setTargetSign] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<MotionSignFeedback | null>(null);
  const [captureError, setCaptureError] = useState<CaptureError | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [recordingFrameCount, setRecordingFrameCount] = useState<number | null>(null);

  // Real-time "Live mode" — off by default, and completely separate from
  // recordingFramesRef/submitRecording above (the real, graded Record flow
  // this never touches or competes with). collectingWindow distinguishes
  // "gathering this window's frames" from "waiting on the /recognize
  // response" so the readout can say something honest either way.
  const [liveMode, setLiveMode] = useState(false);
  const [liveResult, setLiveResult] = useState<MotionSignRecognizeResult | null>(null);
  const [liveCollectingWindow, setLiveCollectingWindow] = useState(false);
  const liveEnabledRef = useRef(false);
  const liveTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    client
      .get<SupportedMotionSigns>('/api/motion-signs/supported')
      .then((res) => {
        setSupportedSigns(res.data.signs);
        // Honour an explicit ?sign= (e.g. from the dashboard's "Practice
        // next" or adaptive-plan panels) only if it's actually one of the
        // signs this endpoint supports — otherwise fall back to the first
        // supported sign rather than silently targeting something invalid.
        setTargetSign((current) => {
          if (current) return current;
          if (explicitSign && res.data.signs.includes(explicitSign)) return explicitSign;
          return res.data.signs[0] ?? null;
        });
      })
      .catch((err) => console.error('Failed to load supported motion signs:', err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [explicitSign]);

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
      if (videoRef.current) videoRef.current.srcObject = stream;
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

  useEffect(() => {
    return () => stopStream();
  }, [stopStream]);

  const submitRecording = useCallback(
    async (frames: Blob[]) => {
      if (!targetSign) return;
      setSubmitting(true);
      setResult(null);
      setCaptureError(null);
      try {
        const formData = new FormData();
        formData.append('target_sign', targetSign);
        frames.forEach((blob, i) => formData.append('images', blob, `frame-${i}.jpg`));

        const response = await client.post<MotionSignFeedback>('/api/motion-signs/feedback', formData);
        setResult(response.data);
      } catch (err) {
        console.error('Motion clip submit failed:', err);
        if (axios.isAxiosError(err) && err.response) {
          setCaptureError({ message: `Request failed with status ${err.response.status}`, status: err.response.status });
        } else {
          setCaptureError({ message: err instanceof Error ? err.message : 'Unknown error' });
        }
      } finally {
        setSubmitting(false);
      }
    },
    [targetSign]
  );

  // One live window: collects its own short frame burst into a local
  // array (never recordingFramesRef, so it can't clobber an in-progress
  // real recording), submits it to the non-scoring /recognize endpoint,
  // then re-schedules the next window — a self-pacing recursive setTimeout
  // rather than setInterval, so a slow response never piles up overlapping
  // requests.
  const runLiveWindow = useCallback(async () => {
    if (!liveEnabledRef.current || !videoRef.current) return;

    setLiveCollectingWindow(true);
    const frames: Blob[] = [];
    for (let i = 0; i < LIVE_WINDOW_FRAME_COUNT; i++) {
      if (!liveEnabledRef.current || !videoRef.current) {
        setLiveCollectingWindow(false);
        return;
      }
      try {
        frames.push(await captureFrame(videoRef.current));
      } catch (err) {
        console.error('Live frame capture failed:', err);
      }
      if (i < LIVE_WINDOW_FRAME_COUNT - 1) {
        await new Promise((resolve) => window.setTimeout(resolve, LIVE_WINDOW_FRAME_INTERVAL_MS));
      }
    }
    setLiveCollectingWindow(false);
    if (!liveEnabledRef.current) return;

    try {
      const formData = new FormData();
      frames.forEach((blob, i) => formData.append('images', blob, `live-${i}.jpg`));
      const response = await client.post<MotionSignRecognizeResult>('/api/motion-signs/recognize', formData);
      if (liveEnabledRef.current) setLiveResult(response.data);
    } catch (err) {
      console.error('Live recognize failed:', err);
    } finally {
      if (liveEnabledRef.current) {
        liveTimeoutRef.current = window.setTimeout(runLiveWindow, LIVE_WINDOW_GAP_MS);
      }
    }
  }, []);

  // Live mode only runs while the learner is actually free to do a real,
  // graded recording — paused during the countdown, an in-flight
  // recording/submission, or once a real result is already showing.
  const canRunLive =
    liveMode && cameraState === 'active' && !result && countdown === null && !submitting && recordingFrameCount === null;

  useEffect(() => {
    liveEnabledRef.current = canRunLive;
  }, [canRunLive]);

  useEffect(() => {
    if (canRunLive) {
      runLiveWindow();
    } else {
      setLiveResult(null);
      setLiveCollectingWindow(false);
      if (liveTimeoutRef.current !== null) {
        window.clearTimeout(liveTimeoutRef.current);
        liveTimeoutRef.current = null;
      }
    }
  }, [canRunLive, runLiveWindow]);

  useEffect(() => {
    return () => {
      liveEnabledRef.current = false;
      if (liveTimeoutRef.current !== null) window.clearTimeout(liveTimeoutRef.current);
    };
  }, []);

  // Runs once the 3-2-1 countdown elapses: grabs frames on a fixed
  // interval for RECORDING_DURATION_MS, then submits the whole clip.
  const startRecording = useCallback(() => {
    if (!videoRef.current) return;
    recordingFramesRef.current = [];
    setRecordingFrameCount(0);

    const intervalId = window.setInterval(async () => {
      if (!videoRef.current) return;
      try {
        const blob = await captureFrame(videoRef.current);
        recordingFramesRef.current.push(blob);
        setRecordingFrameCount(recordingFramesRef.current.length);
      } catch (err) {
        console.error('Frame capture failed mid-recording:', err);
      }
    }, RECORDING_FRAME_INTERVAL_MS);

    window.setTimeout(() => {
      window.clearInterval(intervalId);
      const frames = recordingFramesRef.current;
      setRecordingFrameCount(null);
      submitRecording(frames);
    }, RECORDING_DURATION_MS);
  }, [submitRecording]);

  const triggerCapture = useCallback(() => {
    if (submitting || result || countdown !== null || recordingFrameCount !== null || !targetSign) return;
    setCountdown(COUNTDOWN_START);
  }, [submitting, result, countdown, recordingFrameCount, targetSign]);

  useEffect(() => {
    if (countdown === null) return;
    const timer = setTimeout(() => {
      if (countdown <= 1) {
        setCountdown(null);
        startRecording();
      } else {
        setCountdown(countdown - 1);
      }
    }, COUNTDOWN_TICK_MS);
    return () => clearTimeout(timer);
  }, [countdown, startRecording]);

  const handleTryAgain = useCallback(() => {
    setResult(null);
    setCaptureError(null);
  }, []);

  const isBusy = submitting || countdown !== null || recordingFrameCount !== null;

  return (
    <div className="page motion-signs">
      <Topbar title="Everyday Gestures" />

      <div className="motion-signs__intro">
        <p>
          Generic motion gestures, recognized from real hand-trajectory geometry across a short video clip
          &mdash; this platform&rsquo;s first recognizer that looks at <em>motion</em>, not a single frame.
          Rule-based, not a trained model, and separate from the ASL-vocabulary tiers below, which still need
          a downloaded video dataset.
        </p>
      </div>

      {supportedSigns.length > 0 && (
        <div className="motion-signs__picker" role="radiogroup" aria-label="Choose a gesture to practice">
          {supportedSigns.map((sign) => (
            <button
              key={sign}
              type="button"
              role="radio"
              aria-checked={targetSign === sign}
              className={`motion-signs__pill${targetSign === sign ? ' motion-signs__pill--active' : ''}`}
              onClick={() => {
                setTargetSign(sign);
                setResult(null);
                setCaptureError(null);
              }}
              disabled={isBusy}
            >
              {sign}
            </button>
          ))}
        </div>
      )}

      <section className="camera-panel">
        {cameraState === 'idle' && (
          <div className="camera-state">
            <p className="camera-state__text">
              Turn on your camera, pick a gesture above, then record a short clip of yourself doing it.
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
            <p className="camera-state__text">Camera access was denied.</p>
            <button className="btn" onClick={requestCamera}>
              Try again
            </button>
          </div>
        )}

        {cameraState === 'no-device' && (
          <div className="camera-state camera-state--warn">
            <p className="camera-state__text">No camera was found on this device.</p>
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
              className={`camera-video${cameraState === 'active' ? ' camera-video--visible' : ''}`}
              autoPlay
              playsInline
              muted
            />
            {countdown !== null && (
              <div className="countdown-badge" aria-live="assertive">
                {countdown}
              </div>
            )}
            {recordingFrameCount !== null && (
              <div className="recording-badge" aria-live="polite">
                <span className="recording-badge__dot" />
                REC {recordingFrameCount}
              </div>
            )}
            {cameraState === 'active' && !result && countdown === null && recordingFrameCount === null && (
              <div className="live-indicator">
                <span className="live-indicator__dot" />
                LIVE
              </div>
            )}
          </div>

          {cameraState === 'active' && (
            <div className="camera-toolbar">
              <label className="live-mode-toggle">
                <input type="checkbox" checked={liveMode} onChange={(e) => setLiveMode(e.target.checked)} />
                Live evaluation
              </label>
            </div>
          )}

          {cameraState === 'active' && !result && liveMode && (
            <div
              className={`live-read${
                liveResult?.detected && liveResult.sign && targetSign && liveResult.sign === targetSign
                  ? ' live-read--correct'
                  : liveResult?.detected
                  ? ' live-read--incorrect'
                  : ''
              }${liveCollectingWindow ? ' live-read--waiting' : ''}`}
              aria-live="polite"
            >
              <span className="live-read__dot" />
              {countdown !== null || submitting || recordingFrameCount !== null
                ? 'Live evaluation paused during recording'
                : liveCollectingWindow
                ? 'Gathering a short clip…'
                : !liveResult
                ? 'Watching for motion…'
                : !liveResult.detected
                ? 'No hand detected'
                : !liveResult.sign
                ? 'Motion detected — not Wave or Clap'
                : `Live read: ${liveResult.sign}`}
            </div>
          )}

          {cameraState === 'active' && !result && targetSign && (
            <div className="capture-controls">
              <span className="capture-controls__target">
                Perform <strong>{targetSign}</strong>
              </span>
              <span className="capture-controls__reason">
                {recordingFrameCount !== null
                  ? 'Recording… keep going'
                  : `About ${Math.round(RECORDING_DURATION_MS / 1000)}s of motion, right after the countdown`}
              </span>

              <button className="btn" onClick={triggerCapture} disabled={isBusy}>
                {submitting
                  ? 'Checking…'
                  : recordingFrameCount !== null
                  ? 'Recording…'
                  : countdown !== null
                  ? `Starting in ${countdown}…`
                  : 'Record'}
              </button>

              {captureError && (
                <pre className="debug-output debug-output--error">
                  {`Error: ${captureError.message}` + (captureError.status ? ` (HTTP ${captureError.status})` : '')}
                </pre>
              )}
            </div>
          )}

          {cameraState === 'active' && result && (
            <div className={`result result--${result.status === 'pass' ? 'pass' : 'fail'}`}>
              {result.status === 'pass' && (
                <>
                  <span className="result__badge">Correct</span>
                  <p className="result__feedback">{result.feedback}</p>
                </>
              )}

              {result.status === 'fail' && (
                <>
                  <span className="result__badge">Not quite</span>
                  <p className="result__feedback">{result.feedback}</p>
                  <p className="result__meta">
                    Target: <strong>{result.target_sign}</strong> &middot; Detected:{' '}
                    <strong>{result.predicted_sign ?? '—'}</strong>
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
                <button className="btn" onClick={handleTryAgain}>
                  Try again
                </button>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
