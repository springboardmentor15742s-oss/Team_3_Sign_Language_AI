import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  /** Allow-list: only these roles may access the route. */
  roles?: string[];
  /** Deny-list: these roles are blocked, every other role is allowed. Use
   * this instead of `roles` when the route should stay open to roles that
   * don't have a defined home route of their own yet. */
  deniedRoles?: string[];
  /** Where a disallowed/denied user is sent. Defaults to /dashboard. */
  redirectTo?: string;
}

export function ProtectedRoute({ children, roles, deniedRoles, redirectTo = '/dashboard' }: ProtectedRouteProps) {
  const { token, user } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Fail closed: if a role restriction is given, an unresolved user is
  // treated the same as a disallowed one rather than being let through.
  if (roles && (!user || !roles.includes(user.role))) {
    return <Navigate to={redirectTo} replace />;
  }

  if (deniedRoles && user && deniedRoles.includes(user.role)) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
}
