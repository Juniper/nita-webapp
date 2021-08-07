""" ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** """
import os
import configparser
from django.conf import settings
from time import sleep
import jenkins
import logging

logger=logging.getLogger(__name__)

config = configparser.ConfigParser()
config_location = settings.BASE_DIR+"/../"
config.read_file(open(config_location + 'server_details.ini'))
jenkins_host_name = config['jenkins.server.details']['hostname']
jenkins_port =config['jenkins.server.details']['port']
JENKINS_SERVER_URL = 'http://' + jenkins_host_name + ':' + str(jenkins_port)
JENKINS_SERVER_USER=os.getenv('JENKINS_USER', "admin")
JENKINS_SERVER_PASS=os.getenv('JENKINS_PASS', "admin")

class ServerProperties:

    # Create your views here.
    config = configparser.ConfigParser()
    config_location = settings.BASE_DIR + "/../"
    config.read_file(open(config_location + 'server_details.ini'))

    @staticmethod
    def getServerPort():
        jenkins_port = ServerProperties.config['jenkins.server.details']['port']
        return jenkins_port

    @staticmethod
    def getServerHost():
        return ServerProperties.config['jenkins.server.details']['hostname']

    @staticmethod
    def getWorkspaceLocation():
        return ServerProperties.config['project.details']['path']

    @staticmethod
    def getServerType():
        return ServerProperties.config['environment.details']['build_type']

def wait_and_get_build_status(action_url,build_number):
    buildStatus=None
    interval=2
    try:
        for i in range(0, 60):
            try:
                sleep(interval)
                buildStatus=getBuildStatus(action_url, build_number)
                if buildStatus != None and buildStatus != 'None':
                    break
            except Exception as e:
                logger.error("Error while getting build status of validate template directory")
                logger.error(e)

        if buildStatus != None:
            if buildStatus.lower() == "success":
                return True
    except Exception as e:
        logger.error("Error while triggering validate campus Type Template directory")
        logger.error(e)
    return False


def getBuildStatus(build_name, build_no):
    SERVER = jenkins.Jenkins(JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS)
    buildStatus = None
    RESULT="result"
    try:
        logger.debug('Jenkins server: ' + JENKINS_SERVER_URL)
        buildStatus = SERVER.get_build_info(build_name, build_no)[RESULT]
        if buildStatus != None and buildStatus != 'None':
            logger.info(buildStatus)
    except Exception as e:
        logger.error("StatusUpdater - getBuildStatus - Error while getBuildDuration - Build with build_name: " + build_name + "; build_no: " + str(build_no) + "; is on queue.....")
        logger.error(e)
    return buildStatus
