import '@testing-library/jest-dom/vitest';
import { beforeAll, afterAll, afterEach, vi } from 'vitest';
import { server } from './msw/server';
import { resetDb } from './msw/handlers';

// whatwg-fetch가 설치되어 있으면 fetch 폴리필은 생략 가능
// import 'whatwg-fetch';

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
  resetDb();
  vi.clearAllMocks();
});

afterAll(() => {
  server.close();
});
