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
	return clients.find(client => isKitty(client)) || null;
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
	try {
		return workspace.clientArea(2, screen, workspace.currentDesktop);
	} catch (e) {
		try {
			return workspace.clientArea(0, screen, workspace.currentDesktop);
		} catch (e2) {
			return screen.geometry;
		}
	}
}

function areasEqual(a, b) {
	if (!a || !b) return false;
	return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
}

function applyGeometry(client, targetScreen) {
	let area = getScreenGeometry(targetScreen);
	if (!area) return;

	let outputName = getOutputName(targetScreen);

	// Read user settings via readConfig with default fallbacks
	let widthRatio = readConfig("widthRatio", 0.72);
	let heightRatio = readConfig("heightRatio", 0.78);
	let customWidth = readConfig("customWidth", 0);
	let customHeight = readConfig("customHeight", 0);
	let yOffset = readConfig("yOffset", 1);
	let screenOverridesStr = readConfig("screenOverrides", "");

	let screenConfig = null;
	if (screenOverridesStr && screenOverridesStr.length > 0) {
		try {
			let parsed = JSON.parse(screenOverridesStr);
			if (outputName && parsed[outputName]) {
				screenConfig = parsed[outputName];
			} else if (parsed["default"]) {
				screenConfig = parsed["default"];
			}
		} catch (e) {
			print("applyGeometry: failed to parse screenOverrides JSON: " + e.message);
		}
	}

	let width, height;

	if (screenConfig) {
		if (screenConfig.width !== undefined && screenConfig.width > 0) {
			width = Math.round(screenConfig.width);
		} else if (screenConfig.widthRatio !== undefined && screenConfig.widthRatio > 0) {
			width = Math.round(area.width * Math.max(0.1, Math.min(1.0, screenConfig.widthRatio)));
		} else {
			width = customWidth > 0 ? customWidth : Math.round(area.width * widthRatio);
		}

		if (screenConfig.height !== undefined && screenConfig.height > 0) {
			height = Math.round(screenConfig.height);
		} else if (screenConfig.heightRatio !== undefined && screenConfig.heightRatio > 0) {
			height = Math.round(area.height * Math.max(0.1, Math.min(1.0, screenConfig.heightRatio)));
		} else {
			height = customHeight > 0 ? customHeight : Math.round(area.height * heightRatio);
		}

		if (screenConfig.yOffset !== undefined) {
			yOffset = Math.max(0, Math.round(screenConfig.yOffset));
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
		width = Math.round(area.width * Math.max(0.1, Math.min(1.0, fbW)));
		height = Math.round(area.height * Math.max(0.1, Math.min(1.0, fbH)));
	}

	let x = area.x + Math.round((area.width - width) / 2);
	let y = area.y + yOffset;

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
	if (area && !areasEqual(lastScreenArea, area)) {
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
		function(res) {
			if (!res) {
				callDBus(
					"org.kde.krunner",
					"/App",
					"org.kde.krunner.App",
					"query",
					"kitty --single-instance --instance-group dropdown --class kitty-dropdown --override hide_window_decorations=yes --hold --config $HOME/.config/kitty/kitty-dropdown.conf",
					function(krunnerRes) {
						if (!krunnerRes) {
							print("launchKitty: both systemd and KRunner fallback failed to launch Kitty");
						}
					}
				);
			}
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
	} else if (!kittyLaunching) {
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
