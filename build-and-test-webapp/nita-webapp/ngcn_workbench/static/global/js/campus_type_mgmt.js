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
        $('#del_campus').prop('disabled', true)
	    $('#edit_campus').prop('disabled', true)

        $('#CampusType tr').on('click', function() {
		  if($(this).hasClass('selected'))
		  {
			 $(this).removeClass('selected');

    	  }
		  else
		  {
    	     $(this).addClass('selected').siblings().removeClass('selected');
    	  }

		  var count = 0
		  $.map(table.rows('.selected').data(), function (item) {
		    	count++
		    });

		  if(count == 0)
	      {
			  $('#del_campus').prop('disabled', true)
			  $('#edit_campus').prop('disabled', true)
	      }
		  else
		  {
			  $('#del_campus').prop('disabled', false)
			  $('#edit_campus').prop('disabled', false)
		  }
    	});

        setTimeout(
        		  function()
        		  {
        			  if ( campus_type_actions_table != null && typeof campus_type_actions_table != undefined ) {
        				  campus_type_actions_table.destroy();
        			  	}

        			  campus_type_actions_table = $('#Action').DataTable({
    					  "paging":   true,
    					  "ordering": false,
    					  "info":     false,
    					  "bFilter": false,
    					  "bInfo": false,
    					  "pageLength": 3,
    					  "bLengthChange": false,

    				  });

        			  if ( roles_table != null && typeof roles_table != undefined ) {
        				  roles_table.destroy();
        			  	}

        			  roles_table = $('#Roles').DataTable({
    					  "paging":   true,
    					  "ordering": false,
    					  "info":     false,
    					  "bFilter": false,
    					  "bInfo": false,
    					  "pageLength": 3,
    					  "bLengthChange": false,
    					  "aoColumnDefs": [{ "bVisible": false, "aTargets": [0] },{ "bVisible": false, "aTargets": [2] } ,{ "bVisible": false, "aTargets": [3] }
    					  ,{ "bVisible": false, "aTargets": [4] },{ "bVisible": false, "aTargets": [5] },{ "bVisible": false, "aTargets": [6] }]

    				  });

        			  if ( resources_table != null && typeof resources_table != undefined ) {
        				  resources_table.destroy();
        			  	}

        			  resources_table = $('#Resources').DataTable({
    					  "paging":   true,
    					  "ordering": false,
    					  "info":     false,
    					  "bFilter": false,
    					  "bInfo": false,
    					  "pageLength": 3,
    					  "bLengthChange": false,
    					  "aoColumnDefs": [{ "bVisible": false, "aTargets": [0] },{ "bVisible": false, "aTargets": [2] } ,{ "bVisible": false, "aTargets": [3] }
    					  ,{ "bVisible": false, "aTargets": [4] },{ "bVisible": false, "aTargets": [5] },{ "bVisible": false, "aTargets": [6] }]

    				  });

    				  if ( table != null && typeof table != undefined ) {
        				  table.destroy();
        			  	}

    				  table = $('#CampusType').DataTable({
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

        $('#campus-type-form').submit(function(event){
        	showLoader();
    		var formData = new FormData($(this)[0])
        		var url = $('#campus-type-form').attr('action')
        		var status_text1="added"
        		var status_text2="adding"
    			$("#error_content_div").css("display","none");
        	 //   if(this.action.indexOf("edit"))
        	   /* if(url.indexOf("edit") != -1)
        	    {
        	    	status_text1="changed"
                	status_text2="changing"
        	    }*/

       			var csrftoken = getCookie('csrftoken');
        	    $.ajax({
        	            beforeSend: function(xhr, settings) {
        	                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
        	            },
        	            type: "POST",
        	            url: url,
        	            data : formData,
        	            cache:false,
        	            enctype : "multipart/form-data",
        	            contentType: false,
        	            processData: false,
        	            context: this,
        	            success: function(data)
        	            {
        	            	if(data.result != null && typeof data.result != undefined && data.result=="success")
                	    	{
        	            		showNotification(1, campus_type_i18n + " " + status_text1 + " successfully");
                	    		$('#add-campus-type-modal').modal('hide');
                	    		hideLoader();
                	    		if($('#campus-type-form').data('load_summary')){
                	    			loadCampusTypeSummary($('#campus-type-form').data('campus_type_id'));
                	    		}
                	    		else{
                	    			loadCampusTypeDiv();
                	    			$('.modal-backdrop').hide();
                	    		}

                	    	}
        	            	else if(data.result=="failure")
                	    	{
                	    		hideLoader();
                	    		if(data.reason != null && typeof data.reason != undefined)
                	    		{
                	    			error_message = data.reason.replace(/\n/g, "<br />");
                	    			$('#error_content_div').html(error_message);
                	    			$("#error_content_div").css("display","unset");
                	    		}
                	    		else
                	    			showNotification(4, "Error while " + status_text2 + " " + campus_type_i18n + ".");
                	    	}
        	            	else
        	            	{
        	            		hideLoader();
        	            		$('#campus_type_forms_inner_div').html(data);
        	            	}
        	            },
        	            error: function(){
        	            		hideLoader();
        	            		showNotification(4, "Error while " + status_text2 + " " + campus_type_i18n);
        	            }
        	    });
        	    return false;
        });

});

function showLoader()
{
	$("#loading_overlay_backdrop").css("display","unset");
	$("#loading_overlay").css("display","unset");
}

function hideLoader()
{
	$("#loading_overlay_backdrop").css("display","none");
	$("#loading_overlay").css("display","none");
}

function loadCampusTypeDiv()
{
	loadTree();
	var node = $('#tree').tree('getNodeById', "campus_type");
    $('#tree').tree('selectNode', node);
	loadMainDiv(node);
	$('.modal-backdrop').hide();
}
function loadCampusTypeSummary(type_id)
{
	var node = $('#tree').tree('getNodeById', "campustype_"+type_id);
    $('#tree').tree('selectNode', node);
	loadMainDiv(node);
	$('.modal-backdrop').hide();
}

function addCampusType(save)
{
	 $('#campus-type-form').attr('action','/campustype/add/');
	 $("#error_content_div").css("display","none");
	 var url =  $('#campus-type-form').attr('action');
	    var csrftoken = getCookie('csrftoken');
	    $.ajax({
	            beforeSend: function(xhr, settings) {
	                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
	            },
	            type: "GET",
	            url: url,
	            success: function(data)
	            {
	            	    $("#campus_type_form").attr('action',url)
	            	    $("#add_campus_type_header").text("Add " + campus_type_i18n)
	                    $('#campus_type_forms_inner_div').html(data);
	                    $('#add-campus-type-modal').modal('show');
	            },
	            error: function(){
	                    console.log('failure');
	            }
	    });
}

/*
function editCampusTypebySelection(){
	var campusTypeId = "";
    var ids = $.map(table.rows('.selected').data(), function (item) {
    	campusTypeId =  item[0];
    });
    $('#campus_type_form').data('load_summary',false);
    editCampusType(campusTypeId);
}

function editCampusTypebyId(campusTypeId){
	console.log($('#campus_type_form'));
    $('#campus-type-form').data('load_summary',true);
    $('#campus-type-form').data('campus_type_id',campusTypeId);
    editCampusType(campusTypeId);
}

function editCampusType(campusTypeId)
{
	    $('#campus-type-form').attr('action','/campustype/'+campusTypeId+'/edit/');
	    var url =  $('#campus-type-form').attr('action');
	    var csrftoken = getCookie('csrftoken');
	    $.ajax({
	            beforeSend: function(xhr, settings) {
	                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
	            },
	            type: "GET",
	            url: url,
	            success: function(data)
	             {
	            	    $("#campus_type_form").attr('action',url)
	            	    $("#add_campus_type_header").text("Edit Campus Type")
	                    $('#campus_type_forms_inner_div').html(data);
	            	    $("#id_name").attr('disabled','disabled')
	                    $('#add-campus-type-modal').modal('show');
	            },
	            error: function(){
	                    console.log('failure');
	            }
	    });
}
*/
function deleteCampusType()
{
	$('#delete-campus-type-modal').modal('show');
}
function deleteCampusTypes(){
	var campusTypeId = [];
    var ids = $.map(table.rows('.selected').data(), function (item) {
    	campusTypeId=item[0];
    });
    deleteCampusTypesbyId(campusTypeId);
}
function deleteCampusTypesbyId(campusTypeId) {
    var url = "/campustype/delete/"
    var csrftoken = getCookie('csrftoken');
    showLoader();
    $.ajax({
	    	beforeSend: function(xhr, settings) {
	            xhr.setRequestHeader("X-CSRFToken", csrftoken);
	    	},
            type: "POST",
            url: url,
            data: {
            	'campus_type_ids':campusTypeId,
            	},
            success: function(data)
            {
            	var message;
            	hideLoader();
            	if(data["status"]=="success") {
            		message = "The selected" + campus_type_i18n+ " <b>- " + data.name + "</b> deleted successfully";
			showNotification(1, message);
            	}
            	else {
            		message = data["message"]
			showNotification(4, message);
            	}
            	loadCampusTypeDiv();
            },
            error: function(){
            	hideLoader();
            	var message="Error while deleting the selected " + campus_type_i18n + ".";
            	showNotification(4, message);
            }
    });
}
