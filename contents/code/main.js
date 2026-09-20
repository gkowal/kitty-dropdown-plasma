/*
# vim:tabstop=4:shiftwidth=4:noexpandtab
*/

var kittyLaunching = false;
var lastScreenArea = null;

function isKitty(client) {
	if (!client || client.deleted || !client.normalWindow) return false;
	let rClass = client.resourceClass ? client.resourceClass.toString() : "";
	let rName = client.resourceName ? client.resourceName.toString() : "";
	return rClass === "kitty-dropdown" || rName === "kitty-dropdown";
}

function findKitty() {
	let clients = workspace.windowList();
	let matches = clients.filter(client => isKitty(client));
	if (matches.length <= 1) return matches[0] || null;
	// Several dropdown windows (e.g. manually launched copies):
	// prefer the one on the active screen for deterministic toggles.
	let screen = workspace.activeScreen;
	if (screen) {
		let s = null;
		try {
			s = getScreenGeometry(screen);
		} catch (e) {
			s = null;
		}
		if (s) {
			for (let i = 0; i < matches.length; i++) {
				let r = matches[i].frameGeometry;
				if (!r) continue;
				let cx = r.x + r.width / 2, cy = r.y + r.height / 2;
				if (cx >= s.x && cx < s.x + s.width
					&& cy >= s.y && cy < s.y + s.height) {
					return matches[i];
				}
			}
		}
	}
	return matches[0];
}

function isVisible(client) {
	return !client.minimized;
}

function isActive(client) {
	return client === workspace.activeWindow;
}

function activate(client) {
	workspace.activeWindow = client;
}

function getOutputName(output) {
	if (!output) return "";
	return output.name ? output.name.toString() : "";
}

function getScreenGeometry(screen) {
	if (!screen) return null;
	// Plasma 6 resolves per-screen work areas through the two-argument
	// (options, Output) overload. Passing the virtual desktop as a third
	// argument matches no overload, and KWin then answers with the union
	// work area of all screens (observed: one 3863px area for a
	// 1536+2328 layout), which centers the dropdown across a boundary.
	try {
		return workspace.clientArea(5, screen);
	} catch (e) {
		try {
			return workspace.clientArea(0, screen);
		} catch (e2) {
			try {
				return screen.geometry;
			} catch (e3) {
				return null;
			}
		}
	}
}

function areasEqual(a, b) {
	if (!a || !b) return false;
	return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
}

function containsRect(outer, inner) {
	return outer.x <= inner.x
		&& outer.y <= inner.y
		&& outer.x + outer.width >= inner.x + inner.width
		&& outer.y + outer.height >= inner.y + inner.height;
}

function isOnScreen(client, screen) {
	let r = client.frameGeometry;
	if (!r || !screen) return false;
	let s = null;
	try {
		s = screen.geometry;
	} catch (e) {
		return false;
	}
	if (!s) return false;
	return containsRect(s, r);
}

function toPositiveInt(value) {
	let n = Number(value);
	if (!isFinite(n) || n <= 0) return 0;
	return Math.round(n);
}

function toNonNegativeInt(value) {
	let n = Number(value);
	if (!isFinite(n) || n < 0) return 0;
	return Math.round(n);
}

function toRatio(value, fallback) {
	let n = Number(value);
	if (!isFinite(n) || n <= 0) return fallback;
	return Math.max(0.1, Math.min(1.0, n));
}

function parseScreenConfig(raw) {
	if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
	let cfg = {};
	if (raw.width !== undefined) cfg.width = toPositiveInt(raw.width);
	if (raw.height !== undefined) cfg.height = toPositiveInt(raw.height);
	let rw = toRatio(raw.widthRatio, 0);
	if (rw > 0) cfg.widthRatio = rw;
	let rh = toRatio(raw.heightRatio, 0);
	if (rh > 0) cfg.heightRatio = rh;
	if (raw.yOffset !== undefined) cfg.yOffset = toNonNegativeInt(raw.yOffset);
	return cfg;
}

