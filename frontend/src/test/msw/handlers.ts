import { http, HttpResponse } from 'msw';
import type { Character } from '@/types/characters';

// 메모리 DB
let seq = 1;
let db: Character[] = [];

export const resetDb = () => {
  seq = 1;
  db = [];
};

const API_PREFIX = `${import.meta.env.VITE_API_URL || '/api/v1'}`;

// 정렬 유틸
function sortItems(items: Character[], orderBy?: string, order?: string) {
  if (!orderBy) return items;
  const dir = order === 'desc' ? -1 : 1;
  return [...items].sort((a, b) => {
    const av = (a as any)[orderBy];
    const bv = (b as any)[orderBy];
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });
}

export const handlers = [
  // 목록
  http.get(`${API_PREFIX}/characters`, ({ request }) => {
    const url = new URL(request.url);
    const name = url.searchParams.get('name') || '';
    const order_by = url.searchParams.get('order_by') || undefined;
    const order = url.searchParams.get('order') || undefined;
    const limit = Number(url.searchParams.get('limit') || '0');
    const offset = Number(url.searchParams.get('offset') || '0');

    let items = db.filter((c) =>
      name ? c.name.toLowerCase().includes(name.toLowerCase()) : true
    );
    const total = items.length;
    items = sortItems(items, order_by, order);
    if (limit) {
      items = items.slice(offset, offset + limit);
    }

    return HttpResponse.json(items, {
      headers: { 'X-Total-Count': String(total) },
    });
  }),

  // 생성
  http.post(`${API_PREFIX}/characters`, async ({ request }) => {
    const body = (await request.json()) as Omit<Character, 'id'> & Partial<Pick<Character, 'id'>>;
    if (!body.name) {
      return new HttpResponse(JSON.stringify({ detail: 'name is required' }), { status: 422 });
    }
    if (db.some((c) => c.name === body.name)) {
      return new HttpResponse(JSON.stringify({ detail: 'Character name already exists' }), { status: 409 });
    }
    const created: Character = {
      id: seq++,
      name: body.name,
      clazz: body.clazz || 'Warrior',
      level: body.level ?? 1,
    };
    db.push(created);
    return HttpResponse.json(created, { status: 201 });
  }),

  // 수정 (PUT)
  http.put(`${API_PREFIX}/characters/:id`, async ({ params, request }) => {
    const id = Number(params.id);
    const idx = db.findIndex((c) => c.id === id);
    if (idx < 0) return new HttpResponse(null, { status: 404 });

    const payload = (await request.json()) as Partial<Character>;
    // 이름 중복 체크
    if (payload.name && db.some((c) => c.name === payload.name && c.id !== id)) {
      return new HttpResponse(JSON.stringify({ detail: 'Character name already exists' }), { status: 409 });
    }

    db[idx] = { ...db[idx], ...payload };
    return HttpResponse.json(db[idx], { status: 200 });
  }),

  // 삭제
  http.delete(`${API_PREFIX}/characters/:id`, ({ params }) => {
    const id = Number(params.id);
    const before = db.length;
    db = db.filter((c) => c.id !== id);
    if (db.length === before) return new HttpResponse(null, { status: 404 });
    return new HttpResponse(null, { status: 204 });
  }),
];
