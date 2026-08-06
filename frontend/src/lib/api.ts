const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');

  const res = await fetch(`${API_BASE}${path}`, {
    method: init?.method,
    body: init?.body,
    credentials: 'include',
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;

    let message = 'Request failed';

    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail.map((e) => e.msg ?? JSON.stringify(e)).join(', ');
    }

    throw new ApiError(res.status, message);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
