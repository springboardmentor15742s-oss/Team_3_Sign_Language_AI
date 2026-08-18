import React, { ReactNode } from 'react';
import './StatsRow.css';

export function StatsRow({ children }: { children: ReactNode }) {
  return <section className="stats-row">{children}</section>;
}

interface StatTileProps {
  value: ReactNode;
  label: string;
  variant?: 'default' | 'accent' | 'warn';
}

export function StatTile({ value, label, variant = 'default' }: StatTileProps) {
  const variantClass = variant !== 'default' ? ` stat-tile__value--${variant}` : '';
  return (
    <div className="stat-tile">
      <span className={`stat-tile__value${variantClass}`}>{value}</span>
      <span className="stat-tile__label">{label}</span>
    </div>
  );
}
