import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listCharacters,
  createCharacter,
  updateCharacter,
  deleteCharacter,
} from '@/services/characters';
import type {
  Character,
  CharacterListParams,
  CharacterCreate,
} from '@/types/characters';

// 목록 조회 훅
export function useCharacters(params: CharacterListParams) {
  return useQuery({
    queryKey: ['characters', params],
    queryFn: () => listCharacters(params),
    keepPreviousData: true,
  });
}

// 생성 훅
export function useCreateCharacter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CharacterCreate) => createCharacter(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters'] });
    },
  });
}

// 수정 훅
type CharacterPatch = Partial<Pick<Character, 'name' | 'clazz' | 'level'>>;
export function useUpdateCharacter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: CharacterPatch }) =>
      updateCharacter(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters'] });
    },
  });
}

// 삭제 훅
export function useDeleteCharacter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteCharacter(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters'] });
    },
  });
}
