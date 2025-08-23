import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 캐시/리트라이/스테일타임은 필요에 맞게 조절
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 5, // 5s
    },
  },
});
