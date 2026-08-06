const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export async function apiFetch<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // 1. Отримуємо токен, збережений при вході
  const token = localStorage.getItem('session_token');

  // 2. Формуємо заголовки
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // 3. Додаємо Authorization заголовок, якщо токен є
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // 4. Виконуємо запит з підтримкою cookie та Bearer-токена
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Передає Cookie для десктопних браузерів
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Якщо 401 — сесія недійсна, можна очистити localStorage
      localStorage.removeItem('session_token');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(response.status, errorData.detail || `Request failed with status ${response.status}`);
  }

  // Якщо відповідь 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}
