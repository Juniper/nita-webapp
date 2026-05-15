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


def add_job(job_name, file_name):
    xml_file = None
    try:
        server = jenkins.Jenkins(
            JENKINS_SERVER_URL,
            username=JENKINS_SERVER_USER,
            password=JENKINS_SERVER_PASS,
        )
        print("Jenkins server: " + JENKINS_SERVER_URL)
        xml_file = open(file_name, "r")
        xml = xml_file.read()
        xml_file.close()
        print("Job xml: " + xml)
        server.create_job(job_name, xml)
    except Exception as e:
        print("Error while adding job")
        print(e)
    finally:
        if xml_file is not None:
            xml_file.close()


add_job(sys.argv[3], sys.argv[4])
