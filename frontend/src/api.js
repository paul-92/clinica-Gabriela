export const API_BASE = "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, { status = null, cause = null } = {}) {
    super(message, { cause });
    this.name = "ApiError";
    this.status = status;
  }
}

export function parseMoneyToCents(value) {
  const normalized = String(value).trim().replace(/\s/g, "").replace("R$", "").replace(",", ".");
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized)) {
    throw new TypeError("Informe um valor positivo com no maximo duas casas decimais.");
  }
  const [whole, fraction = ""] = normalized.split(".");
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  if (cents <= 0n || cents > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new TypeError("Valor monetario fora do intervalo suportado.");
  }
  return Number(cents);
}

export function formatMoneyFromCents(value) {
  if (!Number.isSafeInteger(value)) {
    return "Valor invalido";
  }
  const negative = value < 0;
  const absolute = BigInt(negative ? -value : value);
  const whole = (absolute / 100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const fraction = (absolute % 100n).toString().padStart(2, "0");
  return `${negative ? "-" : ""}R$ ${whole},${fraction}`;
}

export function canAccessFinancialUi(role) {
  return role === "admin" || role === "reception";
}

export function buildAppointmentPatch(appointment, form) {
  const changes = {};
  const scheduledAt = `${form.scheduled_date}T${form.scheduled_time}:00`;
  if (scheduledAt !== appointment.scheduled_at.slice(0, 19)) changes.scheduled_at = scheduledAt;
  if (Number(form.duration_minutes) !== appointment.duration_minutes) {
    changes.duration_minutes = Number(form.duration_minutes);
  }
  if (form.notes !== (appointment.notes || "")) changes.notes = form.notes;
  return changes;
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
