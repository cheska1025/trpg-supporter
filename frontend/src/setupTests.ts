import '@testing-library/jest-dom';
import { server } from './test/server';

// 테스트 전후 MSW 서버 관리
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
