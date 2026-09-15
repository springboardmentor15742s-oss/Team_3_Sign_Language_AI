import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="page-center">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="page-center">
        <div className="card">
          <h2>⛔ Access denied</h2>
          <p>
            This page is restricted to: <strong>{allowedRoles.join(", ")}</strong>.
          </p>
          <p>
            Your role: <strong>{user.role}</strong>
          </p>
        </div>
      </div>
    );
  }

  return children;
}
