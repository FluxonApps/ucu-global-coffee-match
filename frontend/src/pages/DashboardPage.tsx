import { useEffect, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { Navigate } from 'react-router';

import { useAuth } from '../context/useAuth.ts';
import { ApiError } from '../lib/api.ts';

const DashboardPage = () => {
  const { user, loading, logout, updateProfile } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [name, setName] = useState('');
  const [team, setTeam] = useState('');
  const [timezone, setTimezone] = useState('');

  useEffect(() => {
    setName(user?.name ?? '');
    setTeam(user?.team ?? '');
    setTimezone(user?.timezone ?? '');
  }, [user]);

  // Do not show page content until auth state is fetched.
  if (loading) {
    return null;
  }

  // If user isn't signed in, redirect to auth page.
  if (!user) {
    return <Navigate to="/" replace />;
  }

  const handleSignOut = async () => {
    setIsSigningOut(true);
    try {
      await logout();
    } finally {
      setIsSigningOut(false);
    }
  };

  const handleSaveProfile = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateProfile({ name, team, timezone });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to save profile. Please, try again.';
      alert(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 flex flex-col gap-6">
      <p>Welcome, {user.email}!</p>

      <form className="flex flex-col gap-4 max-w-sm" onSubmit={handleSaveProfile}>
        <input
          className="border border-solid border-slate-200 rounded-lg py-2 px-4"
          placeholder="Name"
          value={name}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
        />
        <input
          className="border border-solid border-slate-200 rounded-lg py-2 px-4"
          placeholder="Team"
          value={team}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setTeam(e.target.value)}
        />
        <input
          className="border border-solid border-slate-200 rounded-lg py-2 px-4"
          placeholder="Timezone"
          value={timezone}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setTimezone(e.target.value)}
        />
        <button type="submit" disabled={isSaving} className="bg-blue-400 rounded-lg px-4 py-2 font-medium">
          Save profile
        </button>
      </form>

      <button
        type="button"
        className="bg-green-500 rounded-lg px-4 py-2 font-medium w-fit"
        onClick={handleSignOut}
        disabled={isSigningOut}
      >
        Sign out
      </button>
    </div>
  );
};

export default DashboardPage;
