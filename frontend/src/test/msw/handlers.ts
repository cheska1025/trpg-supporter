import { http, HttpResponse } from 'msw';
import type { Character } from '@/types/characters';
import { API_BASE } from '@/lib/api'; // ✅ api.ts 에 정의된 BASE 재사용

// --- 인메모리 DB ---
let characters: Character[] = [
  { id: 1, name: 'Alice', clazz: 'Wizard', level: 3 },
  { id: 2, name: 'Bob', clazz: 'Warrior', level: 2 },
  { id: 3, name: 'Charlie', clazz: 'Rogue', level: 1 },
];
let nextId = 4;

export function resetDb() {
  characters = [
    { id: 1, name: 'Alice', clazz: 'Wizard', level: 3 },
    { id: 2, name: 'Bob', clazz: 'Warrior', level: 2 },
    { id: 3, name: 'Charlie', clazz: 'Rogue', level: 1 },
  ];
  nextId = 4;
}

// 정렬 유틸
function sortItems(
  items: Character[],
  order_by: 'id' | 'name' | 'level',
  order: 'asc' | 'desc'
) {
  const sorted = [...items].sort((a, b) => {
    let va: number | string;
    let vb: number | string;
    if (order_by === 'name') {
      va = a.name.toLowerCase();
      vb = b.name.toLowerCase();
    } else if (order_by === 'level') {
      va = a.level;
      vb = b.level;
    } else {
      va = a.id;
      vb = b.id;
    }
    if (va < vb) return -1;
    if (va > vb) return 1;
    return 0;
  });
  return order === 'desc' ? sorted.reverse() : sorted;
}

// --- 핸들러들 ---
export const handlers = [
  // 헬스체크
  http.get(`*${API_BASE}/healthz`, () => {
    return new HttpResponse('ok', { status: 200 });
  }),

  // 목록 조회
  http.get(`*${API_BASE}/characters`, ({ request }) => {
    const url = new URL(request.url);
    const order_by =
      (url.searchParams.get('order_by') as 'id' | 'name' | 'level') ?? 'id';
    const order = (url.searchParams.get('order') as 'asc' | 'desc') ?? 'desc';
    const limit = Number(url.searchParams.get('limit') ?? '10');
    const offset = Number(url.searchParams.get('offset') ?? '0');

    const total = characters.length;
    const sorted = sortItems(characters, order_by, order);
    const paged = sorted.slice(offset, offset + limit);

    return HttpResponse.json({ items: paged, total }, { status: 200 });
  }),

  // 생성
  http.post(`*${API_BASE}/characters`, async ({ request }) => {
    const body = (await request.json()) as {
      name: string;
      clazz: string;
      level: number;
    };

    if (characters.some((c) => c.name.toLowerCase() === body.name.toLowerCase())) {
      return new HttpResponse('Duplicate name', { status: 409 });
    }

    const newChar: Character = { id: nextId++, ...body };
    characters.push(newChar);
    return HttpResponse.json(newChar, { status: 201 });
  }),

  // 수정
  http.put(`*${API_BASE}/characters/:id`, async ({ params, request }) => {
    const id = Number(params.id);
    const body = (await request.json()) as Partial<Character>;
    const idx = characters.findIndex((c) => c.id === id);
    if (idx === -1) return new HttpResponse('Not found', { status: 404 });

    characters[idx] = { ...characters[idx], ...body };
    return HttpResponse.json(characters[idx], { status: 200 });
  }),
  http.patch(`*${API_BASE}/characters/:id`, async ({ params, request }) => {
    const id = Number(params.id);
    const body = (await request.json()) as Partial<Character>;
    const idx = characters.findIndex((c) => c.id === id);
    if (idx === -1) return new HttpResponse('Not found', { status: 404 });

    characters[idx] = { ...characters[idx], ...body };
    return HttpResponse.json(characters[idx], { status: 200 });
  }),

  // 삭제
  http.delete(`*${API_BASE}/characters/:id`, ({ params }) => {
    const id = Number(params.id);
    const before = characters.length;
    characters = characters.filter((c) => c.id !== id);
    if (characters.length === before) {
      return new HttpResponse('Not found', { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),
];
