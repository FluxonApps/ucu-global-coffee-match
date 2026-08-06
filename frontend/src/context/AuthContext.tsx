import { createContext, useContext, useEffect, useState } from 'react';
import type { PropsWithChildren } from 'react';

import { apiFetch } from '../lib/api.ts';

export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  timezone: string | null;
};

type AuthResponse = User & {
  token: string;
  verification_code?: string;
};

export type AuthContextValue = {
  user: User | null;
  loading: boolean;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<string>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;

  updateProfile: (
    fields: Partial<Pick<User, 'first_name' | 'last_name' | 'timezone'>> & {
      personal_interests?: string[];
      skills?: string[];
      languages?: string[];
      avatar_url?: string;
      role_title?: string;
      department?: string;
      bio?: string;
    },
  ) => Promise<User & { personal_interests?: string[]; skills?: string[]; languages?: string[]; avatar_url?: string }>;
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

  const register = async (email: string, password: string, firstName: string, lastName: string) => {
    const newUser = await apiFetch<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, first_name: firstName, last_name: lastName }),
    });
    localStorage.setItem('session_token', newUser.token);
    setUser(newUser);
    return newUser.verification_code ?? '';
  };

  const login = async (email: string, password: string) => {
    const loggedInUser = await apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('session_token', loggedInUser.token);
    setUser(loggedInUser);
  };

  const logout = async () => {
    await apiFetch<void>('/auth/logout', { method: 'POST' });
    localStorage.removeItem('session_token');
    setUser(null);
  };

  const updateProfile = async (
    fields: Partial<Pick<User, 'first_name' | 'last_name' | 'timezone'>> & {
      personal_interests?: string[];
      skills?: string[];
      languages?: string[];
      avatar_url?: string;
      role_title?: string;
      department?: string;
      bio?: string;
    },
  ) => {
    const updatedUser = await apiFetch<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(fields),
    });

    setUser(updatedUser);

    return updatedUser;
  };

  return <AuthContext.Provider value={{ user, loading, register, login, logout, updateProfile }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};
