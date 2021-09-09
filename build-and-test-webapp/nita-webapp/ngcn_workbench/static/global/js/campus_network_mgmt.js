/* ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** */
jQuery(document).ready(function($) {
		$('#main_pane').css("display","none");

		$(".select-row").css("cursor","pointer");
        $('#del_network').prop('disabled', true)
	    $('#edit_network').prop('disabled', true)

	        $('#CampusNetwork tr').on('click', function() {
			  if($(this).hasClass('selected'))
			  {
				 $(this).removeClass('selected');

	    	  }
			  else
			  {
	    	     $(this).addClass('selected').siblings().removeClass('selected');
	    	  }

			  var count = 0
			  $.map(table2.rows('.selected').data(), function (item) {
			    	count++
			    });

			  if(count == 0)
		      {
				  $('#del_network').prop('disabled', true)
				  $('#edit_network').prop('disabled', true)
		      }
			  else
			  {
				  $('#del_network').prop('disabled', false)
				  $('#edit_network').prop('disabled', false)
			  }
	    	});

        setTimeout(
        		  function()
        		  {
        			  if ( table2 != null && typeof table2 != undefined ) {
        				  table2.destroy();
        			  	}
        			  table2 = $('#CampusNetwork').DataTable({
        				  "paging":   true,
        				  "ordering": false,
        				  "info":     false,
        				  "bFilter": false,
        				  "bInfo": false,
        				  "bLengthChange": false,
        				  "aoColumnDefs": [{ "bVisible": false, "aTargets": [0] }]
        			  });
        			  $('#main_pane').css("display","unset");
        		  }, 100);

    	$("#campus_network_form").submit(function(event) {
    		showLoader();
    		var formData = new FormData($(this)[0])
    		var status_text1="added"
    		var status_text2="adding"
    		var actionVal=this.action

    		console.log(this.action.indexOf("edit"))
    	    if(this.action.indexOf("edit") != -1)
    	    {
    	    	status_text1="changed"
            	status_text2="changing"
    	    }

        	$.ajax({
        	    type: $(this).attr('method'),
        	    url: this.action,
        	    enctype: "multipart/form-data",
        	    data : formData,
        	    cache: false,
                contentType: false,
                processData: false,
        	    context: this,
        	    success: function(data, status) {
        	    	if(data.result != null && data.result != undefined && data.result=="success")
        	    	{
        	    		$('#add-campus-network-modal').modal('hide');
        	    		showNotification(1, campus_network_i18n + " - <b>" + data.name + "</b> " + status_text1 + " successfully");
        	    		if($('#campus_network_form').data('load_summary')){
        	    			loadCampusNetworkSummary($('#campus_network_form').data('network_id'));
        	    		}
        	    		else {
        	    			loadCampusNetworkDiv();
        	    		}
        	    	}
        	    	if(data.result != null && data.result != undefined && data.result=="failure")
        	    	{
        	    		showNotification(4, "Error while " + status_text2 + " " + campus_network_i18n);
        	    	}
        	    	else
        	    	{
        	    		data += '</br><p style="margin-bottom:0px"><label style="padding-left: 11px; margin-bottom:0px"><b>Note</b>: By Enabling the Dynamic ansible workspace,'
    	    				+ 'the "build_dir" variable in the configuration excel file will be configured dynamically, which will create new  ansible build directory for each Network</label></p>'
        	    		$('#campus_network_forms').html(data);
        	    	}
        	    	hideLoader();
        	    },
	            error: function(){
	            	showNotification(4, "Error while " + status_text2 + " " + campus_network_i18n);
	            	hideLoader();
	            }
        	    });
        	    return false;
    		});

});

function loadCampusNetworkDiv()
{
	loadTreeData();
    setTimeout(
  		  function()
  		  {
  			var node = $('#tree').tree('getNodeById', "campus_network");
  		    $('#tree').tree('selectNode', node);
  			loadMainDiv(node);
  			$('.modal-backdrop').hide();
  		  }, 100);
}

