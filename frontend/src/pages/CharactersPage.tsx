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
      const currentLevel =
        Array.isArray(data?.items) && data.items.find((i) => i.id === id)?.level;
      const next = (currentLevel ?? 0) + 1;
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
    <div style={{ display: 'grid', gap: 24, margin: '0 auto', maxWidth: 800 }}>
      {/* 1. 최상단 h1(테스트 & 접근성) */}
      <h1>Characters</h1>

      {/* 2. 에러 메시지 */}
      {error && (
        <div role="alert" aria-live="polite" style={{ color: 'tomato', fontWeight: 600 }}>
          {error}
        </div>
      )}

      {/* 3. 새로고침 & 로딩 안내 */}
      <section aria-label="Refresh and Loading Status">
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          aria-label="Refresh Character List"
        >
          {isLoading ? 'Loading…' : 'Refresh'}
        </button>
        {isLoading && (
          <span style={{ marginLeft: 8 }} aria-label="Loading">
            불러오는 중...
          </span>
        )}
      </section>

      {/* 4. 정렬·페이징 UI */}
      <section aria-label="Sorting and Pagination Controls">
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <label>
            Order by:&nbsp;
            <select
              value={params.order_by}
              onChange={(e) =>
                setParams((p) => ({ ...p, order_by: e.target.value as any, offset: 0 }))
              }
              aria-label="정렬 기준 선택"
            >
              <option value="id">id</option>
              <option value="level">level</option>
              <option value="name">name</option>
            </select>
          </label>
          <label>
            <select
              value={params.order}
              onChange={(e) =>
                setParams((p) => ({ ...p, order: e.target.value as any, offset: 0 }))
              }
              aria-label="정렬 순서 선택"
            >
              <option value="desc">desc</option>
              <option value="asc">asc</option>
            </select>
          </label>

          <button
            onClick={() => setParams((p) => ({ ...p, offset: Math.max(0, p.offset - p.limit) }))}
            disabled={(params.offset ?? 0) <= 0}
            aria-label="이전 페이지"
          >
            Prev
          </button>
          <button
            onClick={() => setParams((p) => ({ ...p, offset: (p.offset ?? 0) + p.limit }))}
            disabled={(data?.items?.length ?? 0) < (params.limit ?? 10)}
            aria-label="다음 페이지"
          >
            Next
          </button>
        </div>
      </section>

      {/* 5. 캐릭터 목록 테이블 */}
      <section aria-label="Character List">
        <CharactersTable
          items={Array.isArray(data?.items) ? data.items : []} // 방어적 처리 추가
          onEdit={handlePromote}
          onDelete={handleDelete}
        />
        {(!data?.items || data.items.length === 0) && (
          <p style={{ color: '#888', marginTop: 16 }}>캐릭터가 없습니다.</p>
        )}
      </section>

      {/* 6. 새 캐릭터 생성 폼 */}
      <section aria-label="Create Character" style={{ marginTop: 32 }}>
        <h2>Create Character</h2>
        <CharacterForm onSubmit={handleCreate} isSubmitting={createM.isPending} />
      </section>
    </div>
  );
}
