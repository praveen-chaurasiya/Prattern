interface ModeToggleProps {
  live: boolean;
  onChange: (live: boolean) => void;
  disabled: boolean;
}

export function ModeToggle({ live, onChange, disabled }: ModeToggleProps) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-muted">
        Mode
      </label>
      <div className="flex rounded-md border border-border text-sm">
        <button
          className={`flex-1 rounded-l-md px-3 py-1.5 transition-colors ${!live ? 'bg-accent/20 text-accent' : 'text-muted hover:text-text'}`}
          onClick={() => onChange(false)}
          disabled={disabled}
        >
          Pre-computed
        </button>
        <button
          className={`flex-1 rounded-r-md px-3 py-1.5 transition-colors ${live ? 'bg-accent/20 text-accent' : 'text-muted hover:text-text'}`}
          onClick={() => onChange(true)}
          disabled={disabled}
        >
          Live
        </button>
      </div>
    </div>
  );
}
