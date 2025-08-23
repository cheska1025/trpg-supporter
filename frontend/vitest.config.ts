import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // 기존 exclude 항목에 추가/갱신
    exclude: ['node_modules', 'dist', 'e2e/**', 'playwright.*', 'some-new-exclude/**'],
    globals: true,
  },
});
