# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import urllib.request
import urllib.error
import base64

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = (
    "http://" + jenkins_host_name + ":" + str(jenkins_port) + "/jenkins"
)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")

try:
    credentials = base64.b64encode(
        f"{JENKINS_SERVER_USER}:{JENKINS_SERVER_PASS}".encode()
    ).decode()
    req = urllib.request.Request(
        JENKINS_SERVER_URL + "/api/json",
        headers={"Authorization": f"Basic {credentials}"},
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
