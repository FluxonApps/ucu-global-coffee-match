import { Coffee, LogOut, User, Users, X } from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';

import { useAuth } from '../../context/useAuth.ts';

const NAV_ITEMS = [
  { to: '/matches', label: 'Matches', icon: Users },
  { to: '/profile', label: 'Profile', icon: User },
];

const Nav = () => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleSignOut = async () => {
    setOpen(false);
    await logout();
    void navigate('/');
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/matches" className="flex items-center gap-2 font-display">
          <Coffee size={20} className="text-primary" />
          <span className="text-lg font-semibold text-foreground">Coffee Match</span>
        </Link>
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`relative px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors
                ${location.pathname.startsWith(to) ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`}
            >
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="hidden md:flex items-center gap-2">
          <button
            onClick={handleSignOut}
            className="text-muted-foreground hover:text-foreground p-1.5 rounded-lg hover:bg-muted transition-colors"
            title="Sign out"
          >
            <LogOut size={15} />
          </button>
        </div>
        <button className="md:hidden p-2 rounded-lg hover:bg-muted" onClick={() => setOpen(!open)}>
          {open ? <X size={20} /> : <Coffee size={20} className="text-primary" />}
        </button>
      </div>
      {open && (
        <div className="md:hidden bg-card border-t border-border px-4 py-3 flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={`relative px-3 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors
                ${location.pathname.startsWith(to) ? 'bg-primary/10 text-primary' : 'text-foreground hover:bg-muted'}`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
          <button onClick={handleSignOut} className="px-3 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 text-foreground hover:bg-muted">
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      )}
    </header>
  );
};

export default Nav;
