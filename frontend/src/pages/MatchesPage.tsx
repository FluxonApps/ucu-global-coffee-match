import { ArrowRight, Calendar, Clock, Coffee, ExternalLink, Globe, Star, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';

import Avatar from '../components/ui/Avatar.tsx';
import Btn from '../components/ui/Btn.tsx';
import Card from '../components/ui/Card.tsx';
import Tag from '../components/ui/Tag.tsx';
import { useProfileDetails } from '../context/useProfileDetails.ts';
import { getMatches } from '../services/matches.ts';
import type { Match } from '../types/coffeeMatch.ts';

const MatchesPage = () => {
  const { details } = useProfileDetails();
  const isReady = details.interests.length > 0;
  const [matches, setMatches] = useState<Match[] | null>(null);

  useEffect(() => {
    void getMatches().then(setMatches);
  }, []);

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-medium mb-6 font-display">Matches</h1>

        {!isReady && (
          <div className="max-w-md">
            <Card className="p-8 text-center border-dashed">
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                <Users size={24} className="text-muted-foreground" />
              </div>
              <h2 className="font-semibold text-foreground mb-2 font-display">No matches yet</h2>
              <p className="text-sm text-muted-foreground leading-relaxed mb-5">
                Add at least a few interests so we can find the right colleagues for you.
              </p>
              <Link to="/profile">
                <Btn variant="primary" size="md">
                  Complete My Profile <ArrowRight size={14} />
                </Btn>
              </Link>
            </Card>
          </div>
        )}

        {isReady && matches === null && <p className="text-sm text-muted-foreground">Loading matches…</p>}

        {isReady && matches && (
          <div className="flex flex-col gap-4">
            {[...matches].reverse().map((match) => (
              <Card key={match.id} className="p-5">
                <div className="flex items-start gap-4">
                  <Link to={`/profile/${match.colleague.id}`}>
                    <Avatar src={match.colleague.avatar} name={match.colleague.name} size={52} />
                  </Link>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          to={`/profile/${match.colleague.id}`}
                          className="font-semibold text-foreground hover:text-primary transition-colors"
                        >
                          {match.colleague.name}
                        </Link>
                        <p className="text-sm text-muted-foreground">
                          {match.colleague.role} · {match.colleague.department}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {match.status === 'current' && (
                          <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full font-mono">
                            Active
                          </span>
                        )}
                        {match.status === 'upcoming' && (
                          <span className="text-xs font-medium text-[#7A6030] bg-[#D8D3B3]/60 px-2 py-0.5 rounded-full font-mono">
                            Upcoming
                          </span>
                        )}
                        {match.status === 'previous' && !match.feedbackGiven && (
                          <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full font-mono">
                            Needs feedback
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {match.sharedInterests.map((i) => (
                        <Tag key={i} label={i} />
                      ))}
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-muted-foreground font-mono">
                      <span className="flex items-center gap-1">
                        <Clock size={11} /> Matched {match.matchDate}
                      </span>
                      {match.scheduledDate && (
                        <span className="flex items-center gap-1">
                          <Calendar size={11} /> {match.scheduledDate}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Globe size={11} /> {match.colleague.timezone}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
                  <Link to={`/profile/${match.colleague.id}`}>
                    <Btn variant="outline" size="sm">
                      <ExternalLink size={12} /> View Profile
                    </Btn>
                  </Link>
                  {match.status === 'previous' && !match.feedbackGiven && (
                    <Link to="/feedback">
                      <Btn variant="secondary" size="sm">
                        <Star size={12} /> Leave Feedback
                      </Btn>
                    </Link>
                  )}
                </div>
              </Card>
            ))}
            {matches.length === 0 && (
              <div className="text-center py-16 text-muted-foreground">
                <Coffee size={32} className="mx-auto mb-3 opacity-30" />
                <p className="font-medium">Nothing here yet</p>
                <p className="text-sm mt-1">Your matches will appear here.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MatchesPage;
