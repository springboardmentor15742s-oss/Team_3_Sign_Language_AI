import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { learnerProfileApi } from '../api/learnerProfile';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { LoadingScreen } from '../components/LoadingScreen';
import { Award, Flame, BookCheck, User, Sparkles, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await learnerProfileApi.getProfile();
        setProfile(data);
      } catch (e) {
        console.error('Failed to load profile details', e);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  if (loading) {
    return <LoadingScreen message="Loading Dashboard..." />;
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl p-6 md:p-8 bg-gradient-to-r from-indigo-950 via-slate-900 to-slate-950 border border-indigo-500/20 shadow-2xl">
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -mr-20 -mt-20" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span className="capitalize">Role: {user?.role?.name?.replace('_', ' ')}</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight">
              Welcome back, {profile?.full_name || user?.username}!
            </h1>
            <p className="text-slate-300 text-sm mt-1 max-w-xl">
              Track your learning goals, view daily streak progression, and manage your learner profile credentials.
            </p>
          </div>

          <Link to="/profile">
            <Button variant="primary" size="md">
              <User className="w-4 h-4 mr-2" />
              Manage Profile
            </Button>
          </Link>
        </div>
      </div>

      {/* Progress Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card hoverEffect>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Points</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{profile?.total_points || 0}</h3>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center">
              <Award className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-4 flex items-center">
            <span className="text-emerald-400 font-semibold mr-1">+10 pts</span> earned per gesture module
          </p>
        </Card>

        <Card hoverEffect>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Current Streak</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{profile?.current_streak || 0} Days</h3>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center">
              <Flame className="w-6 h-6 animate-bounce" />
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-4">Keep practicing daily to build your sign habits</p>
        </Card>

        <Card hoverEffect>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lessons Completed</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{profile?.completed_lessons_count || 0}</h3>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
              <BookCheck className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-4 capitalize">
            Current Level: <span className="text-cyan-300 font-semibold">{profile?.learning_level || 'Beginner'}</span>
          </p>
        </Card>
      </div>

      {/* Profile Overview & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Learner Profile Credentials</CardTitle>
            <CardDescription>Verified account data connected to PostgreSQL</CardDescription>
          </CardHeader>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <p className="text-xs text-slate-400">Account Email</p>
              <p className="font-semibold text-white mt-1">{user?.email}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <p className="text-xs text-slate-400">Username</p>
              <p className="font-semibold text-white mt-1">@{user?.username}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <p className="text-xs text-slate-400">Preferred Language</p>
              <p className="font-semibold text-indigo-300 mt-1">{profile?.preferred_language || 'ASL'}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <p className="text-xs text-slate-400">Learning Goals</p>
              <p className="font-semibold text-slate-300 mt-1 truncate">
                {profile?.learning_goals || 'Not configured yet'}
              </p>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <Link to="/profile">
              <Button variant="outline" size="sm">Edit Details & Goals</Button>
            </Link>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Milestone 1 Status</CardTitle>
            <CardDescription>Core Platform Readiness</CardDescription>
          </CardHeader>

          <ul className="space-y-3 text-xs">
            <li className="flex items-center text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 shrink-0" />
              <span>FastAPI Backend & CORS API</span>
            </li>
            <li className="flex items-center text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 shrink-0" />
              <span>PostgreSQL & Alembic ORM</span>
            </li>
            <li className="flex items-center text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 shrink-0" />
              <span>JWT Authentication & Tokens</span>
            </li>
            <li className="flex items-center text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 shrink-0" />
              <span>Role-Based Access Control (4 Roles)</span>
            </li>
            <li className="flex items-center text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 shrink-0" />
              <span>Learner Profile CRUD & Uploads</span>
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
};
