'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { login as apiLogin, setAuthToken, getAuthToken } from '@/lib/api';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  login: (userId: string, email: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = getAuthToken();
    if (storedToken) {
      setToken(storedToken);
    }
    setIsLoading(false);
  }, []);

  // Auto-login in dev mode
  useEffect(() => {
    const autoLogin = async () => {
      if (!token && !isLoading) {
        try {
          const newToken = await apiLogin('demo-user', 'demo@sovereign-ai.dev');
          setToken(newToken);
          setError(null);
        } catch (err) {
          // Auto-login failed - backend might not be in dev mode
          console.log('Auto-login failed, manual login required');
        }
      }
    };
    autoLogin();
  }, [token, isLoading]);

  const login = useCallback(async (userId: string, email: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const newToken = await apiLogin(userId, email);
      setToken(newToken);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        isLoading,
        token,
        login,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
