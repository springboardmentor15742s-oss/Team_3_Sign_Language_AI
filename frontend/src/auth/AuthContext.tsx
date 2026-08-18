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
  register: (name: string, email: string, password: string, role: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem('auth_user');
    return stored ? JSON.parse(stored) : null;
  });

  const applySession = (accessToken: string, sessionUser: AuthUser) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('auth_user', JSON.stringify(sessionUser));
    setToken(accessToken);
    setUser(sessionUser);
  };

  const login = async (email: string, password: string): Promise<AuthUser> => {
    const response = await client.post('/api/auth/login', { email, password });
    const { access_token, user: loggedInUser } = response.data;
    applySession(access_token, loggedInUser);
    return loggedInUser;
  };

  const register = async (name: string, email: string, password: string, role: string): Promise<AuthUser> => {
    const response = await client.post('/api/auth/register', { name, email, password, role });
    const { access_token, user: registeredUser } = response.data;
    applySession(access_token, registeredUser);
    return registeredUser;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
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
