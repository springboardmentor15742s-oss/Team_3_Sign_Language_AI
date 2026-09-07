import axios from 'axios';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import client from '../api/client';
import { Topbar } from '../components/Topbar';
import { SupportedWordSigns, WordSignFeedback, WordSignRecognizeResult } from '../types/wordSigns';
import './Practice.css';
import './ConversationalFluency.css';

interface CaptureError {
  message: string;
  status?: number;
}

// reference_images values are relative /media/... paths (see
// word_sign_service.get_reference_image_urls) — same convention
// AssignedFocusPanel.tsx uses for instructor-uploaded reference media,
// resolved against the same backend origin the app already talks to.
function mediaSrc(relativeUrl: string): string {
  return `${client.defaults.baseURL}${relativeUrl}`;
}

type CameraState = 'idle' | 'requesting' | 'active' | 'denied' | 'no-device' | 'error';

const CAPTURE_WIDTH = 480;
const COUNTDOWN_START = 3;
const COUNTDOWN_TICK_MS = 1000;
// A full word sign needs a bit more than a wave/clap to complete —
// matches routers/word_signs.py's MIN_FRAMES/MAX_FRAMES bounds ([8, 90]).
const RECORDING_DURATION_MS = 3000;
const RECORDING_FRAME_INTERVAL_MS = 120; // ~25 frames per recording

// Real-time "Live mode": word signs can't classify from a single instant
// either (same reasoning as MotionSigns.tsx), so each live window collects
// LIVE_WINDOW_FRAME_COUNT frames (respecting this router's own
// [MIN_FRAMES=8, MAX_FRAMES=90] bounds) and submits them to the
// non-scoring /recognize endpoint before pausing and starting the next
// window. Honestly ~2s-latency "live", not frame-by-frame.
const LIVE_WINDOW_FRAME_COUNT = 10;
const LIVE_WINDOW_FRAME_INTERVAL_MS = 150; // ~1.5s to collect one window
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

