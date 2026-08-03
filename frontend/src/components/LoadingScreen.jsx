import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingScreen = ({ message = 'Loading platform...' }) => {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="relative flex flex-col items-center">
        <div className="w-16 h-16 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin mb-4" />
        <p className="text-slate-300 font-medium tracking-wide animate-pulse">{message}</p>
      </div>
    </div>
  );
};

export const InlineSpinner = ({ size = 'sm', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <Loader2 className={`animate-spin text-current ${sizeClasses[size]} ${className}`} />
  );
};
