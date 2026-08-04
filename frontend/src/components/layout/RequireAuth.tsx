import type { PropsWithChildren } from 'react';
import { Navigate } from 'react-router';

import Nav from './Nav.tsx';
import { useAuth } from '../../context/useAuth.ts';

/** Wraps pages that need a signed-in user: shows the Nav, redirects to /login otherwise. */
const RequireAuth = ({ children }: PropsWithChildren) => {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <>
      <Nav />
      {children}
    </>
  );
};

export default RequireAuth;
