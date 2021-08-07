""" ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** """
from django.conf.urls import url
from django.contrib.auth import views as djangoview
from django.contrib.auth import logout
from django.shortcuts import redirect
from . import views

def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect('index')

urlpatterns = [

    url(r'^$', views.indexView, name='index'),
    url(r'^tree_pane/$', views.treeView, name='treepane'),
    url(r'^tree_data/$', views.getTreeData, name='treepanedata'),
    url(r'^campustype/$', views.campusTypeMgmtView, name='campustypemanagement'),
    url(r'^campustype/add/$', views.addCampusTypeView, name='campustypeadd'),
    url(r'^campustype/delete/$', views.deleteCampusTypeView, name='campustypedelete'),
    #url(r'^campustype/(?P<campus_type_id>[0-9]+)/edit/$', views.editCampusTypeView, name='campustypeedit'),
    url(r'^campustype/(?P<campus_type_id>[0-9]+)/$', views.campusTypeView, name='campustype'),
    url(r'^campusnetwork/$', views.campusNetworkMgmtView, name='campusnetworkmanagement'),
    url(r'^campusnetwork/add/$', views.addCampusNetworkView, name='campusnetworkadd'),
    url(r'^campusnetwork/delete/$', views.deleteCampusNetworkView, name='campusnetworkdelete'),
    url(r'^campusnetwork/(?P<campus_network_id>[0-9]+)/edit/$', views.editCampusNetworkView, name='campusnetworkedit'),
    url(r'^campusnetwork/(?P<campus_network_id>[0-9]+)/$', views.campusNetworkView, name='campusnetwork'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/upload_file/$',views.uploadFileView,name ='configuration_view'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/configuration_view/$',views.configurationView,name ='configuration_view'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/summary/$', views.campusNetworkSummaryView, name='summary'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/action_history/$', views.actionHistoryView, name='action_history'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/action_history/(?P<action_category_id>[0-9]+)/$', views.actionHistoryDetailView, name='action_history_category'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/action_category/(?P<action_category_id>[0-9]+)/$', views.actionsView, name='actions_view'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/save_data/$',views.saveGridDataView,name = 'save_data'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/action/(?P<action_id>[0-9]+)/trigger_action/$', views.triggerAction, name='trigger_action_view'),
    url(r'^logout/$',logout_view,name='logout'),
    url(r'^action_history/(?P<action_history_id>[0-9]+)/$',views.jenkinsConsoleView,name="jenkinsconsole"),
    url(r'^action_history/(?P<action_history_id>[0-9]+)/console_log/$',views.jenkinsConsoleLogView,name="jenkinsconsoleLog"),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/clear_data/$',views.clearGridDataView,name = 'clear_data'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/download_config_data/$',views.downloadConfigDataView,name = 'download_config_data'),
    url(r'^campus_network/(?P<campus_network_id>[0-9]+)/create_excel_data/$',views.createExcelFileView,name = 'create_excel_config_data'),
]
