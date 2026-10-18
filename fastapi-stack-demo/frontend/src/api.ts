const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
if (!API_BASE_URL) {
  throw new Error("VITE_API_BASE_URL не задан (см. frontend/.env.example)");
}

export interface ReadinessResponse {
  ready: boolean;
  checks: Record<string, string>;
}
export interface UserResponse {
  name: string;
  email: string;
}
export interface LoginResponse {
  access_token: string;
  token_type: string;
}
export interface TaskCreated {
  task_id: string;
}
export interface TaskStatus {
  task_id: string;
  state: string;
  result: number | null;
  error: string | null;
}

/** URL WebSocket: из VITE_WS_URL (dev) или от текущего хоста (прод, через nginx /ws/). */
export function wsUrl(): string {
  const explicit = import.meta.env.VITE_WS_URL;
  if (explicit) return explicit;
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${location.host}/ws/counter`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  if (!response.ok && response.status !== 503) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? JSON.stringify((body as { detail: unknown }).detail)
        : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return body as T;
}

const json = (data: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export const getStatus = () => request<ReadinessResponse>("/status");
export const registerUser = (name: string, email: string, password: string) =>
  request<UserResponse>("/users/register", json({ name, email, password }));
export const loginUser = (email: string, password: string) =>
  request<LoginResponse>("/users/login", json({ email, password }));
export const getMe = (token: string) =>
  request<UserResponse>("/users/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
export const enqueueAdd = (a: number, b: number) =>
  request<TaskCreated>("/tasks/add", json({ a, b }));
export const getTask = (id: string) => request<TaskStatus>(`/tasks/${id}`);
