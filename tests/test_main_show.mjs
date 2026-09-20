// Regression test for multi-monitor placement: show() must leave the
// window fully on the active screen - repairing straddling or
// wrong-screen positions - while preserving a manually placed window
// inside the active screen. Run with: node tests/test_main_show.mjs
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

// Laptop 1920x1080 at (0,0); external 2560x1440 at (1920,0).
const screen1 = { name: "eDP-1", geometry: { x: 0, y: 0, width: 1920, height: 1080 } };
const screen2 = { name: "HDMI-A-1", geometry: { x: 1920, y: 0, width: 2560, height: 1440 } };
const work = new Map([
	[screen1, { ...screen1.geometry }],
	[screen2, { ...screen2.geometry }],
]);
let activeScreen = screen1;
let config = {};
const sandbox = {
	workspace: {
		windowList: () => [],
		windowAdded: { connect() {} },
		get activeScreen() { return activeScreen; },
		currentDesktop: 0,
		screens: [screen1, screen2],
		clientArea: (...args) => {
			// Faithful to KWin: only the two-argument (options, Output)
			// overload resolves per-screen areas. A third (desktop)
			// argument matches no overload and yields the union area.
			if (args.length === 2 && args[1] && typeof args[1] === "object") {
				const hit = work.get(args[1]);
				if (hit) return { ...hit };
			}
			if (args.length === 3) return { x: 0, y: 0, width: 3864, height: 1080 };
			throw new Error("unsupported clientArea overload");
		},
		get activeWindow() { return null; },
		set activeWindow(v) {},
	},
	readConfig: (k, d) => (k in config ? config[k] : d),
	print: () => {},
	callDBus: () => {},
	registerShortcut: () => {},
	console,
	Math, JSON, Number, Object, Array,
};
const loader = new Function(
	...Object.keys(sandbox),
	`${src}\nreturn { applyGeometry, show };`,
);
const { applyGeometry, show } = loader(...Object.values(sandbox));

function baseConfig() {
	config = { widthRatio: 0.72, heightRatio: 0.78, yOffset: 1,
		customWidth: 0, customHeight: 0, screenOverrides: "",
		recenterOnShow: false };
}
function inside(rect, outer) {
	return outer.x <= rect.x && outer.y <= rect.y
		&& outer.x + outer.width >= rect.x + rect.width
		&& outer.y + outer.height >= rect.y + rect.height;
}
function centeredX(g, area) {
	return area.x + Math.round((area.width - g.width) / 2);
}

// 1. Straddling window is repaired onto the active screen.
baseConfig();
applyGeometry({}, screen2); // prime lastScreenArea = area2
activeScreen = screen2;
const straddle = { frameGeometry: { x: 1500, y: 10, width: 1843, height: 700 }, minimized: true };
show(straddle);
check("straddle repaired fully inside active screen", inside(straddle.frameGeometry, screen2.geometry));
check("repaired window centered", straddle.frameGeometry.x === centeredX(straddle.frameGeometry, work.get(screen2)));
check("repaired window unminimized", straddle.frameGeometry && straddle.minimized === false);

// 2. Window fully on the wrong screen moves to the active screen.
const wrong = { frameGeometry: { x: 100, y: 10, width: 800, height: 600 }, minimized: true };
show(wrong);
check("wrong-screen window moved to active screen", inside(wrong.frameGeometry, screen2.geometry));

// 3. Manually placed window inside the active screen is preserved.
const manual = { frameGeometry: { x: 2000, y: 100, width: 800, height: 600 }, minimized: true };
const before = JSON.stringify(manual.frameGeometry);
show(manual);
check("manual placement preserved", JSON.stringify(manual.frameGeometry) === before);
check("manual window unminimized", manual.minimized === false);

// 4. recenterOnShow still forces a refit.
config.recenterOnShow = true;
const rec = { frameGeometry: { x: 2000, y: 100, width: 800, height: 600 }, minimized: true };
show(rec);
check("recenter refits to centered geometry", rec.frameGeometry.x === centeredX(rec.frameGeometry, work.get(screen2)));

process.exit(failures ? 1 : 0);
