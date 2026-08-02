import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import {
  useAuthState,
  useCreateUserWithEmailAndPassword,
  useSignInWithEmailAndPassword,
} from 'react-firebase-hooks/auth';
import { Navigate } from 'react-router';

import { auth } from '../../firebase.config.ts';
import MainLayout from '../components/layout/MainLayout.tsx';

const AuthPage = () => {
  const [user] = useAuthState(auth);
  const [signInWithEmailAndPassword, , signInLoading] = useSignInWithEmailAndPassword(auth);
  const [createUserWithEmailAndPassword, , signUpLoading] = useCreateUserWithEmailAndPassword(auth);
  const loading = signInLoading || signUpLoading;

  const [showSignIn, setShowSignIn] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const switchAuthMode = () => {
    setShowSignIn((prevState) => !prevState);
    setEmail('');
    setPassword('');
  };

  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
  };

  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
  };

  const signIn = async () => {
    try {
      const res = await signInWithEmailAndPassword(email, password);
      if (!res) throw new Error();
    } catch (e) {
      console.error(e);
      alert('Failed to sign in. Please, try again.');
    }
  };

  const signUp = async () => {
    try {
      const res = await createUserWithEmailAndPassword(email, password);
      if (!res) throw new Error();
    } catch (e) {
      console.error(e);
      alert('Failed to create a new account. Please, try again.');
    }
  };

  const handleAuth = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (showSignIn) {
      await signIn();
    } else {
      await signUp();
    }
  };

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
            <button type="submit" disabled={loading} className="bg-blue-400 rounded-lg py-2 font-medium">
              Submit
            </button>
            <button
              type="button"
              className="mt-4 text-sm text-black text-slate-400"
              onClick={switchAuthMode}
              disabled={loading}
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
