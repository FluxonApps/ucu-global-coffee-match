import { ExternalLink, Search, SlidersHorizontal, X } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router';

import Avatar from '../components/ui/Avatar.tsx';
import Btn from '../components/ui/Btn.tsx';
import Card from '../components/ui/Card.tsx';
import Tag from '../components/ui/Tag.tsx';
import { ApiError } from '../lib/api.ts';
import { getAllColleagues } from '../services/matches.ts';
import type { Colleague } from '../types/coffeeMatch.ts';

const AllColleaguesPage = () => {
  const [colleagues, setColleagues] = useState<Colleague[] | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');

  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const filtersRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getAllColleagues()
      .then(setColleagues)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : 'Could not load colleagues.');
        setColleagues([]);
      });
  }, []);

  // Close the filters panel on outside click.
  useEffect(() => {
    if (!filtersOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (filtersRef.current && !filtersRef.current.contains(e.target as Node)) {
        setFiltersOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [filtersOpen]);

  const skillOptions = useMemo(() => {
    if (!colleagues) return [];
    return [...new Set(colleagues.flatMap((c) => c.skills))].sort((a, b) => a.localeCompare(b));
  }, [colleagues]);

  const interestOptions = useMemo(() => {
    if (!colleagues) return [];
    return [...new Set(colleagues.flatMap((c) => c.interests))].sort((a, b) => a.localeCompare(b));
  }, [colleagues]);

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) => (prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]));
  };

  const toggleInterest = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest],
    );
  };

  const clearFilters = () => {
    setSelectedSkills([]);
    setSelectedInterests([]);
  };

  const activeFilterCount = selectedSkills.length + selectedInterests.length;

  const filtered = useMemo(() => {
    if (!colleagues) return [];
    const q = query.trim().toLowerCase();

    return colleagues.filter((c) => {
      const matchesQuery =
        !q || [c.name, c.role, c.department].some((field) => field.toLowerCase().includes(q));

      const matchesSkills =
        selectedSkills.length === 0 || selectedSkills.some((skill) => c.skills.includes(skill));

      const matchesInterests =
        selectedInterests.length === 0 || selectedInterests.some((interest) => c.interests.includes(interest));

      return matchesQuery && matchesSkills && matchesInterests;
    });
  }, [colleagues, query, selectedSkills, selectedInterests]);

  return (
    <div className="min-h-screen bg-primary pt-14">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between gap-4 mb-1">
          <h1 className="text-2xl font-medium font-display text-primary-foreground">All Colleagues</h1>
        </div>
        <p className="text-sm text-primary-foreground/80 mb-6">Everyone registered in Coffee Match.</p>

        <div className="flex items-start gap-2 mb-6">
          <div className="relative" ref={filtersRef}>
            <Btn variant="secondary" size="md" onClick={() => setFiltersOpen((v) => !v)}>
              <SlidersHorizontal size={14} />
              Filters
              {activeFilterCount > 0 && (
                <span className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-primary text-primary-foreground text-[11px] font-semibold">
                  {activeFilterCount}
                </span>
              )}
            </Btn>

            {filtersOpen && (
              <Card className="absolute left-0 top-[calc(100%+8px)] z-10 w-80 max-h-96 overflow-y-auto p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold font-display">Filters</h3>
                  <button
                    onClick={() => setFiltersOpen(false)}
                    className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-muted"
                  >
                    <X size={14} />
                  </button>
                </div>

                {skillOptions.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-foreground mb-2">Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {skillOptions.map((skill) => (
                        <Tag
                          key={skill}
                          label={skill}
                          active={selectedSkills.includes(skill)}
                          onClick={() => toggleSkill(skill)}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {interestOptions.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-semibold text-foreground mb-2">Interests</p>
                    <div className="flex flex-wrap gap-1.5">
                      {interestOptions.map((interest) => (
                        <Tag
                          key={interest}
                          label={interest}
                          active={selectedInterests.includes(interest)}
                          onClick={() => toggleInterest(interest)}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {skillOptions.length === 0 && interestOptions.length === 0 && (
                  <p className="text-xs text-muted-foreground">No skills or interests to filter by yet.</p>
                )}

                {activeFilterCount > 0 && (
                  <button
                    onClick={clearFilters}
                    className="mt-2 text-xs font-medium text-primary hover:underline"
                  >
                    Clear all filters
                  </button>
                )}
              </Card>
            )}
          </div>

          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name, role or department…"
              className="w-full rounded-xl border border-border bg-input-background pl-9 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
            />
          </div>
        </div>

        {activeFilterCount > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 mb-6 -mt-3">
            {selectedSkills.map((skill) => (
              <Tag key={`skill-${skill}`} label={skill} active onClick={() => toggleSkill(skill)} />
            ))}
            {selectedInterests.map((interest) => (
              <Tag key={`interest-${interest}`} label={interest} active onClick={() => toggleInterest(interest)} />
            ))}
            <button onClick={clearFilters} className="text-xs text-primary-foreground/80 hover:text-primary-foreground underline">
              Clear all
            </button>
          </div>
        )}

        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

        {colleagues === null && <p className="text-sm text-primary-foreground/80">Loading colleagues…</p>}

        {colleagues && (
          <>
            {filtered.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {filtered.map((colleague) => (
                  <Card key={colleague.id} className="flex flex-col items-center text-center p-5">
                    <Link to={`/profile/${colleague.id}`}>
                      <Avatar src={colleague.avatar} name={colleague.name} size={64} />
                    </Link>

                    <Link
                      to={`/profile/${colleague.id}`}
                      className="mt-3 font-medium text-foreground hover:text-primary transition-colors line-clamp-1"
                    >
                      {colleague.name}
                    </Link>

                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2 min-h-[2.2em]">
                      {[colleague.role, colleague.department].filter(Boolean).join(' · ') || '—'}
                    </p>

                    <Link to={`/profile/${colleague.id}`} className="mt-4 w-full">
                      <Btn variant="outline" size="sm" fullWidth>
                        <ExternalLink size={12} /> View Profile
                      </Btn>
                    </Link>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="px-5 py-8 text-center text-sm text-muted-foreground">
                {colleagues.length === 0
                  ? 'No colleagues found yet.'
                  : 'No colleagues match your search or filters.'}
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AllColleaguesPage;