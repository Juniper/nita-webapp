# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import urllib.request
import urllib.error

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = (
    "http://" + jenkins_host_name + ":" + str(jenkins_port) + "/jenkins"
)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")

try:
    req = urllib.request.Request(
        JENKINS_SERVER_URL + "/api/json",
        headers={"X-Forwarded-User": JENKINS_SERVER_USER},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        version = resp.headers.get("X-Jenkins", "unknown")
    print("Jenkins server: " + JENKINS_SERVER_URL)
    print(version)
except Exception as e:
    print("Error contacting jenkins")
    print(e)
    sys.exit(-1)

sys.exit(0)
