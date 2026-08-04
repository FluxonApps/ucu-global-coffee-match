import type { ReactNode } from 'react';

export type BtnVariant = 'primary' | 'secondary' | 'ghost' | 'outline';
export type BtnSize = 'sm' | 'md' | 'lg';

interface BtnProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: BtnVariant;
  size?: BtnSize;
  fullWidth?: boolean;
  type?: 'button' | 'submit';
  disabled?: boolean;
}

const base =
  'inline-flex items-center justify-center gap-2 font-medium rounded-xl transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed';

const variants: Record<BtnVariant, string> = {
  primary: 'bg-primary text-primary-foreground hover:bg-[#657450] active:scale-[0.98]',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-[#ccc8a8] active:scale-[0.98]',
  ghost: 'text-foreground hover:bg-muted active:scale-[0.98]',
  outline: 'border border-border text-foreground hover:bg-muted active:scale-[0.98] bg-card',
};

const sizes: Record<BtnSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
};

const Btn = ({ children, onClick, variant = 'primary', size = 'md', fullWidth = false, type = 'button', disabled = false }: BtnProps) => (
  <button
    type={type}
    onClick={onClick}
    disabled={disabled}
    className={`${base} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''}`}
  >
    {children}
  </button>
);

export default Btn;
