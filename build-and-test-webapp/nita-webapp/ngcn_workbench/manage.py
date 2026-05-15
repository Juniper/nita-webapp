#!/usr/bin/env python
# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ngcn_workbench.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
