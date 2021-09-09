""" ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** """
import os
import yaml
import re
import jenkins
from django.db import transaction
from django.conf import settings
import json
# from pykwalify.core import Core
import logging
import traceback
import string
import configparser
import tempfile
import shutil

from ngcn.models import CampusType
from ngcn.models import Action
from ngcn.models import ActionCategory
from ngcn.models import Role
from ngcn.models import Resource
from ngcn.models import ActionProperty
#from ngcn.models import JenkinsJobProperty
from ngcn.utils import ServerProperties
from ngcn.utils import wait_and_get_build_status
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.core.files.storage import default_storage

from xml.dom.minidom import parseString
from zipfile import ZipFile
from jenkinsapi.jenkins import Jenkins

from MySQLdb import _mysql
#from _mysql import IntegrityError

logger=logging.getLogger(__name__)


config = configparser.ConfigParser()
config_location = settings.BASE_DIR+"/../"
config.read_file(open(config_location + 'server_details.ini'))
jenkins_host_name = config['jenkins.server.details']['hostname']
jenkins_port =config['jenkins.server.details']['port']
JENKINS_SERVER_URL = 'http://' + jenkins_host_name + ':' + str(jenkins_port)
JENKINS_SERVER_USER=os.getenv('JENKINS_USER', "admin")
JENKINS_SERVER_PASS=os.getenv('JENKINS_PASS', "admin")

