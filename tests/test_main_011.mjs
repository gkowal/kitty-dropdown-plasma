// Regression test for AUDIT-011: applyGeometry() must clamp yOffset so
// y + height never leaves the work area, whatever kwinrc or
// screenOverrides request. Run with: node tests/test_main_011.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const repo = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = readFileSync(join(repo, "contents", "code", "main.js"), "utf8");

let failures = 0;
function check(desc, cond) {
	if (cond) console.log(`ok: ${desc}`);
	else { console.log(`FAIL: ${desc}`); failures++; }
}

// KWin scripting stubs. init() runs on load: no windows, one screen.
let area = { x: 0, y: 0, width: 1920, height: 800 };
let config = {};
const screen = { name: "eDP-1", geometry: { ...area } };
const sandbox = {
	workspace: {
		windowList: () => [],
		windowAdded: { connect() {} },
		activeScreen: screen,
		currentDesktop: 0,
		screens: [screen],
		clientArea: () => ({ ...area }),
		activeWindow: null,
	},
	readConfig: (k, d) => (k in config ? config[k] : d),
	print: () => {},
	callDBus: () => {},
	registerShortcut: () => {},
	console,
	Math, JSON, Number, Object, Array,
};
// Load main.js function declarations into this scope.
const loader = new Function(
	...Object.keys(sandbox),
	`${src}\nreturn { applyGeometry };`,
);
const { applyGeometry } = loader(...Object.values(sandbox));

function geometry(cfg, overrides) {
	config = { widthRatio: 0.72, heightRatio: 0.78, yOffset: 1,
		customWidth: 0, customHeight: 0, screenOverrides: "", ...cfg };
	if (overrides !== undefined)
		config.screenOverrides = JSON.stringify(overrides);
	const client = {};
	applyGeometry(client, screen);
	return client.frameGeometry;
}

// 1. Oversized global yOffset is clamped inside the area.
let g = geometry({ yOffset: 500 });
check("clamped: y + height <= area bottom", g.y + g.height <= area.y + area.height);
check("clamped: y stays at top when height fits", g.y === area.y + (area.height - g.height));

// 2. Normal offsets are untouched.
g = geometry({ yOffset: 1 });
check("normal offset preserved", g.y === area.y + 1);

// 3. Per-screen override yOffset is clamped too.
g = geometry({}, { "eDP-1": { yOffset: 700 } });
check("override clamped: y + height <= area bottom", g.y + g.height <= area.y + area.height);

// 4. Zero offset still lands on the top edge.
g = geometry({ yOffset: 0 });
check("zero offset lands on top edge", g.y === area.y);

process.exit(failures ? 1 : 0);
