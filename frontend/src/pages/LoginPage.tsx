import { Coffee } from 'lucide-react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate } from 'react-router';

import Btn from '../components/ui/Btn.tsx';
import { FormInput } from '../components/ui/FormInput.tsx';
import { useAuth } from '../context/useAuth.ts';
import { ApiError } from '../lib/api.ts';

const LoginPage = () => {
  const { user, loading, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (loading) return null;
  if (user) return <Navigate to="/matches" replace />;

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please, try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      <div className="hidden md:block w-1/2 relative">
        <img
          src="https://images.unsplash.com/photo-1445116572660-236099ec97a0?w=800&h=900&fit=crop&auto=format"
          alt="Coffee shop atmosphere"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-foreground/40 flex flex-col justify-end p-12">
          <blockquote className="text-white text-xl font-medium leading-relaxed font-display">
            "The best ideas I've had came from conversations I almost didn't have."
          </blockquote>
          <p className="text-white/70 text-sm mt-3">— Maya Okafor, Engineering Manager</p>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <Link to="/" className="flex items-center gap-2 mb-8 font-display">
            <Coffee size={20} className="text-primary" />
            <span className="text-lg font-semibold text-foreground">Coffee Match</span>
          </Link>
          <h1 className="text-2xl font-medium mb-1 font-display">Welcome back</h1>
          <p className="text-sm text-muted-foreground mb-8">Sign in with your work email</p>
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            <FormInput label="Work Email" type="email" value={email} onChange={setEmail} placeholder="you@company.com" required />
            <FormInput label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" required />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Btn variant="primary" size="lg" fullWidth type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in…' : 'Sign In'}
            </Btn>
          </form>
          <p className="text-sm text-center text-muted-foreground mt-6">
            New here?{' '}
            <Link to="/register" className="text-primary font-medium hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
