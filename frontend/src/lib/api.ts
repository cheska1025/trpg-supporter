const BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1";

async function handle(res: Response) {
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) msg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      // ignore
    }
    throw new Error(msg);
  }
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export const api = {
  async get(path: string, params?: Record<string, any>) {
    const q =
      params &&
      "?" +
        Object.entries(params)
          .filter(([, v]) => v !== undefined && v !== null && v !== "")
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
          .join("&");
    const res = await fetch(`${BASE}${path}${q || ""}`, { credentials: "omit" });
    return handle(res);
  },
  async post(path: string, body?: any) {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    return handle(res);
  },
};
