import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Administrator is intentionally excluded here — admin accounts are never
// self-registered from the public form, only created/promoted by an
// existing Administrator via the Admin Panel.
const ROLES = ["Learner", "Instructor", "Accessibility Trainer"];

export default function Login() {
  // Top-level split: which kind of account is signing in.
  const [portal, setPortal] = useState("staff"); // "staff" | "admin"

  // Learner/Staff portal has its own login/register sub-tabs.
  const [tab, setTab] = useState("login");
  const { login, logout, register } = useAuth();
  const navigate = useNavigate();

  // Login state (shared field values, used by both portals)
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Admin portal state
  const [adminUsername, setAdminUsername] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminError, setAdminError] = useState("");
  const [adminLoading, setAdminLoading] = useState(false);

  // Register state
  const [rUsername, setRUsername] = useState("");
  const [rEmail, setREmail] = useState("");
  const [rRole, setRRole] = useState("Learner");
  const [rPassword, setRPassword] = useState("");
  const [rConfirm, setRConfirm] = useState("");
  const [registerError, setRegisterError] = useState("");
  const [registerSuccess, setRegisterSuccess] = useState("");
  const [registerLoading, setRegisterLoading] = useState(false);

  function switchPortal(next) {
    setPortal(next);
    setLoginError("");
    setAdminError("");
  }

  async function handleLogin(e) {
    e.preventDefault();
    setLoginError("");
    if (!username || !password) {
      setLoginError("Please enter both username and password.");
      return;
    }
    setLoginLoading(true);
    try {
      const loggedInUser = await login(username, password);
      if (loggedInUser.role === "Administrator") {
        // Administrator accounts should use the Administrator portal instead.
        logout();
        setLoginError(
          "This is an Administrator account. Please use the Administrator tab above to log in."
        );
        return;
      }
      navigate("/dashboard");
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setLoginLoading(false);
    }
  }

  async function handleAdminLogin(e) {
    e.preventDefault();
    setAdminError("");
    if (!adminUsername || !adminPassword) {
      setAdminError("Please enter both username and password.");
      return;
    }
    setAdminLoading(true);
    try {
      const loggedInUser = await login(adminUsername, adminPassword);
      if (loggedInUser.role !== "Administrator") {
        // Valid credentials, but not an admin account — reject clearly and
        // don't leave a stray session behind.
        logout();
        setAdminError("This account is not an Administrator account.");
        return;
      }
      navigate("/admin");
    } catch (err) {
      setAdminError(err.message);
    } finally {
      setAdminLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setRegisterError("");
    setRegisterSuccess("");

    if (rUsername.length < 3) return setRegisterError("Username must be at least 3 characters long.");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(rEmail)) return setRegisterError("Please enter a valid email address.");
    if (rPassword.length < 6) return setRegisterError("Password must be at least 6 characters long.");
    if (rPassword !== rConfirm) return setRegisterError("Passwords do not match.");

    setRegisterLoading(true);
    try {
      await register({ username: rUsername, email: rEmail, password: rPassword, role: rRole });
      setRegisterSuccess("Account created successfully! Please log in from the Login tab.");
      setRUsername("");
      setREmail("");
      setRPassword("");
      setRConfirm("");
      setTab("login");
    } catch (err) {
      setRegisterError(err.message);
    } finally {
      setRegisterLoading(false);
    }
  }

  return (
    <div className="page page-narrow">
      <h1>🔐 Login / Register</h1>

      <div className="tabs">
        <button
          className={portal === "staff" ? "tab active" : "tab"}
          onClick={() => switchPortal("staff")}
        >
          Learner / Staff
        </button>
        <button
          className={portal === "admin" ? "tab active" : "tab"}
          onClick={() => switchPortal("admin")}
        >
          Administrator
        </button>
      </div>

      {portal === "admin" && (
        <form className="card form" onSubmit={handleAdminLogin}>
          <h3>Administrator sign-in</h3>
          <p className="muted small">
            For platform administrators only. Learner, Instructor, and Accessibility Trainer
            accounts should use the Learner / Staff tab instead.
          </p>
          <label>
            Username
            <input value={adminUsername} onChange={(e) => setAdminUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input
              type="password"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
            />
          </label>
          {adminError && <div className="alert alert-error">{adminError}</div>}
          <button className="btn-primary" type="submit" disabled={adminLoading}>
            {adminLoading ? "Logging in..." : "Log in as Administrator"}
          </button>
        </form>
      )}

      {portal === "staff" && (
        <>
          <div className="tabs">
            <button className={tab === "login" ? "tab active" : "tab"} onClick={() => setTab("login")}>
              Login
            </button>
            <button
              className={tab === "register" ? "tab active" : "tab"}
              onClick={() => setTab("register")}
            >
              Register
            </button>
          </div>

          {tab === "login" && (
        <form className="card form" onSubmit={handleLogin}>
          <h3>Login to your account</h3>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {loginError && <div className="alert alert-error">{loginError}</div>}
          <button className="btn-primary" type="submit" disabled={loginLoading}>
            {loginLoading ? "Logging in..." : "Log in"}
          </button>
        </form>
      )}

      {tab === "register" && (
        <form className="card form" onSubmit={handleRegister}>
          <h3>Create a new account</h3>
          <label>
            Choose a username
            <input value={rUsername} onChange={(e) => setRUsername(e.target.value)} />
          </label>
          <label>
            Email address
            <input type="email" value={rEmail} onChange={(e) => setREmail(e.target.value)} />
          </label>
          <label>
            Role
            <select value={rRole} onChange={(e) => setRRole(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <label>
            Password
            <input type="password" value={rPassword} onChange={(e) => setRPassword(e.target.value)} />
          </label>
          <label>
            Confirm password
            <input type="password" value={rConfirm} onChange={(e) => setRConfirm(e.target.value)} />
          </label>
          {registerError && <div className="alert alert-error">{registerError}</div>}
          {registerSuccess && <div className="alert alert-success">{registerSuccess}</div>}
          <button className="btn-primary" type="submit" disabled={registerLoading}>
            {registerLoading ? "Registering..." : "Register"}
          </button>
        </form>
          )}
        </>
      )}

      <p className="muted small">
        Passwords are stored as salted SHA-256 hashes for this Milestone-1 prototype; sessions use
        signed JWTs. See docs/architecture.md for the full production auth plan (OAuth2, etc.)
      </p>
    </div>
  );
}
