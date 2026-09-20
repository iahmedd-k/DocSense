import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useAuth as useClerkAuth, useUser as useClerkUser, useClerk } from "@clerk/react";
import type { User } from "../api/types";
import { api, setToken, clearToken, setAuthTokenGetter } from "../api/client";

interface AuthState {
  user: User | null;
  loading: boolean;
  isSignedIn: boolean | undefined;
}

interface AuthContextType extends AuthState {
  loadUser: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { isSignedIn, isLoaded, getToken } = useClerkAuth();
  const { user: clerkUser } = useClerkUser();
  const { signOut } = useClerk();
  const [dbUser, setDbUser] = useState<User | null>(null);
  const [loadingProfile, setLoadingProfile] = useState<boolean>(true);

  useEffect(() => {
    setAuthTokenGetter(async () => {
      try {
        return await getToken();
      } catch {
        return null;
      }
    });
  }, [getToken]);

  const loadUser = async () => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      clearToken();
      setDbUser(null);
      setLoadingProfile(false);
      return;
    }

    try {
      const token = await getToken();
      if (token) setToken(token);
      const profile = await api.get<User>("/auth/me");
      setDbUser(profile);
    } catch {
      if (clerkUser) {
        setDbUser({
          id: 1,
          first_name: clerkUser.firstName || "User",
          last_name: clerkUser.lastName || "",
          email: clerkUser.primaryEmailAddress?.emailAddress || "",
          role: "user",
          is_active: true,
          is_verified: true,
          created_at: clerkUser.createdAt ? new Date(clerkUser.createdAt).toISOString() : new Date().toISOString(),
        });
      }
    } finally {
      setLoadingProfile(false);
    }
  };

  useEffect(() => {
    if (isLoaded) {
      loadUser();
    }
  }, [isLoaded, isSignedIn, clerkUser]); // eslint-disable-line react-hooks/exhaustive-deps

  const logout = async () => {
    clearToken();
    setDbUser(null);
    await signOut();
  };

  return (
    <AuthContext.Provider
      value={{
        user: dbUser,
        loading: !isLoaded || loadingProfile,
        isSignedIn,
        loadUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}