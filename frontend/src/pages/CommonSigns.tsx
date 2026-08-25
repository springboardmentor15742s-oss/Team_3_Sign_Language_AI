import axios from 'axios';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import client from '../api/client';
import { Topbar } from '../components/Topbar';
import { HandLandmarkOverlay } from '../components/HandLandmarkOverlay';
import { CommonSignResult, SupportedSigns } from '../types/commonSigns';
import './Practice.css';
import './CommonSigns.css';

interface CaptureError {
  message: string;
  status?: number;
}

type CameraState = 'idle' | 'requesting' | 'active' | 'denied' | 'no-device' | 'error';

const CAPTURE_WIDTH = 640;
const COUNTDOWN_START = 3;
const COUNTDOWN_TICK_MS = 1000;

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
      (blob) => (blob ? resolve(blob) : reject(new Error('Failed to encode capture as JPEG'))),
      'image/jpeg',
      0.8
    );
  });
}

// This page is intentionally separate from Practice/gesture recognition:
// it uses a rule-based geometry detector (common_signs_service on the
// backend), not the trained alphabet classifier, and isn't scored or
// logged as PracticeAttempt data — it's a standalone "try it" tester.
export function CommonSigns() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraState, setCameraState] = useState<CameraState>('idle');
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [supportedSigns, setSupportedSigns] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<CommonSignResult | null>(null);
  const [captureError, setCaptureError] = useState<CaptureError | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [capturedImageUrl, setCapturedImageUrl] = useState<string | null>(null);

  useEffect(() => {
    client
      .get<SupportedSigns>('/api/common-signs/supported')
      .then((res) => setSupportedSigns(res.data.signs))
      .catch((err) => console.error('Failed to load supported signs:', err));
  }, []);

  useEffect(() => {
    return () => {
      if (capturedImageUrl) URL.revokeObjectURL(capturedImageUrl);
    };
  }, [capturedImageUrl]);

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

  const performCapture = useCallback(async () => {
    if (!videoRef.current || submitting) return;
    setSubmitting(true);
    setResult(null);
    setCaptureError(null);
    try {
      const blob = await captureFrame(videoRef.current);
      setCapturedImageUrl(URL.createObjectURL(blob));

      const formData = new FormData();
      formData.append('image', blob, 'capture.jpg');

      const response = await client.post<CommonSignResult>('/api/common-signs/recognize', formData);
      setResult(response.data);
    } catch (err) {
      console.error('Capture/send failed:', err);
      if (axios.isAxiosError(err) && err.response) {
        setCaptureError({ message: `Request failed with status ${err.response.status}`, status: err.response.status });
      } else {
        setCaptureError({ message: err instanceof Error ? err.message : 'Unknown error' });
      }
    } finally {
      setSubmitting(false);
    }
  }, [submitting]);

  const triggerCapture = useCallback(() => {
    if (submitting || result || countdown !== null) return;
    setCountdown(COUNTDOWN_START);
  }, [submitting, result, countdown]);

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

  const handleTryAgain = useCallback(() => {
    setResult(null);
    setCaptureError(null);
  }, []);

  return (
    <div className="page common-signs">
      <Topbar title="Common Signs" />

      <div className="common-signs__intro">
        <p>
          A small set of common ASL signs recognized with rule-based hand-landmark geometry &mdash; not the
          trained alphabet model, and not scored or logged to your practice stats. Try:{' '}
          {supportedSigns.map((sign, i) => (
            <React.Fragment key={sign}>
              <strong>{sign}</strong>
              {i < supportedSigns.length - 1 ? ', ' : ''}
            </React.Fragment>
          ))}
        </p>
      </div>

      <section className="camera-panel">
        {cameraState === 'idle' && (
          <div className="camera-state">
            <p className="camera-state__text">Turn on your camera to try one of the common signs above.</p>
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
            {cameraState === 'active' && !result && countdown === null && (
              <div className="live-indicator">
                <span className="live-indicator__dot" />
                LIVE
              </div>
            )}
          </div>

          {cameraState === 'active' && !result && (
            <div className="capture-controls">
              <button className="btn" onClick={triggerCapture} disabled={submitting || countdown !== null}>
                {submitting ? 'Checking…' : countdown !== null ? `Capturing in ${countdown}…` : 'Capture'}
              </button>
              <p className="capture-controls__hint">Hold one of the signs above steady in frame</p>
              {captureError && (
                <pre className="debug-output debug-output--error">
                  {`Error: ${captureError.message}` + (captureError.status ? ` (HTTP ${captureError.status})` : '')}
                </pre>
              )}
            </div>
          )}

          {cameraState === 'active' && result && (
            <div className={`result result--${result.sign ? 'pass' : 'fail'}`}>
              {!result.detected_hand && (
                <>
                  <span className="result__badge">No hand detected</span>
                  <p className="result__feedback">Make sure your hand is in frame and try again.</p>
                </>
              )}
              {result.detected_hand && result.sign && (
                <>
                  <span className="result__badge">Detected</span>
                  <p className="result__feedback">{result.sign}</p>
                </>
              )}
              {result.detected_hand && !result.sign && (
                <>
                  <span className="result__badge">Not recognized</span>
                  <p className="result__feedback">
                    A hand was found, but it didn&rsquo;t match I Love You, Yes, or No.
                  </p>
                </>
              )}

              {capturedImageUrl && result.landmarks && result.landmarks.length === 21 && (
                <HandLandmarkOverlay
                  imageUrl={capturedImageUrl}
                  landmarks={result.landmarks}
                  variant={result.sign ? 'pass' : 'fail'}
                />
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
