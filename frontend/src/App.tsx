import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { ADMIN_ROLES, INSTRUCTOR_ROLES } from './auth/roles';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Practice } from './pages/Practice';
import { CommonSigns } from './pages/CommonSigns';
import { MotionSigns } from './pages/MotionSigns';
import { Courses } from './pages/Courses';
import { Instructor } from './pages/Instructor';
import { Admin } from './pages/Admin';
import { SpeedQuiz } from './pages/SpeedQuiz';
import { AnalyticsReports } from './pages/AnalyticsReports';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public — same page for logged-out visitors and logged-in
              users alike (the nav/CTA adapt via useAuth inside Landing);
              this is now the default landing spot, not an auto-redirect
              into /dashboard. */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor">
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/practice"
            element={
              <ProtectedRoute>
                <Practice />
              </ProtectedRoute>
            }
          />
          <Route
            path="/common-signs"
            element={
              <ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor">
                <CommonSigns />
              </ProtectedRoute>
            }
          />
          <Route
            path="/motion-signs"
            element={
              <ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor">
                <MotionSigns />
              </ProtectedRoute>
            }
          />
          <Route
            path="/courses"
            element={
              <ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor">
                <Courses />
              </ProtectedRoute>
            }
          />
          <Route path="/speed-quiz" element={<ProtectedRoute><SpeedQuiz /></ProtectedRoute>} />
          <Route path="/analytics-reports" element={<ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor"><AnalyticsReports /></ProtectedRoute>} />
          <Route
            path="/instructor"
            element={
              <ProtectedRoute roles={INSTRUCTOR_ROLES} redirectTo="/dashboard">
                <Instructor />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={ADMIN_ROLES} redirectTo="/dashboard">
                <Admin />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