class NetworkTypeParser:

    def parseProjectFile(self,file_name):
        result = ""
        zip_validation = self.validateZipFile(file_name)
        # update the filename based on normalization in the validation step
        file_name = zip_validation['filename']
        zip_file = None
        logger.debug('zip_validation ' + str(zip_validation['status']))
        if zip_validation['status']:
            try:
                zip_file = ZipFile(default_storage.path(file_name),'r')
                app_name = re.sub('\.zip$','',file_name)
                project_yaml_file = zip_file.read(app_name + '/project.yaml').decode('utf-8')
                logger.debug(project_yaml_file)
                project_file_dict = yaml.load(project_yaml_file)
                logger.debug("YAML Parsed Successfully")
                zip_file.close()
                validation_error = self.validateProjectYaml(project_yaml_file)
                if validation_error != None:
                    return JsonResponse({'result':'failure', 'reason':validation_error})

                job_name = 'network_type_validator'
                server = jenkins.Jenkins(JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS)
                logger.debug('Jenkins server: ' + JENKINS_SERVER_URL)
                tree = parseString(server.get_job_config(job_name))
                logger.debug('Job xml: ' + tree.toxml())
                tree.getElementsByTagName("customWorkspace")[0].firstChild.replaceWholeText(ServerProperties.getWorkspaceLocation())
                server.reconfig_job(job_name, tree.toxml())
                current_build_number = server.get_job_info(job_name)['nextBuildNumber']
                logger.debug("Current build number is: "+ str(current_build_number))
                with open(default_storage.path(file_name),'rb') as app_zip_file:
                    jenkins_job=Jenkins(JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS).get_job(job_name)
                    jenkins_job.invoke(build_params={'file_name':file_name, 'operation':'add'}, files={'app.zip':app_zip_file}, block=True)
                logger.debug("Invoked Jenkins Job to add zip file")
                if wait_and_get_build_status(job_name,current_build_number) :
                    db_status = self.updateNetworkTypeDetailsOnDB(project_yaml_file,file_name)
                    logger.debug('db_status server: ' + str(db_status))
                    if db_status:
                        result = JsonResponse({'result':'success'})
                    else:
                        result = JsonResponse({'result':'failure'})
                    logger.debug("Updated network type details: " + str(result))
                else:
                    output = server.get_build_console_output(job_name, current_build_number)
                    logger.debug('Jenkins get_build_console_output: ' + output)
                    validation_error = output.partition('|--|')[-1].rpartition('|--|')[0]
                    logger.error(validation_error)
                    result = JsonResponse({'result':'failure', 'reason':validation_error})
                    logger.debug("Got build console output! " + str(result))
            except Exception as e:
                logger.error("Error while adding Campus Type")
                logger.error(traceback.format_exc())
                logger.error(e)
                result = JsonResponse({'result':'failure', 'reason':validation_error})
            finally:
                if zip_file is not None:
                    zip_file.close()
        else:
            result = JsonResponse({'result':'failure', 'reason':zip_validation['message']})

        logger.info(result)
        return result

    def normalizeZipFile(self, filename):

        # inner function to find project file
        def find_file(top, filename):
            for root, dirs, files in os.walk(top):
                for file in files:
                    logger.debug("find_file: " + file)
                    if file.endswith(filename):
                        return root + "/" + file

        tmp = tempfile.mkdtemp()

        os.mkdir(tmp + "/tmp1")
        zf = ZipFile(filename)
        zf.extractall(tmp + "/tmp1")
        zf.close()

        projectfilename = find_file(tmp + "/tmp1/","project.yaml")
        logger.debug("projectfilename = find_file('" + tmp + "/tmp1','project.yaml')")
        logger.debug("projectfilename = " + projectfilename)
        if projectfilename == None:
            msg = "Can't find project.yaml file in: " + filename
            logger.error(msg)
            # bomb out of this by returning the original filename because there are checks
            # later that will pick up project.yaml problems
            return filename

        try:
            logger.debug("open(" + projectfilename + ")")
            projectfile = open(projectfilename)
            projectdata = yaml.load(projectfile)
            projectfile.close()
            projectname = projectdata['name']
        except Exception as e:
            msg = "Can't read project name from project.yaml file in: " + filename + "(" + e + ")"
            logger.error(msg)
            # bomb out of this by returning the original filename because there are checks
            # later that will pick up project.yaml problems
            return filename

        projectbase = os.path.basename(os.path.dirname(projectfilename))
        logger.debug("projectbase = " + projectbase)

        os.mkdir(tmp + "/tmp2")
        if projectbase == "tmp1":
            os.replace(tmp + "/tmp1", tmp + "/tmp2/" + projectname)
            logger.debug("os.replace(" + "/tmp1", tmp + "/tmp2/" + projectname + ")")
        else:
            os.replace(tmp + "/tmp1/" + projectbase, tmp + "/tmp2/" + projectname)
            logger.debug("os.replace(" + tmp + "/tmp1/" + projectbase, tmp + "/tmp2/" + projectname + ")")

        # put the new zipfile in the default storage location
        zf = ZipFile(default_storage.path(projectname + ".zip"), 'w')
        for root, dirs, files in os.walk(tmp + "/tmp2/" + projectname):
            for file in files:
                zf.write(os.path.join(root, file), os.path.join(root, file).replace(tmp + "/tmp2/", ""))
        zf.close()

        # remove the file if it doesn't match the original name
        if filename != default_storage.path(projectname + ".zip"):
            os.remove(filename)
        # cleanup the tmp dir
        shutil.rmtree(tmp, True)

        return projectname + ".zip"

    def validateZipFile(self,file_name):
        list_of_files = ['project.yaml', 'ansible.cfg']
        zip_file = None
        result={}
        result["status"]=True
        try:
            file_name = self.normalizeZipFile(default_storage.path(file_name))
            zip_file = ZipFile(default_storage.path(file_name), 'r')
            logger.error("Unzipping zipfile to: " + default_storage.path(file_name))
            app_name = re.sub('\.zip$','',file_name)
            logger.debug(app_name)
            archive_member_list = zip_file.namelist()
            logger.debug(archive_member_list)
            if (archive_member_list[0].find(app_name+'/') != 0) and (app_name not in archive_member_list):
                result['message']= "Zip file name and the project directory name should be same"
                result['status']=False
                logger.error(result)
                return result
            if app_name+'/project.yaml' not in archive_member_list:
                result['message']= "Cannot find the project.yaml file in the zip"
                result['status']=False
                logger.error(result)
                return result
            no_member_list = []
            for member in list_of_files:
                if app_name+"/"+member not in archive_member_list:
                    no_member_list.append(member);
                    result["status"] = False
                    result["message"]= member +" is not present in the project directory"
                    logger.error(result)
                    return result
            result['message']= "Uploaded file is valid zip file"
            # the normalization can change the file name
            result['filename'] = file_name
            logger.debug(result)
        except Exception as e:
            logger.error(e)
            result['message'] = "Undefined exception occured"
            result['status'] = False
            return result
        finally:
            if zip_file is not None:
                zip_file.close()
        logger.info(result)
        return result

    def validateProjectYaml(self,project_file):
        error_string=None
        campus_type_locale=_('network_type_heading')
        project_file_dict = yaml.load(project_file)
        try:
            campus_type_name=project_file_dict['name']
            if not campus_type_name or campus_type_name.isspace():
                error_string="Invalid Campus Type name. Campus Type name must be empty"
                return error_string
            campus_type_name=campus_type_name.strip()

            if CampusType.objects.filter(name=campus_type_name).count() > 0:
                error_string= campus_type_locale +" with the name - " + campus_type_name + " already exists."
                return error_string

            if not project_file_dict['action']:
                error_string="Invalid project.yaml file. Actions must not be must be empty"
                return error_string

            for action in project_file_dict['action']:
                action_name=action['name']
                category_name=action['category']
                jenkins_url=action['jenkins_url']
                shell_command=action['configuration']['shell_command']

                if not action_name or action_name.isspace():
                    error_string="Invalid Action name. Action name must be empty"
                    return error_string
                action_name=action_name.strip()

                if not category_name or category_name.isspace():
                    error_string="Invalid category. Action category must be empty"
                    return error_string
                category_name=category_name.strip()

                if ActionCategory.objects.filter(category_name=category_name).count() == 0:
                    error_string="Invalid Action category name - " + category_name
                    return error_string

                if not jenkins_url or jenkins_url.isspace():
                    error_string="Invalid Action jenkins_url. The jenkins_url must not be empty."
                    return error_string
                jenkins_url=jenkins_url.strip()

                if not shell_command or shell_command.isspace():
                    error_string="Invalid shell command. The shell command must not be empty."
                    return error_string
                shell_command=shell_command.strip()

                if category_name == 'TEST':
                    output_path=action['configuration']['output_path']

                    if not output_path or output_path.isspace():
                        error_string="Invalid output path. The output path must not be empty for the TEST jobs."
                        return error_string
                    output_path=output_path.strip()

            #if not project_file_dict['roles_and_resources']:
            #   error_string="The roles and resources must not be empty."
            #   return error_string

            #if not project_file_dict['roles_and_resources']['roles']:
            #    error_string="The roles must not be empty."
            #    return error_string

            #if not project_file_dict['roles_and_resources']['resources']:
            #    error_string="The resources must not be empty."
            #    return error_string

        except IntegrityError:
            error_string="Invalid project.yaml file"
            return error_string
        return error_string

    @transaction.atomic
    def updateNetworkTypeDetailsOnDB(self,project_file,app_zip_name_param):

        try:
            with transaction.atomic():
                logger.info(project_file)
                project_file_dict = yaml.load(project_file)
                logger.info(project_file_dict)
                campus_type = CampusType(
                                            name=project_file_dict['name'].strip(),
                                            description=project_file_dict['description'].strip(),
                                            app_zip_name=app_zip_name_param.strip()
                                        )
                campus_type.save()

                #for role_name in project_file_dict['roles_and_resources']['roles']:
                #    try:
                #        role = Role.objects.get(name=role_name.strip())
                #    except:
                #        role= Role(name=role_name.strip())
                #        role.save()
                #
                #campus_type.roles.add(role)

                #for resource_name in project_file_dict['roles_and_resources']['resources']:
                #   try:
                #       resource = Resource.objects.get(name=resource_name.strip())
                #   except:
                #       resource = Resource(name=resource_name.strip())
                #       resource.save()
                #campus_type.resources.add(resource)

                for action in project_file_dict['action']:
                    action_category = ActionCategory.objects.get(category_name=action['category'].strip().upper())
                    if action['category'].strip().upper() == 'TEST':
                        output_path_val=action['configuration']['output_path'].strip()
                    else:
                        output_path_val=None

                    custom_workspace_val=""
                    if 'custom_workspace' in action['configuration'].keys() and not action['configuration']['custom_workspace'].isspace():
                        custom_workspace_val=action['configuration']['custom_workspace']

                    action_property=ActionProperty(
                                                shell_command=action['configuration']['shell_command'].strip(),
                                                output_path=output_path_val,
                                                custom_workspace=custom_workspace_val
                                            )
                    action_property.save()

                    action = Action(
                                action_name=action['name'].strip(),
                                jenkins_url=action['jenkins_url'].strip(),
                                campus_type_id=campus_type,
                                action_property=action_property,
                                action_category=action_category,
                            )
                    action.save()
        except Exception as e:
            logger.error("Error while adding the project.yaml entries in the database")
            logger.error(e)
            logger.error(traceback.print_exc())
            logger.error(traceback.format_exc())
            return False
        return True
