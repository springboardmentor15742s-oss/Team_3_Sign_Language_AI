import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CertificatesPanel } from './CertificatesPanel';
import { Certificate, CourseCertificationStatus } from '../types/certificate';

// CertificatesPanel imports the shared axios instance directly (for its
// own PDF-download action) rather than taking it as a prop — mocked here
// so a test never makes a real network call.
jest.mock('../api/client', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));
// eslint-disable-next-line @typescript-eslint/no-var-requires
const client = require('../api/client').default as { get: jest.Mock };

function makeCertificate(overrides: Partial<Certificate> = {}): Certificate {
  return {
    id: 'cert-1',
    learner_id: 'learner-1',
    course_id: 'everyday-gestures',
    course_title: 'Everyday Gestures',
    verification_code: 'AB23CD45EF',
    issued_at: '2026-08-01T00:00:00Z',
    issued_by: 'system',
    issued_by_name: 'Sign Language Learning Platform',
    revoked: false,
    revoked_at: null,
    revoked_reason: null,
    ...overrides,
  };
}

function makeStatus(overrides: Partial<CourseCertificationStatus> = {}): CourseCertificationStatus {
  return {
    course_id: 'alphabet-fundamentals',
    course_title: 'ASL Alphabet Fundamentals',
    items_total: 26,
    items_passed: 10,
    eligible: false,
    already_issued: false,
    certificate_id: null,
    ...overrides,
  };
}

beforeEach(() => {
  client.get.mockReset();
});

test('shows the empty state when no certificates have been earned yet', () => {
  render(<CertificatesPanel learnerId="learner-1" certificates={[]} status={[]} />);
  expect(screen.getByText(/no certificates earned yet/i)).toBeInTheDocument();
});

test('lists an earned certificate with its verification code', () => {
  render(<CertificatesPanel learnerId="learner-1" certificates={[makeCertificate()]} status={[]} />);
  expect(screen.getByText('Everyday Gestures')).toBeInTheDocument();
  expect(screen.getByText(/Code: AB23CD45EF/)).toBeInTheDocument();
});

test('shows honest in-progress bars for courses not yet certified', () => {
  render(
    <CertificatesPanel
      learnerId="learner-1"
      certificates={[]}
      status={[makeStatus({ items_passed: 10, items_total: 26 })]}
    />
  );
  expect(screen.getByText('10/26 passed')).toBeInTheDocument();
});

test('a learner (not staff) never sees issue or revoke controls', () => {
  render(
    <CertificatesPanel
      learnerId="learner-1"
      certificates={[makeCertificate()]}
      status={[makeStatus({ eligible: true })]}
    />
  );
  expect(screen.queryByRole('button', { name: /issue certificate/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /revoke/i })).not.toBeInTheDocument();
});

test('staff sees an issue button for an eligible in-progress course, wired to onIssue', async () => {
  const onIssue = jest.fn().mockResolvedValue(undefined);
  render(
    <CertificatesPanel
      learnerId="learner-1"
      certificates={[]}
      status={[makeStatus({ course_id: 'alphabet-fundamentals', eligible: true })]}
      isStaff
      onIssue={onIssue}
    />
  );
  await userEvent.click(screen.getByRole('button', { name: /issue certificate/i }));
  expect(onIssue).toHaveBeenCalledWith('alphabet-fundamentals');
  // Wait for the in-flight state to settle back (setIssuingCourseId(null)
  // in the component's finally block) so this doesn't leak an unawaited
  // state update into the next test.
  await waitFor(() => expect(screen.getByRole('button', { name: /issue certificate/i })).toBeEnabled());
});

test('staff revoke asks for confirmation and only calls onRevoke when confirmed', async () => {
  const onRevoke = jest.fn().mockResolvedValue(undefined);
  const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

  render(
    <CertificatesPanel learnerId="learner-1" certificates={[makeCertificate()]} status={[]} isStaff onRevoke={onRevoke} />
  );
  await userEvent.click(screen.getByRole('button', { name: /revoke/i }));
  expect(confirmSpy).toHaveBeenCalled();
  expect(onRevoke).not.toHaveBeenCalled();

  confirmSpy.mockReturnValue(true);
  await userEvent.click(screen.getByRole('button', { name: /revoke/i }));
  expect(onRevoke).toHaveBeenCalledWith('cert-1');
  // Same reasoning as the issue test above — wait for setRevokingId(null)
  // to actually land before the test (and its mocks) tear down.
  await waitFor(() => expect(screen.getByRole('button', { name: /revoke/i })).toBeEnabled());

  confirmSpy.mockRestore();
});

test('shows a revoked certificate separately, with its reason', () => {
  render(
    <CertificatesPanel
      learnerId="learner-1"
      certificates={[makeCertificate({ id: 'cert-2', revoked: true, revoked_reason: 'Issued by mistake' })]}
      status={[]}
    />
  );
  expect(screen.getByText('Revoked')).toBeInTheDocument();
  expect(screen.getByText(/Issued by mistake/)).toBeInTheDocument();
  expect(screen.getByText(/no certificates earned yet/i)).toBeInTheDocument();
});

test('downloading a certificate calls the PDF endpoint for this learner and certificate', async () => {
  client.get.mockResolvedValue({
    data: new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
    headers: { 'content-disposition': 'attachment; filename="certificate-everyday-gestures-AB23CD45EF.pdf"' },
  });
  // jsdom doesn't implement these — the component calls them as part of
  // triggering the actual file download.
  window.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
  window.URL.revokeObjectURL = jest.fn();

  render(<CertificatesPanel learnerId="learner-1" certificates={[makeCertificate()]} status={[]} />);
  await userEvent.click(screen.getByRole('button', { name: /download pdf/i }));

  await waitFor(() => expect(client.get).toHaveBeenCalledWith('/api/certificates/learner/learner-1/cert-1/pdf', { responseType: 'blob' }));
});
