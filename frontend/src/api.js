export const API_BASE = "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, { status = null, cause = null } = {}) {
    super(message, { cause });
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiRequest(path, { token, fetchImpl = fetch, ...options } = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response;
  try {
    response = await fetchImpl(`${API_BASE}${path}`, { ...options, headers });
  } catch (cause) {
    throw new ApiError("API indisponivel.", { cause });
  }

  if (!response.ok) {
    let detail = `Falha na API (HTTP ${response.status}).`;
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") detail = payload.detail;
    } catch { /* resposta sem JSON: manter mensagem sanitizada */ }
    throw new ApiError(detail, { status: response.status });
  }

  return response.json();
}

export async function authenticate(username, password, fetchImpl = fetch) {
  const login = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    fetchImpl
  });
  const user = await apiRequest("/auth/me", {
    token: login.access_token,
    fetchImpl
  });

  return { token: login.access_token, user };
}
