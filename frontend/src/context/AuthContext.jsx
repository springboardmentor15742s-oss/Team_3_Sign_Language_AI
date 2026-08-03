import React, { createContext, useState, useEffect } from 'react';
import { authApi } from '../api/auth';
import {
  getAccessToken,
  setAccessToken,
  setRefreshToken,
  getStoredUser,
  setStoredUser,
  clearAuthStorage,
} from '../utils/storage';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = getAccessToken();
      if (token) {
        try {
          const userData = await authApi.getMe();
          setUser(userData);
          setStoredUser(userData);
        } catch (err) {
          clearAuthStorage();
          setUser(null);
        }
      } else {
        clearAuthStorage();
        setUser(null);
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    setError(null);
    try {
      const data = await authApi.login(credentials);
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(data.user);
      setStoredUser(data.user);
      return data.user;
    } catch (err) {
      setError(err);
      throw err;
    }
  };

  const register = async (payload) => {
    setError(null);
    try {
      const newUser = await authApi.register(payload);
      // Auto login after registration
      return await login({ email: payload.email, password: payload.password });
    } catch (err) {
      setError(err);
      throw err;
    }
  };

  const logout = () => {
    clearAuthStorage();
    setUser(null);
  };

  const updateUserState = (updatedUser) => {
    setUser(updatedUser);
    setStoredUser(updatedUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        error,
        login,
        register,
        logout,
        updateUserState,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
