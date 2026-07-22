# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Jenkins server configuration and connection helpers.

Holds the Jenkins connection constants (read from ``server_details.ini`` and the
environment) and the factory for a ``jenkins.Jenkins`` client. Extracted from the
legacy ``ngcn.views`` module so the API layer and ``jenkins_jobs`` no longer
depend on the server-rendered UI code.
"""

import configparser
import os

import jenkins
from django.conf import settings

config = configparser.ConfigParser()
config_location = settings.BASE_DIR + "/../"
config.read_file(open(config_location + "server_details.ini"))
jenkins_host_name = config["jenkins.server.details"]["hostname"]
jenkins_port = config["jenkins.server.details"]["port"]
JENKINS_SERVER_URL = "http://" + jenkins_host_name + ":" + str(jenkins_port) + "/jenkins"
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")


def _make_jenkins_server():
    """Return a new jenkins.Jenkins connection."""
    return jenkins.Jenkins(
        JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS
    )
