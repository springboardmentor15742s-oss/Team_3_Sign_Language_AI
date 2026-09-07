import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { VerifyCertificate } from './VerifyCertificate';
import { AuthProvider } from '../auth/AuthContext';

// This page is deliberately public (see its own top-of-file comment) and
// talks to the backend directly through the shared axios instance — mocked
// here so these tests never hit a real network call.
jest.mock('../api/client', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));
// eslint-disable-next-line @typescript-eslint/no-var-requires
const client = require('../api/client').default as { get: jest.Mock };

beforeEach(() => {
  client.get.mockReset();
  localStorage.clear();
});

function renderAt(path: string) {
  // Topbar (rendered by VerifyCertificate) reads useAuth() for its nav —
  // this page is public, so there's deliberately no logged-in user here,
  // same as a real visitor arriving from a printed certificate's link.
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/verify" element={<VerifyCertificate />} />
          <Route path="/verify/:code" element={<VerifyCertificate />} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

test('with no code in the URL, shows the entry form and does not call the API', () => {
  renderAt('/verify');
  expect(screen.getByPlaceholderText(/AB23CD45EF/i)).toBeInTheDocument();
  expect(client.get).not.toHaveBeenCalled();
});

test('a code in the URL is verified automatically on load', async () => {
  client.get.mockResolvedValue({
    data: {
      valid: true,
      learner_name: 'Cert Learner',
      course_title: 'Everyday Gestures',
      issued_at: '2026-08-01T00:00:00Z',
      revoked: false,
      revoked_at: null,
    },
  });

  renderAt('/verify/AB23CD45EF');

  expect(await screen.findByText('Valid certificate')).toBeInTheDocument();
  expect(screen.getByText('Cert Learner')).toBeInTheDocument();
  expect(screen.getByText('Everyday Gestures')).toBeInTheDocument();
  expect(client.get).toHaveBeenCalledWith('/api/certificates/verify/AB23CD45EF');
});

test('an unknown code shows "Not found", distinct from a revoked one', async () => {
  client.get.mockResolvedValue({
    data: { valid: false, learner_name: null, course_title: null, issued_at: null, revoked: false, revoked_at: null },
  });

  renderAt('/verify/NOTAREALCODE');

  expect(await screen.findByText('Not found')).toBeInTheDocument();
});

test('a revoked certificate is shown as Revoked, with the learner and course still named', async () => {
  client.get.mockResolvedValue({
    data: {
      valid: false,
      learner_name: 'Cert Learner',
      course_title: 'Everyday Gestures',
      issued_at: '2026-08-01T00:00:00Z',
      revoked: true,
      revoked_at: '2026-08-15T00:00:00Z',
    },
  });

  renderAt('/verify/AB23CD45EF');

  expect(await screen.findByText('Revoked')).toBeInTheDocument();
  expect(screen.getByText(/has since been revoked/i)).toBeInTheDocument();
});

test('typing a code and submitting the form checks it manually', async () => {
  client.get.mockResolvedValue({
    data: { valid: false, learner_name: null, course_title: null, issued_at: null, revoked: false, revoked_at: null },
  });

  renderAt('/verify');
  await userEvent.type(screen.getByPlaceholderText(/AB23CD45EF/i), 'ZZ99ZZ99ZZ');
  await userEvent.click(screen.getByRole('button', { name: /verify/i }));

  await waitFor(() => expect(client.get).toHaveBeenCalledWith('/api/certificates/verify/ZZ99ZZ99ZZ'));
});

test('a network failure surfaces an error instead of a silent blank result', async () => {
  client.get.mockRejectedValue(new Error('network down'));

  renderAt('/verify');
  await userEvent.type(screen.getByPlaceholderText(/AB23CD45EF/i), 'ZZ99ZZ99ZZ');
  await userEvent.click(screen.getByRole('button', { name: /verify/i }));

  expect(await screen.findByText(/could not check this code/i)).toBeInTheDocument();
});
