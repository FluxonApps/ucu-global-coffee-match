import { useEffect, useState } from 'react';

import { DAYS, HOURS, slotKey } from '../../data/options.ts';

interface AvailabilityCalendarProps {
  selected: string[];
  onToggle: (slot: string) => void;
}

const AvailabilityCalendar = ({ selected, onToggle }: AvailabilityCalendarProps) => {
  const [dragging, setDragging] = useState(false);
  const [dragMode, setDragMode] = useState<'add' | 'remove'>('add');

  const handleMouseDown = (slot: string) => {
    const mode = selected.includes(slot) ? 'remove' : 'add';
    setDragMode(mode);
    setDragging(true);
    onToggle(slot);
  };
  const handleMouseEnter = (slot: string) => {
    if (!dragging) return;
    const isSelected = selected.includes(slot);
    if (dragMode === 'add' && !isSelected) onToggle(slot);
    if (dragMode === 'remove' && isSelected) onToggle(slot);
  };

  useEffect(() => {
    const up = () => setDragging(false);
    window.addEventListener('mouseup', up);
    return () => window.removeEventListener('mouseup', up);
  }, []);

  return (
    <div className="select-none">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse" style={{ minWidth: 20 + HOURS.length * 44 }}>
          <thead>
            <tr>
              <th className="pb-3 w-20 sticky left-0 bg-card" aria-hidden="true" />
              {HOURS.map((h) => (
                <th key={h.key} className="pb-3 text-center" style={{ minWidth: 44 }} scope="col">
                  <div className="flex flex-col items-center leading-none">
                    <span className="text-xs font-semibold text-foreground font-mono">{h.label}</span>
                    <span className="text-[10px] text-muted-foreground font-mono">{h.period}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DAYS.map((d) => (
              <tr key={d.key}>
                <td className="pr-3 py-1 text-right sticky left-0 bg-card">
                  <span className="text-xs font-medium text-foreground font-mono">{d.key}</span>
                </td>
                {HOURS.map((h) => {
                  const slot = slotKey(d.key, h.key);
                  const on = selected.includes(slot);
                  return (
                    <td key={h.key} className="p-0.5">
                      <div
                        role="button"
                        tabIndex={0}
                        aria-pressed={on}
                        aria-label={`${d.label} ${h.label} ${h.period}`}
                        onMouseDown={() => handleMouseDown(slot)}
                        onMouseEnter={() => handleMouseEnter(slot)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            onToggle(slot);
                          }
                        }}
                        title={`${d.label} ${h.label} ${h.period}`}
                        className={`h-10 rounded-lg border cursor-pointer transition-all duration-100 flex items-center justify-center
                          ${on ? 'bg-primary border-primary shadow-sm' : 'bg-muted/40 border-border hover:bg-secondary/50 hover:border-secondary'}`}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-3.5 h-3.5 rounded bg-primary" />
          <span className="text-xs text-muted-foreground">Available</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3.5 h-3.5 rounded bg-muted/40 border border-border" />
          <span className="text-xs text-muted-foreground">Unavailable</span>
        </div>
        {selected.length > 0 && (
          <span className="text-xs text-primary font-medium ml-auto">
            {selected.length} slot{selected.length !== 1 ? 's' : ''} selected
          </span>
        )}
      </div>
      <p className="text-xs text-muted-foreground mt-1">Click a cell to toggle · Click and drag to select multiple</p>
    </div>
  );
};

export default AvailabilityCalendar;
