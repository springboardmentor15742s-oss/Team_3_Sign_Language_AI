import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import DatasetExplorer from "./pages/DatasetExplorer";
import GesturePractice from "./pages/GesturePractice";
import AdminPanel from "./pages/AdminPanel";
import Certifications from "./pages/Certifications";
import Reports from "./pages/Reports";
import CourseCatalog from "./pages/CourseCatalog";
import CourseWatch from "./pages/CourseWatch";
import Quiz from "./pages/Quiz";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/datasets"
              element={
                <ProtectedRoute>
                  <DatasetExplorer />
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses"
              element={
                <ProtectedRoute>
                  <CourseCatalog />
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses/:courseId"
              element={
                <ProtectedRoute>
                  <CourseWatch />
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses/:courseId/lesson/:lessonId"
              element={
                <ProtectedRoute>
                  <CourseWatch />
                </ProtectedRoute>
              }
            />
            <Route
              path="/gesture-practice"
              element={
                <ProtectedRoute>
                  <GesturePractice />
                </ProtectedRoute>
              }
            />
            <Route
              path="/certifications"
              element={
                <ProtectedRoute>
                  <Certifications />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <Reports />
                </ProtectedRoute>
              }
            />
            <Route
              path="/quiz"
              element={
                <ProtectedRoute>
                  <Quiz />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={["Administrator"]}>
                  <AdminPanel />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  );
}
