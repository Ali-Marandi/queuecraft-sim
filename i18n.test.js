import assert from "node:assert/strict";
import test from "node:test";

import { normalizeLanguage, t } from "./locales/i18n.js";

test("i18n returns English and Persian translations", () => {
  assert.equal(t("forecast", "en"), "Run AI–Monte Carlo Analysis");
  assert.equal(t("forecast", "fa"), "اجرای تحلیل AI–Monte Carlo");
});

test("i18n normalizes unsupported languages to English", () => {
  assert.equal(normalizeLanguage("fr"), "en");
  assert.equal(normalizeLanguage("fa"), "fa");
  assert.equal(t("missing-key", "en"), "missing-key");
});
