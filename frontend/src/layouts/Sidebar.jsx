import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, User, BookOpen, Award, Shield, Accessibility, Sparkles, Activity } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Sidebar = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  const navigationItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['learner', 'instructor', 'accessibility_trainer', 'administrator'] },
    { name: 'Learner Profile', path: '/profile', icon: User, roles: ['learner', 'instructor', 'accessibility_trainer', 'administrator'] },
    { name: 'Learning Progress', path: '/learning-progress', icon: Activity, roles: ['learner', 'instructor', 'accessibility_trainer', 'administrator'] },
    { name: 'Instructor Area', path: '/instructor', icon: BookOpen, roles: ['instructor', 'administrator'], badge: 'Role' },
    { name: 'Trainer Tools', path: '/trainer', icon: Accessibility, roles: ['accessibility_trainer', 'administrator'], badge: 'Role' },
    { name: 'Admin Console', path: '/admin', icon: Shield, roles: ['administrator'], badge: 'Admin' },
  ];

  const userRole = user?.role?.name || 'learner';
  const filteredNav = navigationItems.filter(item => item.roles.includes(userRole));

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:sticky top-16 left-0 z-40 w-64 h-[calc(100vh-4rem)] bg-slate-950 border-r border-slate-800 transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } flex flex-col justify-between p-4`}
      >
        <div className="space-y-6">
          <div className="px-3 py-2 bg-gradient-to-r from-indigo-900/40 to-slate-900 rounded-xl border border-indigo-500/20">
            <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Active Workspace</p>
            <p className="text-xs font-semibold text-white mt-0.5 capitalize">Milestone 1 — Platform Ready</p>
          </div>

          <nav className="space-y-1">
            {filteredNav.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-semibold shadow-lg shadow-indigo-500/10'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
                    }`
                  }
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer info inside sidebar */}
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>FastAPI Connected</span>
          </div>
        </div>
      </aside>
    </>
  );
};
