import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { ADMIN_ROLES, INSTRUCTOR_ROLES } from './auth/roles';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Practice } from './pages/Practice';
import { Instructor } from './pages/Instructor';
import { Admin } from './pages/Admin';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
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
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
