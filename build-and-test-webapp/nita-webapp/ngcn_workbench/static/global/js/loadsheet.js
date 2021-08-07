/* ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** */
function createGrid(workbook) {
	//var workbook = JSON.parse(jsondata["workbook"]);
	var tabs_div = '<div class="wrapper"><ul id="tabs-list" class="nav nav-tabs list"></ul></div><div id="wb-tabs" class="tab-content"></div>';
	$("#wb-tabs").remove();
	$(".scrtabs-tab-container").remove();
	//$("#scrtabs-tab-container").remove();
	$('#grid').append(tabs_div);
	var browser_width = $(window).width();
	var grid_width = browser_width - (browser_width*.19);
	//create tabs based on the sheet names
	workbook.forEach(
	function(sheet){
		var tab_id = sheet.name.replace("+","_") ;
		var tab_list = '<li><a id="' + tab_id +'_header" data-toggle="tab" data-target="#'+tab_id+'">'+sheet.name+'</a></li>';
		var tab_div = '<div id="'+tab_id+'" class="tab-pane" style="width:100%">'+
	                        '<div id="'+tab_id+'data" style="width:' + grid_width +'px;height:' + $("#pane_container").height()*.81 +'px; border-top:1px solid #ccc;">'+sheet.name+'</div>'+
		               '</div>';
    	$('#tabs-list').append(tab_list);
		$("#wb-tabs").append(tab_div);
  	});

	$(function() {
		$("#"+$("#grid").find(".tab-pane")[0].id).addClass("active")
		$( "#wb-tabs" ).tab('show');
	});

	//Add the Grid in to the tab

	workbook.forEach(function(sheet){
		var grid;
  		var options = {
			editable: true,
			asyncEditorLoading: false,
			autoEdit: false,
    		enableAddRow: false,
			enableCellNavigation: true,
			enableColumnReorder: false,
			autoHeight: false,
			leaveSpaceForNewRows: true,
  		};
		sheet["columns"].forEach(function(column){
			column["editor"] = Slick.Editors.LongText
		});
		var data = sheet[sheet.name];
		var div_id = '#'+sheet.name+"data" ;
		div_id = div_id.replace("+", "_");
		 $(function () {
		grid = new Slick.Grid(div_id, data, sheet["columns"], options);
		grid.autosizeColumns();
		grid.setSelectionModel(new Slick.CellSelectionModel());
		grid.registerPlugin( new Slick.AutoTooltips({ enableForCells: true,enableForHeaderCells:true }) );
		$(div_id).data("gridInstance", grid);
		$(div_id).data("name",sheet.name)
		})
  	});

}
$('#grid').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
   id  = e.target.getAttribute("data-target")+"data";
   var grid = $(id).data("gridInstance");
   if (typeof grid != 'undefined') {
	   grid.resizeCanvas();
   }
});

function isUnsavedData() {
	unsaveddata = false;
	grid_list = $('[class^="slickgrid_"]').get();
	grid_list.forEach(function(grid){
		if($(grid).find('.highlighted').get().length > 0){
			return unsaveddata=true;

		}
	});
	return unsaveddata
}
