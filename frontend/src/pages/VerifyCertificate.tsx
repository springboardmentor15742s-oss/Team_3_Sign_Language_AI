import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import client from '../api/client';
import { Topbar } from '../components/Topbar';
import { CertificateVerificationResponse } from '../types/certificate';
import './VerifyCertificate.css';

// Fully public — no ProtectedRoute, no auth header needed (see
// api/client.ts: it only attaches a token when one exists in
// localStorage, and GET /api/certificates/verify/{code} takes none).
// This is the page a verification code on a printed/downloaded
// certificate actually points at, so anyone holding one — an employer,
// say — can land here straight from a link with nothing to log into.
export function VerifyCertificate() {
  const { code: routeCode } = useParams<{ code: string }>();
  const [code, setCode] = useState(routeCode ?? '');
  const [result, setResult] = useState<CertificateVerificationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runVerification = useCallback(async (codeToCheck: string) => {
    if (!codeToCheck.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await client.get<CertificateVerificationResponse>(
        `/api/certificates/verify/${encodeURIComponent(codeToCheck.trim())}`
      );
      setResult(response.data);
    } catch (err) {
      console.error('Failed to verify certificate:', err);
      setError('Could not check this code right now. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (routeCode) runVerification(routeCode);
  }, [routeCode, runVerification]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runVerification(code);
  };

  return (
    <div className="page verify-certificate">
      <Topbar title="Verify a Certificate" />

      <section className="verify-certificate__intro">
        <h2>Verify a certificate</h2>
        <p>Enter the verification code printed on a Sign Language Learning Platform certificate.</p>
      </section>

      <form className="verify-certificate__form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="e.g. AB23CD45EF"
          className="verify-certificate__input"
          autoCapitalize="characters"
        />
        <button type="submit" className="btn" disabled={loading || !code.trim()}>
          {loading ? 'Checking…' : 'Verify'}
        </button>
      </form>

      {error && <p className="status-message status-message--error">{error}</p>}

      {result && (
        <div
          className={`verify-certificate__result verify-certificate__result--${
            result.valid ? 'valid' : 'invalid'
          }`}
        >
          {result.valid ? (
            <>
              <span className="verify-certificate__badge verify-certificate__badge--valid">Valid certificate</span>
              <p className="verify-certificate__line">
                <strong>{result.learner_name}</strong> completed <strong>{result.course_title}</strong>
              </p>
              <p className="verify-certificate__meta">
                Issued {result.issued_at ? new Date(result.issued_at).toLocaleDateString() : '—'}
              </p>
            </>
          ) : result.course_title ? (
            <>
              <span className="verify-certificate__badge verify-certificate__badge--invalid">Revoked</span>
              <p className="verify-certificate__line">
                This certificate for <strong>{result.course_title}</strong> was issued to{' '}
                <strong>{result.learner_name}</strong>, but has since been revoked and is no longer valid.
              </p>
              <p className="verify-certificate__meta">
                {result.revoked_at ? `Revoked ${new Date(result.revoked_at).toLocaleDateString()}` : ''}
              </p>
            </>
          ) : (
            <>
              <span className="verify-certificate__badge verify-certificate__badge--invalid">Not found</span>
              <p className="verify-certificate__line">
                No certificate exists with that code. Double-check it against the certificate and try again.
              </p>
            </>
          )}
        </div>
      )}

      <p className="verify-certificate__back">
        <Link to="/">&larr; Back to the platform</Link>
      </p>
    </div>
  );
}
