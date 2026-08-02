import { use } from 'react';

import { AuthContext } from './AuthContext.tsx';

export const useAuth = () => {
  const ctx = use(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
