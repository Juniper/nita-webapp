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

set -e
ARCH=`uname -p`
if [ $ARCH = aarch64 ] ; then # it is ARM64
	# By some reason PyYAML does not work with 5.4 version so change it to 5.3
        REQ_WEBAPP_BACKUP=/var/tmp/requirements.txt.$$
        cp requirements.txt ${REQ_WEBAPP_BACKUP}
        cat requirements.txt | sed 's/PyYAML==5.4/PyYAML==5.3/' > /var/tmp/requirements.tmp.$$
        mv /var/tmp/requirements.tmp.$$ requirements.txt
fi

docker build -t juniper/nita-webapp:25.10-1 .

if [ $ARCH = aarch64 ] ; then 
        # restoring requirement.txt to the origial
	 mv ${REQ_WEBAPP_BACKUP} requirements.txt
fi
