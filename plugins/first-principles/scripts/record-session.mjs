#!/usr/bin/env node
// Record a hands-on test run of a web app for an agent to read.
//
//   cd <your project>            # any folder where Playwright is installed
//   node <plugin>/scripts/record-session.mjs http://localhost:5173 [--out <dir>]
//
// A browser opens. Use the app as usual. To flag a problem press Ctrl+Shift+F (Cmd+Shift+F on
// a Mac) and type a note; start it with the task number ("3: the bars lost their colours").
// Close the browser window when done. The folder it prints holds:
//   summary.md     read this first: flags, errors, failed requests, a timeline of clicks
//   events.jsonl   every event, one JSON object per line
//   shots/         a screenshot after each click and at each flag
// Never recorded: what is typed into password, token, secret, code or card fields, and
// sign-in tokens in page addresses.

import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const args = process.argv.slice(2);
const url = args.find((a) => !a.startsWith("--"));
const outArg = args.includes("--out") ? args[args.indexOf("--out") + 1] : null;
if (!url) {
  console.error("usage: node record-session.mjs <app url> [--out <dir>]");
  process.exit(1);
}

function loadPlaywright() {
  const req = createRequire(path.join(process.cwd(), "package.json"));
  for (const name of [process.env.PLAYWRIGHT_PATH, "playwright", "@playwright/test"].filter(Boolean)) {
    try { return req(name); } catch {}
  }
  // pnpm keeps packages under node_modules/.pnpm
  const store = path.join(process.cwd(), "node_modules", ".pnpm");
  const hit = fs.existsSync(store) && fs.readdirSync(store).filter((d) => /^playwright@\d/.test(d)).sort().pop();
  if (hit) return req(path.join(store, hit, "node_modules", "playwright"));
  console.error("Playwright not found. Run this from a project that has it installed, or set PLAYWRIGHT_PATH.");
  process.exit(1);
}

const SECRET = /pass|token|secret|otp|code|card|cvc|cvv|ssn|auth|key/i;
const scrubUrl = (u) => {
  try {
    const x = new URL(u);
    for (const k of [...x.searchParams.keys()]) if (SECRET.test(k)) x.searchParams.set(k, "REDACTED");
    if (SECRET.test(x.hash)) x.hash = "#REDACTED";
    return x.toString();
  } catch { return u; }
};

const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
// Outside the project, so a recording is never committed by accident.
const out = path.resolve(outArg || path.join(os.homedir(), ".cache", "first-principles", "recordings", stamp));
fs.mkdirSync(path.join(out, "shots"), { recursive: true });
const log = fs.createWriteStream(path.join(out, "events.jsonl"));
const events = [];
const t0 = Date.now();
let n = 0;

function record(ev, when = Date.now()) {
  const e = { i: events.length, t: ((when - t0) / 1000).toFixed(1), ...ev };
  if (e.url) e.url = scrubUrl(e.url);
  events.push(e);
  log.write(JSON.stringify(e) + "\n");
  return e;
}

// The same fields the log redacts are blacked out in every screenshot.
const SECRET_WORDS = SECRET.source.split("|");
const SECRET_FIELDS = ["input[type=password]", ...["name", "id", "autocomplete", "aria-label"].flatMap((attr) =>
  SECRET_WORDS.map((w) => `input[${attr}*="${w}" i], textarea[${attr}*="${w}" i]`))].join(", ");

async function shot(page, label) {
  const file = `shots/${String(++n).padStart(4, "0")}-${label}.png`;
  try {
    await page.screenshot({ path: path.join(out, file), mask: [page.locator(SECRET_FIELDS)], maskColor: "#000" });
    return file;
  } catch { return null; }
}

// Runs inside every page and frame.
const pageScript = `(() => {
  if (window.__fpRecorder) return; window.__fpRecorder = true;
  const SECRET = ${SECRET};
  const describe = (el) => {
    const t = el.closest('button,a,[role],input,select,textarea,label,summary,[data-testid]') || el;
    const label = t.labels && t.labels[0] ? t.labels[0].innerText : '';
    const name = (t.getAttribute('aria-label') || label || t.innerText || t.title || t.placeholder || t.alt || '')
      .trim().replace(/\\s+/g, ' ').slice(0, 80);
    return { role: t.getAttribute('role') || t.tagName.toLowerCase(), name, testid: t.dataset ? t.dataset.testid : undefined };
  };
  const sensitive = (el) => el.type === 'password' || SECRET.test([el.name, el.id, el.autocomplete, el.getAttribute('aria-label')].join(' '));
  document.addEventListener('click', (e) => window.__fpRecord({ type: 'click', ...describe(e.target), x: e.clientX, y: e.clientY }), true);
  document.addEventListener('change', (e) => {
    const el = e.target; if (!('value' in el)) return;
    const value = sensitive(el) ? 'REDACTED' : String(el.type === 'checkbox' ? el.checked : el.value).slice(0, 120);
    window.__fpRecord({ type: 'change', ...describe(el), value });
  }, true);
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'f') {
      e.preventDefault();
      const note = prompt('What is wrong here? (start with the task number)');
      if (note) window.__fpRecord({ type: 'flag', note });
    } else if (['Enter', 'Escape', 'Tab'].includes(e.key) || ((e.ctrlKey || e.metaKey) && e.key.length === 1)) {
      window.__fpRecord({ type: 'key', key: (e.metaKey ? 'Cmd+' : e.ctrlKey ? 'Ctrl+' : '') + e.key, ...describe(e.target) });
    }
  }, true);
})();`;

