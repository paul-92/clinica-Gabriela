import assert from "node:assert/strict";
import test from "node:test";

import { ApiError, apiRequest, authenticate, buildAppointmentPatch, buildFinancePeriodQuery, canAccessFinancialUi, formatCompetencePeriod, formatMoneyFromCents, nextCompetencePeriod, parseCompetencePeriod, parseMoneyToCents } from "../src/api.js";
import { clearFrontendSession } from "../src/session.js";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

test("autenticacao usa o contrato do login e valida a identidade em /auth/me", async () => {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/auth/login")) {
      return jsonResponse({ access_token: "jwt-valido", token_type: "bearer", user: { username: "ana" } });
    }
    return jsonResponse({ id: 7, name: "Ana", username: "ana", role: "psychologist", active: true });
  };

  const session = await authenticate("ana", "segredo", fetchImpl);

  assert.equal(session.token, "jwt-valido");
  assert.equal(session.user.username, "ana");
  assert.deepEqual(JSON.parse(calls[0].options.body), { username: "ana", password: "segredo" });
  assert.equal(calls[1].options.headers.get("Authorization"), "Bearer jwt-valido");
});

test("requisicao privada envia Bearer token", async () => {
  let authorization;
  const fetchImpl = async (_url, options) => {
    authorization = options.headers.get("Authorization");
    return jsonResponse([]);
  };

  await apiRequest("/patients", { token: "token-da-sessao", fetchImpl });

  assert.equal(authorization, "Bearer token-da-sessao");
});

test("edicao de atendimento envia PATCH, If-Match e somente campos alterados", async () => {
  const appointment = { id: 8, version: 3, scheduled_at: "2030-01-10T09:00:00", duration_minutes: 50, notes: "Inicial" };
  const changes = buildAppointmentPatch(appointment, {
    scheduled_date: "2030-01-10", scheduled_time: "09:00", duration_minutes: "60", notes: "Inicial"
  });
  const calls = [];
  const result = await apiRequest(`/appointments/${appointment.id}`, {
    method: "PATCH", body: JSON.stringify(changes), token: "jwt", headers: { "If-Match": `"${appointment.version}"` },
    fetchImpl: async (url, options) => { calls.push({ url, options }); return jsonResponse({ id: 8, version: 4 }); }
  });

  assert.deepEqual(changes, { duration_minutes: 60 });
  assert.equal(calls[0].url, "http://127.0.0.1:8000/appointments/8");
  assert.equal(calls[0].options.method, "PATCH");
  assert.equal(calls[0].options.headers.get("If-Match"), '"3"');
  assert.deepEqual(JSON.parse(calls[0].options.body), { duration_minutes: 60 });
  assert.equal(result.version, 4);
});

test("edicao preserva erros sanitizados de conflito e stale write", async () => {
  for (const [status, detail] of [[409, "Conflito de agenda."], [412, "Versao obsoleta."]]) {
    await assert.rejects(apiRequest("/appointments/8", {
      method: "PATCH", body: JSON.stringify({ notes: "novo" }), fetchImpl: async () => jsonResponse({ detail }, status)
    }), (error) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.status, status);
      assert.equal(error.message, detail);
      assert.equal(error.message.includes("traceback"), false);
      return true;
    });
  }
});

test("API indisponivel rejeita a autenticacao", async () => {
  const fetchImpl = async () => {
    throw new TypeError("fetch failed");
  };

  await assert.rejects(authenticate("admin", "admin123", fetchImpl), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, null);
    return true;
  });
});

test("credenciais rejeitadas nao criam sessao", async () => {
  const fetchImpl = async () => jsonResponse({ detail: "Invalid credentials" }, 401);

  await assert.rejects(authenticate("admin", "incorreta", fetchImpl), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, 401);
    return true;
  });
});

test("logout descarta token e limpa dados da sessao", () => {
  let session = { token: "jwt", user: { role: "psychologist" } };
  let activeView = "records";
  let state = {
    patients: [1], psychologists: [1], appointments: [1], records: [1],
    payments: [1], expenses: [1], dashboard: { active_patients: 1 }, loading: true
  };
  clearFrontendSession(
    (value) => { session = value; },
    (value) => { activeView = value; },
    (updater) => { state = updater(state); }
  );
  assert.equal(session, null);
  assert.equal(activeView, "dashboard");
  assert.deepEqual(state.records, []);
  assert.deepEqual(state.patients, []);
  assert.equal(state.loading, false);
});

test("dinheiro financeiro converte texto para centavos sem deriva de float", () => {
  assert.equal(parseMoneyToCents("0,10"), 10);
  assert.equal(parseMoneyToCents("0.20"), 20);
  assert.equal(parseMoneyToCents("150,37"), 15037);
  assert.equal(formatMoneyFromCents(10 + 20), "R$ 0,30");
  assert.equal(formatMoneyFromCents(15037), "R$ 150,37");
});

test("dinheiro financeiro rejeita arredondamento, zero e entradas ambiguas", () => {
  for (const invalid of ["0", "-1,00", "1,001", "abc", ""] ) {
    assert.throws(() => parseMoneyToCents(invalid), TypeError);
  }
});

test("interface financeira fica indisponivel para psicologo", () => {
  assert.equal(canAccessFinancialUi("admin"), true);
  assert.equal(canAccessFinancialUi("reception"), true);
  assert.equal(canAccessFinancialUi("psychologist"), false);
});

test("competencia financeira usa somente ano e mes", () => {
  assert.deepEqual(parseCompetencePeriod("2026-07"), { competence_year: 2026, competence_month: 7 });
  assert.equal(formatCompetencePeriod(2026, 7), "2026-07");
  assert.equal(nextCompetencePeriod("2030-12"), "2031-01");
  for (const invalid of ["2026-00", "2026-13", "2026-07-01", ""] ) {
    assert.throws(() => parseCompetencePeriod(invalid), TypeError);
  }
});

test("filtro accrual envia fronteiras mensais sem fabricar dia", () => {
  const query = buildFinancePeriodQuery({
    regime: "accrual", accrualStart: "2030-12", accrualEnd: "2031-01",
    cashStart: "", cashEnd: ""
  });
  const params = new URLSearchParams(query);
  assert.deepEqual(Object.fromEntries(params), {
    regime: "accrual", start_year: "2030", start_month: "12", end_year: "2031", end_month: "1"
  });
  assert.equal(query.includes("-01-01"), false);
});
