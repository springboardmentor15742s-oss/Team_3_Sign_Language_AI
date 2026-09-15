import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

const LEVEL_COLOR = {
  Beginner: "level-pill level-developing",
  Intermediate: "level-pill level-developing",
  Advanced: "level-pill level-good",
  Professional: "level-pill level-good",
};

function openPrintableCertificate(cert) {
  const win = window.open("", "_blank", "width=800,height=600");
  if (!win) return;
  win.document.write(`
    <html>
      <head>
        <title>${cert.certificate_code}</title>
        <style>
          body { font-family: Georgia, serif; text-align: center; padding: 60px; color: #1f2430; }
          .frame { border: 10px double #6d28d9; padding: 50px; }
          h1 { font-size: 2rem; color: #6d28d9; margin-bottom: 4px; }
          h2 { font-weight: normal; color: #6b7280; margin-top: 0; }
          .name { font-size: 1.8rem; margin: 30px 0 6px; font-weight: bold; }
          .level { font-size: 1.3rem; color: #6d28d9; margin-bottom: 30px; }
          .stats { margin: 20px 0; color: #444; }
          .code { margin-top: 40px; font-size: 0.85rem; color: #6b7280; letter-spacing: 1px; }
        </style>
      </head>
      <body onload="window.print()">
        <div class="frame">
          <h1>🤟 Sign Language Learning &amp; Assessment Platform</h1>
          <h2>Certificate of Completion</h2>
          <p>This certifies that</p>
          <div class="name">${cert.username}</div>
          <div class="level">has achieved the ${cert.level} level</div>
          <div class="stats">
            Overall accuracy: <strong>${cert.overall_accuracy}%</strong> &nbsp;|&nbsp;
            Practice attempts: <strong>${cert.total_attempts}</strong> &nbsp;|&nbsp;
            Gestures certified: <strong>${cert.gestures_certified}</strong>
          </div>
          <div class="stats">Issued: ${cert.issued_at}</div>
          <div class="code">Certificate code: ${cert.certificate_code} — verify at /api/certification/verify/${cert.certificate_code}</div>
        </div>
      </body>
    </html>
  `);
  win.document.close();
}

