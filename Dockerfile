# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# ── Stage 1: Build React SPA ──────────────────────────────────────────────────
FROM node:22-slim AS frontend-builder

WORKDIR /build
COPY frontend/ .
RUN npm ci
RUN npm run build

# ── Stage 2: Django application image ────────────────────────────────────────
FROM python:3.12-slim-bookworm

ENV WEBAPP_USER=vagrant
ENV WEBAPP_PASS=vagrant123
ENV JENKINS_USER=admin
ENV JENKINS_PASS=admin

WORKDIR /app

# Copy compiled React SPA from builder stage
COPY --from=frontend-builder /build/dist /app/frontend/dist

RUN apt-get update -y
RUN apt-get install gcc default-mysql-client default-libmysqlclient-dev pkg-config wget unzip -y

#COPY nita-yaml-to-excel/ yaml-to-excel/

RUN wget https://github.com/Juniper/nita-yaml-to-excel/archive/refs/heads/22.8.zip
RUN unzip 22.8.zip
COPY requirements.txt .
RUN pip install -r requirements.txt
# python-jenkins 1.8.0 declares setuptools<66, but that version of setuptools
# uses pkgutil.ImpImporter which was removed in Python 3.12. Upgrade setuptools
# in a separate step so pip's resolver only considers setuptools's own deps.
RUN pip install "setuptools>=67.6.0"

COPY nita.properties /etc/nita.properties

COPY build-and-test-webapp/ build-and-test-webapp/
RUN mkdir /var/log/nita-webapp
RUN touch /var/log/nita-webapp/server.log

RUN useradd --system --no-create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser /app /var/log/nita-webapp

USER appuser

LABEL net.juniper.framework="NITA"
LABEL org.opencontainers.image.source="https://github.com/aburston/nita-webapp"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -qO- http://localhost:8000/api/v1/auth/token/ || exit 1
