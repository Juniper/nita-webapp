/* ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** */
function triggerAction()
{
    var actionId = $('#action-selector').val();
    var campusNetworkId = $('#tree').tree('getSelectedNode').id.split("_")[1];
   	$.ajax({
		beforeSend: function(xhr, settings) {
        	xhr.setRequestHeader("X-CSRFToken", csrftoken);
		},
		type: "POST",
		contentType: 'application/json',
    	url: "/campus_network/" + campusNetworkId + "/action/" + actionId + "/trigger_action/",
       	success: function(data)
        {
            if(data.status=="success")
            {
                loadTable();
                var message = "Jenkins Action triggered successfully"
            	showNotification(1, message);
            	console.log("triggered Successfully");
        	}
        	else
        	{
        		if(data.reason != null || data.reason != undefined)
        		{
        			$('#triggerActionSizeDiv').attr('class','modal-dialog modal-md');
        			$('#action-status-text').text('No configuration found for this ' + campus_network_i18n +'. Please import Configuration before triggering Jenkins Action.');
        			$('#trigger-action-modal').modal('show');
        		}
        		else
        		{
        			$('#triggerActionSizeDiv').attr('class','modal-dialog modal-sm');
	        	    var message = "Error while triggering Jenkins Action"
                	showNotification(4, message);
        		}
        	    console.log("triggered failure");
        	}
        },
        error: function(){
        	var message = "Error while triggering Jenkins Action"
        	showNotification(4, message);
        	console.log("not working");
        }
	});

}

function loadConsoleLog()
{
	 var history_id = $('#history_id').attr("value")
	 if(history_id == null || history_id == undefined || history_id == "")
		 return;

	 $.ajax({
		    beforeSend: function(xhr,setting){
			    xhr.setRequestHeader("X-CSRFToken", csrftoken);
		    },
		    type: "POST",
		    url:"/action_history/"+history_id +"/console_log/" ,
		    success:function(data){
			    $("#console-pane-pre").html(data);
		    },
		    error:function(data){
			    console.log(data);
		    }
	    });
}

function scrollConsolePaneToBottom()
{
	$('#console-pane-pre').scrollTop(50000);
}

function initiateIframeTimer()
{
	if(iframeTimer == null || iframeTimer == undefined)
	{
		iframeTimer = $.timer(function() {
			loadConsoleLog();
			scrollConsolePaneToBottom();
		});
		iframeTimer.set({ time : 5000, autostart : false });
	}
	else
	{
		iframeTimer.pause();
	}
}

function toggleAutoRefresh()
{
	var text=$('#auto_refresh_badge').text()
	if(text=="Disabled")
	{
		text="Enabled"
		$("#auto_refresh_badge").attr("class", "badge progress-bar-success");
		scrollConsolePaneToBottom();
		iframeTimer.play()
	}
	else
	{
		text="Disabled"
		$("#auto_refresh_badge").attr("class", "badge progress-bar-danger");
		iframeTimer.pause()
	}
	$('#auto_refresh_badge').text(text)
}

jQuery(document).ready(function($) {
    loadTable();
    initiateIframeTimer();
});

$('#body').ready(function(){
    adjustHeightOfPanes()
});

function loadTable()
{
    var tabUrl=$("ul#main-tabs-list li.active").children()[0].href;
    var index=tabUrl.split("/").length-2;
    var id=tabUrl.split("/")[index];
    var campusNetworkId = $('#tree').tree('getSelectedNode').id.split("_")[1];
	$.ajax({
		beforeSend: function(xhr,setting){
			xhr.setRequestHeader("X-CSRFToken", csrftoken);
		},
		type: "POST",
		url:"/campus_network/" + campusNetworkId + "/action_history/"+id +"/" ,
		success:function(data){
			var count=0;
			$("#action-history-pane").html(data);

			$('#action-history-table tr').each(function(){
				count++;
				if(count>1)
					return;
		    });
			if(count > 1)
				$('#history_id').attr("value","");
		},
		error:function(data){
			console.log(data);
		}
	});
}

function adjustHeightOfPanes()
{
    //$("#pane_container").css("height", pane_height+"px");
    var selectorPane = $("#selector-pane");
    var actionMainPane = $("#action-main-pane");
    var mainPaneHeight = $("#main_pane").height();

    //set height
    $("#selector-pane").css("height", (mainPaneHeight *0.03)+"px");
    $("#action-main-pane").css("height", (mainPaneHeight*0.38)+"px");
    $("#console-pane").css("height", (mainPaneHeight*0.48)+"px");
    var actionMainPaneHeight = $("#action-main-pane").height();
    $("#action-history-pane").css("height", (actionMainPaneHeight *0.80)+"px");
    //$("#console-pane").css("height", (actionMainPaneHeight *0.48)+"px");
}
function displayStatus()
{
	console.log("ERRRROR LOADING >>>>>> CONSOLE VIEW")
}
