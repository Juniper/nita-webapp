// Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
/**
 * Notification constants
 *
 * 1 - success
 * 2 - info
 * 3 - warning
 * 4 - danger
 */
prev_class = "alert-success"

function repositionNotifier()
{
	var half_width= window_width/2;
	var notifier_width=$("#notifier").width()
	var notifier_half_width=notifier_width/2
	var notifier_position=half_width-notifier_half_width

	$("#notifier").css({'left':notifier_position+"px", "position":"absolute"})
}

function showNotification(type, text)
{
	$("#notifier-text").html(text);
	$("#notifier").removeClass(prev_class)
	prev_class = getAlertClass(type);
	$("#notifier").addClass(prev_class);
	repositionNotifier();
	$("#notifier").addClass("in");

	window.setTimeout(function() {
		$("#notifier").removeClass("in").addClass("out");
	}, 8000);
}

function getAlertClass(type)
{
	switch(type) {
		case 1:
			return "alert-success"
		case 2:
			return "alert-info"
		case 3:
			return "alert-warning"
		case 4:
			return "alert-danger"
	}
}

function fadeOutNotifier()
{
	$("#notifier").removeClass("in").addClass("out");
}
