import { ArrowRight, Calendar, Clock, ExternalLink, Users, Coffee } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';

import Avatar from '../components/ui/Avatar.tsx';
import Btn from '../components/ui/Btn.tsx';
import Card from '../components/ui/Card.tsx';
import { useProfileDetails } from '../context/useProfileDetails.ts';
import { createMatch, getMatchHistory } from '../services/matches.ts';
import type { CreateMatchResponse, MatchHistoryEntry } from '../services/matches.ts';
import MatchTopicsCard from '../components/MatchTopicsCard.tsx';

import { useAuth } from '../context/useAuth.ts';
import { ApiError } from '../lib/api.ts';

const MatchesPage = () => {
  const { details } = useProfileDetails();
  const isReady = details.interests.length > 0;

  const [history, setHistory] = useState<MatchHistoryEntry[] | null>(null);
  const [latestMatch, setLatestMatch] = useState<CreateMatchResponse | null>(null);

  const { user } = useAuth();
  const [isMatching, setIsMatching] = useState(false);
  const [matchError, setMatchError] = useState('');

  useEffect(() => {
    void getMatchHistory()
      .then(setHistory)
      .catch((error) => {
        setMatchError(error instanceof ApiError ? error.message : 'Could not load match history.');
        setHistory([]);
      });
  }, []);

  const handleFindMatch = async () => {
    if (!user) return;

    setIsMatching(true);
    setMatchError('');

    try {
      const result = await createMatch();
      setLatestMatch(result);

      // Reload the list so the newly created match appears.
      const updatedHistory = await getMatchHistory();
      setHistory(updatedHistory);
    } catch (error) {
      setMatchError(
        error instanceof ApiError
          ? error.message
          : 'Could not create a match. Please try again.',
      );
    } finally {
      setIsMatching(false);
    }
  };

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between gap-4 mb-6">
          <h1 className="text-2xl font-medium font-display">Matches</h1>

          {isReady && (
            <Btn
              variant="primary"
              size="md"
              onClick={handleFindMatch}
              disabled={isMatching}
            >
              <Coffee size={14} />
              {isMatching ? 'Finding match...' : 'Find a coffee match'}
            </Btn>
          )}
        </div>

        {matchError && <p className="mb-4 text-sm text-destructive">{matchError}</p>}

        {latestMatch && (
          <MatchTopicsCard
            colleague={latestMatch.match}
            topics={latestMatch.conversation_topics}
            onDismiss={() => setLatestMatch(null)}
          />
        )}

        {!isReady && (
          <div className="max-w-md mb-8">
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
                    <li key={match.id} className="flex items-start gap-3 px-5 py-4">
                      <Link to={`/profile/${match.colleague.id}`} className="flex-shrink-0 pt-1">
                        <Avatar src={match.colleague.avatar_url} name={fullName} size={44} />
                      </Link>

                      <div className="min-w-0 flex-1">
                        <Link
                          to={`/profile/${match.colleague.id}`}
                          className="font-medium text-foreground hover:text-primary transition-colors"
                        >
                          {fullName}
                        </Link>
                        <p className="truncate text-sm text-muted-foreground mb-2">{match.colleague.email}</p>

                        {match.conversation_topics && match.conversation_topics.length > 0 && (
                          <div className="mt-1">
                            <p className="text-xs font-semibold text-foreground mb-1">
                              Conversation topic suggestions
                            </p>
                            <ul className="space-y-1">
                              {match.conversation_topics.map((topic, index) => (
                                <li
                                  key={index}
                                  className="text-xs text-muted-foreground leading-relaxed"
                                >
                                  • {topic}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                        <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono whitespace-nowrap">
                          <Clock size={11} /> {matchedAt}
                        </span>
                        {match.recommended_time ? (
                          <div className="flex max-w-56 items-start gap-1 text-right text-xs text-muted-foreground">
                            <Calendar size={11} className="mt-0.5 flex-shrink-0 text-primary" />
                            <span>
                              <span className="block">Your time: {match.recommended_time.user_local.display}</span>
                              <span className="block">
                                Their time: {match.recommended_time.match_local.display}
                              </span>
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">No common available hour</span>
                        )}
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
