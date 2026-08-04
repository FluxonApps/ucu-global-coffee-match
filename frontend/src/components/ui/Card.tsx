import type { ReactNode } from 'react';

const Card = ({ children, className = '' }: { children: ReactNode; className?: string }) => (
  <div className={`bg-card rounded-2xl border border-border shadow-sm ${className}`}>{children}</div>
);

export default Card;
