# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

FROM node:22-slim AS frontend-builder

WORKDIR /build
COPY frontend/ .
RUN npm ci \
 && npm run build

FROM python:3.12-slim-trixie AS python-builder

ARG YAML_TO_EXCEL_COMMIT=46bce45d811772d9b973c95c453df1ad703f6b31
ARG YAML_TO_EXCEL_SHA256=f76d9a70b52afe35c6df5fb668ea9859adcc399f7ff6fd5afcbb7fea5d2e1fac

RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl default-libmysqlclient-dev gcc pkg-config \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN curl --fail --location --silent --show-error \
      --output nita-yaml-to-excel.tar.gz \
      "https://github.com/Juniper/nita-yaml-to-excel/archive/${YAML_TO_EXCEL_COMMIT}.tar.gz" \
 && echo "${YAML_TO_EXCEL_SHA256}  nita-yaml-to-excel.tar.gz" | sha256sum --check --strict \
 && mkdir nita-yaml-to-excel-22.8 \
 && tar -xzf nita-yaml-to-excel.tar.gz --strip-components=1 \
      -C nita-yaml-to-excel-22.8 \
 && python -m venv /opt/nita-venv \
 && /opt/nita-venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/nita-venv/bin/pip install --no-cache-dir -r requirements.txt \
 && /opt/nita-venv/bin/pip install --no-cache-dir "setuptools>=67.6.0" \
 && /opt/nita-venv/bin/pip check

FROM python:3.12-slim-trixie

ENV WEBAPP_USER=vagrant
ENV WEBAPP_PASS=vagrant123
ENV JENKINS_USER=admin
ENV JENKINS_PASS=admin
ENV PATH="/opt/nita-venv/bin:$PATH"

RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      libmariadb3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=frontend-builder /build/dist /app/frontend/dist
COPY --from=python-builder /opt/nita-venv /opt/nita-venv
COPY nita.properties /etc/nita.properties
COPY build-and-test-webapp/ build-and-test-webapp/

RUN mkdir -p /var/log/nita-webapp \
 && touch /var/log/nita-webapp/server.log \
 && useradd --system --no-create-home --shell /usr/sbin/nologin appuser \
 && chown -R appuser /app /var/log/nita-webapp

USER appuser

LABEL net.juniper.framework="NITA"
LABEL org.opencontainers.image.source="https://github.com/Juniper/nita-webapp"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/app/', timeout=5)" || exit 1
