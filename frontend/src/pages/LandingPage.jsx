import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Shield, Accessibility, BookOpen, ArrowRight, CheckCircle, Video, Award, Users } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-800/80 backdrop-blur-md sticky top-0 z-50 bg-slate-950/80 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-xl shadow-lg shadow-indigo-500/30">
            🤟
          </div>
          <span className="text-xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-100 to-cyan-300">
            SignAI
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link to="/register">
            <Button variant="accent" size="sm">Get Started</Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-28 px-6 text-center max-w-5xl mx-auto flex-1 flex flex-col items-center justify-center">
        <div className="absolute inset-0 -z-10 flex items-center justify-center">
          <div className="w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
          <div className="w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl -ml-32" />
        </div>



        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white max-w-4xl leading-tight mb-6">
          Learn Sign Language with <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400">
            AI-Driven Feedback & Assessments
          </span>
        </h1>

        <p className="text-base md:text-lg text-slate-300 max-w-2xl mb-10 leading-relaxed">
          Empowering learners, accessibility trainers, and instructors with computer vision gesture analysis, structured learning paths, and personalized learner profiles.
        </p>

        <div className="flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
          <Link to="/register" className="w-full sm:w-auto">
            <Button variant="primary" size="lg" className="w-full sm:w-auto group">
              Start Free Learning Account
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
          <Link to="/login" className="w-full sm:w-auto">
            <Button variant="secondary" size="lg" className="w-full sm:w-auto">
              Sign In to Dashboard
            </Button>
          </Link>
        </div>
      </section>

      {/* Role Access Section */}
      <section className="py-16 px-6 bg-slate-900/50 border-t border-b border-slate-800/80">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Designed for Every Stakeholder</h2>
            <p className="text-slate-400 text-sm">Role-Based Access Control built right into the platform security layer.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl glass-panel border border-slate-800 hover:border-indigo-500/40 transition-all">
              <div className="w-12 h-12 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center mb-4">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white mb-1">Learners</h3>
              <p className="text-xs text-slate-400 leading-relaxed">Access interactive sign modules, track daily streaks, and view skill progression.</p>
            </div>

            <div className="p-6 rounded-2xl glass-panel border border-slate-800 hover:border-cyan-500/40 transition-all">
              <div className="w-12 h-12 rounded-xl bg-cyan-600/20 text-cyan-400 flex items-center justify-center mb-4">
                <Video className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white mb-1">Instructors</h3>
              <p className="text-xs text-slate-400 leading-relaxed">Create structured sign curricula and evaluate learner assessment metrics.</p>
            </div>

            <div className="p-6 rounded-2xl glass-panel border border-slate-800 hover:border-amber-500/40 transition-all">
              <div className="w-12 h-12 rounded-xl bg-amber-600/20 text-amber-400 flex items-center justify-center mb-4">
                <Accessibility className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white mb-1">Accessibility Trainers</h3>
              <p className="text-xs text-slate-400 leading-relaxed">Guide specialized inclusion workflows and accessibility standards.</p>
            </div>

            <div className="p-6 rounded-2xl glass-panel border border-slate-800 hover:border-rose-500/40 transition-all">
              <div className="w-12 h-12 rounded-xl bg-rose-600/20 text-rose-400 flex items-center justify-center mb-4">
                <Shield className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white mb-1">Administrators</h3>
              <p className="text-xs text-slate-400 leading-relaxed">Manage system configurations, user permissions, and database operations.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 text-center text-xs text-slate-500 border-t border-slate-900">
        <p>© 2026 AI Sign Language Platform — Built with FastAPI, React, PostgreSQL & Docker.</p>
      </footer>
    </div>
  );
};
