import React from 'react';
import { useAuth } from '../auth/AuthContext';
import './Topbar.css';

interface TopbarProps {
  title: string;
}

export function Topbar({ title }: TopbarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div>
        <span className="topbar__eyebrow">Sign Language Platform</span>
        <h1 className="topbar__title">{title}</h1>
      </div>
      <div className="topbar__account">
        <span>{user?.email}</span>
        <button className="topbar__logout" onClick={logout}>
          Log out
        </button>
      </div>
    </header>
  );
}
