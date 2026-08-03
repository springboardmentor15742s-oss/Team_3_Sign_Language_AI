import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { User, LogOut, Settings, Shield, Bell, Menu } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Navbar = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const getRoleBadgeColor = (roleName) => {
    switch (roleName) {
      case 'administrator':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'instructor':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'accessibility_trainer':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30 px-4 md:px-6 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <Link to="/dashboard" className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            🤟
          </div>
          <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-indigo-300 hidden sm:inline text-lg">
            SignAI Platform
          </span>
        </Link>
      </div>

      <div className="flex items-center space-x-4">
        <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyan-400 ring-2 ring-slate-950" />
        </button>

        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center space-x-3 p-1.5 rounded-xl hover:bg-slate-800/80 transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-300 font-semibold text-sm">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="text-left hidden md:block">
              <div className="text-xs font-semibold text-white">{user?.username}</div>
              <span className={`inline-block px-1.5 py-0.5 text-[10px] uppercase font-bold rounded border ${getRoleBadgeColor(user?.role?.name)}`}>
                {user?.role?.name?.replace('_', ' ')}
              </span>
            </div>
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl glass-panel border border-slate-800 shadow-2xl py-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-4 py-2 border-b border-slate-800">
                <p className="text-xs font-semibold text-white truncate">{user?.email}</p>
                <p className="text-[10px] text-slate-400 capitalize">Role: {user?.role?.name}</p>
              </div>

              <Link
                to="/profile"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center space-x-2.5 px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <User className="w-4 h-4 text-indigo-400" />
                <span>Learner Profile</span>
              </Link>

              <button
                onClick={() => {
                  setDropdownOpen(false);
                  logout();
                }}
                className="w-full flex items-center space-x-2.5 px-4 py-2 text-xs text-rose-400 hover:bg-rose-500/10"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
