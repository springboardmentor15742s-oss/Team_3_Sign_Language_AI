import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Avatar from "../components/Avatar";

const LEARNING_LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"];
const PREFERRED_LANGUAGES = [
  "ASL (American Sign Language)",
  "BSL (British Sign Language)",
  "ISL (Indian Sign Language)",
  "Other",
];
const LEARNING_GOAL_OPTIONS = [
  "Everyday Communication",
  "Educational Vocabulary",
  "Professional Communication",
  "Certification Preparation",
];

const MAX_DIMENSION = 300;

function resizeImageToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read that file."));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("That file isn't a readable image."));
      img.onload = () => {
        let { width, height } = img;
        if (width > height && width > MAX_DIMENSION) {
          height = Math.round((height * MAX_DIMENSION) / width);
          width = MAX_DIMENSION;
        } else if (height > MAX_DIMENSION) {
          width = Math.round((width * MAX_DIMENSION) / height);
          height = MAX_DIMENSION;
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        canvas.getContext("2d").drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL("image/jpeg", 0.85));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

export default function Profile() {
  const { user, profile, refreshProfile } = useAuth();
  const fileInputRef = useRef(null);

  const [displayName, setDisplayName] = useState("");
  const [editingName, setEditingName] = useState(false);
  const [avatarBusy, setAvatarBusy] = useState(false);

  const [learningLevel, setLearningLevel] = useState("Beginner");
  const [preferredLanguage, setPreferredLanguage] = useState(PREFERRED_LANGUAGES[0]);
  const [goals, setGoals] = useState([]);
  const [bio, setBio] = useState("");
  const [prefsMessage, setPrefsMessage] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);

  const [openSection, setOpenSection] = useState("preferences");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setLearningLevel(p.learning_level);
        setPreferredLanguage(p.preferred_language);
        setGoals(p.learning_goals);
        setBio(p.bio || "");
      })
      .catch(() => {
        // No profile yet — defaults stay, that's fine.
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (profile?.display_name) setDisplayName(profile.display_name);
  }, [profile]);

  function toggleGoal(goal) {
    setGoals((prev) => (prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal]));
  }

  async function handlePhotoChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarBusy(true);
    try {
      const dataUrl = await resizeImageToDataUrl(file);
      await api.saveProfileIdentity({ display_name: profile?.display_name || null, avatar_data: dataUrl });
      await refreshProfile();
    } catch (err) {
      alert(err.message);
    } finally {
      setAvatarBusy(false);
      e.target.value = "";
    }
  }

  async function saveDisplayName() {
    try {
      await api.saveProfileIdentity({ display_name: displayName || null, avatar_data: profile?.avatar_data || null });
      await refreshProfile();
      setEditingName(false);
    } catch (err) {
      alert(err.message);
    }
  }

  async function handlePrefsSubmit(e) {
    e.preventDefault();
    setPrefsMessage("");
    try {
      await api.saveProfile({
        learning_level: learningLevel,
        preferred_language: preferredLanguage,
        learning_goals: goals,
        bio,
      });
      setPrefsMessage("Learning preferences saved!");
    } catch (err) {
      setPrefsMessage(`Error: ${err.message}`);
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setPasswordMessage("");
    if (newPassword !== confirmPassword) {
      setPasswordMessage("Error: New passwords don't match.");
      return;
    }
    setPasswordBusy(true);
    try {
      await api.changePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordMessage("Password updated successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordMessage(`Error: ${err.message}`);
    } finally {
      setPasswordBusy(false);
    }
  }

  if (loading) return <div className="page">Loading profile…</div>;

  const nameForAvatar = profile?.display_name || user.username;

  return (
    <div className="page page-narrow">
      {/* ---- Profile header: photo + identity ---- */}
      <div className="profile-header card">
        <div className="profile-avatar-wrap">
          <Avatar name={nameForAvatar} photo={profile?.avatar_data} size={96} />
          <button
            className="avatar-edit-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={avatarBusy}
            title="Change profile photo"
          >
            {avatarBusy ? "…" : "📷"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="visually-hidden"
            onChange={handlePhotoChange}
          />
        </div>

        <div className="profile-identity">
          {editingName ? (
            <div className="edit-name-row">
              <input
                autoFocus
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={user.username}
                maxLength={60}
              />
              <button className="btn-primary btn-small" onClick={saveDisplayName}>
                Save
              </button>
              <button className="btn-secondary btn-small" onClick={() => setEditingName(false)}>
                Cancel
              </button>
            </div>
          ) : (
            <h1 className="profile-name" onClick={() => setEditingName(true)} title="Click to edit">
              {profile?.display_name || user.username} <span className="edit-pencil">✏️</span>
            </h1>
          )}
          <p className="muted">
            @{user.username} · {user.email}
          </p>
          <span className="role-pill">{user.role}</span>
          <span className="muted small"> · Member since {new Date(user.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* ---- Settings sections ---- */}
      <h2 className="settings-heading">⚙️ Settings</h2>

      <div className="card settings-section">
        <button
          className="settings-toggle"
          onClick={() => setOpenSection(openSection === "preferences" ? null : "preferences")}
        >
          <span>🎯 Learning Preferences</span>
          <span>{openSection === "preferences" ? "▲" : "▼"}</span>
        </button>
        {openSection === "preferences" && (
          <form className="form settings-body" onSubmit={handlePrefsSubmit}>
            <label>
              Learning Level
              <select value={learningLevel} onChange={(e) => setLearningLevel(e.target.value)}>
                {LEARNING_LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Preferred Sign Language
              <select value={preferredLanguage} onChange={(e) => setPreferredLanguage(e.target.value)}>
                {PREFERRED_LANGUAGES.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </label>

            <div>
              <div className="field-label">Learning Goals</div>
              {LEARNING_GOAL_OPTIONS.map((g) => (
                <label key={g} className="checkbox-label">
                  <input type="checkbox" checked={goals.includes(g)} onChange={() => toggleGoal(g)} />
                  {g}
                </label>
              ))}
            </div>

            <label>
              About you (optional)
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="E.g. Learning ASL to communicate with my hard-of-hearing colleague..."
                rows={3}
              />
            </label>

            {prefsMessage && (
              <div className={prefsMessage.startsWith("Error") ? "alert alert-error" : "alert alert-success"}>
                {prefsMessage}
              </div>
            )}

            <button className="btn-primary" type="submit">
              💾 Save Preferences
            </button>
          </form>
        )}
      </div>

      <div className="card settings-section">
        <button
          className="settings-toggle"
          onClick={() => setOpenSection(openSection === "security" ? null : "security")}
        >
          <span>🔒 Account & Security</span>
          <span>{openSection === "security" ? "▲" : "▼"}</span>
        </button>
        {openSection === "security" && (
          <form className="form settings-body" onSubmit={handlePasswordSubmit}>
            <label>
              Current Password
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </label>
            <label>
              New Password
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={6}
                required
              />
            </label>
            <label>
              Confirm New Password
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={6}
                required
              />
            </label>

            {passwordMessage && (
              <div className={passwordMessage.startsWith("Error") ? "alert alert-error" : "alert alert-success"}>
                {passwordMessage}
              </div>
            )}

            <button className="btn-primary" type="submit" disabled={passwordBusy}>
              {passwordBusy ? "Updating…" : "🔑 Update Password"}
            </button>
          </form>
        )}
      </div>

      <div className="card settings-section">
        <button
          className="settings-toggle"
          onClick={() => setOpenSection(openSection === "account" ? null : "account")}
        >
          <span>👤 Account Info</span>
          <span>{openSection === "account" ? "▲" : "▼"}</span>
        </button>
        {openSection === "account" && (
          <div className="settings-body">
            <p>
              <strong>Username:</strong> {user.username}
            </p>
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>Role:</strong> {user.role}
            </p>
            <p>
              <strong>Account created:</strong> {new Date(user.created_at).toLocaleString()}
            </p>
            <p className="muted small">Username and role are managed by your Administrator.</p>
          </div>
        )}
      </div>
    </div>
  );
}
