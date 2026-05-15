"""********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

********************************************************"""

from django.urls import path
from django.contrib.auth import logout
from django.shortcuts import redirect
from . import views


def logout_view(request):
    logout(request)
    return redirect("index")


urlpatterns = [
    path("", views.indexView, name="index"),
    path("tree_pane/", views.treeView, name="treepane"),
    path("tree_data/", views.getTreeData, name="treepanedata"),
    path("campustype/", views.campusTypeMgmtView, name="campustypemanagement"),
    path("campustype/add/", views.addCampusTypeView, name="campustypeadd"),
    path("campustype/delete/", views.deleteCampusTypeView, name="campustypedelete"),
    path("campustype/<int:campus_type_id>/", views.campusTypeView, name="campustype"),
    path("campusnetwork/", views.campusNetworkMgmtView, name="campusnetworkmanagement"),
    path("campusnetwork/add/", views.addCampusNetworkView, name="campusnetworkadd"),
    path("campusnetwork/delete/", views.deleteCampusNetworkView, name="campusnetworkdelete"),
    path("campusnetwork/<int:campus_network_id>/edit/", views.editCampusNetworkView, name="campusnetworkedit"),
    path("campusnetwork/<int:campus_network_id>/", views.campusNetworkView, name="campusnetwork"),
    path("campus_network/<int:campus_network_id>/upload_file/", views.uploadFileView, name="upload_file"),
    path("campus_network/<int:campus_network_id>/configuration_view/", views.configurationView, name="configuration_view"),
    path("campus_network/<int:campus_network_id>/summary/", views.campusNetworkSummaryView, name="summary"),
    path("campus_network/<int:campus_network_id>/action_history/", views.actionHistoryView, name="action_history"),
    path("campus_network/<int:campus_network_id>/action_history/<int:action_category_id>/", views.actionHistoryDetailView, name="action_history_category"),
    path("campus_network/<int:campus_network_id>/action_category/<int:action_category_id>/", views.actionsView, name="actions_view"),
    path("campus_network/<int:campus_network_id>/save_data/", views.saveGridDataView, name="save_data"),
    path("campus_network/<int:campus_network_id>/action/<int:action_id>/trigger_action/", views.triggerAction, name="trigger_action_view"),
    path("logout/", logout_view, name="logout"),
    path("action_history/<int:action_history_id>/", views.jenkinsConsoleView, name="jenkinsconsole"),
    path("action_history/<int:action_history_id>/console_log/", views.jenkinsConsoleLogView, name="jenkinsconsoleLog"),
    path("campus_network/<int:campus_network_id>/clear_data/", views.clearGridDataView, name="clear_data"),
    path("campus_network/<int:campus_network_id>/download_config_data/", views.downloadConfigDataView, name="download_config_data"),
    path("campus_network/<int:campus_network_id>/create_excel_data/", views.createExcelFileView, name="create_excel_config_data"),
]
