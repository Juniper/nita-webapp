/* ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** */
    $('#tree').bind(
        'tree.click',
        function(event) {
        	if(typeof($('#main-tabs-list .active').children()[0])!='undefined' && $('#main-tabs-list .active').children()[0].id == "configuration_header"){
        		if(isUnsavedData()) {
        				event.preventDefault();
        	 			$('#save-warning-modal').modal('show');
        	 			console.log(event);
        	 			$('#save-warning-confirm').click(function(event1){
        	 				if (this.id == 'save-warning-confirm') {
        	 					loadMainDiv(event.node);
        	                    $('#tree').tree('selectNode', event.node);
        	 			    }
        	 			});
        			}
        		else{
            			loadMainDiv(event.node);
        		}

        	}else {
    			loadMainDiv(event.node);
    		}

        }
     );


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

    function loadTreeData()
    {
	    var url = "/tree_data/"
	    var csrftoken = getCookie('csrftoken');
	    $.ajax({
	            beforeSend: function(xhr, settings) {
	                 xhr.setRequestHeader("X-CSRFToken", csrftoken);
	            },
	            type: "GET",
	            url: url,
	            success: function(data)
	            {
	                 $('#tree').tree('loadData', data);
	            },
	            error: function(){
	                 console.log('failure');
	            }
	    });
    }