// This is the platform's first WORD-level sign recognizer backed by a
// genuinely trained classifier (msasl_intermediate_classifier.pkl,
// trained on real MS-ASL video clips) rather than hand-written rules —
// unlike MotionSigns' Wave/Clap detector. Only 16 words are supported:
// an earlier attempt at the full 30-word MS-ASL vocabulary only reached
// 32.5% test accuracy because several words had too few real clips to
// learn from; cutting to the words with enough real samples got a
// meaningfully better (but still imperfect) 49% test accuracy — see the
// model-accuracy note below, sourced live from the backend rather than
// hardcoded here.
export function ConversationalFluency() {
  const [searchParams] = useSearchParams();
  const explicitWord = searchParams.get('word');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingFramesRef = useRef<Blob[]>([]);
  const [cameraState, setCameraState] = useState<CameraState>('idle');
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [supportedWords, setSupportedWords] = useState<string[]>([]);
  const [modelAccuracy, setModelAccuracy] = useState<number | null>(null);
  const [referenceImages, setReferenceImages] = useState<Record<string, string>>({});
  const [targetWord, setTargetWord] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<WordSignFeedback | null>(null);
  const [captureError, setCaptureError] = useState<CaptureError | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [recordingFrameCount, setRecordingFrameCount] = useState<number | null>(null);

  // Real-time "Live mode" — off by default, and completely separate from
  // recordingFramesRef/submitRecording above (the real, graded Record flow
  // this never touches or competes with).
  const [liveMode, setLiveMode] = useState(false);
  const [liveResult, setLiveResult] = useState<WordSignRecognizeResult | null>(null);
  const [liveCollectingWindow, setLiveCollectingWindow] = useState(false);
  const liveEnabledRef = useRef(false);
  const liveTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    client
      .get<SupportedWordSigns>('/api/word-signs/supported')
      .then((res) => {
        setSupportedWords(res.data.words);
        setModelAccuracy(res.data.model_test_accuracy);
        setReferenceImages(res.data.reference_images ?? {});
        setTargetWord((current) => {
          if (current) return current;
          if (explicitWord && res.data.words.includes(explicitWord)) return explicitWord;
          return res.data.words[0] ?? null;
        });
      })
      .catch((err) => console.error('Failed to load supported words:', err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [explicitWord]);

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
      if (!targetWord) return;
      setSubmitting(true);
      setResult(null);
      setCaptureError(null);
      try {
        const formData = new FormData();
        formData.append('target_word', targetWord);
        frames.forEach((blob, i) => formData.append('images', blob, `frame-${i}.jpg`));

        const response = await client.post<WordSignFeedback>('/api/word-signs/feedback', formData);
        setResult(response.data);
      } catch (err) {
        console.error('Word clip submit failed:', err);
        if (axios.isAxiosError(err) && err.response) {
          setCaptureError({ message: `Request failed with status ${err.response.status}`, status: err.response.status });
        } else {
          setCaptureError({ message: err instanceof Error ? err.message : 'Unknown error' });
        }
      } finally {
        setSubmitting(false);
      }
    },
    [targetWord]
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
      const response = await client.post<WordSignRecognizeResult>('/api/word-signs/recognize', formData);
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
    if (submitting || result || countdown !== null || recordingFrameCount !== null || !targetWord) return;
    setCountdown(COUNTDOWN_START);
  }, [submitting, result, countdown, recordingFrameCount, targetWord]);

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
    <div className="page word-signs">
      <Topbar title="Intermediate Conversational Fluency" />

      <div className="word-signs__intro">
        <p>
          A real classifier trained on MS-ASL video clips &mdash; not hand-written rules like Everyday Gestures.
          {modelAccuracy !== null && (
            <>
              {' '}
              It currently gets <strong>{(modelAccuracy * 100).toFixed(0)}%</strong> right on held-out test clips
              across these {supportedWords.length} words, so treat &ldquo;not quite&rdquo; results as expected
              sometimes, not necessarily a sign you signed it wrong.
            </>
          )}{' '}
          Only words with enough real training clips are included; more will be added as more real data is
          collected.
        </p>
      </div>

      {supportedWords.length > 0 && (
        <div className="word-signs__picker" role="radiogroup" aria-label="Choose a word to practice">
          {supportedWords.map((word) => (
            <button
              key={word}
              type="button"
              role="radio"
              aria-checked={targetWord === word}
              className={`word-signs__pill${targetWord === word ? ' word-signs__pill--active' : ''}`}
              onClick={() => {
                setTargetWord(word);
                setResult(null);
                setCaptureError(null);
              }}
              disabled={isBusy}
            >
              {word}
            </button>
          ))}
        </div>
      )}

      {targetWord && (
        <div className="word-signs__reference">
          {referenceImages[targetWord] ? (
            <>
              <img
                className="word-signs__reference-image"
                src={mediaSrc(referenceImages[targetWord])}
                alt={`How to sign '${targetWord}'`}
              />
              <p className="word-signs__reference-caption">
                Reference: how <strong>{targetWord}</strong> is signed &mdash; a real frame from the MS-ASL clips
                this classifier was trained on.
              </p>
            </>
          ) : (
            <p className="word-signs__reference-caption">
              No reference photo for &lsquo;{targetWord}&rsquo; yet.
            </p>
          )}
        </div>
      )}

      <section className="camera-panel">
        {cameraState === 'idle' && (
          <div className="camera-state">
            <p className="camera-state__text">
              Turn on your camera, pick a word above, then record yourself signing it.
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
                liveResult?.detected && liveResult.word && targetWord && liveResult.word === targetWord
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
                ? 'Watching for a pose…'
                : !liveResult.detected
                ? 'No pose detected'
                : `Live read: ${liveResult.word}${
                    liveResult.confidence !== null ? ` (${Math.round(liveResult.confidence * 100)}%)` : ''
                  }`}
            </div>
          )}

          {cameraState === 'active' && !result && targetWord && (
            <div className="capture-controls">
              <span className="capture-controls__target">
                Sign <strong>{targetWord}</strong>
              </span>
              <span className="capture-controls__reason">
                {recordingFrameCount !== null
                  ? 'Recording… keep going'
                  : `About ${Math.round(RECORDING_DURATION_MS / 1000)}s, right after the countdown`}
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
                  <span className="result__badge">No pose detected</span>
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
