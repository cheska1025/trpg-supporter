import type { ReactElement, PropsWithChildren } from 'react';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// 단순히 UI를 감싸서 즉시 render까지 수행합니다.
export function renderWithProviders(ui: ReactElement) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={qc}>
      <ErrorBoundary>{ui}</ErrorBoundary>
    </QueryClientProvider>
  );
}

// 필요하면 컴포넌트만 감싸는 HOC도 제공 (현재 테스트에선 안 써도 됨)
export function withClient(children: ReactElement) {
  const qc = new QueryClient();
  return (
    <QueryClientProvider client={qc}>
      <ErrorBoundary>{children}</ErrorBoundary>
    </QueryClientProvider>
  );
}
