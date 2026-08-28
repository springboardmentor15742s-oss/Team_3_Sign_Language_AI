import React, { useCallback, useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { AchievementsPanel } from '../components/AchievementsPanel';
import { Topbar } from '../components/Topbar';
import { LearnerProfile as LearnerProfileData, LearnerProfileUpdate } from '../types/profile';
import { LearnerProgress } from '../types/progress';
import './Profile.css';

const LEARNING_LEVELS = ['beginner', 'intermediate', 'advanced'];

export function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<LearnerProfileData | null>(null);
  const [progress, setProgress] = useState<LearnerProgress | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [learningLevel, setLearningLevel] = useState('beginner');
  const [preferredLanguage, setPreferredLanguage] = useState('ASL');
  const [learningGoals, setLearningGoals] = useState('');

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    setLoadError(null);
    try {
      const [profileRes, progressRes] = await Promise.all([
        client.get<LearnerProfileData>('/api/profile/me'),
        client.get<LearnerProgress>(`/api/learner/${user.id}/progress`),
      ]);
      setProfile(profileRes.data);
      setLearningLevel(profileRes.data.learning_level);
      setPreferredLanguage(profileRes.data.preferred_language);
      setLearningGoals(profileRes.data.learning_goals ?? '');
      setProgress(progressRes.data);
    } catch (err) {
      console.error('Failed to load profile:', err);
      setLoadError('Could not load your profile.');
    }
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSaving(true);
      setSaveError(null);
      setSavedAt(null);
      try {
        const updates: LearnerProfileUpdate = {
          learning_level: learningLevel,
          preferred_language: preferredLanguage,
          learning_goals: learningGoals,
        };
        const response = await client.put<LearnerProfileData>('/api/profile/me', updates);
        setProfile(response.data);
        setSavedAt(Date.now());
      } catch (err) {
        console.error('Failed to save profile:', err);
        setSaveError('Could not save your changes. Please try again.');
      } finally {
        setSaving(false);
      }
    },
    [learningLevel, preferredLanguage, learningGoals]
  );

  const initial = user?.name?.trim()?.[0]?.toUpperCase() ?? '?';

  return (
    <div className="page profile">
      <Topbar title="Your Profile" />

      {user && (
        <div className="profile-header">
          <div className="profile-header__avatar">{initial}</div>
          <div>
            <h2 className="profile-header__name">{user.name}</h2>
            <p className="profile-header__email">{user.email}</p>
            <span className="profile-header__role">{user.role}</span>
          </div>
        </div>
      )}

      {loadError && <p className="status-message status-message--error">{loadError}</p>}

      {!loadError && profile === null && (
        <div className="content-loading">
          <p className="status-message">Loading your profile&hellip;</p>
        </div>
      )}

      {profile && (
        <form className="panel profile-form" onSubmit={handleSave}>
          <h2 className="panel__title">Learning preferences</h2>

          <label className="profile-form__field">
            Current level
            <select value={learningLevel} onChange={(e) => setLearningLevel(e.target.value)}>
              {LEARNING_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </label>

          <label className="profile-form__field">
            Preferred sign language
            <input
              type="text"
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)}
              placeholder="ASL"
            />
          </label>

          <label className="profile-form__field">
            Your learning goals
            <textarea
              value={learningGoals}
              onChange={(e) => setLearningGoals(e.target.value)}
              placeholder="e.g. Get comfortable with the full alphabet, then move on to everyday phrases."
            />
          </label>

          <div className="profile-form__actions">
            <button type="submit" className="btn" disabled={saving}>
              {saving ? 'Saving…' : 'Save changes'}
            </button>
            {savedAt && <span className="status-message">Saved.</span>}
            {saveError && <span className="status-message status-message--error">{saveError}</span>}
          </div>
        </form>
      )}

      {progress && <AchievementsPanel achievements={progress.achievements} />}
    </div>
  );
}
