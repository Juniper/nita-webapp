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

echo "Ensuring admin user (${WEBAPP_USER}) exists..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py create_admin \
    --username "${WEBAPP_USER}" --password "${WEBAPP_PASS}"

echo "Collecting static files..."
python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py collectstatic --noinput

# ── Start Django server ───────────────────────────────────────────────────────
echo "Starting Django development server on 0.0.0.0:8000..."
exec python build-and-test-webapp/nita-webapp/ngcn_workbench/manage.py runserver 0.0.0.0:8000
