/* ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** */
   iframeTimer = null;
   table=null;
   table2=null;
   campus_network_table=null;
   campus_network_summary_table=null;
   network_action_history_table=null;
   global_action_history_table=null;
   campus_type_actions_table=null;
   roles_table=null;
   resources_table=null;

   function getCookie(name) {
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
		    var cookies = document.cookie.split(';');
		    for (var i = 0; i < cookies.length; i++) {
			    var cookie = jQuery.trim(cookies[i]);
			    // Does this cookie string begin with the name we want?
			    if (cookie.substring(0, name.length + 1) == (name + '=')) {
				    cookieValue = decodeURIComponent(cookie
						    .substring(name.length + 1));
				    break;
			    }
		    }
	    }
	    return cookieValue;
    }

    //setting the left_pane and right_pane height
    $('#body').ready(function(){
    	window_height = $(window).height();
    	window_width = $(window).width();
        adjustHeight()
        loadTree()
        var node = {};
        node.id="campus_type"
        loadMainDiv(node);
    });

    function adjustHeight() {
        var navbar_height = 40;
        var buffer_height = 5;
        var pane_height = window_height-(navbar_height+buffer_height);

        $("#pane_container").css("height", pane_height+"px");
    }

    $(window).resize(function() {
      adjustHeight()
    });

    //	loads the tree component when this page loads
    function loadTree()
    {
	    var url = "/tree_pane"
	    var csrftoken = getCookie('csrftoken');
	    $.ajax({
	            beforeSend: function(xhr, settings) {
	                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
	            },
	            type: "GET",
	            url: url,
	            success: function(data)
	             {
	                    $('#left_tree_pane').html(data);

	                    var node = $('#tree').tree('getNodeById', "campus_type");
	                    $('#tree').tree('selectNode', node);
	            },
	            error: function(){
	                    console.log('failure');
	            }
	    });
    }

    function loadMainDiv(node) {
        var url = ""
        if(node.id == "campus_type")
        {
            url = "campustype/"
        }
        else if(node.id == "campus_network")
        {
            url = "campusnetwork/"
        }
        else
        {
            urls = node.id.split('_');
            url = urls[0] + '/' + urls[1] + "/"
        }

        var csrftoken = getCookie('csrftoken');
        $.ajax({
                beforeSend: function(xhr, settings) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                },
                type: "GET",
                url: url,
                success: function(data)
                 {
                        $('#main_pane').html(data);
                },
                error: function(){
                        console.log('failure');
                }
        });

    }

