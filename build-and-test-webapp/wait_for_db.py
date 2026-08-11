#!/usr/bin/env python3

# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wait for the NITA MariaDB service without shipping the MariaDB CLI."""

import os
import time

import MySQLdb


def wait_for_database() -> None:
    host = os.getenv("DB_HOST", "db")
    user = os.getenv("DB_ROOT_USER", "root")
    password = os.getenv("DB_ROOT_PASS", "root")

    while True:
        try:
            connection = MySQLdb.connect(
                host=host,
                user=user,
                passwd=password,
                connect_timeout=2,
            )
            connection.close()
            return
        except MySQLdb.Error:
            print("Waiting for db...", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    wait_for_database()
