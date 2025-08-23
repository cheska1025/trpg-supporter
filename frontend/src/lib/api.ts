const API_BASE =
  (import.meta as any).env?.VITE_API_BASE?.replace(/\/$/, '') ?? '/api/v1'; // ← 기본값

export { API_BASE };

export const api = {
  get: (path: string, opts?: RequestInit & { params?: Record<string, any> }) => {
    const url = new URL(`${API_BASE}${path}`, window.location.origin);
    if (opts?.params) {
      Object.entries(opts.params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      });
    }
    return fetch(url.toString(), { method: 'GET', ...opts });
  },
  post: (path: string, opts?: RequestInit) =>
    fetch(`${API_BASE}${path}`, { method: 'POST', ...opts }),
  put: (path: string, opts?: RequestInit) =>
    fetch(`${API_BASE}${path}`, { method: 'PUT', ...opts }),
  delete: (path: string, opts?: RequestInit) =>
    fetch(`${API_BASE}${path}`, { method: 'DELETE', ...opts }),
};
