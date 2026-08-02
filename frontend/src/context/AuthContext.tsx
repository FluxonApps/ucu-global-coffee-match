import { createContext, useEffect, useState } from 'react';
import type { PropsWithChildren } from 'react';

import { apiFetch } from '../lib/api.ts';

export type User = {
  id: number;
  email: string;
  name: string | null;
  team: string | null;
  timezone: string | null;
};

export type AuthContextValue = {
  user: User | null;
  loading: boolean;
  register: (email: string, password: string, name?: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (fields: Partial<Pick<User, 'name' | 'team' | 'timezone'>>) => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<User>('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const register = async (email: string, password: string, name?: string) => {
    const newUser = await apiFetch<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
    setUser(newUser);
  };

  const login = async (email: string, password: string) => {
    const loggedInUser = await apiFetch<User>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setUser(loggedInUser);
  };

  const logout = async () => {
    await apiFetch<void>('/auth/logout', { method: 'POST' });
    setUser(null);
  };

  const updateProfile = async (fields: Partial<Pick<User, 'name' | 'team' | 'timezone'>>) => {
    const updatedUser = await apiFetch<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(fields),
    });
    setUser(updatedUser);
  };

  return <AuthContext value={{ user, loading, register, login, logout, updateProfile }}>{children}</AuthContext>;
};
