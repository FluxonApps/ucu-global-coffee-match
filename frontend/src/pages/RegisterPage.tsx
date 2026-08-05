import { ArrowRight, Coffee } from 'lucide-react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router';

import Btn from '../components/ui/Btn.tsx';
import { FormInput } from '../components/ui/FormInput.tsx';
import { useAuth } from '../context/useAuth.ts';
import { ApiError } from '../lib/api.ts';

const MIN_PASSWORD_LENGTH = 6;

const RegisterPage = () => {
  const { user, loading, register } = useAuth();
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationCode, setVerificationCode] = useState<string | null>(null);

  if (loading) return null;
  if (user && !verificationCode) return <Navigate to="/matches" replace />;

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters long.`);
      return;
    }

    setIsSubmitting(true);
    try {
      const code = await register(email, password, firstName, lastName);
      setVerificationCode(code);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please, try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (verificationCode) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm text-center">
        <Link to="/" className="flex items-center justify-center gap-2 mb-8 font-display">
          <Coffee size={20} className="text-primary" />
          <span className="text-lg font-semibold text-foreground">Coffee Match</span>
        </Link>

        <h1 className="text-2xl font-medium mb-1 font-display">One more step</h1>
        <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
          Enter this code in our Slack bot to verify your account:
        </p>

        <p className="text-lg font-mono font-semibold text-foreground bg-muted rounded-lg py-3 px-4 mb-6 inline-block">
          {verificationCode}
        </p>

        <p className="text-sm text-muted-foreground mb-8 leading-relaxed">
          Open Slack, message the Coffee Match bot, and paste the code above to finish setting up your account.
        </p>

        <Btn variant="primary" size="lg" fullWidth onClick={() => navigate('/matches')}>
          Go to my page <ArrowRight size={16} />
        </Btn>
      </div>
    </div>
  );
}

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
          <div className="grid grid-cols-2 gap-4">
            <FormInput label="First name" value={firstName} onChange={setFirstName} placeholder="Alex" required />
            <FormInput label="Last name" value={lastName} onChange={setLastName} placeholder="Chen" required />
          </div>
          <FormInput label="Work Email" type="email" value={email} onChange={setEmail} placeholder="alex@company.com" required />
          <FormInput
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="At least 6 characters"
            minLength={MIN_PASSWORD_LENGTH}
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
