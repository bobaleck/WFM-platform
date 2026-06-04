export type AuthUser = {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: string;
  permissions: string[];
};

export function getToken(): string {
  return localStorage.getItem("wfm_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("wfm_token", token);
}

export function clearToken() {
  localStorage.removeItem("wfm_token");
}

function authHeaders(extra: Record<string, string> = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function handleResponse<T>(response: Response, path: string): Promise<T> {
  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("wfm-auth-required"));
    throw new Error(`AUTH_REQUIRED:${path}`);
  }
  if (response.status === 403) {
    throw new Error(`FORBIDDEN:${path}`);
  }
  if (!response.ok) {
    throw new Error(`${response.status} ${path}`);
  }
  return response.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: authHeaders() });
  return handleResponse<T>(response, path);
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  return handleResponse<T>(response, path);
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: authHeaders(),
    body: formData
  });
  return handleResponse<T>(response, path);
}

export async function apiPut<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  return handleResponse<T>(response, path);
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(path, { method: "DELETE", headers: authHeaders() });
  await handleResponse(response, path);
}
