""" ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** """
from django import forms
from django.core.validators import validate_slug
from django.forms import ModelForm
from ngcn.models import CampusType, CampusNetwork, Action
from django.forms import inlineformset_factory
import ngcn.views
import logging

logger=logging.getLogger(__name__)

class CampusTypeForm(forms.Form):
    app_zip_file = forms.FileField(label="Application Zip File",widget=forms.FileInput(attrs={'class': 'app_zip_file_upload_class','id':'app_zip_file_upload'}))

    def clean(self):
        if any(self.errors):
            return

        app_zip_file=self.cleaned_data['app_zip_file']

        if CampusType.objects.filter(app_zip_name=app_zip_file.name).count() > 0:
            self.add_error('app_zip_file', 'The given Application zip already exist')
            return

    # if ' '  in app_zip_file.name.strip():
    #     self.add_error('app_zip_file', 'Invalid file name. Please remove white space')

    #     if app_zip_file is None:
    #         self.add_error('app_zip_file', 'Please upload the valid zip file')
    #     if not app_zip_file.name.endswith('.zip'):
    #         self.add_error('app_zip_file', 'Please upload the valid zip file')

class EditCampusTypeForm(ModelForm):
    logger.debug("Entered EditCampusTypeForm")
    name =forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': "vTextField"}),
     )
    description =forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': "vTextField"}),
     )
    app_zip_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': "app_zip_upload"}),
    )
    class Meta:
        model = CampusType
        fields = ['name','description','app_zip_file']
        fields_required = ['name','description','app_zip_file']

    def clean(self):
        if any(self.errors):
            return
        app_zip_file=self.cleaned_data['app_zip_file']

        if app_zip_file is None:
            self.add_error('app_zip_file', 'Please upload the valid zip file')
            return
        if not app_zip_file.name.endswith('.zip'):
            self.add_error('app_zip_file', 'Please upload the proper zip file')
            return
        if CampusType.objects.filter(app_zip_name=app_zip_file.name).count() > 0:
            self.add_error('app_zip_file', 'The given Application zip already exist')
            return

class UploadFileForm(forms.Form):
    up_file = forms.FileField(label="Upload Spreadsheet File",widget=forms.FileInput(attrs={'class': 'file_upload_class','id':'file_upload'}))

class CampusNetworkForm(ModelForm):
    logger.debug("Entered CampusNetworkForm")

    name =forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': "vTextField"}),
        validators=[validate_slug]
     )
    description =forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': "vTextField"}),
     )
    host_file=forms.FileField()

    dynamic_ansible_workspace = forms.BooleanField(initial=True,required=False)

    class Meta:
        model = CampusNetwork
        fields = ['name','description','status', 'host_file', 'campus_type', 'dynamic_ansible_workspace']
        fields_required = ['name','description', 'campus_type']
        exclude = ('status',)


class EditCampusNetworkForm(ModelForm):

    name =forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': "vTextField"}),
        validators=[validate_slug]
     )
    description =forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': "vTextField"}),
     )
    host_file =forms.CharField(
        widget=forms.Textarea(),
     )

    dynamic_ansible_workspace = forms.BooleanField(required=False)

    class Meta:
        model = CampusNetwork
        fields = ['name','description','status', 'host_file', 'campus_type', 'dynamic_ansible_workspace']
        fields_required = ['name','description', 'campus_type']
        exclude = ('status',)

from django.forms import BaseInlineFormSet

class CustomInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(CustomInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

ActionFormSet = inlineformset_factory(CampusType,Action, fields=('action_name','jenkins_url','action_category'),extra=0, min_num=1, validate_min=True,formset=CustomInlineFormSet)
