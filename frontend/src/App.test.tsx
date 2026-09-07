import React from 'react';
import { act, render, screen } from '@testing-library/react';

// Flushes any already-pending promise chain (e.g. Landing's three
// independent .get(...).then(setState) calls) inside an act() boundary.
// A plain `await Promise.resolve()` only advances one microtask hop,
// which isn't reliably enough for a chained .then() on a mocked promise;
// a macrotask (setTimeout 0) runs after the whole microtask queue drains.
async function flushPendingEffects() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}
import App from './App';

// Landing.tsx (rendered at "/") fetches the real supported-signs lists on
// mount purely to decorate its feature cards — irrelevant to what these
// tests check, and left unmocked they're real network calls that this
// sandbox has no route to, which fail asynchronously *after* a test has
// already finished and its assertions have run, tripping Jest's "Cannot
// log after tests are done" warning. Mocked here so every request in this
// file resolves deterministically and synchronously with the render.
jest.mock('./api/client', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));
// eslint-disable-next-line @typescript-eslint/no-var-requires
const client = require('./api/client').default as { get: jest.Mock };

// AuthProvider (see auth/AuthContext.tsx) reads its session straight out of
// localStorage on mount, and App.tsx owns its own BrowserRouter (there's no
// way to inject a starting route from outside) — so each test drives the
// starting URL via window.history.pushState before rendering, and every
// test starts from a clean, logged-out localStorage so one test's session
// can never leak into the next.
//
// The mock's resolved value is (re)set here, not in the jest.mock factory
// above — CRA's default jest config resets all mocks before every test, so
// an implementation set once in the factory (which only runs at module
// load) would already be wiped out by the time the first test runs.
beforeEach(() => {
  localStorage.clear();
  window.history.pushState({}, '', '/');
  client.get.mockResolvedValue({ data: { signs: [], words: [] } });
});

test('shows the public landing page at the root for a logged-out visitor', async () => {
  render(<App />);
  expect(
    screen.getByRole('heading', { name: /learn sign language with real-time feedback/i })
  ).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /^log in$/i })).toBeInTheDocument();
  // Landing also kicks off its own decorative fetches on mount (see the
  // jest.mock comment above) — flushed out here so their state updates
  // land inside this test's act() boundary instead of after it.
  await flushPendingEffects();
});

test('redirects an unauthenticated visitor away from a protected route, to login', () => {
  window.history.pushState({}, '', '/dashboard');
  render(<App />);
  expect(screen.getByRole('heading', { name: /sign language platform/i })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: /log in/i })).toBeInTheDocument();
});

test('redirects an unknown path back to the landing page', async () => {
  window.history.pushState({}, '', '/this-route-does-not-exist');
  render(<App />);
  expect(
    screen.getByRole('heading', { name: /learn sign language with real-time feedback/i })
  ).toBeInTheDocument();
  await flushPendingEffects();
});
