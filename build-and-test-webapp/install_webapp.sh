#!/bin/sh
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

. /etc/nita.properties

PROJECT=./
NITAWEBAPP=nita-webapp


# create log file
mkdir /var/log/${NITAWEBAPP}
touch /var/log/${NITAWEBAPP}/server.log
chown -R ${NITA_USER}:${NITA_GROUP} /var/log/${NITAWEBAPP}


# install the nita-webapp to /usr/local/
cp -rf $PROJECT/${NITAWEBAPP} /usr/local/
chown -R ${NITA_USER}:${NITA_GROUP} /usr/local/${NITAWEBAPP}

# install the nita-webapp service script
cp $PROJECT/data/etc/init.d/${NITAWEBAPP} /etc/init.d/
chown  ${NITA_USER}:${NITA_GROUP} /etc/init.d/${NITAWEBAPP}
chmod -R 775 /etc/init.d/${NITAWEBAPP}

#install the nita-webapp uninstall script
#install -m 0755 $PROJECT/uninstall_webapp.sh   /usr/local/bin/uninstall_webapp.sh

exit 0
