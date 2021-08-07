""" ********************************************************

Project: nita-webapp

Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

******************************************************** """
import os
import jenkins
import string
import sys
from jenkinsapi.jenkins import Jenkins

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = 'http://' + jenkins_host_name + ':' + str(jenkins_port)
JENKINS_SERVER_USER=os.getenv('JENKINS_USER', "admin")
JENKINS_SERVER_PASS=os.getenv('JENKINS_PASS', "admin")

try:
    server = jenkins.Jenkins(JENKINS_SERVER_URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS)
    print ('Jenkins server: ' + JENKINS_SERVER_URL)
    result = server.get_version()
    print (result)
except Exception as e:
    print ("Error contacting jenkins")
    print (e)
    sys.exit(-1)

sys.exit(0)
