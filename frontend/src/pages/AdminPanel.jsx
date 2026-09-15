import { useEffect, useState } from "react";
import { api } from "../api";

const ROLES = ["Learner", "Instructor", "Accessibility Trainer", "Administrator"];
const LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"];

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [selectedUsername, setSelectedUsername] = useState("");
  const [newRole, setNewRole] = useState("Learner");
  const [active, setActive] = useState(true);
  const [newLevel, setNewLevel] = useState("Beginner");
  const [log, setLog] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [certificates, setCertificates] = useState([]);
  const [certError, setCertError] = useState("");
  const [certMessage, setCertMessage] = useState("");

  const [annTitle, setAnnTitle] = useState("");
  const [annMessage, setAnnMessage] = useState("");
  const [annSending, setAnnSending] = useState(false);
  const [annError, setAnnError] = useState("");
  const [annSuccess, setAnnSuccess] = useState("");

  function loadUsers() {
    api.listUsers().then((u) => {
      setUsers(u);
      if (u.length > 0 && !selectedUsername) {
        setSelectedUsername(u[0].username);
      }
    });
  }

  function loadCertificates() {
    api
      .getAllCertificates()
      .then(setCertificates)
      .catch((err) => setCertError(err.message));
  }

  useEffect(() => {
    loadUsers();
    loadCertificates();
    api.getDatasetLog().then(setLog);
  }, []);

  useEffect(() => {
    const u = users.find((x) => x.username === selectedUsername);
    if (u) {
      setNewRole(u.role);
      setActive(!!u.is_active);
      setNewLevel(LEVELS.includes(u.learning_level) ? u.learning_level : "Beginner");
    }
  }, [selectedUsername, users]);

  const selectedUser = users.find((u) => u.username === selectedUsername);

  async function handleUpdateRole() {
    if (!selectedUser) return;
    setError("");
    try {
      await api.updateUserRole(selectedUser.id, newRole);
      setMessage(`Updated ${selectedUser.username}'s role to ${newRole}.`);
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpdateActive() {
    if (!selectedUser) return;
    setError("");
    try {
      await api.updateUserActive(selectedUser.id, active);
      setMessage(`Updated ${selectedUser.username}'s active status to ${active}.`);
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpdateLevel() {
    if (!selectedUser) return;
    setError("");
    try {
      await api.updateUserLevel(selectedUser.id, newLevel);
      setMessage(`Updated ${selectedUser.username}'s learning level to ${newLevel}.`);
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleToggleCertificateStatus(cert) {
    setCertError("");
    setCertMessage("");
    const nextStatus = cert.status === "Active" ? "Revoked" : "Active";
    try {
      await api.updateCertificateStatus(cert.id, nextStatus);
      setCertMessage(`${cert.username}'s ${cert.level} certificate is now ${nextStatus}.`);
      loadCertificates();
    } catch (err) {
      setCertError(err.message);
    }
  }

  async function handlePostAnnouncement(e) {
    e.preventDefault();
    setAnnError("");
    setAnnSuccess("");
    if (annTitle.length < 3) return setAnnError("Title must be at least 3 characters.");
    if (!annMessage) return setAnnError("Please write a message.");
    setAnnSending(true);
    try {
      await api.postAnnouncement({ title: annTitle, message: annMessage });
      setAnnSuccess("📢 Announcement posted — every user will see it in their notification bell.");
      setAnnTitle("");
      setAnnMessage("");
    } catch (err) {
      setAnnError(err.message);
    } finally {
      setAnnSending(false);
    }
  }

  return (
    <div className="page">
      <h1>🛠️ Admin Panel</h1>
      <p className="muted">User management & role-based access control (Administrator only).</p>

      <div className="card">
        <h3>👥 Registered Users</h3>
        {users.length === 0 ? (
          <p className="muted">No users registered yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Level</th>
                <th>Created</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td>{u.learning_level || "Not set"}</td>
                  <td>{u.created_at}</td>
                  <td>{u.is_active ? "✅" : "🚫"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {users.length > 0 && (
        <div className="card">
          <h3>✏️ Manage a User</h3>
          <label>
            Select user
            <select value={selectedUsername} onChange={(e) => setSelectedUsername(e.target.value)}>
              {users.map((u) => (
                <option key={u.id} value={u.username}>
                  {u.username}
                </option>
              ))}
            </select>
          </label>

          <div className="grid-2">
            <div>
              <label>
                New role
                <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn-secondary" onClick={handleUpdateRole}>
                Update role
              </button>
            </div>
            <div>
              <label className="checkbox-label">
                <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
                Account active
              </label>
              <button className="btn-secondary" onClick={handleUpdateActive}>
                Update active status
              </button>
            </div>
            <div>
              <label>
                Learner level (admin override)
                <select value={newLevel} onChange={(e) => setNewLevel(e.target.value)}>
                  {LEVELS.map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn-secondary" onClick={handleUpdateLevel}>
                Update level
              </button>
            </div>
          </div>

          {message && <div className="alert alert-success">{message}</div>}
          {error && <div className="alert alert-error">{error}</div>}
        </div>
      )}

      <div className="card">
        <h3>📢 Post a Platform Announcement</h3>
        <p className="muted small">
          Broadcasts to every user's notification bell immediately (type: <code>announcement</code>).
        </p>
        <form className="form" onSubmit={handlePostAnnouncement}>
          <label>
            Title
            <input value={annTitle} onChange={(e) => setAnnTitle(e.target.value)} maxLength={120} />
          </label>
          <label>
            Message
            <input value={annMessage} onChange={(e) => setAnnMessage(e.target.value)} maxLength={500} />
          </label>
          {annError && <div className="alert alert-error">{annError}</div>}
          {annSuccess && <div className="alert alert-success">{annSuccess}</div>}
          <button className="btn-primary" type="submit" disabled={annSending}>
            {annSending ? "Posting…" : "Post Announcement"}
          </button>
        </form>
      </div>

      <div className="card">
        <h3>🎓 Certificates — Revoke / Reactivate</h3>
        {certError && <div className="alert alert-error">{certError}</div>}
        {certMessage && <div className="alert alert-success">{certMessage}</div>}
        {certificates.length === 0 ? (
          <p className="muted">No certificates issued yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Learner</th>
                <th>Level</th>
                <th>Accuracy</th>
                <th>Code</th>
                <th>Status</th>
                <th>Issued</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {certificates.map((c) => (
                <tr key={c.id}>
                  <td>{c.username}</td>
                  <td>{c.level}</td>
                  <td>{c.overall_accuracy}%</td>
                  <td className="mono small">{c.certificate_code}</td>
                  <td>{c.status === "Active" ? "✅ Active" : "🚫 Revoked"}</td>
                  <td>{c.issued_at}</td>
                  <td>
                    <button className="btn-secondary btn-small" onClick={() => handleToggleCertificateStatus(c)}>
                      {c.status === "Active" ? "Revoke" : "Reactivate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>🗂️ Dataset Integration Log</h3>
        {log.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>Dataset</th>
                <th>Action</th>
                <th>Details</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {log.map((l) => (
                <tr key={l.id}>
                  <td>{l.dataset_name}</td>
                  <td>{l.action}</td>
                  <td>{l.details}</td>
                  <td>{l.performed_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No dataset actions logged yet.</p>
        )}
      </div>
    </div>
  );
}