function applyGeometry(client, targetScreen) {
	let area = getScreenGeometry(targetScreen);
	if (!area) return;

	let outputName = getOutputName(targetScreen);

	// Read user settings via readConfig with default fallbacks
	let widthRatio = toRatio(readConfig("widthRatio", 0.72), 0.72);
	let heightRatio = toRatio(readConfig("heightRatio", 0.78), 0.78);
	let customWidth = toPositiveInt(readConfig("customWidth", 0));
	let customHeight = toPositiveInt(readConfig("customHeight", 0));
	let yOffset = toNonNegativeInt(readConfig("yOffset", 1));
	let screenOverridesStr = readConfig("screenOverrides", "");

	let screenConfig = null;
	if (screenOverridesStr && screenOverridesStr.length > 0) {
		try {
			let parsed = JSON.parse(screenOverridesStr);
			let raw = null;
			if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
				if (outputName && parsed[outputName]) {
					raw = parsed[outputName];
				} else if (parsed["default"]) {
					raw = parsed["default"];
				}
			}
			screenConfig = parseScreenConfig(raw);
		} catch (e) {
			print("applyGeometry: failed to parse screenOverrides JSON: " + e.message);
		}
	}

	let width, height;

	if (screenConfig) {
		if (screenConfig.width !== undefined && screenConfig.width > 0) {
			width = screenConfig.width;
		} else if (screenConfig.widthRatio !== undefined && screenConfig.widthRatio > 0) {
			width = Math.round(area.width * screenConfig.widthRatio);
		} else {
			width = customWidth > 0 ? customWidth : Math.round(area.width * widthRatio);
		}

		if (screenConfig.height !== undefined && screenConfig.height > 0) {
			height = screenConfig.height;
		} else if (screenConfig.heightRatio !== undefined && screenConfig.heightRatio > 0) {
			height = Math.round(area.height * screenConfig.heightRatio);
		} else {
			height = customHeight > 0 ? customHeight : Math.round(area.height * heightRatio);
		}

		if (screenConfig.yOffset !== undefined) {
			yOffset = screenConfig.yOffset;
		}
	} else {
		width = customWidth > 0 ? customWidth : Math.round(area.width * widthRatio);
		height = customHeight > 0 ? customHeight : Math.round(area.height * heightRatio);
	}

	if (width > area.width || height > area.height) {
		let fbW = (screenConfig && screenConfig.widthRatio !== undefined && screenConfig.widthRatio > 0)
			? screenConfig.widthRatio : widthRatio;
		let fbH = (screenConfig && screenConfig.heightRatio !== undefined && screenConfig.heightRatio > 0)
			? screenConfig.heightRatio : heightRatio;
		if (width > area.width) {
			width = Math.round(area.width * fbW);
		}
		if (height > area.height) {
			height = Math.round(area.height * fbH);
		}
	}

	let x = area.x + Math.round((area.width - width) / 2);
	// Keep the window inside the usable area: an oversized yOffset
	// (e.g. from screenOverrides) must not push it off-screen.
	let y = area.y + Math.min(yOffset, Math.max(0, area.height - height));

	client.frameGeometry = {
		x: x,
		y: y,
		width: width,
		height: height
	};

	lastScreenArea = area;
}

function setupClient(client) {
	client.noBorder = true;
	client.onAllDesktops = true;
	client.skipTaskbar = true;
	client.skipSwitcher = true;
	client.skipPager = true;
	client.keepAbove = true;
	client.fullScreen = false;
	client.setMaximize(false, false);

	let targetScreen = workspace.activeScreen;
	if (targetScreen) {
		applyGeometry(client, targetScreen);
	}
}

function show(client) {
	let targetScreen = workspace.activeScreen;
	let area = targetScreen ? getScreenGeometry(targetScreen) : null;
	let recenterOnShow = readConfig("recenterOnShow", false);
	// Refit unless the window already sits fully on the active screen:
	// that also repairs windows left straddling a boundary or fully on
	// another screen, which a bare area comparison can miss.
	if (area && (recenterOnShow || !areasEqual(lastScreenArea, area) || !isOnScreen(client, targetScreen))) {
		applyGeometry(client, targetScreen);
	}
	client.minimized = false;
}

function hide(client) {
	client.minimized = true;
}

function launchKitty() {
	callDBus(
		"org.freedesktop.systemd1",
		"/org/freedesktop/systemd1",
		"org.freedesktop.systemd1.Manager",
		"StartUnit",
		"kitty-dropdown.service",
		"replace",
		function(job) {
			// This callback runs only on a successful D-Bus reply:
			// KWin does not invoke it on D-Bus errors (those surface
			// in KWin's own log, not here), and a successful
			// StartUnit reply carries systemd's job object path, so
			// a falsy check here could never detect failure. `job`
			// only confirms systemd accepted the request; the new
			// window arrives via windowAdded -> setupKitty, which
			// clears kittyLaunching. A failed launch leaves no
			// window and the next toggle simply retries. Keep this
			// callback attached: KWin only watches the D-Bus call
			// (and reports errors in its log) when a callback is
			// given; without it failures would be silent. There is
			// deliberately no KRunner fallback: App.query() only
			// fills the runner UI and never launches anything.
		}
	);
}

function toggleKitty() {
	let kitty = findKitty();
	if ( kitty ) {
		if ( isVisible(kitty) ) {
			if ( isActive(kitty) ) {
				hide(kitty);
			} else {
				activate(kitty);
			}
		} else {
			show(kitty);
			activate(kitty);
		}
	} else {
		// No dropdown window: (re)launch. Deliberately no
		// `if (kittyLaunching) return` guard here: launch failure
		// is unobservable from the script (see launchKitty), so a
		// permanent guard could wedge the toggle after one failed
		// launch; and duplicate StartUnit requests are harmless
		// because systemd replaces the queued job. Every press
		// while no window exists simply retries.
		kittyLaunching = true;
		launchKitty();
	}
}

function setupKitty(client) {
	if ( isKitty(client) ) {
		setupClient(client);
		if (kittyLaunching) {
			kittyLaunching = false;
			show(client);
			activate(client);
		}
	}
}

function init() {
	let kitty = findKitty();
	if ( kitty ) {
		setupClient(kitty);
	}

	workspace.windowAdded.connect(setupKitty);
	registerShortcut("Toggle Kitty", "Toggle Kitty Drop-Down", "Meta+F12", toggleKitty);
}

init();
