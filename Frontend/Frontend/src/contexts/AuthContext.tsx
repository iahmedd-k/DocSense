import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import type { User, TokenResponse } from "../api/types";
import { api, setToken, clearToken } from "../api/client";

interface AuthState {
  user: User | null;
  loading: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    confirm_password: string;
  }) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
  });

  const loadUser = useCallback(async () => {
    try {
      const user = await api.get<User>("/auth/me");
      setState({ user, loading: false });
    } catch {
      clearToken();
      setState({ user: null, loading: false });
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post<TokenResponse>("/auth/login", {
        email,
        password,
      });
      setToken(res.access_token);
      setState({ user: res.user, loading: false });
    },
    [],
  );

  const register = useCallback(
    async (data: {
      first_name: string;
      last_name: string;
      email: string;
      password: string;
      confirm_password: string;
    }) => {
      const res = await api.post<TokenResponse>("/auth/register", data);
      setToken(res.access_token);
      setState({ user: res.user, loading: false });
    },
    [],
  );

  const logout = useCallback(() => {
    clearToken();
    setState({ user: null, loading: false });
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
