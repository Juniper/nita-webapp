#!/bin/bash

# ********************************************************
#
# Project: nita-webapp
# Version: 20.10
#
# Copyright (c) Juniper Networks, Inc., 2020. All rights reserved.
#
# Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html
#
# SPDX-License-Identifier: Apache-2.0
#
# Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.
#
# ********************************************************

set -e

if [ -d nita-yaml-to-excel ]; then
    echo "nita-yaml-to-excel already exists"
else
    git clone https://github.com/Juniper/nita-yaml-to-excel.git
fi
(cd nita-yaml-to-excel; git checkout main)

docker build -t juniper/nita-webapp:20.10-1 .
