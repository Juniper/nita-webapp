#!/bin/bash

# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -e
ARCH=`uname -p`
if [ $ARCH = aarch64 ] ; then # it is ARM64
	# By some reason PyYAML does not work with 5.4 version so change it to 5.3
        REQ_WEBAPP_BACKUP=/var/tmp/requirements.txt.$$
        cp requirements.txt ${REQ_WEBAPP_BACKUP}
        cat requirements.txt | sed 's/PyYAML==5.4/PyYAML==5.3/' > /var/tmp/requirements.tmp.$$
        mv /var/tmp/requirements.tmp.$$ requirements.txt
fi

docker build -t juniper/nita-webapp:$(tr -d '\r\n[:space:]' < VERSION.txt) .

if [ $ARCH = aarch64 ] ; then 
        # restoring requirement.txt to the origial
	 mv ${REQ_WEBAPP_BACKUP} requirements.txt
fi
