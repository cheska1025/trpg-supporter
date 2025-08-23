import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { Character, CharacterListParams, CharacterCreate } from '@/types/characters';
import { listCharacters, createCharacter } from '@/services/characters';

const key = (params: CharacterListParams) => ['characters', params];

export function useCharactersQuery(params: CharacterListParams) {
  return useQuery({
    queryKey: key(params),
    queryFn: () => listCharacters(params),
    // 서버에서 X-Total-Count 같은 메타가 있다면 여기선 data만 반환하고,
    // totalCount는 커스텀으로 따로 가져오는 형태로 구성 가능
  });
}

export function useCreateCharacterMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CharacterCreate) => createCharacter(payload),
    onSuccess: (_data, _vars, _ctx) => {
      // 캐시 무효화 → 현재 파라미터 조합의 목록들을 깔끔히 리페치
      qc.invalidateQueries({ queryKey: ['characters'] });
    },
  });
}
