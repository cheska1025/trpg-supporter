import { useState, FormEvent } from 'react';

type Props = {
  onSubmit: (payload: { name: string; clazz: string; level: number }) => void | Promise<void>;
  isSubmitting?: boolean;
};

export function CharacterForm({ onSubmit, isSubmitting }: Props) {
  const [name, setName] = useState('');
  const [clazz, setClazz] = useState('');
  const [level, setLevel] = useState<number>(1);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({ name: name.trim(), clazz: clazz.trim(), level: Number(level) || 1 });
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 8, maxWidth: 320 }}>
      <label>
        Name
        <input
          placeholder="e.g. Alice"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <label>
        Class
        <input
          placeholder="e.g. Wizard"
          value={clazz}
          onChange={(e) => setClazz(e.target.value)}
        />
      </label>
      <label>
        Level (default 1)
        <input
          type="number"
          min={1}
          value={level}
          onChange={(e) => setLevel(Number(e.target.value))}
        />
      </label>
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating…' : 'Create'}
      </button>
    </form>
  );
}
