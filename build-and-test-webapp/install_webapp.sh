#!/bin/sh
# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

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
