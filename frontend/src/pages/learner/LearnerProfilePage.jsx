import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { learnerProfileApi } from '../../api/learnerProfile';
import { Card, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { LoadingScreen } from '../../components/LoadingScreen';
import { formatApiError } from '../../utils/errors';
import { User, Phone, BookOpen, Globe, Target, Camera, Save, Award, Flame, CheckCircle } from 'lucide-react';

export const LearnerProfilePage = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: '', message: '' });

  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    bio: '',
    learning_level: 'beginner',
    preferred_language: 'ASL',
    learning_goals: '',
  });

  const [progressData, setProgressData] = useState({
    total_points: 0,
    current_streak: 0,
    completed_lessons_count: 0,
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await learnerProfileApi.getProfile();
      setProfile(data);
      setFormData({
        full_name: data.full_name || '',
        phone_number: data.phone_number || '',
        bio: data.bio || '',
        learning_level: data.learning_level || 'beginner',
        preferred_language: data.preferred_language || 'ASL',
        learning_goals: data.learning_goals || '',
      });
      setProgressData({
        total_points: data.total_points || 0,
        current_streak: data.current_streak || 0,
        completed_lessons_count: data.completed_lessons_count || 0,
      });
    } catch (err) {
      setStatusMsg({ type: 'error', message: formatApiError(err) });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setStatusMsg({ type: '', message: '' });
  };

  const handleProgressChange = (e) => {
    setProgressData({ ...progressData, [e.target.name]: parseInt(e.target.value) || 0 });
    setStatusMsg({ type: '', message: '' });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg({ type: '', message: '' });

    try {
      const updated = await learnerProfileApi.updateProfile(formData);
      setProfile(updated);
      setStatusMsg({ type: 'success', message: 'Learner profile updated successfully!' });
    } catch (err) {
      setStatusMsg({ type: 'error', message: formatApiError(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleProgressSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg({ type: '', message: '' });

    try {
      const updated = await learnerProfileApi.updateProgress(progressData);
      setProfile(updated);
      setStatusMsg({ type: 'success', message: 'Learner progress metrics updated successfully!' });
    } catch (err) {
      setStatusMsg({ type: 'error', message: formatApiError(err) });
    } finally {
      setSaving(false);
    }
  };

  const handlePictureUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setStatusMsg({ type: '', message: '' });

    try {
      const updated = await learnerProfileApi.uploadPicture(file);
      setProfile(updated);
      setStatusMsg({ type: 'success', message: 'Profile picture uploaded successfully!' });
    } catch (err) {
      setStatusMsg({ type: 'error', message: formatApiError(err) });
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return <LoadingScreen message="Loading profile..." />;
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white">Learner Profile & Goals</h1>
          <p className="text-xs text-slate-400 mt-1">Manage your personal information, skill level, and training preferences.</p>
        </div>
      </div>

      {statusMsg.message && (
        <Alert type={statusMsg.type} message={statusMsg.message} />
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Avatar Card & Account Meta */}
        <div className="space-y-6">
          <Card className="flex flex-col items-center text-center">
            <div className="relative group mb-4">
              <div className="w-28 h-28 rounded-full bg-slate-900 border-2 border-indigo-500/50 flex items-center justify-center overflow-hidden shadow-xl">
                {profile?.profile_picture_url ? (
                  <img
                    src={profile.profile_picture_url}
                    alt="Profile"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-4xl font-extrabold text-indigo-300">
                    {user?.username?.[0]?.toUpperCase()}
                  </span>
                )}
              </div>

              <label className="absolute bottom-0 right-0 p-2 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer shadow-lg transition-transform hover:scale-105">
                <Camera className="w-4 h-4" />
                <input
                  type="file"
                  accept="image/*"
                  onChange={handlePictureUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
            </div>

            <h3 className="text-lg font-bold text-white">{profile?.full_name || user?.username}</h3>
            <p className="text-xs text-slate-400">@{user?.username}</p>

            <div className="mt-4 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
              {user?.role?.name?.replace('_', ' ')}
            </div>
          </Card>

          {/* Quick Stats Box */}
          <Card>
            <CardHeader>
              <CardTitle>Learning Overview</CardTitle>
            </CardHeader>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Learning Level</span>
                <span className="font-semibold text-cyan-300 capitalize">{profile?.learning_level}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Preferred Language</span>
                <span className="font-semibold text-indigo-300">{profile?.preferred_language}</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">Account Created</span>
                <span className="font-semibold text-slate-300">
                  {new Date(user?.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Profile Edit & Progress Forms */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal & Learning Preferences</CardTitle>
              <CardDescription>Update your personal information and sign language training preferences</CardDescription>
            </CardHeader>

            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Full Name"
                  name="full_name"
                  icon={User}
                  value={formData.full_name}
                  onChange={handleInputChange}
                />
                <Input
                  label="Phone Number"
                  name="phone_number"
                  icon={Phone}
                  value={formData.phone_number}
                  onChange={handleInputChange}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                    Learning Level
                  </label>
                  <select
                    name="learning_level"
                    value={formData.learning_level}
                    onChange={handleInputChange}
                    className="glass-input rounded-lg py-2.5 px-3.5 text-sm border-slate-700 bg-slate-900 text-white"
                  >
                    <option value="beginner">Beginner (Foundational Signs & Alphabet)</option>
                    <option value="intermediate">Intermediate (Sentences & Flow)</option>
                    <option value="advanced">Advanced (Fluid Real-Time Signing)</option>
                  </select>
                </div>

                <div className="flex flex-col space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                    Preferred Sign Language
                  </label>
                  <select
                    name="preferred_language"
                    value={formData.preferred_language}
                    onChange={handleInputChange}
                    className="glass-input rounded-lg py-2.5 px-3.5 text-sm border-slate-700 bg-slate-900 text-white"
                  >
                    <option value="ASL">American Sign Language (ASL)</option>
                    <option value="ISL">Indian Sign Language (ISL)</option>
                    <option value="BSL">British Sign Language (BSL)</option>
                    <option value="Auslan">Australian Sign Language (Auslan)</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Bio / Personal Notes
                </label>
                <textarea
                  name="bio"
                  rows={2}
                  value={formData.bio}
                  onChange={handleInputChange}
                  placeholder="Share a short bio or reasons for learning sign language..."
                  className="glass-input rounded-lg py-2.5 px-3.5 text-sm border-slate-700 bg-slate-900 text-white resize-none"
                />
              </div>

              <div className="flex flex-col space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Learning Goals
                </label>
                <textarea
                  name="learning_goals"
                  rows={3}
                  value={formData.learning_goals}
                  onChange={handleInputChange}
                  placeholder="E.g., Master 50 core medical signs by end of month..."
                  className="glass-input rounded-lg py-2.5 px-3.5 text-sm border-slate-700 bg-slate-900 text-white resize-none"
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" variant="primary" isLoading={saving}>
                  <Save className="w-4 h-4 mr-2" />
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </Card>

          {/* Progress Fields Card */}
          <Card>
            <CardHeader>
              <CardTitle>Learner Progress Fields</CardTitle>
              <CardDescription>View or adjust your points, streak, and completed lessons counter</CardDescription>
            </CardHeader>

            <form onSubmit={handleProgressSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Input
                  label="Total Points"
                  name="total_points"
                  type="number"
                  min="0"
                  icon={Award}
                  value={progressData.total_points}
                  onChange={handleProgressChange}
                />
                <Input
                  label="Current Streak (Days)"
                  name="current_streak"
                  type="number"
                  min="0"
                  icon={Flame}
                  value={progressData.current_streak}
                  onChange={handleProgressChange}
                />
                <Input
                  label="Lessons Completed"
                  name="completed_lessons_count"
                  type="number"
                  min="0"
                  icon={CheckCircle}
                  value={progressData.completed_lessons_count}
                  onChange={handleProgressChange}
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" variant="secondary" isLoading={saving}>
                  Update Progress Fields
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};
