import React, { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { ADMIN_ROLES, INSTRUCTOR_ROLES } from '../auth/roles';

function homeRouteFor(role: string): string {
  if (ADMIN_ROLES.includes(role)) return '/admin';
  if (INSTRUCTOR_ROLES.includes(role)) return '/instructor';
  return '/dashboard';
}

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const loggedInUser = await login(email, password);
      navigate(homeRouteFor(loggedInUser.role));
    } catch (err) {
      setError('Login failed. Check your email and password.');
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Log in</button>
      </form>
      {error && <p>{error}</p>}
    </div>
  );
}
