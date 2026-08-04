import { ArrowRight, Coffee } from 'lucide-react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate } from 'react-router';

import Btn from '../components/ui/Btn.tsx';
import { FormInput } from '../components/ui/FormInput.tsx';
import { useAuth } from '../context/useAuth.ts';
import { ApiError } from '../lib/api.ts';

const RegisterPage = () => {
  const { user, loading, register } = useAuth();
  // The backend only stores a single `name` field (no first/last split), so
  // the form mirrors that instead of the two-field version from the mock.
  const [name, setName] = useState('');
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
      await register(email, password, name || undefined);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please, try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="flex items-center gap-2 mb-8 font-display">
          <Coffee size={20} className="text-primary" />
          <span className="text-lg font-semibold text-foreground">Coffee Match</span>
        </Link>

        <h1 className="text-2xl font-medium mb-1 font-display">Create your account</h1>
        <p className="text-sm text-muted-foreground mb-8">Just the basics — set up your full profile once you're in.</p>

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <FormInput label="Name" value={name} onChange={setName} placeholder="Alex Chen" />
          <FormInput label="Work Email" type="email" value={email} onChange={setEmail} placeholder="alex@company.com" required />
          <FormInput
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="At least 6 characters"
            required
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Btn variant="primary" size="lg" fullWidth type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Create Account'} <ArrowRight size={16} />
          </Btn>
        </form>

        <p className="text-xs text-muted-foreground text-center mt-4 leading-relaxed">
          Add your photo, interests, and availability from your profile.
        </p>
        <p className="text-sm text-center text-muted-foreground mt-3">
          Already have an account?{' '}
          <Link to="/login" className="text-primary font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
