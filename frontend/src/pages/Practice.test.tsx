import React from 'react';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Practice } from './Practice';
import { AuthProvider } from '../auth/AuthContext';

// Practice.tsx talks to the backend through the shared axios instance —
// mocked here so these tests never hit a real network call. Both GET
// (recommendation/accuracy lookups) and POST (the /recognize Live-mode
// endpoint) are exercised.
jest.mock('../api/client', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));
// eslint-disable-next-line @typescript-eslint/no-var-requires
const client = require('../api/client').default as { get: jest.Mock; post: jest.Mock };

// jsdom has no real camera or canvas pipeline — these stand in for just
// enough of getUserMedia/<video>/<canvas> to let requestCamera reach
// 'active' and captureFrame produce a Blob, without asserting on pixel
// content (which Live mode's tests below don't care about).
function stubCameraAndCanvas() {
  Object.defineProperty(window.HTMLMediaElement.prototype, 'play', {
    configurable: true,
    value: jest.fn(),
  });
  Object.defineProperty(window.HTMLVideoElement.prototype, 'videoWidth', {
    configurable: true,
    get: () => 640,
  });
  Object.defineProperty(window.HTMLVideoElement.prototype, 'videoHeight', {
    configurable: true,
    get: () => 480,
  });
  window.HTMLCanvasElement.prototype.getContext = jest.fn().mockReturnValue({
    drawImage: jest.fn(),
  }) as unknown as typeof window.HTMLCanvasElement.prototype.getContext;
  window.HTMLCanvasElement.prototype.toBlob = function toBlob(callback: BlobCallback) {
    callback(new Blob(['fake-frame'], { type: 'image/jpeg' }));
  };

  Object.defineProperty(window.navigator, 'mediaDevices', {
    configurable: true,
    value: {
      getUserMedia: jest.fn().mockResolvedValue({
        getTracks: () => [{ stop: jest.fn() }],
      }),
    },
  });
}

beforeEach(() => {
  client.get.mockReset();
  client.post.mockReset();
  localStorage.clear();
  localStorage.setItem('access_token', 'test-token');
  localStorage.setItem(
    'auth_user',
    JSON.stringify({ id: 'learner-1', name: 'Live Learner', email: 'live@test.com', role: 'learner' })
  );

  client.get.mockImplementation((url: string) => {
    if (url.includes('/recommendations')) {
      return Promise.resolve({ data: { recommendations: [{ topic: 'A', topic_type: 'letter', reason: 'Test pick' }] } });
    }
    if (url.includes('/analytics')) {
      return Promise.resolve({ data: { per_letter: {} } });
    }
    return Promise.reject(new Error(`Unexpected GET ${url}`));
  });

  stubCameraAndCanvas();
});

// Several independent async chains here (the mount-time recommendation
// fetch, requestCamera's getUserMedia await, and runLiveStep's own
// capture -> POST -> setState chain) resolve on their own microtasks
// outside any act() boundary that a synchronous userEvent.click(v13)
// covers — this drains the microtask queue inside one, same pattern as
// App.test.tsx's flushPendingEffects.
async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

async function renderAndTurnOnCamera() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/practice']}>
        <Practice />
      </MemoryRouter>
    </AuthProvider>
  );
  await flush(); // let the mount-time recommendation fetch settle

  await userEvent.click(screen.getByRole('button', { name: /turn on camera/i }));
  await flush(); // let requestCamera's getUserMedia await settle
  expect(screen.getByLabelText(/live evaluation/i)).toBeInTheDocument();
}

test('Live evaluation toggle is not shown before the camera is on', async () => {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/practice']}>
        <Practice />
      </MemoryRouter>
    </AuthProvider>
  );
  await flush(); // let the mount-time recommendation fetch settle

  expect(screen.queryByLabelText(/live evaluation/i)).not.toBeInTheDocument();
});

test('turning Live mode on polls /api/practice/recognize and shows a detected letter', async () => {
  client.post.mockResolvedValue({
    data: { detected: true, predicted_letter: 'A', confidence: 0.87, landmarks: null },
  });

  await renderAndTurnOnCamera();
  await userEvent.click(screen.getByLabelText(/live evaluation/i));
  await flush();

  expect(client.post).toHaveBeenCalledWith('/api/practice/recognize', expect.any(FormData));
  expect(screen.getByText(/live read: a \(87%\)/i)).toBeInTheDocument();
});

test('an honest "no hand detected" read is shown rather than a fabricated result', async () => {
  client.post.mockResolvedValue({
    data: { detected: false, predicted_letter: null, confidence: null, landmarks: null },
  });

  await renderAndTurnOnCamera();
  await userEvent.click(screen.getByLabelText(/live evaluation/i));
  await flush();

  expect(screen.getByText(/no hand detected/i)).toBeInTheDocument();
});

test('turning Live mode back off stops the polling loop', async () => {
  client.post.mockResolvedValue({
    data: { detected: true, predicted_letter: 'A', confidence: 0.5, landmarks: null },
  });

  // Real timers for setup (renderAndTurnOnCamera's flush() relies on a
  // real setTimeout) — fake timers only go on once the loop itself is
  // what needs controlling.
  await renderAndTurnOnCamera();

  jest.useFakeTimers();
  try {
    await userEvent.click(screen.getByLabelText(/live evaluation/i));
    // This Jest version has no advanceTimersByTimeAsync — runLiveStep's
    // captureFrame -> client.post -> setLiveResult chain resolves on
    // plain microtasks (no timer involved) before its first setTimeout is
    // even scheduled, so draining the microtask queue inside act() is
    // enough to let the first call land.
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(client.post).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByLabelText(/live evaluation/i)); // toggle off
    expect(screen.queryByText(/live read:/i)).not.toBeInTheDocument();

    // Advance well past several poll intervals — the toggle-off should
    // have cleared the scheduled setTimeout, so no further calls fire.
    await act(async () => {
      jest.advanceTimersByTime(700 * 5);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(client.post).toHaveBeenCalledTimes(1);
  } finally {
    jest.useRealTimers();
  }
});
