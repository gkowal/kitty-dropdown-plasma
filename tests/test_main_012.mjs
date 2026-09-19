// Regression test for AUDIT-012: findKitty() must deterministically
// prefer the dropdown window on the active screen when several match.
// Case 5 pins the deliberate always-retry semantics (no launch guard):
// launch failure is unobservable from the script, so a guard could
// wedge the toggle after one failed launch.
// Run with: node tests/test_main_012.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const repo = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = readFileSync(join(repo, "contents/code/main.js"), "utf8");

let failures = 0;
function check(desc, cond) {
	if (cond) console.log(`ok: ${desc}`);
	else { console.log(`FAIL: ${desc}`); failures++; }
}

function kitty(id, rect) {
	return { __id: id, deleted: false, normalWindow: true,
		resourceClass: "kitty-dropdown", resourceName: "kitty-dropdown",
		frameGeometry: { ...rect }, minimized: false };
}
const area1 = { x: 0, y: 0, width: 1920, height: 1080 };
const area2 = { x: 1920, y: 0, width: 1920, height: 1080 };
const screen1 = { name: "DP-1" };
const screen2 = { name: "DP-2" };
const areas = new Map([[screen1, area1], [screen2, area2]]);

let windows = [];
let activeScreen = screen1;
let dbusCalls = [];
const sandbox = {
	workspace: {
		windowList: () => windows.slice(),
		windowAdded: { connect() {} },
		get activeScreen() { return activeScreen; },
		currentDesktop: 0,
		screens: [screen1, screen2],
		clientArea: (opt, screen) => ({ ...areas.get(screen) }),
		get activeWindow() { return null; },
		set activeWindow(v) {},
	},
	readConfig: (k, d) => d,
	print: () => {},
	callDBus: (...args) => { dbusCalls.push(args); },
	registerShortcut: () => {},
	console,
	Math, JSON, Number, Object, Array,
};
const loader = new Function(
	...Object.keys(sandbox),
	`${src}\nreturn { findKitty, toggleKitty };`,
);
const { findKitty, toggleKitty } = loader(...Object.values(sandbox));

// 1. No match -> null.
windows = [{ deleted: false, normalWindow: true,
	resourceClass: "konsole", resourceName: "konsole",
	frameGeometry: { x: 0, y: 0, width: 100, height: 100 } }];
check("no match returns null", findKitty() === null);

// 2. Single match -> itself.
const solo = kitty("solo", { x: 100, y: 10, width: 800, height: 600 });
windows = [solo];
check("single match returned", findKitty() === solo);

// 3. Two matches -> the one on the active screen.
const w1 = kitty("w1", { x: 100, y: 10, width: 800, height: 600 });
const w2 = kitty("w2", { x: 2020, y: 10, width: 800, height: 600 });
windows = [w1, w2];
activeScreen = screen2;
check("prefers window on active screen", findKitty() === w2);
activeScreen = screen1;
check("follows active screen", findKitty() === w1);

// 4. Neither on a known screen -> first match (deterministic).
const off = kitty("off", { x: 5000, y: 0, width: 100, height: 100 });
windows = [off, w1];
activeScreen = screen2;
check("falls back to first match", findKitty() === off);

// 5. Missing window keeps retrying (no wedging guard).
windows = [];
dbusCalls = [];
toggleKitty();
toggleKitty();
const starts = dbusCalls.filter(c => c[3] === "StartUnit");
check("retry issues StartUnit per press", starts.length === 2);
check("StartUnit targets dropdown unit",
	starts.every(c => c[4] === "kitty-dropdown.service" && c[5] === "replace"));

process.exit(failures ? 1 : 0);
