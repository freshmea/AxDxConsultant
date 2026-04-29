"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { apiFetch, type LoginResponse, type LoginUser } from "../lib/api";

type AuthContextValue = {
  token: string | null;
  user: LoginUser | null;
  ready: boolean;
  login: (payload: { username: string; password: string }) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "dxax-auth";

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<LoginUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      setReady(true);
      return;
    }

    try {
      const parsed = JSON.parse(saved) as { token: string; user: LoginUser };
      setToken(parsed.token);
      setUser(parsed.user);
      apiFetch<{ user: LoginUser }>("/api/me", undefined, parsed.token)
        .then((response) => {
          setUser(response.user);
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: parsed.token, user: response.user }));
        })
        .catch(() => {
          window.localStorage.removeItem(STORAGE_KEY);
          setToken(null);
          setUser(null);
        })
        .finally(() => setReady(true));
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
      setReady(true);
    }
  }, []);

  const login = async (payload: { username: string; password: string }) => {
    const response = await apiFetch<LoginResponse>("/api/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setToken(response.token);
    setUser(response.user);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(response));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    window.localStorage.removeItem(STORAGE_KEY);
  };

  return <AuthContext.Provider value={{ token, user, ready, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
