import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { ADMIN_ROLES, INSTRUCTOR_ROLES } from './auth/roles';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { AnalyticsReports } from './pages/AnalyticsReports';
import { Practice } from './pages/Practice';
import { CommonSigns } from './pages/CommonSigns';
import { MotionSigns } from './pages/MotionSigns';
import { Courses } from './pages/Courses';
import { ConversationalFluency } from './pages/ConversationalFluency';
import { Instructor } from './pages/Instructor';
import { InstructorLearnerDetail } from './pages/InstructorLearnerDetail';
import { Admin } from './pages/Admin';

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
            path="/analytics-reports"
            element={
              <ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor">
                <AnalyticsReports />
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
          {/* Also wasn't wired up — ConversationalFluency.tsx (the
              16-word MS-ASL course) existed and was linked from the
              Landing page's course catalog and from assignment links,
              but had no route, so every link to it bounced to "/". */}
          <Route
            path="/conversational-fluency"
            element={
              <ProtectedRoute deniedRoles={INSTRUCTOR_ROLES} redirectTo="/instructor">
                <ConversationalFluency />
              </ProtectedRoute>
            }
          />
          <Route
            path="/instructor"
            element={
              <ProtectedRoute roles={INSTRUCTOR_ROLES} redirectTo="/dashboard">
                <Instructor />
              </ProtectedRoute>
            }
          />
          {/* Wasn't wired up until now — InstructorLearnerDetail.tsx
              (the roster drill-down: weak areas, assignments, reference
              media, notes) existed but had no route pointing at it, so a
              roster row had nowhere to link to. */}
          <Route
            path="/instructor/learners/:learnerId"
            element={
              <ProtectedRoute roles={INSTRUCTOR_ROLES} redirectTo="/dashboard">
                <InstructorLearnerDetail />
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
