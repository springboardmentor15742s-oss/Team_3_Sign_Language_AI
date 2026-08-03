import React from 'react';
import { useAuth } from '../hooks/useAuth';

export function InstructorDashboard() {
  const { user } = useAuth();

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-3xl">👨‍🏫</span>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Instructor Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Welcome, Instructor {user?.username}!</p>
        </div>
      </div>
      <div className="p-4 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg">
        <p className="text-sm text-amber-800 dark:text-amber-300 font-medium">
          Role-Based Workspace Reserved: Instructor Module
        </p>
        <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
          Curriculum creation, student progress evaluation, and assessment feedback tools will be unlocked in upcoming milestones.
        </p>
      </div>
    </div>
  );
}

export function AccessibilityTrainerDashboard() {
  const { user } = useAuth();

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-3xl">🤟</span>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Accessibility Trainer Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Welcome, Trainer {user?.username}!</p>
        </div>
      </div>
      <div className="p-4 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-800 dark:text-blue-300 font-medium">
          Role-Based Workspace Reserved: Accessibility & Gesture Studio
        </p>
        <p className="text-xs text-blue-700 dark:text-blue-400 mt-1">
          Specialized feedback tools, gesture adaptation datasets, and accessibility calibration controls reserved for trainers.
        </p>
      </div>
    </div>
  );
}

export function AdminDashboard() {
  const { user } = useAuth();

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-3xl">⚙️</span>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Administrator Control Panel</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Welcome, Admin {user?.username}!</p>
        </div>
      </div>
      <div className="p-4 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 rounded-lg">
        <p className="text-sm text-purple-800 dark:text-purple-300 font-medium">
          Role-Based Workspace Reserved: System Administration
        </p>
        <p className="text-xs text-purple-700 dark:text-purple-400 mt-1">
          User management, role assignment, platform analytics, and dataset model deployment settings are accessible here.
        </p>
      </div>
    </div>
  );
}
