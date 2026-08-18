import React, { createContext, useContext, useState, ReactNode } from 'react';
import client from '../api/client';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  token: string | null;
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem('auth_user');
    return stored ? JSON.parse(stored) : null;
  });

  const login = async (email: string, password: string): Promise<AuthUser> => {
    const response = await client.post('/api/auth/login', { email, password });
    const { access_token, user: loggedInUser } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('auth_user', JSON.stringify(loggedInUser));
    setToken(access_token);
    setUser(loggedInUser);

    return loggedInUser;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
