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

# stop the script if a command fails
#set -e
#set -x

# removing nita using docker compose
docker-compose -p nitawebapp -f /etc/${PACKAGE}/docker-compose.yaml down

# wait 15 seconds for the containers to exit
sleep 15

# remove exited containers:
docker ps --filter status=dead --filter status=exited -aq | xargs -r docker rm -v

# remove unused volumes:
docker volume ls -qf dangling=true | xargs -r docker volume rm

# remove docker network
if [[ `docker network ls -f 'name=nita-network' -q` == '' ]]
then
    echo "NITA network not present, skipping removal"
else
    echo "NITA network found, trying to remove"
    if [[ `docker network inspect nita-network | grep "EndpointID"` == '' ]]
    then
        echo "Removing NITA network"
        docker network rm nita-network
    else
        echo "NITA network is still in use, skipping removal"
    fi
fi

# remove docker images
docker rmi -f mariadb:10.4.12
docker rmi -f mariadb:_nita_release_$VERSION
docker rmi -f nginx:1.17.9
docker rmi -f nginx:_nita_release_$VERSION
docker rmi -f juniper/nita-webapp:$VERSION
docker rmi -f juniper/nita-webapp:_nita_release_$VERSION

# remove unused images
docker images --no-trunc | grep '<none>' | awk '{ print $3 }' | xargs -r docker rmi
