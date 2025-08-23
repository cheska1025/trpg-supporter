import { api } from '@/lib/api';
import type { Character, CharacterListParams, CharacterCreate } from '@/types/characters';

// 목록 조회
export async function listCharacters(
  params: CharacterListParams
): Promise<{ items: Character[]; total: number }> {
  const resp = await api.get('/characters', { params });
  const items = await resp.json<Character[]>();
  const total = Number(resp.headers.get('X-Total-Count') ?? items.length);
  return { items, total };
}

// 생성
export async function createCharacter(payload: CharacterCreate): Promise<Character> {
  const resp = await api.post('/characters', { json: payload });
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    const detail = (data as any)?.detail || resp.statusText || 'Create failed';
    throw new Error(detail);
  }
  return resp.json<Character>();
}

// 수정
export async function updateCharacter(
  id: number,
  payload: Partial<Pick<Character, 'name' | 'clazz' | 'level'>>
): Promise<Character> {
  const resp = await api.put(`/characters/${id}`, { json: payload });
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    const detail = (data as any)?.detail || resp.statusText || 'Update failed';
    throw new Error(detail);
  }
  return resp.json<Character>();
}

// 삭제
export async function deleteCharacter(id: number): Promise<void> {
  const resp = await api.delete(`/characters/${id}`);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    const detail = (data as any)?.detail || resp.statusText || 'Delete failed';
    throw new Error(detail);
  }
}
