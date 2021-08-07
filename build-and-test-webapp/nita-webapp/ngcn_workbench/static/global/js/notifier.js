/* ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** */
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
