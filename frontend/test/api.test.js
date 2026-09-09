import assert from "node:assert/strict";
import test from "node:test";

import { ApiError, apiRequest, authenticate } from "../src/api.js";
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
