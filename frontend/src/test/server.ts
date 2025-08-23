import { setupServer } from 'msw/node';
import { rest } from 'msw';
import type { Character } from '@/types/characters';

let characters: Character[] = [
  { id: 1, name: 'Alice', clazz: 'Wizard', level: 2 },
];

export const server = setupServer(
  rest.get('/api/v1/characters', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(characters));
  }),

  rest.post('/api/v1/characters', async (req, res, ctx) => {
    const body = await req.json();
    const newChar: Character = { id: Date.now(), ...body };
    characters.push(newChar);
    return res(ctx.status(201), ctx.json(newChar));
  }),

  rest.delete('/api/v1/characters/:id', (req, res, ctx) => {
    const id = Number(req.params.id);
    characters = characters.filter((c) => c.id !== id);
    return res(ctx.status(204));
  })
);
