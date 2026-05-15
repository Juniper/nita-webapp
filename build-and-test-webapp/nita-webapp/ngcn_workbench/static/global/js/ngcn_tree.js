// Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
    $('#tree').bind(
        'tree.click',
        function(event) {
            if(typeof($('#main-tabs-list .active').children()[0])!='undefined' && $('#main-tabs-list .active').children()[0].id == "configuration-header"){
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