const { chromium } = loadPlaywright();
const profile = path.join(os.homedir(), ".cache", "first-principles", "recorder-profile");
const launch = (extra) => chromium.launchPersistentContext(profile, { headless: false, viewport: null, ...extra });
const context = await launch({}).catch(() => launch({ channel: "chrome" }));

await context.exposeBinding("__fpRecord", async ({ page }, ev) => {
  const t = Date.now();
  if (ev.type === "click" || ev.type === "flag") {
    if (ev.type === "click") await new Promise((r) => setTimeout(r, 400)); // let the click land
    ev.shot = await shot(page, ev.type);
  }
  record({ ...ev, url: page.url() }, t);
});
await context.addInitScript(pageScript);

// Failed loads are logged once, as http-error or request-failed, not again as a console error.
const noise = (u) => /\/favicon\.ico(\?|$)/.test(u);
function watch(page) {
  // On a Mac, closing the last window leaves the browser running; that is the end of the session.
  page.on("close", () => setTimeout(() => context.pages().length === 0 && finish(), 500));
  page.on("framenavigated", (f) => f === page.mainFrame() && record({ type: "navigate", url: f.url() }));
  page.on("console", (m) => ["error", "warning"].includes(m.type()) && !m.text().startsWith("Failed to load resource") && record({ type: `console-${m.type()}`, text: m.text().slice(0, 500), url: page.url() }));
  page.on("pageerror", (err) => record({ type: "page-error", text: String(err).slice(0, 500), url: page.url() }));
  page.on("requestfailed", (r) => !noise(r.url()) && record({ type: "request-failed", method: r.method(), url: r.url(), text: r.failure()?.errorText }));
  page.on("response", (r) => r.status() >= 400 && !noise(r.url()) && record({ type: "http-error", status: r.status(), method: r.request().method(), url: r.url() }));
  page.on("dialog", (d) => d.type() !== "prompt" && record({ type: "dialog", text: d.message() }));
}
context.pages().forEach(watch);
context.on("page", watch);

const page = context.pages()[0] || (await context.newPage());
await page.goto(url);
record({ type: "start", url });
console.log(`Recording to ${out}\nFlag a problem: Ctrl+Shift+F (Cmd+Shift+F on a Mac). Close the browser when done.`);

let finished = false;
async function finish() {
  if (finished) return;
  finished = true;
  record({ type: "end" });
  const at = (e) => `${e.t}s${e.shot ? ` ([shot](${e.shot}))` : ""}`;
  const pick = (types) => events.filter((e) => types.includes(e.type)).sort((a, b) => a.t - b.t);
  const flags = pick(["flag"]);
  const errors = pick(["page-error", "console-error", "http-error", "request-failed"]);
  const timeline = pick(["navigate", "click", "change", "key", "flag", "dialog"]);
  const lines = [
    `# Recorded session ${stamp}`, "",
    `${url} · ${events.at(-1).t}s · ${pick(["click"]).length} clicks · ${flags.length} flags · ${errors.length} errors`, "",
    "## Flags", ...(flags.length ? flags.map((e) => `- ${at(e)} **${e.note}** on ${e.url}`) : ["none"]), "",
    "## Errors and failed requests", ...(errors.length ? errors.map((e) => `- ${e.t}s ${e.type} ${e.status || ""} ${e.method || ""} ${e.text || ""} ${e.url || ""}`.replace(/ +/g, " ")) : ["none"]), "",
    "## Timeline",
    ...timeline.map((e) => {
      if (e.type === "navigate") return `- ${e.t}s → ${e.url}`;
      if (e.type === "flag") return `- ${at(e)} ⚑ ${e.note}`;
      if (e.type === "change") return `- ${e.t}s set ${e.role} "${e.name}" = ${e.value}`;
      if (e.type === "key") return `- ${e.t}s key ${e.key} in ${e.role} "${e.name}"`;
      if (e.type === "dialog") return `- ${e.t}s dialog: ${e.text}`;
      return `- ${at(e)} click ${e.role} "${e.name}"`;
    }),
  ];
  fs.writeFileSync(path.join(out, "summary.md"), lines.join("\n") + "\n");
  log.end();
  console.log(`Done. Give the agent this folder: ${out}`);
  await context.close().catch(() => {});
  process.exit(0);
}
context.on("close", finish);
process.on("SIGINT", finish);
