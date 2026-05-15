# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import base64

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = "http://" + jenkins_host_name + ":" + str(jenkins_port)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")


def _auth_header() -> str:
    credentials = base64.b64encode(
        f"{JENKINS_SERVER_USER}:{JENKINS_SERVER_PASS}".encode()
    ).decode()
    return f"Basic {credentials}"


def add_job(job_name, file_name):
    with open(file_name, "r") as f:
        xml = f.read()
    try:
        print("Jenkins server: " + JENKINS_SERVER_URL)
        print("Job xml: " + xml)
        url = f"{JENKINS_SERVER_URL}/createItem?name={urllib.parse.quote(job_name)}"
        data = xml.encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": _auth_header(),
                "Content-Type": "text/xml; charset=utf-8",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"Job '{job_name}' created: HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            # Job already exists — treat as success
            print(f"Job '{job_name}' already exists (HTTP 400), skipping.")
        else:
            print(f"Error while adding job: HTTP {e.code} {e.reason}")
    except Exception as e:
        print("Error while adding job")
        print(e)


add_job(sys.argv[3], sys.argv[4])
