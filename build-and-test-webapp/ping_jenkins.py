# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import jenkins
import sys

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = "http://" + jenkins_host_name + ":" + str(jenkins_port)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")

try:
    server = jenkins.Jenkins(
        JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS
    )
    print("Jenkins server: " + JENKINS_SERVER_URL)
    result = server.get_version()
    print(result)
except Exception as e:
    print("Error contacting jenkins")
    print(e)
    sys.exit(-1)

sys.exit(0)
