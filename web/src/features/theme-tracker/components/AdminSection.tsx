import { useState } from 'react';
import { CreateThemeForm } from './CreateThemeForm';
import { SuggestionsList } from './SuggestionsList';

interface AdminSectionProps {
  themeNames: string[];
  onUpdate: () => void;
}

export function AdminSection({ themeNames, onUpdate }: AdminSectionProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-border">
      <button
        className="flex w-full items-center justify-between px-4 py-2.5 text-sm font-medium text-muted hover:text-text-bright"
        onClick={() => setOpen(!open)}
      >
        Admin Controls
        <span className="text-xs">{open ? '[-]' : '[+]'}</span>
      </button>

      {open && (
        <div className="border-t border-border p-4">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div>
              <CreateThemeForm onCreated={onUpdate} />
            </div>
            <div className="lg:col-span-2">
              <SuggestionsList themeNames={themeNames} onUpdate={onUpdate} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
