import { ArrowRight, Calendar, Clock, Coffee, ExternalLink, Globe, Star, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';

import Avatar from '../components/ui/Avatar.tsx';
import Btn from '../components/ui/Btn.tsx';
import Card from '../components/ui/Card.tsx';
import Tag from '../components/ui/Tag.tsx';
import { useProfileDetails } from '../context/useProfileDetails.ts';
import { getMatchHistory, getMatches } from '../services/matches.ts';
import type { MatchHistoryEntry } from '../services/matches.ts';
import type { Match } from '../types/coffeeMatch.ts';

const MatchesPage = () => {
  const [history, setHistory] = useState<MatchHistoryEntry[] | null>(null);

  useEffect(() => {
    void getMatchHistory().then(setHistory);
  }, []);

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-medium mb-6 font-display">Matches</h1>

        {history === null && <p className="text-sm text-muted-foreground">Loading history…</p>}

        {history && (
          <Card className="overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
              <Clock size={18} className="text-primary" />
              <div>
                <h2 className="font-semibold font-display">History of my matches</h2>
                <p className="text-xs text-muted-foreground">Your completed coffee matches.</p>
              </div>
            </div>

            {history.length > 0 ? (
              <ul className="divide-y divide-border">
                {history.map((match) => {
                  const matchedAt = new Intl.DateTimeFormat('en-GB', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  }).format(new Date(match.matched_at));

                  const fullName = `${match.colleague.first_name} ${match.colleague.last_name}`;

                  return (
                    <li key={match.id} className="flex items-center gap-3 px-5 py-4">
                      <Link to={`/profile/${match.colleague.id}`} className="flex-shrink-0">
                        <Avatar src={match.colleague.avatar_url} name={fullName} size={44} />
                      </Link>

                      <div className="min-w-0 flex-1">
                        <Link
                          to={`/profile/${match.colleague.id}`}
                          className="font-medium text-foreground hover:text-primary transition-colors"
                        >
                          {fullName}
                        </Link>
                        <p className="truncate text-sm text-muted-foreground">{match.colleague.email}</p>
                      </div>

                      <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                        <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono whitespace-nowrap">
                          <Clock size={11} /> {matchedAt}
                        </span>
                        <Link to={`/profile/${match.colleague.id}`}>
                          <Btn variant="outline" size="sm">
                            <ExternalLink size={12} /> View Profile
                          </Btn>
                        </Link>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="px-5 py-8 text-center text-sm text-muted-foreground">No completed matches yet.</p>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default MatchesPage;