/* English-only browser-language regression checks. */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const INDEX = path.join(ROOT, "dashboard/i18n/index.js");
const EN = JSON.parse(fs.readFileSync(path.join(ROOT, "dashboard/i18n/en.json"), "utf8"));
const KEY = Object.keys(EN)[0];
const failures = [];

function check(name, condition, detail) {
  console.log((condition ? "ok   " : "FAIL ") + name + (condition || detail === undefined ? "" : "  [" + detail + "]"));
  if (!condition) failures.push(name);
}

function load({ browser = [], stored = "" } = {}) {
  const storage = { value: stored };
  global.localStorage = { getItem: () => storage.value, setItem: (_key, value) => { storage.value = value; } };
  global.document = { documentElement: { setAttribute() {}, lang: "" }, querySelectorAll: () => [] };
  global.window = { addEventListener() {}, dispatchEvent() {} };
  global.CustomEvent = function () {};
  Object.defineProperty(global, "navigator", {
    value: { languages: browser, language: browser[0] || "" }, configurable: true,
  });
  global.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve(EN) });
  delete require.cache[require.resolve(INDEX)];
  require(INDEX);
  return { api: global.window.JavisI18n, storage };
}

(async () => {
  for (const browser of [["vi-VN", "en-US"], ["en-GB"], ["fr-FR"], []]) {
    const { api } = load({ browser });
    await api.init();
    check("all browser languages resolve to English", api.lang() === "en", api.lang());
    check("English dictionary is used", api.t(KEY) === EN[KEY], api.t(KEY));
  }

  const saved = load({ browser: ["vi-VN"], stored: "vi" });
  await saved.api.init();
  check("legacy Vietnamese preference migrates to English", saved.storage.value === "en", saved.storage.value);
  check("legacy language preference cannot change the interface", saved.api.lang() === "en");

  const selected = load({ browser: ["en-US"] });
  await selected.api.setLang();
  check("explicit language selection stores English", selected.storage.value === "en", selected.storage.value);

  if (failures.length) {
    console.error("FAIL - " + failures.length + " check(s)");
    process.exitCode = 1;
  }
})();
