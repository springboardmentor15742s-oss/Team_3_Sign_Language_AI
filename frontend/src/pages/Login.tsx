import axios from 'axios';
import React, { useState, FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { ADMIN_ROLES, INSTRUCTOR_ROLES } from '../auth/roles';
import './Auth.css';

// Self-service registration only ever creates learner accounts —
// instructor/admin accounts are provisioned separately.
const SELF_SERVICE_ROLE = 'learner';

type AuthTab = 'login' | 'signup';

function homeRouteFor(role: string): string {
  if (ADMIN_ROLES.includes(role)) return '/admin';
  if (INSTRUCTOR_ROLES.includes(role)) return '/instructor';
  return '/dashboard';
}

export function Login() {
  const location = useLocation();
  const navigate = useNavigate();
  const [tab, setTab] = useState<AuthTab>(location.pathname === '/register' ? 'signup' : 'login');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { login, register } = useAuth();

  const switchTab = (nextTab: AuthTab) => {
    setTab(nextTab);
    setError(null);
  };

  const handleLoginSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const loggedInUser = await login(email, password);
      navigate(homeRouteFor(loggedInUser.role));
    } catch (err) {
      setError('Login failed. Check your email and password.');
    }
  };

  const handleRegisterSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await register(name, email, password, SELF_SERVICE_ROLE);
      navigate('/dashboard');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 400) {
        setError(err.response.data?.detail ?? 'Registration failed.');
      } else {
        setError('Registration failed. Please try again.');
      }
    }
  };

  return (
    <div className="page auth-page">
      <div className="auth-card">
        <h1 className="auth-card__heading">Sign Language Platform</h1>

        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'login'}
            className={`auth-tabs__tab${tab === 'login' ? ' auth-tabs__tab--active' : ''}`}
            onClick={() => switchTab('login')}
          >
            Log in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'signup'}
            className={`auth-tabs__tab${tab === 'signup' ? ' auth-tabs__tab--active' : ''}`}
            onClick={() => switchTab('signup')}
          >
            Sign up
          </button>
        </div>

        {tab === 'login' ? (
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <label className="auth-form__field" htmlFor="email">
              <span>Email</span>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="auth-form__field" htmlFor="password">
              <span>Password</span>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {error && <p className="status-message status-message--error">{error}</p>}
            <button type="submit" className="btn auth-form__submit">
              Log in
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
            <label className="auth-form__field" htmlFor="name">
              <span>Name</span>
              <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className="auth-form__field" htmlFor="email">
              <span>Email</span>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="auth-form__field" htmlFor="password">
              <span>Password</span>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <label className="auth-form__field" htmlFor="role">
              <span>Account type</span>
              <select id="role" value={SELF_SERVICE_ROLE} disabled>
                <option value="learner">Learner</option>
              </select>
            </label>
            {error && <p className="status-message status-message--error">{error}</p>}
            <button type="submit" className="btn auth-form__submit">
              Sign up
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
