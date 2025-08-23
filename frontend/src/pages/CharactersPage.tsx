import { useState } from 'react';
import {
  useCharacters,
  useCreateCharacter,
  useUpdateCharacter,
  useDeleteCharacter,
} from '@/hooks/characters';
import { CharacterForm } from '@/components/CharacterForm';
import { CharactersTable } from '@/components/CharactersTable';
import type { CharacterListParams } from '@/types/characters';

export default function CharactersPage() {
  const [params, setParams] = useState<CharacterListParams>({
    order_by: 'id',
    order: 'desc',
    limit: 10,
    offset: 0,
  });

  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, refetch } = useCharacters(params);
  const createM = useCreateCharacter();
  const updateM = useUpdateCharacter();
  const deleteM = useDeleteCharacter();

  const handleCreate = async (payload: { name: string; clazz: string; level: number }) => {
    setError(null);
    try {
      await createM.mutateAsync(payload);
      await refetch();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handlePromote = async (id: number) => {
    setError(null);
    try {
      const next = (data?.items.find((i) => i.id === id)?.level ?? 0) + 1;
      await updateM.mutateAsync({ id, payload: { level: next } });
      await refetch();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDelete = async (id: number) => {
    setError(null);
    try {
      await deleteM.mutateAsync(id);
      await refetch();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Characters</h2>

      {error && (
        <div role="alert" style={{ color: 'tomato' }}>
          {error}
        </div>
      )}

      <div>
        <button onClick={() => refetch()} disabled={isLoading}>
          {isLoading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {/* 정렬 및 페이징 컨트롤 */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <label>
          Order by:&nbsp;
          <select
            value={params.order_by}
            onChange={(e) =>
              setParams((p) => ({ ...p, order_by: e.target.value as any, offset: 0 }))
            }
          >
            <option value="id">id</option>
            <option value="level">level</option>
            <option value="name">name</option>
          </select>
        </label>
        <select
          value={params.order}
          onChange={(e) =>
            setParams((p) => ({ ...p, order: e.target.value as any, offset: 0 }))
          }
        >
          <option value="desc">desc</option>
          <option value="asc">asc</option>
        </select>

        <button
          onClick={() =>
            setParams((p) => ({ ...p, offset: Math.max(0, p.offset - p.limit) }))
          }
          disabled={(params.offset ?? 0) <= 0}
        >
          Prev
        </button>
        <button
          onClick={() => setParams((p) => ({ ...p, offset: (p.offset ?? 0) + p.limit }))}
          disabled={(data?.items.length ?? 0) < (params.limit ?? 10)}
        >
          Next
        </button>
      </div>

      <CharactersTable
        items={data?.items ?? []}
        onEdit={(id) => handlePromote(id)}
        onDelete={(id) => handleDelete(id)}
      />

      <section>
        <h3>Create Character</h3>
        <CharacterForm onSubmit={handleCreate} isSubmitting={createM.isPending} />
      </section>
    </div>
  );
}
