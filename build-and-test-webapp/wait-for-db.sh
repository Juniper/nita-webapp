#!/bin/bash

# ********************************************************
#
# Project: nita-webapp
#
# Copyright (c) Juniper Networks, Inc., 2021. All rights reserved.
#
# Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html
#
# SPDX-License-Identifier: Apache-2.0
#
# Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.
#
# ********************************************************

echo ""
echo "##############################################"
echo ""
echo "        Cheking for non default credentials"
echo ""
echo "##############################################"
if [ -z "$WEBAPP_USER" ]
then
      echo "Using default username for Webapp"
      export WEBAPP_USER=vagrant
else
      echo "Using custom username for Webapp"
fi
if [ -z "$WEBAPP_PASS" ]
then
      echo "Using default password for Webapp"
      export WEBAPP_PASS=vagrant123
else
      echo "Using custom password for Webapp"
fi
if [ -z "$JENKINS_USER" ]
then
      echo "Using default username for Jenkins connection"
      export JENKINS_USER=admin
else
      echo "Using custom username for Jenkins connection"
fi
if [ -z "$JENKINS_PASS" ]
then
      echo "Using default password for Jenkins connection"
      export JENKINS_PASS=admin
else
      echo "Using custom password for Jenkins connection"
fi

echo ""
echo "##############################################"
echo ""
echo "        Connecting to DB"
echo ""
echo "##############################################"

while ! mysqladmin ping -hdb -u"root" -p"root" --silent; do
   echo "Waiting for db..."
   sleep 2
done

echo ""
echo "##############################################"
echo ""
echo "        Django makemigrations"
echo ""
echo "##############################################"

python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py makemigrations --check
# python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py makemigrations ngcn --check

echo ""
echo "##############################################"
echo ""
echo "        Django migrate "
echo ""
echo "##############################################"

python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py migrate
# python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py migrate ngcn
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py loaddata campus_detail_data

echo ""
echo "##############################################"
echo ""
echo "        Django Superuser: "
echo "        ${WEBAPP_USER}/${WEBAPP_PASS}"
echo ""
echo "##############################################"

echo "Checking default superuser on Django application..."
if python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py shell -c \
    "from django.contrib.auth.models import User; \
    print(User.objects.filter(username='${WEBAPP_USER}').exists())" \
    | grep -qi true; then
    echo "Superuser was already created"
    python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py shell -c \
"from django.contrib.auth.models import User; usr = User.objects.get(username='${WEBAPP_USER}'); usr.set_password('${WEBAPP_PASS}'); usr.save()"
else
    python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py shell -c \
"from django.contrib.auth.models import User; User.objects.create_superuser('${WEBAPP_USER}', '', '${WEBAPP_PASS}')"
fi

echo ""
echo "##############################################"
echo ""
echo "        Wait for jenkins to startup"
echo ""
echo "##############################################"

while ! python build-and-test-webapp/ping_jenkins.py jenkins 8080; do "jenkins offline"; sleep 10; done;

echo ""
echo "##############################################"
echo ""
echo "        Add webapp jenkins jobs"
echo ""
echo "##############################################"

python build-and-test-webapp/add_jenkins_job.py jenkins 8080 network_template_mgr build-and-test-webapp/network_template_mgr.xml
python build-and-test-webapp/add_jenkins_job.py jenkins 8080 network_type_validator build-and-test-webapp/network_type_validator.xml

echo ""
echo "##############################################"
echo ""
echo "        Starting the server "
echo ""
echo "##############################################"

python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py runserver 0.0.0.0:8000
