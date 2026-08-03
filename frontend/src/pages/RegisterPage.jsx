import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, UserCheck, ShieldCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Alert } from '../components/ui/Alert';
import { formatApiError } from '../utils/errors';

export const RegisterPage = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role_name: 'learner',
  });
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const roles = [
    { id: 'learner', name: 'Learner', desc: 'Default student account to learn sign language' },
    { id: 'instructor', name: 'Instructor', desc: 'Course management & evaluation' },
    { id: 'accessibility_trainer', name: 'Accessibility Trainer', desc: 'Inclusion & accessibility lead' },
    { id: 'administrator', name: 'Administrator', desc: 'System admin & user management' },
  ];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.username || !formData.email || !formData.password) {
      setErrorMsg('Please fill in all required fields.');
      return;
    }

    if (formData.password.length < 8) {
      setErrorMsg('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);
    setErrorMsg('');

    try {
      await register(formData);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 selection:bg-indigo-500 selection:text-white my-8">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center space-x-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center text-2xl font-bold shadow-xl shadow-indigo-500/25">
              🤟
            </div>
          </Link>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Create Account</h1>
          <p className="text-xs text-slate-400 mt-1">Join the AI-Powered Sign Language Platform</p>
        </div>

        <div className="rounded-2xl glass-panel p-8 border border-slate-800 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMsg && <Alert type="error" message={errorMsg} />}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Full Name"
                name="full_name"
                placeholder="Alex Morgan"
                icon={User}
                value={formData.full_name}
                onChange={handleChange}
              />
              <Input
                label="Username *"
                name="username"
                placeholder="alexmorgan"
                icon={UserCheck}
                value={formData.username}
                onChange={handleChange}
                required
              />
            </div>

            <Input
              label="Email Address *"
              name="email"
              type="email"
              placeholder="alex@example.com"
              icon={Mail}
              value={formData.email}
              onChange={handleChange}
              required
            />

            <Input
              label="Password *"
              name="password"
              type="password"
              placeholder="Min. 8 characters"
              icon={Lock}
              value={formData.password}
              onChange={handleChange}
              required
            />

            {/* Role Selection */}
            <div className="space-y-1.5 pt-2">
              <label className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
                Select Platform Role
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {roles.map((role) => (
                  <button
                    key={role.id}
                    type="button"
                    onClick={() => setFormData({ ...formData, role_name: role.id })}
                    className={`p-3 rounded-xl text-left border transition-all ${
                      formData.role_name === role.id
                        ? 'bg-indigo-600/20 border-indigo-500/80 text-white shadow-md shadow-indigo-500/10'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <p className="text-xs font-bold capitalize">{role.name}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5 leading-snug">{role.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              className="w-full mt-4"
            >
              Complete Registration
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-indigo-400 hover:text-indigo-300 underline underline-offset-4">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
