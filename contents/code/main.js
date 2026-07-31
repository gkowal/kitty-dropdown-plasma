/*
# vim:tabstop=4:shiftwidth=4:noexpandtab
*/

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

function isGeometryOnScreen(fg, screenArea) {
	if (!fg || !screenArea) return false;
	let centerX = fg.x + fg.width / 2;
	let centerY = fg.y + fg.height / 2;
	return (centerX >= screenArea.x && centerX < screenArea.x + screenArea.width &&
	        centerY >= screenArea.y && centerY < screenArea.y + screenArea.height);
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

	print("applyGeometry: outputName=" + outputName + " screenOverridesStr=" + screenOverridesStr);

	let screenConfig = null;
	if (screenOverridesStr && screenOverridesStr.length > 0) {
		try {
			let parsed = JSON.parse(screenOverridesStr);
			if (outputName && parsed[outputName]) {
				screenConfig = parsed[outputName];
				print("applyGeometry: matched screenConfig for " + outputName + ": " + JSON.stringify(screenConfig));
			} else if (parsed["default"]) {
				screenConfig = parsed["default"];
				print("applyGeometry: using default screenConfig: " + JSON.stringify(screenConfig));
			}
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

	let x = area.x + Math.round((area.width - width) / 2);
	let y = area.y + yOffset;

	client.frameGeometry = {
		x: x,
		y: y,
		width: width,
		height: height
	};
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

function printClient(client) {
	print("resourceName=" + client.resourceName.toString() +
		";resourceClass=" + client.resourceClass.toString() +
		";normalWindow=" + client.normalWindow +
		";onAllDesktops=" + client.onAllDesktops +
		";skipTaskbar=" + client.skipTaskbar +
		";skipSwitcher=" + client.skipSwitcher +
		";skipPager=" + client.skipPager +
		";keepAbove=" + client.keepAbove +
		";fullScreen=" + client.fullScreen +
		"");
}

function getTargetGeometry(client) {
	let screen = workspace.activeScreen;
	return applyGeometry(client, screen);
}

function show(client) {
	client.minimized = false;
	let targetScreen = workspace.activeScreen;
	if (targetScreen) {
		let screenArea = getScreenGeometry(targetScreen);
		let fg = client.frameGeometry;
		if (screenArea && fg && !isGeometryOnScreen(fg, screenArea)) {
			applyGeometry(client, targetScreen);
		}
	}
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
					"kitty --single-instance --instance-group dropdown --class kitty-dropdown --override hide_window_decorations=yes --hold --config ~/.config/kitty/kitty-dropdown.conf"
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
	} else {
		launchKitty();
	}
}

function setupKitty(client) {
	if ( isKitty(client) ) {
		setupClient(client);
		show(client);
		activate(client);
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
