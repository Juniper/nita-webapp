# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Jenkins server configuration and connection helpers.

Holds the Jenkins connection constants (read from ``server_details.ini`` and the
environment) and the factory for a ``jenkins.Jenkins`` client. Extracted from the
legacy ``ngcn.views`` module so the API layer and ``jenkins_jobs`` no longer
depend on the server-rendered UI code.
"""

import configparser
import os

import jenkins
from django.conf import settings

config = configparser.ConfigParser()
config_location = settings.BASE_DIR + "/../"
config.read_file(open(config_location + "server_details.ini"))
jenkins_host_name = config["jenkins.server.details"]["hostname"]
jenkins_port = config["jenkins.server.details"]["port"]
JENKINS_SERVER_URL = (
    "http://" + jenkins_host_name + ":" + str(jenkins_port) + "/jenkins"
)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")

# Jenkins runs the Reverse Proxy Auth realm: identity is asserted by these
# request headers (set by the webapp on direct calls, and by the proxy from the
# forward-auth response for browser traffic). No password is exchanged.
JENKINS_IDENTITY_HEADER = "X-Forwarded-User"
JENKINS_GROUPS_HEADER = "X-Forwarded-Groups"
JENKINS_GROUPS_DELIMITER = "|"


def jenkins_team_group(team_id):
    """Jenkins group name for a webapp team (id-based so renames are harmless)."""
    return f"team-{team_id}"


def jenkins_groups_for(user):
    """Jenkins groups mirroring the webapp model: the role plus one group per team."""
    groups = [getattr(user, "role", "") or ""]
    groups += [
        jenkins_team_group(tid) for tid in user.teams.values_list("id", flat=True)
    ]
    return [g for g in groups if g]


def jenkins_identity_headers(username=None, groups=None):
    """Return headers asserting ``username`` (default: service identity) to Jenkins."""
    headers = {JENKINS_IDENTITY_HEADER: username or JENKINS_SERVER_USER}
    if groups:
        headers[JENKINS_GROUPS_HEADER] = JENKINS_GROUPS_DELIMITER.join(groups)
    return headers


def _make_jenkins_server(acting_user=None):
    """Return a new jenkins.Jenkins connection acting as ``acting_user``."""
    server = jenkins.Jenkins(JENKINS_SERVER_URL)
    server._session.headers.update(jenkins_identity_headers(acting_user))
    return server
