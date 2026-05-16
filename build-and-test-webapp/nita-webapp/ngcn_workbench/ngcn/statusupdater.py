# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import configparser
import jenkins
import logging
import os
import threading
import time
import traceback

from django.conf import settings

from ngcn.models import ActionHistory

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config_location = settings.BASE_DIR + "/../"
config.read_file(open(config_location + "server_details.ini"))
jenkins_host_name = config["jenkins.server.details"]["hostname"]
jenkins_port = config["jenkins.server.details"]["port"]
JENKINS_SERVER_URL = "http://" + jenkins_host_name + ":" + str(jenkins_port)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")


class StatusUpdater:

    SERVER = None
    interval = 30
    RUN_SERVICE = True
    SERVICE_STATUS = False

    @staticmethod
    def isServiceRunning():
        return StatusUpdater.SERVICE_STATUS

    @staticmethod
    def getInstance():
        return StatusUpdater()

    def getBuildStatus(self, build_name, build_no):
        if self.SERVER is None:
            StatusUpdater.SERVER = jenkins.Jenkins(
                JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS
            )
        buildStatus = None
        RESULT = "result"
        try:
            buildStatus = self.SERVER.get_build_info(build_name, build_no)[RESULT]
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
            logger.error(traceback.print_exc())
            logger.error(traceback.format_exc())
        return buildStatus

    def updateBuildStatusOnDB(self, action_history_id, buildStatus):
        historyObj = ActionHistory.objects.get(pk=action_history_id)
        historyObj.status = buildStatus.title()
        historyObj.save()

    def updateAllRunningJobs(self):
        RUNNING = "Running"
        # print ":::::::updateAllRunningJobs Fetching all the running jobs "
        queryset = ActionHistory.objects.filter(status=RUNNING)

        for actionHistory in queryset:
            action = actionHistory.action_id
            build_name = action.jenkins_url
            build_no = actionHistory.jenkins_job_build_no
            campus_network = actionHistory.campus_network_id
            build_status = self.getBuildStatus(
                build_name + "-" + campus_network.name, build_no
            )
            # print ":::::::updateAllRunningJobs getting build status for: " + str(actionHistory.id) + "---" +build_status
            if build_status is not None:
                self.updateBuildStatusOnDB(actionHistory.id, build_status)
                logger.debug(
                    ":::::::updateAllRunningJobs updated build status on DB: "
                    + str(actionHistory.id)
                    + "---"
                    + build_status
                )

    def statusUpdaterTimerService(self):

        while self.RUN_SERVICE:
            self.updateAllRunningJobs()
            # print ":::::::statusUpdaterTimerService sleeping for - " + str(self.interval)
            time.sleep(self.interval)
        logger.info(":::::::statusUpdaterTimerService Service Interrupted..")

    def startStatusUpdaterService(self):
        try:
            if not StatusUpdater.isServiceRunning():
                s_thread = threading.Thread(
                    name="StatusUpdaterThread", target=self.statusUpdaterTimerService
                )
                s_thread.setDaemon(True)
                StatusUpdater.SERVICE_STATUS = True
                s_thread.start()
                logger.info(":::::::::::::Timer service started")
        except Exception as e:
            logger.error("Error while starting startStatusUpdaterTimerService")
            logger.error(e)
            logger.error(traceback.print_exc())
            logger.error(traceback.format_exc())
