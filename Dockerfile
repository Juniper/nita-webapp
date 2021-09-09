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

FROM python:3.8-slim-buster

ENV WEBAPP_USER vagrant
ENV WEBAPP_PASS vagrant123
ENV JENKINS_USER admin
ENV JENKINS_PASS admin

WORKDIR /app

RUN apt-get update -y
RUN apt-get install gcc default-mysql-client default-libmysqlclient-dev wget unzip -y

#COPY nita-yaml-to-excel/ yaml-to-excel/

RUN wget --no-check-certificate https://github.com/Juniper/nita-yaml-to-excel/archive/refs/heads/21.7.zip
RUN unzip 21.7.zip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY nita.properties /etc/nita.properties

COPY build-and-test-webapp/ build-and-test-webapp/
RUN mkdir /var/log/nita-webapp
RUN touch /var/log/nita-webapp/server.log

LABEL net.juniper.framework="NITA"

EXPOSE 8000
