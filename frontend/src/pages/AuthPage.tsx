import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { Navigate } from 'react-router';

import MainLayout from '../components/layout/MainLayout.tsx';
import { useAuth } from '../context/useAuth.ts';
import { ApiError } from '../lib/api.ts';

const AuthPage = () => {
  const { user, loading, login, register } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [showSignIn, setShowSignIn] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const switchAuthMode = () => {
    setShowSignIn((prevState) => !prevState);
    setEmail('');
    setPassword('');
    setName('');
  };

  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
  };

  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
  };

  const handleNameChange = (e: ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
  };

  const handleAuth = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      if (showSignIn) {
        await login(email, password);
      } else {
        await register(email, password, name || undefined);
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Something went wrong. Please, try again.';
      alert(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Do not show page content until auth state is fetched.
  if (loading) {
    return null;
  }

  // Check if user is already signed in. If yes, redirect to main app.
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <MainLayout>
      <div className="flex w-full h-full items-center justify-between">
        <form className="mx-auto" onSubmit={handleAuth}>
          <div className="flex flex-col gap-4 w-[500px] bg-white rounded-md p-8">
            <h2 className="text-2xl! text-black">{showSignIn ? 'Sign in' : 'Sign up'}</h2>
            {!showSignIn && (
              <input
                className="border border-solid border-slate-200 rounded-lg py-2 px-4 text-black"
                placeholder="Name"
                type="text"
                name="name"
                onChange={handleNameChange}
                value={name}
              />
            )}
            <input
              className="border border-solid border-slate-200 rounded-lg py-2 px-4 text-black"
              placeholder="Email"
              type="email"
              name="email"
              onChange={handleEmailChange}
              value={email}
              required
            />
            <input
              className="border border-solid border-slate-200 rounded-lg py-2 px-4 text-black"
              placeholder="Password"
              type="password"
              name="password"
              onChange={handlePasswordChange}
              value={password}
              minLength={6}
              required
            />
            <button type="submit" disabled={isSubmitting} className="bg-blue-400 rounded-lg py-2 font-medium">
              Submit
            </button>
            <button
              type="button"
              className="mt-4 text-sm text-black text-slate-400"
              onClick={switchAuthMode}
              disabled={isSubmitting}
            >
              {showSignIn ? 'Create a new account?' : 'Already have an account?'}
            </button>
          </div>
        </form>
      </div>
    </MainLayout>
  );
};

export default AuthPage;
