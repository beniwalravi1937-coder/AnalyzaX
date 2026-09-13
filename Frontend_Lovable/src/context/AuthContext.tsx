"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User, WorkspaceMembership, RoleName } from "../types/auth";
import { authApi, setAuthToken, getLocalUser } from "../services/authApi";

interface AuthContextType {
  user: User | null;
  workspaceMemberships: WorkspaceMembership[];
  permissions: string[];
  currentRole: RoleName | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PUBLIC_ROUTES = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
];

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => getLocalUser());
  const [workspaceMemberships, setWorkspaceMemberships] = useState<WorkspaceMembership[]>([]);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const refreshUser = useCallback(async () => {
    // Check if there is an existing local session or token before attempting network refresh
    const local = getLocalUser();
    const hasToken = typeof window !== "undefined" && Boolean(localStorage.getItem("analyzax_auth_token"));
    if (!local && !hasToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const res = await authApi.getMe();
      setUser(res.user);
      setWorkspaceMemberships(res.workspace_memberships || []);
      setPermissions(res.permissions_summary || []);
      setError(null);
    } catch (err: any) {
      // If network fails or backend is in static preview, keep local user if available
      const cached = getLocalUser();
      if (cached) {
        setUser(cached);
      } else {
        setUser(null);
        setWorkspaceMemberships([]);
        setPermissions([]);
        setAuthToken(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const res = await authApi.login(email, password);
      setUser(res.user);
      await refreshUser();
    } catch (err: any) {
      setError(err.message || "Failed to sign in");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, displayName: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const res = await authApi.register(email, password, displayName);
      setUser(res.user);
      await refreshUser();
    } catch (err: any) {
      setError(err.message || "Failed to create account");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore
    } finally {
      setUser(null);
      setWorkspaceMemberships([]);
      setPermissions([]);
      setAuthToken(null);
      // Clean private client storage to prevent cross-user data leakage
      if (typeof window !== "undefined") {
        sessionStorage.clear();
        localStorage.removeItem("analyzax_current_project");
        localStorage.removeItem("analyzax_token");
        localStorage.removeItem("analyzax_local_user");
      }
      router.push("/login");
    }
  };

  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission);
  };

  const currentRole: RoleName | null = workspaceMemberships.length > 0
    ? workspaceMemberships[0].role
    : null;

  return (
    <AuthContext.Provider
      value={{
        user,
        workspaceMemberships,
        permissions,
        currentRole,
        isLoading,
        isAuthenticated: !!user,
        error,
        login,
        register,
        logout,
        refreshUser,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
