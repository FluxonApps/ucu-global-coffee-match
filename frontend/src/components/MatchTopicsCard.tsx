import { MessageCircle, X } from 'lucide-react';

import Avatar from './ui/Avatar.tsx';
import Card from './ui/Card.tsx';
import Btn from './ui/Btn.tsx';

type MatchTopicsCardProps = {
  colleague: {
    first_name: string;
    last_name: string;
    email: string;
    avatar_url?: string;
  };
  topics: string[];
  onDismiss: () => void;
};

const MatchTopicsCard = ({ colleague, topics, onDismiss }: MatchTopicsCardProps) => {
  const fullName = `${colleague.first_name} ${colleague.last_name}`;

  return (
    <Card className="overflow-hidden mb-6 border-primary/30">
      <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border bg-primary/5">
        <div className="flex items-center gap-3">
          <Avatar src={colleague.avatar_url} name={fullName} size={44} />
          <div>
            <h2 className="font-semibold font-display">You matched with {fullName}!</h2>
            <p className="text-xs text-muted-foreground">{colleague.email}</p>
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
              <li
                key={index}
                className="text-sm text-foreground bg-muted rounded-lg px-3 py-2 leading-relaxed"
              >
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
