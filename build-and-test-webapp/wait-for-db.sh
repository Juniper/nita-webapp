#!/bin/bash

# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

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

python build-and-test-webapp/wait_for_db.py

echo ""
echo "##############################################"
echo ""
echo "        Django makemigrations"
echo ""
echo "##############################################"

python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py makemigrations ngcn
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
echo "        Django Admin User: "
echo "        ${WEBAPP_USER}/${WEBAPP_PASS}"
echo ""
echo "##############################################"

echo "Ensuring the admin user exists (role=admin)..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py create_admin \
    --username "${WEBAPP_USER}" --password "${WEBAPP_PASS}"

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
echo "        Configure Jenkins"
echo ""
echo "##############################################"

python build-and-test-webapp/configure_jenkins.py jenkins 8080

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
echo "        Collecting static files"
echo ""
echo "##############################################"

python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py collectstatic --noinput

echo ""
echo "##############################################"
echo ""
echo "        Starting the server "
echo ""
echo "##############################################"

python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py runserver 0.0.0.0:8000
