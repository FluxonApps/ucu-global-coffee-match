import { ArrowRight, ChevronDown, ChevronUp, Coffee, Star, Users } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router';

import Btn from '../components/ui/Btn.tsx';

const FAQS = [
  {
    q: 'How are matches made?',
    a: 'Our algorithm pairs colleagues based on shared interests, complementary roles, and mutual availability — never repeating a previous pair.',
  },
  {
    q: 'Is participation mandatory?',
    a: 'No. Coffee Match is fully opt-in. Pause or stop at any time from your profile.',
  },
  {
    q: "What happens after I'm matched?",
    a: 'You receive an in-app notification and intro message. From there, coordinate a time directly.',
  },
  {
    q: 'How long are the conversations?',
    a: 'You choose — 20, 30, or 45 minutes. Most people find 30 minutes the sweet spot.',
  },
  {
    q: 'Is my profile visible to everyone?',
    a: 'Only to colleagues on Coffee Match. You control what you share — bio and interests are optional.',
  },
];

const LandingPage = () => {
  const [faq, setFaq] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-background">
      <header className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 font-display">
          <Coffee size={22} className="text-primary" />
          <span className="text-xl font-semibold text-foreground">Coffee Match</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Btn variant="ghost" size="sm">
              Sign In
            </Btn>
          </Link>
          <Link to="/register">
            <Btn variant="primary" size="sm">
              Get Started
            </Btn>
          </Link>
        </div>
      </header>

      <section className="py-20 md:py-32 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <p className="text-xs font-semibold text-primary uppercase tracking-widest mb-4 font-mono">Internal Platform</p>
          <h1 className="text-4xl md:text-6xl font-medium text-foreground mb-6 leading-tight font-display">
            Every great team starts
            <br className="hidden md:block" /> with a good conversation.
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-10 leading-relaxed">
            Coffee Match connects you with colleagues you wouldn't normally meet — one friendly, professional conversation at a
            time.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/register">
              <Btn variant="primary" size="lg">
                Get Started <ArrowRight size={16} />
              </Btn>
            </Link>
            <Link to="/login">
              <Btn variant="outline" size="lg">
                Sign In
              </Btn>
            </Link>
          </div>
        </div>
        <div className="mt-16 max-w-3xl mx-auto rounded-2xl overflow-hidden shadow-lg border border-border">
          <img
            src="https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=900&h=400&fit=crop&auto=format"
            alt="Two colleagues having a coffee conversation"
            className="w-full h-56 md:h-72 object-cover"
          />
        </div>
      </section>

      <section className="py-16 px-6 bg-card border-y border-border">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-medium text-center mb-12 font-display">Why Coffee Match?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Users,
                title: 'Break out of your silo',
                desc: "Meet engineers, designers, marketers, and leaders you wouldn't cross paths with otherwise.",
              },
              {
                icon: Coffee,
                title: 'Low-stakes, high-value',
                desc: 'No agenda required. Just a 30-minute conversation that might spark your next big idea.',
              },
              {
                icon: Star,
                title: 'Build real relationships',
                desc: 'Meaningful professional relationships start with genuine human connection — not Slack pings.',
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex flex-col items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Icon size={18} className="text-primary" />
                </div>
                <h3 className="font-semibold text-foreground">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-medium text-center mb-12 font-display">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { n: '01', label: 'Create your account', desc: 'Sign up with your name and work email in seconds.' },
              { n: '02', label: 'Complete your profile', desc: 'Add your interests, skills, and available hours.' },
              { n: '03', label: 'Get matched', desc: 'We pair you with a compatible colleague.' },
              { n: '04', label: 'Have the conversation', desc: 'Enjoy a friendly 30–45 minute coffee chat.' },
            ].map(({ n, label, desc }) => (
              <div key={n} className="flex flex-col gap-2">
                <span className="text-3xl font-medium text-primary/30 font-display">{n}</span>
                <h4 className="font-semibold text-foreground">{label}</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-6 bg-muted/40 border-y border-border">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-medium text-center mb-10 font-display">Frequently Asked Questions</h2>
          <div className="divide-y divide-border">
            {FAQS.map((f, i) => (
              <div key={f.q} className="py-4">
                <button
                  onClick={() => setFaq(faq === i ? null : i)}
                  className="w-full flex items-center justify-between gap-4 text-left font-medium text-foreground hover:text-primary transition-colors"
                >
                  {f.q}
                  {faq === i ? <ChevronUp size={16} className="flex-shrink-0" /> : <ChevronDown size={16} className="flex-shrink-0" />}
                </button>
                {faq === i && <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{f.a}</p>}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-6 text-center">
        <div className="max-w-lg mx-auto">
          <h2 className="text-2xl md:text-3xl font-medium mb-4 font-display">Ready for your first match?</h2>
          <p className="text-muted-foreground mb-8">Takes less than a minute to sign up.</p>
          <Link to="/register">
            <Btn variant="primary" size="lg">
              Create Your Account <ArrowRight size={16} />
            </Btn>
          </Link>
        </div>
      </section>

      <footer className="border-t border-border py-6 text-center text-sm text-muted-foreground">
        © 2026 Coffee Match · Internal Platform · All conversations are private
      </footer>
    </div>
  );
};

export default LandingPage;
