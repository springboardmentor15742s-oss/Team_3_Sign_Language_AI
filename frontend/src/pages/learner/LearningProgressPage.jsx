import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import axios from 'axios';

export function LearningProgressPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};

        const [profileRes, datasetRes] = await Promise.all([
          axios.get('/api/v1/learner-profiles/me', { headers }).catch(() => null),
          axios.get('/api/v1/dataset/summary').catch(() => null),
        ]);

        if (profileRes) setProfile(profileRes.data);
        if (datasetRes) setDatasetInfo(datasetRes.data);
      } catch (err) {
        console.error('Failed to load progress details:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Learning Progress & Performance
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Track your ASL learning milestones, streak records, and practice statistics.
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Skill Level</div>
          <div className="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-1 capitalize">
            {profile?.learning_level || 'Beginner'}
          </div>
          <div className="text-xs text-gray-400 mt-1">Current ASL Tier</div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Points</div>
          <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
            {profile?.total_points || 0} XP
          </div>
          <div className="text-xs text-gray-400 mt-1">Earned via lessons & practice</div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Current Streak</div>
          <div className="text-2xl font-extrabold text-amber-500 mt-1">
            🔥 {profile?.current_streak || 0} Days
          </div>
          <div className="text-xs text-gray-400 mt-1">Active daily learning</div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Lessons Completed</div>
          <div className="text-2xl font-extrabold text-purple-600 dark:text-purple-400 mt-1">
            {profile?.completed_lessons_count || 0}
          </div>
          <div className="text-xs text-gray-400 mt-1">Modules finished</div>
        </div>
      </div>

      {/* Dataset & Practice Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* ASL Dataset Summary Card */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>📚</span> Integrated ASL Dataset Summary
          </h2>
          {datasetInfo ? (
            <div className="mt-4 space-y-3 text-sm text-gray-600 dark:text-gray-300">
              <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                <span className="font-medium">Dataset Status:</span>
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 uppercase">
                  {datasetInfo.dataset_status}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                <span className="font-medium">Alphabet Classes:</span>
                <span className="font-bold text-gray-900 dark:text-white">{datasetInfo.number_of_classes} Classes</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                <span className="font-medium">Total Training Samples:</span>
                <span className="font-bold text-indigo-600 dark:text-indigo-400">{datasetInfo.total_train_images} images</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="font-medium">Test Samples:</span>
                <span className="font-bold text-indigo-600 dark:text-indigo-400">{datasetInfo.total_test_images} images</span>
              </div>
              
              {datasetInfo.available_classes?.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Available Gestures/Letters:</div>
                  <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto p-2 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                    {datasetInfo.available_classes.map((cls) => (
                      <span key={cls} className="px-2 py-0.5 text-xs font-mono bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">
                        {cls}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500 mt-2">Loading dataset status...</p>
          )}
        </div>

        {/* Practice Statistics Placeholder */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>🎯</span> Practice & Assessment History
          </h2>
          <div className="mt-4 space-y-4">
            <div className="p-4 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900">
              <div className="font-semibold text-indigo-900 dark:text-indigo-200 text-sm">
                Target Language: {profile?.preferred_language || 'ASL'}
              </div>
              <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                Goals: {profile?.learning_goals || 'Master ASL alphabet signs and gestures'}
              </p>
            </div>

            <div className="border border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 text-center">
              <div className="text-2xl mb-1">🤖</div>
              <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                Milestone 2 AI Assessment Placeholder
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Real-time gesture recognition, accuracy scoring, and live camera assessment metrics will activate in Milestone 2.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LearningProgressPage;
