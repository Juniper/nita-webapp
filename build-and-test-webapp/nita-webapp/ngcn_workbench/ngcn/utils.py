# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import configparser
import jenkins
import logging
import os
from time import sleep

from django.conf import settings

logger = logging.getLogger(__name__)


class ServerProperties:

    # Create your views here.
    config = configparser.ConfigParser()
    config_location = settings.BASE_DIR + "/../"
    config.read_file(open(config_location + "server_details.ini"))

    @staticmethod
    def getServerPort():
        jenkins_port = ServerProperties.config["jenkins.server.details"]["port"]
        return jenkins_port

    @staticmethod
    def getServerHost():
        return ServerProperties.config["jenkins.server.details"]["hostname"]

    @staticmethod
    def getWorkspaceLocation():
        return ServerProperties.config["project.details"]["path"]

    @staticmethod
    def getServerType():
        return ServerProperties.config["environment.details"]["build_type"]


def wait_and_get_build_status(action_url, build_number):
    buildStatus = None
    interval = 2
    try:
        for _i in range(0, 60):
            try:
                sleep(interval)
                buildStatus = getBuildStatus(action_url, build_number)
                if buildStatus is not None and buildStatus != "None":
                    break
            except Exception as e:
                logger.error(
                    "Error while getting build status of validate template directory"
                )
                logger.error(e)

        if buildStatus is not None:
            if buildStatus.lower() == "success":
                return True
    except Exception as e:
        logger.error("Error while triggering validate campus Type Template directory")
        logger.error(e)
    return False


def getBuildStatus(build_name, build_no):
    # Intentionally imported here rather than at module level.
    config = configparser.ConfigParser()
    config.read_file(open(settings.BASE_DIR + "/../server_details.ini"))
    jenkins_host_name = config["jenkins.server.details"]["hostname"]
    jenkins_port = config["jenkins.server.details"]["port"]
    JENKINS_SERVER_URL = "http://" + jenkins_host_name + ":" + str(jenkins_port)
    JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
    JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")
    SERVER = jenkins.Jenkins(
        JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS
    )
    buildStatus = None
    RESULT = "result"
    try:
        logger.debug("Jenkins server: " + JENKINS_SERVER_URL)
        buildStatus = SERVER.get_build_info(build_name, build_no)[RESULT]
        if buildStatus is not None and buildStatus != "None":
            logger.info(buildStatus)
    except Exception as e:
        logger.error(
            "StatusUpdater - getBuildStatus - Error while getBuildDuration - Build with build_name: "
            + build_name
            + "; build_no: "
            + str(build_no)
            + "; is on queue....."
        )
        logger.error(e)
    return buildStatus
