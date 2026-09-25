import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { buildSettingsPayload } from "../src/api.js";

test("settings payload converts the session value to a number", () => {
  assert.deepEqual(buildSettingsPayload({ clinic_name: "Clinica", default_session_value: "180.50" }), {
    clinic_name: "Clinica",
    default_session_value: 180.5
  });
});

test("settings save is a submitting form with loading and error handling", () => {
  const source = fs.readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
  const formStart = source.indexOf('<form className="settingsGrid" onSubmit={save}>');
  const formEnd = source.indexOf("</form>", formStart);
  const formSource = source.slice(formStart, formEnd);
  assert.match(formSource, /type="submit"/);
  assert.match(formSource, /disabled=\{saving\}/);
  assert.match(source, /setError\(requestError instanceof ApiError/);
});
