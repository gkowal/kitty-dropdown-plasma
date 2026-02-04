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
		print("Kitty dropdown not found. Ensure you launched kitty with: kitty --class kitty-dropdown");
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
