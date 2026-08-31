import React, { useCallback, useEffect, useRef, useState } from 'react';
import client from '../api/client';
import { Topbar } from '../components/Topbar';
import { PracticeFeedback } from '../types/practice';
import './SpeedQuiz.css';

const QUESTION_COUNT = 10;
const SECONDS_PER_QUESTION = 20;
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

function captureFrame(video: HTMLVideoElement): Promise<Blob> {
  const canvas = document.createElement('canvas');
  const width = 640;
  canvas.width = width;
  canvas.height = Math.round(video.videoHeight * (width / video.videoWidth));
  const context = canvas.getContext('2d');
  if (!context) return Promise.reject(new Error('Camera capture is unavailable.'));
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) => canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error('Could not capture image.')), 'image/jpeg', 0.8));
}

function makeQuestions(): string[] {
  const pool = [...LETTERS].sort(() => Math.random() - 0.5);
  return pool.slice(0, QUESTION_COUNT);
}

export function SpeedQuiz() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [questions, setQuestions] = useState<string[]>([]);
  const [index, setIndex] = useState(0);
  const [seconds, setSeconds] = useState(SECONDS_PER_QUESTION);
  const [score, setScore] = useState(0);
  const [started, setStarted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const finished = started && index >= questions.length;
  const target = questions[index];

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const startQuiz = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setQuestions(makeQuestions());
      setIndex(0);
      setScore(0);
      setSeconds(SECONDS_PER_QUESTION);
      setStarted(true);
    } catch {
      setError('Camera permission is required to take the Speed Quiz.');
    }
  }, []);

  const nextQuestion = useCallback(() => {
    setIndex((current) => current + 1);
    setSeconds(SECONDS_PER_QUESTION);
  }, []);

  useEffect(() => {
    if (!started || finished || submitting) return;
    const timer = window.setInterval(() => {
      setSeconds((current) => {
        if (current <= 1) {
          window.clearInterval(timer);
          nextQuestion();
          return SECONDS_PER_QUESTION;
        }
        return current - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [started, finished, submitting, nextQuestion, index]);

  const submitAnswer = useCallback(async () => {
    if (!videoRef.current || !target || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const image = await captureFrame(videoRef.current);
      const form = new FormData();
      form.append('target_letter', target);
      form.append('practice_seconds', String(SECONDS_PER_QUESTION - seconds));
      form.append('image', image, 'speed-quiz.jpg');
      const response = await client.post<PracticeFeedback>('/api/practice/feedback', form);
      if (response.data.correct) setScore((current) => current + 1);
      nextQuestion();
    } catch {
      setError('Could not assess this answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [target, seconds, submitting, nextQuestion]);

  return (
    <div className="page speed-quiz">
      <Topbar title="Speed Quiz" />
      {!started ? (
        <section className="speed-quiz__welcome">
          <span className="speed-quiz__eyebrow">Timed assessment</span>
          <h2>Speed Quiz</h2>
          <p>10 ASL alphabet questions · 20 seconds each · results update your learning plan.</p>
          <ul>
            <li>Use your webcam to sign the shown letter.</li>
            <li>Submit before time expires to record an assessed attempt.</li>
            <li>Finish with 90%+ for an A-level result.</li>
          </ul>
          {error && <p className="status-message status-message--error">{error}</p>}
          <button className="btn" onClick={startQuiz}>Start Speed Quiz</button>
        </section>
      ) : finished ? (
        <section className="speed-quiz__welcome">
          <span className="speed-quiz__eyebrow">Assessment complete</span>
          <h2>{score}/{QUESTION_COUNT} correct</h2>
          <p>Your grade: <strong>{score >= 9 ? 'A' : score >= 7 ? 'B' : score >= 5 ? 'C' : 'Keep practising'}</strong></p>
          <p>Your dashboard and adaptive recommendations have been updated from the assessed answers.</p>
          <button className="btn" onClick={() => { stopCamera(); setStarted(false); }}>Take another quiz</button>
        </section>
      ) : (
        <section className="speed-quiz__active">
          <div className="speed-quiz__status"><span>Question {index + 1} of {QUESTION_COUNT}</span><strong>{seconds}s</strong><span>Score {score}</span></div>
          <p className="speed-quiz__prompt">Sign the letter</p>
          <div className="speed-quiz__letter">{target}</div>
          <video className="speed-quiz__video" ref={videoRef} autoPlay muted playsInline />
          {error && <p className="status-message status-message--error">{error}</p>}
          <button className="btn" disabled={submitting} onClick={submitAnswer}>{submitting ? 'Assessing…' : 'Submit answer'}</button>
        </section>
      )}
    </div>
  );
}
