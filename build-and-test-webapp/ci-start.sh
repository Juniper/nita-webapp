#!/bin/bash
# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# CI startup for nita-webapp.
# Skips the Jenkins health-check so the webapp starts without a Jenkins
# instance.  Used only in the kind-cluster CI job.

set -euo pipefail

. /etc/nita.properties

# ── Defaults ──────────────────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-db}"
DB_ROOT_USER="${DB_ROOT_USER:-root}"
DB_ROOT_PASS="${DB_ROOT_PASS:-root}"
WEBAPP_USER="${WEBAPP_USER:-vagrant}"
WEBAPP_PASS="${WEBAPP_PASS:-vagrant123}"

# ── Wait for MariaDB ──────────────────────────────────────────────────────────
echo "Waiting for MariaDB at ${DB_HOST}..."
until mysqladmin ping -h"${DB_HOST}" -u"${DB_ROOT_USER}" -p"${DB_ROOT_PASS}" --silent 2>/dev/null; do
    echo "  db not ready, retrying in 2s..."
    sleep 2
done
echo "MariaDB is up."

# ── Django setup ──────────────────────────────────────────────────────────────
cd /app

echo "Running makemigrations check..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py makemigrations --check

echo "Running migrate..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py migrate

echo "Loading initial fixture data..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py loaddata campus_detail_data

echo "Ensuring superuser (${WEBAPP_USER}) exists..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py shell -c "
from django.contrib.auth.models import User
if User.objects.filter(username='${WEBAPP_USER}').exists():
    u = User.objects.get(username='${WEBAPP_USER}')
    u.set_password('${WEBAPP_PASS}')
    u.save()
    print('superuser password updated')
else:
    User.objects.create_superuser('${WEBAPP_USER}', '', '${WEBAPP_PASS}')
    print('superuser created')
"

# ── Start Django server ───────────────────────────────────────────────────────
echo "Starting Django development server on 0.0.0.0:8000..."
exec python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py runserver 0.0.0.0:8000
