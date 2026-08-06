import { Clock, Globe, Star } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';

import Avatar from '../components/ui/Avatar.tsx';
import Card from '../components/ui/Card.tsx';
import Tag from '../components/ui/Tag.tsx';
import { useProfileDetails } from '../context/useProfileDetails.ts';
import { DAYS, HOUR_LABELS } from '../data/options.ts';
import { getColleague } from '../services/matches.ts';
import type { Colleague } from '../types/coffeeMatch.ts';

const PublicProfilePage = () => {
  const { id } = useParams<{ id: string }>();
  const { details } = useProfileDetails();
  const [colleague, setColleague] = useState<Colleague | null | undefined>(undefined);

  useEffect(() => {
    if (!id) return;
    void getColleague(id).then((c) => setColleague(c ?? null));
  }, [id]);

  if (colleague === undefined) {
    return <div className="min-h-screen bg-background pt-14" />;
  }

  if (colleague === null) {
    return (
      <div className="min-h-screen bg-background pt-14 flex items-center justify-center">
        <div className="text-center">
          <p className="text-foreground font-medium mb-2">Colleague not found</p>
          <Link to="/matches" className="text-primary text-sm hover:underline">
            Back to Matches
          </Link>
        </div>
      </div>
    );
  }

  const mutual = new Set(colleague.interests.filter((i) => details.interests.includes(i)));
  const availDays = DAYS.map((d) => ({
    day: d,
    hours: colleague.availability.filter((s) => s.startsWith(d.key + '-')).map((s) => HOUR_LABELS[s.split('-')[1]] || s.split('-')[1]),
  })).filter((d) => d.hours.length > 0);

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <Link to="/matches" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors">
          ← Back to Matches
        </Link>

        <Card className="overflow-hidden mb-4">
          <div className="h-24 bg-gradient-to-br from-secondary to-muted" />
          <div className="px-6 pb-6">
            <div className="-mt-10 flex items-end mb-4">
              <Avatar src={colleague.avatar} name={colleague.name} size={80} />
            </div>
            <h1 className="text-xl font-semibold font-display">{colleague.name}</h1>
            <p className="text-muted-foreground text-sm">
              {colleague.role} · {colleague.department}
            </p>
            <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-muted-foreground font-mono">
              <span className="flex items-center gap-1">
                <Globe size={11} /> {colleague.timezone}
              </span>
            </div>
            {colleague.bio && <p className="mt-4 text-sm text-foreground leading-relaxed">{colleague.bio}</p>}
          </div>
        </Card>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <Card className="p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Star size={14} className="text-primary" /> Interests
            </h3>
            <div className="flex flex-wrap gap-2">
              {colleague.interests.map((i) => (
                <Tag key={i} label={i} active={mutual.has(i)} />
              ))}
            </div>
            {mutual.size > 0 && (
              <p className="text-xs text-muted-foreground mt-3">Highlighted interests are shared with you.</p>
            )}
          </Card>
          <Card className="p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Clock size={14} className="text-primary" /> Usual Availability
            </h3>
            {availDays.length > 0 ? (
              <div className="flex flex-col gap-1.5">
                {availDays.map(({ day, hours }) => (
                  <div key={day.key} className="flex items-start gap-2 text-sm">
                    <span className="font-medium text-foreground w-8 flex-shrink-0 font-mono">{day.key}</span>
                    <span className="text-muted-foreground">{hours.join(', ')}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Not specified</p>
            )}
            <p className="text-xs text-muted-foreground mt-3">
              Prefers {colleague.format.join(' or ')} · {colleague.duration}
            </p>
          </Card>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <Card className="p-5">
            <h3 className="font-semibold mb-3">Skills</h3>
            <div className="flex flex-wrap gap-2">
              {colleague.skills.map((s) => (
                <Tag key={s} label={s} />
              ))}
            </div>
          </Card>
          <Card className="p-5">
            <h3 className="font-semibold mb-3">Languages</h3>
            <div className="flex flex-wrap gap-2">
              {colleague.languages.map((l) => (
                <Tag key={l} label={l} />
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PublicProfilePage;
