import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import './Topbar.css';

interface TopbarProps {
  title: string;
}

interface NavLinkConfig {
  to: string;
  label: string;
}

// What each role sees is an explicit, curated list, not just "every route
// this role is technically allowed to reach" — e.g. admin can view
// /instructor too, but their nav only offers their own home. Every link
// listed here must still be a route the role is actually allowed to land
// on (see App.tsx's ProtectedRoute roles/deniedRoles), so nothing here
// ever points at a link that would bounce.
const NAV_LINKS_BY_ROLE: Record<string, NavLinkConfig[]> = {
  learner: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/practice', label: 'Practice' },
  ],
  instructor: [{ to: '/instructor', label: 'Roster' }],
  admin: [{ to: '/admin', label: 'Overview' }],
};

export function Topbar({ title }: TopbarProps) {
  const { user, logout } = useAuth();
  const navLinks = user ? NAV_LINKS_BY_ROLE[user.role] ?? [] : [];

  return (
    <header className="topbar">
      <div>
        <span className="topbar__eyebrow">Sign Language Platform</span>
        <h1 className="topbar__title">{title}</h1>
      </div>
      {navLinks.length > 0 && (
        <nav className="topbar__nav">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `topbar__nav-link${isActive ? ' topbar__nav-link--active' : ''}`}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      )}
      <div className="topbar__account">
        <span>{user?.email}</span>
        <button className="topbar__logout" onClick={logout}>
          Log out
        </button>
      </div>
    </header>
  );
}
