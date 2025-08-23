import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:4173', // 기본 vite preview 포트 사용 (기본값은 4173)
  },
  webServer: {
    // Vite preview 명령어로 프론트엔드 띄우기 (배포 빌드 결과)
    command: 'npm run preview',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
