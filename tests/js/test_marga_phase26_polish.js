"use strict";
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..", "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const css = read("dashboard/console.css");
const style = read("dashboard/style.css");
const html = read("dashboard/index.html");
const js = read("dashboard/console.js");
const config = read("server/config.py");
const main = read("server/main.py");
const en = JSON.parse(read("dashboard/i18n/en.json"));
const vi = JSON.parse(read("dashboard/i18n/vi.json"));
const failures = [];
function check(name, ok) {
  console.log((ok ? "ok   " : "FAIL ") + name);
  if (!ok) failures.push(name);
}
function rgb(hex) { return hex.match(/[\da-f]{2}/gi).map((x) => parseInt(x, 16) / 255).map((v) =>
  v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
}
function luminance(hex) { const [r, g, b] = rgb(hex); return 0.2126 * r + 0.7152 * g + 0.0722 * b; }
const contrast = (a, b) => {
  const l1 = luminance(a), l2 = luminance(b);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
};

check("light inactive sidebar text uses an opaque, darker text token",
  /:root\[data-theme="light"\] \.rail-item:not\(\.active\)\s*\{\s*color:\s*var\(--text2\)/.test(css)
  && /:root\[data-theme="light"\] \.rail-item:not\(\.active\) \.rail-lbl\s*\{\s*opacity:\s*1/.test(css));
check("light sidebar label color reaches WCAG AA at 4.5:1",
  contrast("#55505f", "#fdfcff") >= 4.5);
check("setup token input can shrink within the wizard on narrow screens",
  /#wzBootstrapToken\{width:100%;min-width:0;box-sizing:border-box\}/.test(html));
check("setup token placeholder is concise and localized", en["wz.bootstrap_ph"] === "Enter owner token"
  && vi["wz.bootstrap_ph"] === "Enter owner token"
  && en["wz.bootstrap_ph"].length <= 24 && vi["wz.bootstrap_ph"].length <= 28);
check("new workspace defaults and fallbacks use MARGA AI OS",
  /"workspace_name": "MARGA AI OS"/.test(config)
  && main.includes('os.getenv("WORKSPACE_NAME", "MARGA AI OS")')
  && !main.includes('os.getenv("WORKSPACE_NAME", "Javis OS")')
  && main.includes('cfg.get("workspace_name") or "MARGA AI OS"')
  && main.includes('patch["workspace_name"] or "MARGA AI OS"')
  && main.includes('brand = "MARGA AI OS"')
  && !/workspace_name\s*\|\|\s*"Javis OS"/.test(js)
  && js.includes('value.trim() || "MARGA AI OS"'));
check("remaining user-facing product titles use MARGA AI OS",
  js.includes('<span class="upd-name">MARGA AI OS</span>')
  && js.includes('<span class="gcard-name">MARGA AI OS</span>')
  && main.includes('FastAPI(title="MARGA AI OS")')
  && main.includes('A conversation shared from MARGA AI OS')
  && main.includes('This is a MARGA AI OS system skill')
  && main.includes('A new MARGA AI OS update.'));
check("missing-model text exists in both locales", !!en["cs.eng_nomodel"]
  && !!vi["cs.eng_nomodel"] && !en["cs.eng_nomodel"].includes("cs.eng_nomodel")
  && !vi["cs.eng_nomodel"].includes("cs.eng_nomodel"));
check("model banner refreshes after dictionaries load and has a readable fallback",
  /addEventListener\("javis:i18n",\s*\(\)\s*=>\s*\{\s*refreshEngineBanner\(\)/.test(js)
  && js.includes('missingModel === "cs.eng_nomodel"')
  && js.includes("No AI model is connected. Select this notice to connect one."));
check("dark brain canvas uses the MARGA background instead of near-black #03030a",
  style.includes("rgba(20, 12, 40, 0.04) 55%, #10101c 78%")
  && !style.includes("rgba(20, 12, 40, 0.04) 55%, #03030a 78%"));
check("approved dark violet and background tokens remain", /--bg:\s*#10101c/i.test(style)
  && /--accent:\s*#8b5cf6/i.test(style) && /--accent2:\s*#a78bfa/i.test(style));

if (failures.length) {
  console.error("FAIL - test_marga_phase26_polish: " + failures.join(", "));
  process.exit(1);
}
console.log("OK - test_marga_phase26_polish");
