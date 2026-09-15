import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Avatar from "./Avatar";
import NotificationBell from "./NotificationBell";

const ROLE_BADGE = {
  Learner: "🟢",
  Instructor: "🔵",
  "Accessibility Trainer": "🟣",
  Administrator: "🔴",
};

function navLinkClass({ isActive }) {
  return isActive ? "nav-link active" : "nav-link";
}

export default function Navbar() {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const displayName = profile?.display_name || user?.username;

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <NavLink to="/">🤟 Sign Language Platform</NavLink>
      </div>
      <div className="navbar-links">
        <NavLink to="/" className={navLinkClass} end>
          Home
        </NavLink>
        {user && (
          <>
            <NavLink to="/dashboard" className={navLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/courses" className={navLinkClass}>
              Courses
            </NavLink>
            <NavLink to="/datasets" className={navLinkClass}>
              Dataset Explorer
            </NavLink>
            <NavLink to="/gesture-practice" className={navLinkClass}>
              Gesture Practice
            </NavLink>
            <NavLink to="/quiz" className={navLinkClass}>
              Quiz
            </NavLink>
            <NavLink to="/certifications" className={navLinkClass}>
              Certifications
            </NavLink>
            <NavLink to="/reports" className={navLinkClass}>
              Reports
            </NavLink>
            {user.role === "Administrator" && (
              <NavLink to="/admin" className={navLinkClass}>
                Admin Panel
              </NavLink>
            )}
          </>
        )}
      </div>
      <div className="navbar-user">
        {user ? (
          <>
            <NotificationBell />
            <NavLink to="/profile" className="user-chip">
              <Avatar name={displayName} photo={profile?.avatar_data} size={30} />
              <span className="user-chip-name">
                {ROLE_BADGE[user.role] || "⚪"} {displayName}
              </span>
            </NavLink>
            <button className="btn-secondary" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <NavLink to="/login" className="btn-primary">
            Login / Register
          </NavLink>
        )}
      </div>
    </nav>
  );
}
