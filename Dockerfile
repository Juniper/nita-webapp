# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

FROM python:3.12-slim-bookworm

ENV WEBAPP_USER=vagrant
ENV WEBAPP_PASS=vagrant123
ENV JENKINS_USER=admin
ENV JENKINS_PASS=admin

WORKDIR /app

RUN apt-get update -y
RUN apt-get install gcc default-mysql-client default-libmysqlclient-dev pkg-config wget unzip -y

#COPY nita-yaml-to-excel/ yaml-to-excel/

RUN wget --no-check-certificate https://github.com/Juniper/nita-yaml-to-excel/archive/refs/heads/22.8.zip
RUN unzip 22.8.zip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY nita.properties /etc/nita.properties

COPY build-and-test-webapp/ build-and-test-webapp/
RUN mkdir /var/log/nita-webapp
RUN touch /var/log/nita-webapp/server.log

LABEL net.juniper.framework="NITA"

EXPOSE 8000
