""" ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** """
import django_tables2 as tables
from ngcn.models import *
from django.conf import settings
from django.utils.translation import gettext as _
import configparser
from django.utils.safestring import mark_safe

config = configparser.ConfigParser()
config_location=settings.BASE_DIR+"/../"
config.read_file(open(config_location + 'server_details.ini'))
jenkins_host_name = config['jenkins.server.details']['hostname']
jenkins_port =config['jenkins.server.details']['port']
jenkins_server_url = 'http://'+jenkins_host_name+':'+str(jenkins_port)


class CampusTypeTable(tables.Table):
        id = tables.Column(verbose_name="Id")
        name = tables.Column(verbose_name=_('network_type_heading') + " Name")
        description  = tables.Column(verbose_name="Description")
        app_zip_name  = tables.Column(verbose_name="Application Zip ")
        class Meta:
                model = CampusType
                attrs = {"class": "table table-condensed table-hover table-bordered","id":"CampusType"}
                row_attrs = {"class":"select-row",'data-id': lambda record: record.id}
                orderable = False
                exclude = ('app_zip_name',)

class CampusNetworkTable(tables.Table):
        id = tables.Column(verbose_name="Id")
        name = tables.Column(verbose_name=_('network_heading') + " Name")
        description  = tables.Column(verbose_name="Description")
        status  = tables.Column(verbose_name="Status")
        campus_type = tables.Column(verbose_name="Network Type" ,accessor='campus_type.name')
        class Meta:
                model = CampusNetwork
                attrs = {"class": "table table-condensed table-hover table-bordered","id":"CampusNetwork"}
                orderable = False
                exclude = ('host_file',)

class ActionHistoryTable(tables.Table):
        #id = tables.CheckBoxColumn(accessor='pk')
        action_id = tables.Column(verbose_name="Name",accessor='action_id.action_name')
        #description  = tables.Column(verbose_name="Description")
        timestamp = tables.Column(verbose_name="Timestamp")
        status = tables.Column(verbose_name="Status")
        jenkins_job_build_no  = tables.Column(verbose_name="Jenkins Job Id")
        class Meta:
                model = ActionHistory
                attrs = {"class": "table table-condensed table-bordered","id":"action-history-table",'width':'98%'}
                row_attrs = {"class":"select-row",'data-id': lambda record: record.id}
                orderable = False
                exclude = ('id','category_id','campus_network_id')

class AllActionHistoryTable(tables.Table):
        #id = tables.CheckBoxColumn(accessor='pk')
        action_id = tables.Column(verbose_name="Name")
        category_name = tables.Column(accessor='category_id.category_name')
#        description  = tables.Column(verbose_name="Description")
        timestamp = tables.Column(verbose_name="Timestamp")
        status = tables.Column(verbose_name="Status")
        jenkins_job_build_no  = tables.TemplateColumn('<a href="'+jenkins_server_url+'/job/{{record.action_id.jenkins_url}}/{{record.jenkins_job_build_no}}/console" target="_blank" ">{{record.jenkins_job_build_no}}</a>')
        class Meta:
                model = ActionHistory
                attrs = {"class": "table table-condensed table-bordered","id":"all-action-history-table",'width':'98%'}
                orderable = False
                exclude = ('id','category_id','campus_network_id')
                sequence = ('action_id','category_name','timestamp','status','jenkins_job_build_no')

class ActionListTable(tables.Table):
        #id = tables.CheckBoxColumn(accessor='pk')
        id = tables.Column(verbose_name="Id")
        action_name = tables.Column(verbose_name="Name")
        action_category = tables.Column(verbose_name='Category',accessor='action_category.category_name')
        jenkins_url = tables.Column(verbose_name='Jenkins Url')
        action_property = tables.Column(verbose_name='Shell Command')
        class Meta:
                model = Action
                attrs = {"class":"table table-condensed table-bordered", "id":"Action"}
                orderable= False
                exclude = ('id','campus_type_id', 'action_property')

class CampusNetworkActionListTable(tables.Table):
        #id = tables.CheckBoxColumn(accessor='pk')
        network_name=None
        def __init__(self, *args, **kwargs):
                self.network_name=args[1]
                super(tables.Table, self).__init__(*args, **kwargs)

        id = tables.Column(verbose_name="Id")
        action_name = tables.Column(verbose_name="Name")
        action_category = tables.Column(verbose_name='Category',accessor='action_category.category_name')
        jenkins_url = tables.Column(verbose_name='Jenkins Url')

        def render_jenkins_url(self, value, record):
                return mark_safe(value+"-"+self.network_name)
        class Meta:
                model = Action
                attrs = {"class":"table table-condensed table-bordered", "id":"Action"}
                orderable= False
                exclude = ('campus_type_id', 'action_property')

class RolesTable(tables.Table):
        id = tables.Column(verbose_name="Id")
        name = tables.Column(verbose_name="Roles")
        class Meta:
                model = CampusNetwork
                attrs = {"class": "table table-condensed table-bordered","id":"Roles"}
                orderable = False
                exclude = ('id', 'status')

class ResourcesTable(tables.Table):
        name = tables.Column(verbose_name="Resources")
        class Meta:
                model = CampusNetwork
                attrs = {"class": "table table-condensed table-bordered","id":"Resources"}
                orderable = False
