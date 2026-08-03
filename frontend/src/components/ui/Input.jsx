import React, { forwardRef } from 'react';

export const Input = forwardRef(
  ({ label, error, helperText, icon: Icon, className = '', id, ...props }, ref) => {
    const inputId = id || props.name || Math.random().toString(36).substring(7);

    return (
      <div className="flex flex-col space-y-1.5 w-full">
        {label && (
          <label htmlFor={inputId} className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
            {label}
          </label>
        )}

        <div className="relative">
          {Icon && (
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Icon className="w-5 h-5" />
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={`w-full rounded-lg glass-input py-2.5 px-3.5 text-sm ${
              Icon ? 'pl-11' : ''
            } ${
              error
                ? 'border-rose-500/80 focus:border-rose-500 focus:ring-rose-500/25'
                : 'border-slate-700/80 focus:border-indigo-500 focus:ring-indigo-500/25'
            } ${className}`}
            {...props}
          />
        </div>

        {error && <p className="text-xs text-rose-400 mt-1">{error}</p>}
        {helperText && !error && <p className="text-xs text-slate-400 mt-1">{helperText}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
