import Tag from './Tag.tsx';

interface FormInputProps {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  options?: string[];
  hint?: string;
}

export const FormInput = ({ label, type = 'text', value, onChange, placeholder, required = false, options, hint }: FormInputProps) => {
  const id = label.toLowerCase().replace(/\s+/g, '-');
  const cls =
    'w-full rounded-xl border border-border bg-input-background px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition';
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-foreground">
          {label}
          {required && <span className="text-destructive ml-0.5">*</span>}
        </label>
      )}
      {options ? (
        <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
          <option value="">Select…</option>
          {options.map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          rows={3}
          className={`${cls} resize-none`}
        />
      ) : (
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          className={cls}
        />
      )}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
};

interface MultiSelectProps {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (v: string) => void;
  hint?: string;
}

export const MultiSelect = ({ label, options, selected, onToggle, hint }: MultiSelectProps) => (
  <div>
    <p className="text-sm font-semibold text-foreground mb-1">{label}</p>
    {hint && <p className="text-xs text-muted-foreground mb-2">{hint}</p>}
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <Tag key={o} label={o} active={selected.includes(o)} onClick={() => onToggle(o)} />
      ))}
    </div>
  </div>
);
