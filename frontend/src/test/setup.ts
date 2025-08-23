import { expect, afterAll, afterEach, beforeAll } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { setupServer } from 'msw/node';
import { handlers, resetDb } from './msw/handlers';

// fetch 폴리필 (jsdom 환경에서 필요)
import 'whatwg-fetch';

// MSW 서버 인스턴스
export const server = setupServer(...handlers);

// 선택적: MSW 요청/응답 로깅(원인 추적용)
// DEBUG_MSW=1 환경변수 설정 시에만 콘솔 출력
const enableMswDebug = !!process.env.DEBUG_MSW;

beforeAll(() => {
  server.listen({
    onUnhandledRequest: process.env.CI ? 'error' : 'warn',
  });

  if (enableMswDebug) {
    server.events.on('request:start', ({ request }) => {
      // eslint-disable-next-line no-console
      console.log('[MSW][request]', request.method, request.url);
    });
    server.events.on('response:mocked', ({ request, response }) => {
      // eslint-disable-next-line no-console
      console.log('[MSW][mocked ]', request.method, request.url, '→', response.status);
    });
    server.events.on('request:unhandled', ({ request }) => {
      // eslint-disable-next-line no-console
      console.warn('[MSW][UNHANDLED]', request.method, request.url);
    });
  }
});

afterEach(() => {
  // 각 테스트 격리
  server.resetHandlers(); // 핸들러 복구(테스트 중 override된 경우)
  resetDb();              // 인메모리 DB 초기화
});

afterAll(() => {
  server.close();
});

// vitest + jest-dom 조합에서 expect 확장(유지)
expect.extend({});
