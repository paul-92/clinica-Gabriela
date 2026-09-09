import assert from "node:assert/strict";
import test from "node:test";

import { ApiError, apiRequest, authenticate } from "../src/api.js";

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
