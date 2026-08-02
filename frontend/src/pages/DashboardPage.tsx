import { useAuthState, useSignOut } from 'react-firebase-hooks/auth';
import { Navigate } from 'react-router';

import { auth } from '../../firebase.config.ts';

const DashboardPage = () => {
  const [user, userLoading] = useAuthState(auth);
  const [signOut, isSigningOut] = useSignOut(auth);

  // Do not show page content until auth state is fetched.
  if (userLoading) {
    return null;
  }

  // If user isn't signed in, redirect to auth page.
  if (!user) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="p-6">
      <p>Welcome to your app!</p>
      <button
        type="button"
        className="bg-green-500 rounded-lg px-4 py-2 font-medium"
        onClick={signOut}
        disabled={isSigningOut}
      >
        Sign out
      </button>
    </div>
  );
};

export default DashboardPage;
