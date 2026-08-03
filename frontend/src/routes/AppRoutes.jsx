import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { LearnerProfilePage } from '../pages/learner/LearnerProfilePage';
import { LearningProgressPage } from '../pages/learner/LearningProgressPage';
import { InstructorDashboard, AccessibilityTrainerDashboard, AdminDashboard } from '../pages/RolePlaceholders';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { ProtectedRoute } from './ProtectedRoute';

export const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected Dashboard Routes */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/profile" element={<LearnerProfilePage />} />
        <Route path="/learning-progress" element={<LearningProgressPage />} />
        <Route path="/instructor" element={<InstructorDashboard />} />
        <Route path="/trainer" element={<AccessibilityTrainerDashboard />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Route>

      {/* Fallback Redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
