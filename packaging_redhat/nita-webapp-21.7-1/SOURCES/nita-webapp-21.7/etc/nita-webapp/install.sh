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

PACKAGE=nita-webapp
VERSION=21.7-1
IMAGES_DIR=/usr/share/${PACKAGE}/images

# stop the script if a command fails
set -e

# function to add docker images
function add_image {

    SRC="$1"
    TAG="$2"

    echo "Adding docker image $2"

    # load the image
    RESPONSE=`docker load -q < ${SRC}`
    echo $RESPONSE
    ID=`echo ${RESPONSE} | awk -F: '{ print \$3 }'`

    if [[ "x$ID" == "x" ]]; then
        echo "Failed to load image $SRC"
        exit 1
    fi

    # tag the image if it isn't already tagged in the tar.gz file
    # older versions of docker-ce have this issue
    if [[ `docker images | awk '{print $1":"$2}' | grep -c "$TAG"` == 0 ]]; then
        docker tag "$ID" "$TAG"
    fi

    docker tag "$TAG" "${TAG%:*}:_nita_release_$VERSION"

}

# generate selfsigned certificate for nginx
if [ -e /etc/${PACKAGE}/certificates/nginx-certificate.crt ]
then
    echo "Using existing certificate for webapp https connection"
else
    echo "Generation selfsigned certificate for webapp https connection"
    openssl req -batch -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/${PACKAGE}/certificates/nginx-certificate-key.key -out /etc/${PACKAGE}/certificates/nginx-certificate.crt
fi

# load docker images
add_image $IMAGES_DIR/mariadb.tar.gz mariadb:10.4.12
add_image $IMAGES_DIR/nginx.tar.gz nginx:1.17.9
add_image $IMAGES_DIR/nita-webapp.tar.gz juniper/nita-webapp:${VERSION}

# create nita docker network
if [[ `docker network ls -f 'name=nita-network' -q` == '' ]]
then
    echo "Creating NITA network"
    docker network create -d bridge nita-network
else
    echo "NITA network already exists, skipping creation"
fi

# deploy nita using docker compose
echo "Deploying nita services with docker compose"
docker-compose -p nitawebapp -f /etc/${PACKAGE}/docker-compose.yaml up -d
