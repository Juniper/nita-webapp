# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Configure Jenkins global settings required for NITA operation.

Usage: python configure_jenkins.py <host> <port>

Sets the Jenkins URL so that jenkins-cli.jar can authenticate and create jobs.
Without the Jenkins URL set, the CLI handshake returns 403 on fresh installs.
"""

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = (
    "http://" + jenkins_host_name + ":" + str(jenkins_port) + "/jenkins"
)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")


def _identity_headers() -> dict:
    # Jenkins' reverse-proxy realm trusts this header from the webapp container.
    return {"X-Forwarded-User": JENKINS_SERVER_USER}


def set_jenkins_url():
    """Set the Jenkins URL in global configuration via the Groovy script console.

    The script console requires a valid CSRF crumb bound to the same session,
    so we use a CookieJar opener (same pattern as add_jenkins_job.py).
    """
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # Fetch CSRF crumb
    crumb_headers = {}
    try:
        crumb_req = urllib.request.Request(
            f"{JENKINS_SERVER_URL}/crumbIssuer/api/json",
            headers=_identity_headers(),
        )
        with opener.open(crumb_req, timeout=10) as resp:
            body = json.loads(resp.read())
            field = body.get("crumbRequestField", "Jenkins-Crumb")
            crumb = body.get("crumb", "")
            crumb_headers = {field: crumb}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("CSRF crumb issuer not found — proceeding without crumb.")
        else:
            print(f"Warning: could not fetch CSRF crumb: HTTP {e.code}")
    except Exception as e:
        print(f"Warning: could not fetch CSRF crumb: {e}")

    # Run Groovy script to set the Jenkins URL
    groovy = (
        "import jenkins.model.JenkinsLocationConfiguration\n"
        f"def config = JenkinsLocationConfiguration.get()\n"
        f'config.setUrl("{JENKINS_SERVER_URL}/")\n'
        "config.save()\n"
        'println "Jenkins URL configured: " + config.getUrl()\n'
    )

    payload = urllib.parse.urlencode({"script": groovy}).encode()
    headers = {
        **_identity_headers(),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    headers.update(crumb_headers)

    script_req = urllib.request.Request(
        f"{JENKINS_SERVER_URL}/scriptText",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with opener.open(script_req, timeout=30) as resp:
            result = resp.read().decode("utf-8", errors="replace").strip()
            print(f"Jenkins URL configured: {result}")
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        print(f"Error configuring Jenkins URL: HTTP {e.code} {e.reason}")
        print(f"Response body: {body_text}")
    except Exception as e:
        print(f"Error configuring Jenkins URL: {e}")


import urllib.parse

if __name__ == "__main__":
    set_jenkins_url()
