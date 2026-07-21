#!/bin/bash

# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -e
docker build \
  --tag "juniper/nita-webapp:$(tr -d '\r\n[:space:]' < VERSION.txt)" \
  .
