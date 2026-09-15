import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  function refreshProfile() {
    return api
      .getProfile()
      .then((p) => setProfile(p))
      .catch(() => setProfile(null));
  }

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((u) => {
        setUser(u);
        return refreshProfile();
      })
      .catch(() => {
        localStorage.removeItem("token");
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(username, password) {
    const data = await api.login({ username, password });
    localStorage.setItem("token", data.access_token);
    setUser(data.user);
    refreshProfile();
    return data.user;
  }

  async function register(payload) {
    return api.register(payload);
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
    setProfile(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, profile, loading, login, register, logout, setUser, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
