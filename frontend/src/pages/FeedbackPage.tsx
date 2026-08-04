import { Check, CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';

import Avatar from '../components/ui/Avatar.tsx';
import Btn from '../components/ui/Btn.tsx';
import Card from '../components/ui/Card.tsx';
import { getMatchNeedingFeedback, submitFeedback } from '../services/matches.ts';
import type { Match } from '../types/coffeeMatch.ts';

const QUESTIONS = [
  { id: 'overall', label: 'How satisfied were you with this conversation overall?' },
  { id: 'relevance', label: 'How relevant was this match to your interests and goals?' },
  { id: 'connection', label: 'How well did you connect with your coffee match?' },
  { id: 'recommend', label: 'How likely are you to recommend Coffee Match to a colleague?' },
  { id: 'future', label: 'How interested are you in future conversations with this person?' },
];

const LABELS: Record<number, string> = { 1: 'Not at all', 2: 'Slightly', 3: 'Somewhat', 4: 'Quite', 5: 'Very much' };

const FeedbackPage = () => {
  const navigate = useNavigate();
  const [match, setMatch] = useState<Match | null | undefined>(undefined);
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    void getMatchNeedingFeedback().then((m) => setMatch(m ?? null));
  }, []);

  const allAnswered = QUESTIONS.every((q) => ratings[q.id]);
  const answered = QUESTIONS.filter((q) => ratings[q.id]).length;

  const handleSubmit = async () => {
    if (!allAnswered || !match) return;
    await submitFeedback({ matchId: match.id, ratings, comment });
    setSubmitted(true);
  };

  if (match === undefined) {
    return <div className="min-h-screen bg-background pt-14" />;
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-background pt-14 flex items-center justify-center">
        <div className="text-center max-w-sm px-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={32} className="text-primary" />
          </div>
          <h2 className="text-xl font-medium mb-2 font-display">Thanks for your feedback!</h2>
          <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
            Your response helps us make better matches for you and your colleagues.
          </p>
          <Btn variant="primary" onClick={() => navigate('/matches')}>
            Back to Matches
          </Btn>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="max-w-xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-medium mb-1 font-display">Conversation Feedback</h1>
        <p className="text-sm text-muted-foreground mb-6">Rate your coffee chat — it takes about two minutes.</p>

        {match && (
          <Card className="p-4 mb-6 flex items-center gap-3">
            <Avatar src={match.colleague.avatar} name={match.colleague.name} size={44} />
            <div>
              <p className="font-medium text-foreground">{match.colleague.name}</p>
              <p className="text-sm text-muted-foreground">
                {match.colleague.role} · {match.matchDate}
              </p>
            </div>
          </Card>
        )}

        <div className="flex items-center gap-2 mb-5">
          <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(answered / QUESTIONS.length) * 100}%` }} />
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {answered}/{QUESTIONS.length}
          </span>
        </div>

        <div className="flex flex-col gap-4">
          {QUESTIONS.map((q) => (
            <Card key={q.id} className="p-5">
              <p className="text-sm font-medium text-foreground mb-4">{q.label}</p>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    onClick={() => setRatings((r) => ({ ...r, [q.id]: n }))}
                    className={`flex-1 py-3 rounded-xl border text-sm font-semibold transition-all
                      ${ratings[q.id] === n ? 'bg-primary text-primary-foreground border-primary shadow-sm' : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground bg-card'}`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              {ratings[q.id] && <p className="text-xs text-muted-foreground text-center mt-2 font-mono">{LABELS[ratings[q.id]]}</p>}
            </Card>
          ))}

          <Card className="p-5">
            <p className="text-sm font-medium text-foreground mb-3">
              Anything else to share? <span className="text-muted-foreground font-normal">(optional)</span>
            </p>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              placeholder="What went well? What could be better?"
              className="w-full rounded-xl border border-border bg-input-background px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none transition"
            />
          </Card>

          <Btn variant="primary" size="lg" fullWidth disabled={!allAnswered} onClick={handleSubmit}>
            {allAnswered ? (
              <>
                <Check size={16} /> Submit Feedback
              </>
            ) : (
              `Answer ${QUESTIONS.length - answered} more question${QUESTIONS.length - answered === 1 ? '' : 's'}`
            )}
          </Btn>
          <button
            onClick={() => navigate('/matches')}
            className="text-sm text-center text-muted-foreground hover:text-foreground transition-colors"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackPage;
