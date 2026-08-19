import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { Modal } from './Modal';
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
  const [aboutOpen, setAboutOpen] = useState(false);

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
        <button className="topbar__about" onClick={() => setAboutOpen(true)} aria-label="About this platform">
          ?
        </button>
        <span>{user?.email}</span>
        <button className="topbar__logout" onClick={logout}>
          Log out
        </button>
      </div>

      {aboutOpen && (
        <Modal title="About this platform" onClose={() => setAboutOpen(false)}>
          <p>
            This platform helps you practice American Sign Language (ASL) fingerspelling using your
            webcam, with instant AI feedback on your handshapes.
          </p>
          <p>
            <strong>How it works:</strong> MediaPipe tracks your hand&rsquo;s landmarks from the camera
            feed, an SVM classifier matches your handshape against the target letter, and you get instant
            pass/fail feedback. A recommendation engine then adapts what you practice next based on your
            accuracy and history.
          </p>
          <p>
            <strong>Scope:</strong> this currently covers static ASL alphabet handshapes (A&ndash;Z, plus
            del and space). Motion-based signs &mdash; like the letters J and Z, waving gestures, or full
            phrases &mdash; aren&rsquo;t supported yet; that&rsquo;s a future direction.
          </p>
        </Modal>
      )}
    </header>
  );
}