export default function Certifications() {
  const { user } = useAuth();
  const [eligibility, setEligibility] = useState([]);
  const [myCerts, setMyCerts] = useState([]);
  const [allCerts, setAllCerts] = useState(null);
  const [busyLevel, setBusyLevel] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [verifyCode, setVerifyCode] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);
  const [loading, setLoading] = useState(true);

  const canSeeAll = user && ["Instructor", "Administrator", "Accessibility Trainer"].includes(user.role);

  function refresh() {
    setLoading(true);
    Promise.all([api.getCertEligibility(), api.getMyCertificates()])
      .then(([elig, certs]) => {
        setEligibility(elig.levels);
        setMyCerts(certs);
      })
      .finally(() => setLoading(false));
    if (canSeeAll) {
      api.getAllCertificates().then(setAllCerts);
    }
  }

  useEffect(refresh, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleIssue(level) {
    setBusyLevel(level);
    setError("");
    setMessage("");
    try {
      const cert = await api.issueCertificate(level);
      setMessage(`🎉 ${level} certificate issued! Code: ${cert.certificate_code}`);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyLevel(null);
    }
  }

  async function handleVerify(e) {
    e.preventDefault();
    setVerifyResult(null);
    try {
      const res = await api.verifyCertificate(verifyCode.trim());
      setVerifyResult(res);
    } catch (err) {
      setVerifyResult({ valid: false, message: err.message });
    }
  }

  const earnedLevels = new Set(myCerts.filter((c) => c.status === "Active").map((c) => c.level));

  return (
    <div className="page">
      <h1>🎓 Certification Workflows</h1>
      <p className="muted">
        Certificates are issued automatically once your live practice analytics clear each level's
        requirements — nothing here is manually approved.
      </p>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : (
        <div className="cert-grid">
          {eligibility.map((lvl) => {
            const already = earnedLevels.has(lvl.level);
            return (
              <div className="card cert-card" key={lvl.level}>
                <h3>
                  <span className={LEVEL_COLOR[lvl.level]}>{lvl.level}</span>
                </h3>
                <ul className="cert-checklist">
                  <li className={lvl.progress.total_attempts >= lvl.requirements.min_attempts ? "met" : ""}>
                    {lvl.progress.total_attempts} / {lvl.requirements.min_attempts} attempts
                  </li>
                  <li className={lvl.progress.overall_accuracy >= lvl.requirements.min_accuracy ? "met" : ""}>
                    {lvl.progress.overall_accuracy}% / {lvl.requirements.min_accuracy}% accuracy
                  </li>
                  <li className={lvl.progress.gestures_practiced >= lvl.requirements.min_gestures ? "met" : ""}>
                    {lvl.progress.gestures_practiced} / {lvl.requirements.min_gestures} gestures
                  </li>
                  {lvl.requirements.require_no_weak_areas && (
                    <li className={lvl.progress.weak_area_count === 0 ? "met" : ""}>
                      {lvl.progress.weak_area_count === 0
                        ? "No weak areas remaining"
                        : `${lvl.progress.weak_area_count} weak area(s) remaining`}
                    </li>
                  )}
                </ul>

                {already ? (
                  <p className="muted small">✅ Already earned</p>
                ) : (
                  <button
                    className="btn-primary"
                    disabled={!lvl.eligible || busyLevel === lvl.level}
                    onClick={() => handleIssue(lvl.level)}
                  >
                    {busyLevel === lvl.level ? "Issuing…" : lvl.eligible ? "Issue Certificate" : "Not yet eligible"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="card">
        <h3>📜 My Certificates</h3>
        {myCerts.length === 0 ? (
          <p className="muted small">No certificates earned yet — keep practicing!</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Level</th>
                <th>Accuracy</th>
                <th>Attempts</th>
                <th>Status</th>
                <th>Issued</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {myCerts.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span className={LEVEL_COLOR[c.level]}>{c.level}</span>
                  </td>
                  <td>{c.overall_accuracy}%</td>
                  <td>{c.total_attempts}</td>
                  <td>{c.status === "Active" ? "✅ Active" : "🚫 Revoked"}</td>
                  <td>{c.issued_at}</td>
                  <td className="cert-actions">
                    <button
                      className="btn-secondary btn-small"
                      onClick={() => api.downloadCertificate(c.id, c.certificate_code)}
                    >
                      ⬇️ Text
                    </button>
                    <button
                      className="btn-primary btn-small"
                      onClick={() => api.downloadCertificatePdf(c.id, c.certificate_code)}
                    >
                      ⬇️ PDF
                    </button>
                    <button
                      className="btn-secondary btn-small"
                      onClick={() => openPrintableCertificate({ ...c, username: user.username })}
                    >
                      🖨️ Print
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>🔍 Verify a Certificate</h3>
        <p className="muted small">
          Anyone with a certificate code (e.g. an employer) can confirm it's genuine — no login required.
        </p>
        <form className="verify-form" onSubmit={handleVerify}>
          <input
            type="text"
            placeholder="e.g. SLP-BEG-019569B26F"
            value={verifyCode}
            onChange={(e) => setVerifyCode(e.target.value)}
          />
          <button className="btn-secondary" type="submit">
            Verify
          </button>
        </form>
        {verifyResult && (
          <div className={`alert ${verifyResult.valid ? "alert-success" : "alert-error"}`}>
            {verifyResult.valid
              ? `✅ Valid — ${verifyResult.username} holds an active ${verifyResult.level} certificate (${verifyResult.overall_accuracy}% accuracy, issued ${verifyResult.issued_at}).`
              : `❌ ${verifyResult.message || "Not a valid certificate."}`}
          </div>
        )}
      </div>

      {canSeeAll && (
        <div className="card">
          <h3>🏫 Certification Monitoring (All Learners)</h3>
          {!allCerts ? (
            <p className="muted small">Loading…</p>
          ) : allCerts.length === 0 ? (
            <p className="muted small">No certificates issued platform-wide yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Learner</th>
                  <th>Level</th>
                  <th>Accuracy</th>
                  <th>Status</th>
                  <th>Issued</th>
                </tr>
              </thead>
              <tbody>
                {allCerts.map((c) => (
                  <tr key={c.id}>
                    <td>{c.username}</td>
                    <td>
                      <span className={LEVEL_COLOR[c.level]}>{c.level}</span>
                    </td>
                    <td>{c.overall_accuracy}%</td>
                    <td>{c.status === "Active" ? "✅" : "🚫"}</td>
                    <td>{c.issued_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
