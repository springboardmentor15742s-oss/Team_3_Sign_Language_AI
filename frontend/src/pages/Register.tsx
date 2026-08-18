import axios from 'axios';
import React, { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

// Self-service registration only ever creates learner accounts —
// instructor/admin accounts are provisioned separately (see how the test
// instructor/admin accounts were created via direct API calls, not this form).
const SELF_SERVICE_ROLE = 'learner';

export function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
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
    <div>
      <h1>Register</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name">Name</label>
          <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
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
        <div>
          <label htmlFor="role">Account type</label>
          <select id="role" value={SELF_SERVICE_ROLE} disabled>
            <option value="learner">Learner</option>
          </select>
        </div>
        <button type="submit">Register</button>
      </form>
      {error && <p>{error}</p>}
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
