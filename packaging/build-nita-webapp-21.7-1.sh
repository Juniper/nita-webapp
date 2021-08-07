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

# stop the script if a command fails
set -e

PACKAGE=nita-webapp
VERSION=21.7-1

# cleanup version if the directory name is used
VTMP="${VERSION#$PACKAGE-}"
VERSION=${VTMP%/}


if [[ "x$VERSION" == "x" ]]; then
    echo "Must provide package version"
    exit 1
fi

if [ ! -d ${PACKAGE}-${VERSION} ]; then
    echo "Directory ${PACKAGE}-${VERSION} does not exist"
fi

# installing docker-ce on host
if dpkg-query -s docker-ce >/dev/null 2>&1; then
    echo "docker-ce already installed"
else
    apt-get -y update
    apt-get -y install apt-transport-https ca-certificates curl \
        software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg |apt-key add -
    apt-key fingerprint 0EBFCD88
    add-apt-repository \
       "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
       $(lsb_release -cs) stable"
    apt-get -y update
    apt-get -y install docker-ce
fi

# copy cli scripts
SCRIPTSDIR=${PACKAGE}-${VERSION}/usr/local/bin
rm -rf ${SCRIPTSDIR}
mkdir -p ${SCRIPTSDIR}
install -m 755 ../cli_scripts/* ${SCRIPTSDIR}

# install nita-cmd
rm -rf ${PACKAGE}-${VERSION}/etc/bash_completion.d
mkdir -p ${PACKAGE}-${VERSION}/etc/bash_completion.d
(
   cd ../nita-cmd
   BASH_COMPLETION=../packaging/${PACKAGE}-${VERSION}/etc/bash_completion.d \
       INSTALLDIR=../packaging/${SCRIPTSDIR} ../nita-cmd/install.sh
)

# pull all the required containers
IMAGEDIR=${PACKAGE}-${VERSION}/usr/share/${PACKAGE}/images
mkdir -p ${IMAGEDIR}

docker pull mariadb:10.4.12
docker save mariadb:10.4.12 | gzip > ${IMAGEDIR}/mariadb.tar.gz

docker pull nginx:1.17.9
docker save nginx:1.17.9 | gzip > ${IMAGEDIR}/nginx.tar.gz

(
    cd ..
    ./build_container.sh
)
docker save juniper/nita-webapp:${VERSION} | gzip > ${IMAGEDIR}/nita-webapp.tar.gz


dpkg-deb --build ${PACKAGE}-${VERSION}