function loadCampusNetworkSummary(network_id)
{
	var node = $('#tree').tree('getNodeById', "campusnetwork_"+network_id);
    $('#tree').tree('selectNode', node);
	loadMainDiv(node);
	$('.modal-backdrop').hide();
}

function addCampusNetwork(save)
{
		var url = "/campusnetwork/add/"

	    var csrftoken = getCookie('csrftoken');
	    $.ajax({
	            beforeSend: function(xhr, settings) {
	                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
	            },
	            type: "GET",
	            url: url,
	            success: function(data)
	            {
	            	    $("#campus_network_form").attr('action',url)
	            	    $("#add_campus_network_header").text("Add " + campus_network_i18n)
	            	    data += '</br><p style="margin-bottom:0px"><label style="padding-left: 11px; margin-bottom:0px"><b>Note</b>: By Enabling the Dynamic ansible workspace,'
	    				+ 'the "build_dir" variable in the configuration excel file will be configured dynamically, which will create new  ansible build directory for each Network</label></p>'
	                    $('#campus_network_forms').html(data);
	                    $('#add-campus-network-modal').modal('show');
	            },
	            error: function(){
	                    console.log('failure');
	            }
	    });
}

function editCampusNetworkBySelection(){
	var campusNetworkId = "";
    var ids = $.map(table2.rows('.selected').data(), function (item) {
    	campusNetworkId =  item[0];
    });
    $('#campus_network_form').data('load_summary',false);
    editCampusNetwork(campusNetworkId);
}

function editCampusNetworkbyId(campusNetworkId){
	$('#campus_network_form').data('load_summary',true);
	$('#campus_network_form').data('network_id',campusNetworkId);
    editCampusNetwork(campusNetworkId);
}

function editCampusNetwork(campusNetworkId)
{
    var url = "/campusnetwork/" + campusNetworkId + "/edit/"
    var csrftoken = getCookie('csrftoken');
    $.ajax({
            beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            type: "GET",
            url: url,
            success: function(data)
             {
            	    $("#campus_network_form").attr('action',url)
            	    $("#add_campus_network_header").text("Edit " + campus_network_i18n)
            	    data += '</br><p style="margin-bottom:0px"><label style="padding-left: 11px; margin-bottom:0px"><b>Note</b>: By Enabling the Dynamic ansible workspace,'
	    				+ 'the "build_dir" variable in the configuration excel file will be configured dynamically, which will create new  ansible build directory for each Network</label></p>'
                    $('#campus_network_forms').html(data);
            	    $('#id_campus_type').attr('disabled','disabled');
            	    $("#id_name").prop("readonly", true);
                    $('#add-campus-network-modal').modal('show');
            },
            error: function(){
                    console.log('failure');
            }
    });
}

function deleteCampusNetwork()
{
	$('#delete-campus-network-modal').modal('show');
}

function deleteCampusNetworks() {
	var campusNetworkId;
    var ids = $.map(table2.rows('.selected').data(), function (item) {
    	campusNetworkId=item[0];
    });
    deleteCampusNetworksbyId(campusNetworkId);
}


function deleteCampusNetworksbyId(campusNetworkId) {
    var url = "/campusnetwork/delete/"
    var csrftoken = getCookie('csrftoken');
    showLoader();
    $.ajax({
	    	beforeSend: function(xhr, settings) {
	            xhr.setRequestHeader("X-CSRFToken", csrftoken);
	    	},
            type: "POST",
            url: url,
            data: {
            	'campus_network_ids':campusNetworkId,
            	},
            success: function(data)
            {
            	hideLoader();
            	var message = "The selected "+ campus_network_i18n +" <b>- " + data.name + "</b> deleted successfully"
            	loadCampusNetworkDiv();
            	showNotification(1, message);
            },
            error: function(){
            	hideLoader();
            	var message="Error while deleting the selected " + campus_network_i18n + ".";
            	showNotification(4, message);
            }
    });
}
