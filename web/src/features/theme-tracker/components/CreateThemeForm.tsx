import { useState } from 'react';
import { createTheme } from '../api';

interface CreateThemeFormProps {
  onCreated: () => void;
}

export function CreateThemeForm({ onCreated }: CreateThemeFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<{ text: string; ok: boolean } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setStatus({ text: 'Name is required', ok: false });
      return;
    }
    setSubmitting(true);
    setStatus(null);
    try {
      await createTheme(name.trim(), description.trim());
      setStatus({ text: `Created "${name.trim()}"`, ok: true });
      setName('');
      setDescription('');
      onCreated();
    } catch (err: any) {
      setStatus({ text: err.message || 'Failed', ok: false });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h4 className="text-sm font-semibold text-text-bright">Create Theme</h4>
      <input
        type="text"
        placeholder="Theme name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full rounded border border-border bg-surface px-3 py-1.5 text-sm text-text-bright placeholder:text-muted"
      />
      <input
        type="text"
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full rounded border border-border bg-surface px-3 py-1.5 text-sm text-text-bright placeholder:text-muted"
      />
      {status && (
        <p className={`text-xs ${status.ok ? 'text-accent' : 'text-danger'}`}>{status.text}</p>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-accent px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? 'Creating...' : 'Create'}
      </button>
    </form>
  );
}
