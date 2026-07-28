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

function setupClient(client) {
	print("setupClient: Targeting kitty-dropdown");
	client.onAllDesktops = true;
	client.skipTaskbar = true;
	client.skipSwitcher = true;
	client.skipPager = true;
	client.keepAbove = true;
	client.fullScreen = false;
	client.setMaximize(false, false);
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

function show(client) {
	client.geometry = {
	  x: 290,
	  y: 1,
	  width: 2002,
	  height: 1029
	};
	client.minimized = false;
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
