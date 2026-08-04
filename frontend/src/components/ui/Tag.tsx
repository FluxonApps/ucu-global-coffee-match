import { Check } from 'lucide-react';

interface TagProps {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

const Tag = ({ label, active, onClick }: TagProps) => (
  <button
    type="button"
    onClick={onClick}
    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-all
      ${onClick ? 'cursor-pointer' : 'cursor-default'}
      ${active ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-secondary-foreground border-border hover:border-primary/40'}`}
  >
    {active && onClick && <Check size={10} />}
    {label}
  </button>
);

export default Tag;
