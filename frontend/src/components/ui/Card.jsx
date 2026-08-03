import React from 'react';

export const Card = ({ children, className = '', hoverEffect = false, ...props }) => {
  return (
    <div
      className={`rounded-2xl glass-panel p-6 border border-slate-800/80 shadow-xl ${
        hoverEffect ? 'transition-all duration-300 hover:border-indigo-500/40 hover:-translate-y-1 hover:shadow-2xl hover:shadow-indigo-500/10' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '' }) => (
  <div className={`mb-4 pb-3 border-b border-slate-800/80 ${className}`}>{children}</div>
);

export const CardTitle = ({ children, className = '' }) => (
  <h3 className="text-lg font-bold text-white tracking-tight">{children}</h3>
);

export const CardDescription = ({ children, className = '' }) => (
  <p className="text-xs text-slate-400 mt-1">{children}</p>
);
