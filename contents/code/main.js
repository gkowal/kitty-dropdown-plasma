/*
# vim:tabstop=4:shiftwidth=4:noexpandtab
*/

function isKitty(client) {
	return client &&
		   !client.deleted &&
		   client.normalWindow &&
		   client.resourceClass.toString() === "kitty-dropdown";
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

function hasCustomWindowRule(client) {
	if (!client.frameGeometry) return false;
	let fg = client.frameGeometry;
	// If Y is positioned near top of screen (<= 10) or dimensions were set by window rule, respect KWin rule
	return (fg.y <= 10) || (fg.width >= 1200) || (fg.height >= 800);
}

function setupClient(client) {
	print("setupClient: Targeting kitty-dropdown");
	client.noBorder = true;
	client.onAllDesktops = true;
	client.skipTaskbar = true;
	client.skipSwitcher = true;
	client.skipPager = true;
	client.keepAbove = true;
	client.fullScreen = false;
	client.setMaximize(false, false);

	// Only apply default script geometry if KWin Window Rules have not already set custom geometry
	if (!hasCustomWindowRule(client)) {
		let geom = getTargetGeometry(client);
		client.frameGeometry = geom;
		client.geometry = geom;
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
	let area = null;
	if (screen) {
		try {
			// In KWin 6 API, 2 = MaximizeArea (accounts for top/bottom Plasma panels)
			area = workspace.clientArea(2, screen, workspace.currentDesktop);
		} catch (e) {
			try {
				// 0 = PlacementArea
				area = workspace.clientArea(0, screen, workspace.currentDesktop);
			} catch (e2) {
				area = screen.geometry;
			}
		}
	}
	if (!area && screen && screen.geometry) {
		area = screen.geometry;
	}
	if (area) {
		let width = Math.round(area.width * 0.72);
		let height = Math.round(area.height * 0.78);
		let x = area.x + Math.round((area.width - width) / 2);
		let y = area.y + 1;
		return {
			x: x,
			y: y,
			width: width,
			height: height
		};
	}
	return {
		x: 269,
		y: 1,
		width: 1382,
		height: 842
	};
}

function show(client) {
	client.minimized = false;
	// Only re-apply target geometry if the window moved to a different monitor
	if (client.screen && workspace.activeScreen && client.screen !== workspace.activeScreen) {
		let geom = getTargetGeometry(client);
		client.frameGeometry = geom;
		client.geometry = geom;
	}
}

function hide(client) {
	client.minimized = true;
}

function launchKitty() {
	print("Kitty dropdown not found. Launching kitty via DBus...");
	callDBus(
		"org.freedesktop.systemd1",
		"/org/freedesktop/systemd1",
		"org.freedesktop.systemd1.Manager",
		"StartUnit",
		"kitty-dropdown.service",
		"replace",
		function(res) {
			if (!res) {
				print("Systemd user manager unavailable. Falling back to KRunner launch...");
				callDBus(
					"org.kde.krunner",
					"/App",
					"org.kde.krunner.App",
					"query",
					"kitty --single-instance --class kitty-dropdown --app-id kitty-dropdown --hold --config ~/.config/kitty/kitty-dropdown.conf"
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
