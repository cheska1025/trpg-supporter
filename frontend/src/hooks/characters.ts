import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Character, CharacterListParams } from '@/types/characters';

type ListResponse = { items: Character[]; total: number };

async function listCharacters(params: CharacterListParams): Promise<ListResponse> {
  const res = await api.get('/characters', { params });
  if (!res.ok) {
    const msg = await res.text().catch(() => `${res.status}`);
    throw new Error(`List failed: ${msg}`);
  }
  // ✅ 반드시 return!
  return res.json();
}

async function createCharacter(payload: { name: string; clazz: string; level: number }): Promise<Character> {
  const res = await api.post('/characters', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => `${res.status}`);
    throw new Error(`Create failed: ${msg}`);
  }
  return res.json();
}

async function updateCharacter({ id, payload }: { id: number; payload: Partial<Character> }): Promise<Character> {
  const res = await api.put(`/characters/${id}`, {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => `${res.status}`);
    throw new Error(`Update failed: ${msg}`);
  }
  return res.json();
}

async function deleteCharacter(id: number): Promise<void> {
  const res = await api.delete(`/characters/${id}`);
  if (!res.ok) {
    const msg = await res.text().catch(() => `${res.status}`);
    throw new Error(`Delete failed: ${msg}`);
  }
  // 204면 바디 없음. 그냥 반환.
}

export function useCharacters(params: CharacterListParams) {
  return useQuery({
    queryKey: ['characters', params],
    queryFn: () => listCharacters(params),
    // 페이지네이션 UX 좋게
    keepPreviousData: true,
    // 테스트에선 불필요한 재시도 줄이기(선택)
    retry: 0,
  });
}

export function useCreateCharacter() {
  return useMutation({
    mutationFn: createCharacter,
  });
}

export function useUpdateCharacter() {
  return useMutation({
    mutationFn: updateCharacter,
  });
}

export function useDeleteCharacter() {
  return useMutation({
    mutationFn: deleteCharacter,
  });
}
