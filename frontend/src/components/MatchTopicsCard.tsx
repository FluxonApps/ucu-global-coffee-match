import { MessageCircle, X } from 'lucide-react';

import Avatar from './ui/Avatar.tsx';
import Btn from './ui/Btn.tsx';
import Card from './ui/Card.tsx';

type MatchTopicsCardProps = {
  // One entry for a one-to-one match, several for a group match.
  colleagues: {
    first_name: string;
    last_name: string;
    email: string;
    avatar_url?: string;
  }[];
  topics: string[];
  onDismiss: () => void;
};

const MatchTopicsCard = ({ colleagues, topics, onDismiss }: MatchTopicsCardProps) => {
  if (colleagues.length === 0) return null;

  const names = colleagues.map((c) => `${c.first_name} ${c.last_name}`.trim());
  const isGroup = colleagues.length > 1;

  const headline =
    names.length <= 2 ? names.join(' and ') : `${names.slice(0, -1).join(', ')}, and ${names[names.length - 1]}`;

  return (
    <Card className="overflow-hidden mb-6 border-primary/30">
      <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border bg-primary/5">
        <div className="flex items-center gap-3">
          <div className="flex -space-x-3">
            {colleagues.map((c, index) => (
              <div
                key={c.email}
                className="rounded-full ring-2 ring-background"
                style={{ zIndex: colleagues.length - index }}
              >
                <Avatar src={c.avatar_url} name={`${c.first_name} ${c.last_name}`} size={44} />
              </div>
            ))}
          </div>
          <div>
            <h2 className="font-semibold font-display">
              {isGroup ? `You matched with a group: ${headline}!` : `You matched with ${headline}!`}
            </h2>
            {!isGroup && <p className="text-xs text-muted-foreground">{colleagues[0].email}</p>}
            {isGroup && (
              <p className="text-xs text-muted-foreground">{colleagues.length + 1} people in this coffee chat</p>
            )}
          </div>
        </div>
        <Btn variant="outline" size="sm" onClick={onDismiss}>
          <X size={14} />
        </Btn>
      </div>

      <div className="px-5 py-4">
        <div className="flex items-center gap-2 mb-3">
          <MessageCircle size={16} className="text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Conversation starters</h3>
        </div>

        {topics.length > 0 ? (
          <ul className="space-y-2">
            {topics.map((topic, index) => (
              <li key={index} className="text-sm text-foreground bg-muted rounded-lg px-3 py-2 leading-relaxed">
                {topic}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No topic suggestions available.</p>
        )}
      </div>
    </Card>
  );
};

export default MatchTopicsCard;
