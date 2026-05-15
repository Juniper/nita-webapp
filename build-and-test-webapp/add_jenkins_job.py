# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import base64

jenkins_host_name = sys.argv[1]
jenkins_port = sys.argv[2]
JENKINS_SERVER_URL = "http://" + jenkins_host_name + ":" + str(jenkins_port)
JENKINS_SERVER_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_SERVER_PASS = os.getenv("JENKINS_PASS", "admin")


def _auth_header() -> str:
    credentials = base64.b64encode(
        f"{JENKINS_SERVER_USER}:{JENKINS_SERVER_PASS}".encode()
    ).decode()
    return f"Basic {credentials}"


def _get_crumb() -> dict:
    """Return Jenkins CSRF crumb headers, or {} if CSRF is disabled."""
    try:
        req = urllib.request.Request(
            f"{JENKINS_SERVER_URL}/crumbIssuer/api/json",
            headers={"Authorization": _auth_header()},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json
            body = json.loads(resp.read())
            field = body.get("crumbRequestField", "Jenkins-Crumb")
            crumb = body.get("crumb", "")
            print(f"Got Jenkins CSRF crumb (field={field})")
            return {field: crumb}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("CSRF crumb issuer not found — CSRF likely disabled, proceeding without crumb.")
        else:
            print(f"Warning: could not fetch CSRF crumb: HTTP {e.code}")
        return {}
    except Exception as e:
        print(f"Warning: could not fetch CSRF crumb: {e}")
        return {}


def add_job(job_name, file_name):
    with open(file_name, "r") as f:
        xml = f.read()
    crumb_headers = _get_crumb()
    try:
        print("Jenkins server: " + JENKINS_SERVER_URL)
        url = f"{JENKINS_SERVER_URL}/createItem?name={urllib.parse.quote(job_name)}"
        data = xml.encode("utf-8")
        headers = {
            "Authorization": _auth_header(),
            "Content-Type": "text/xml; charset=utf-8",
        }
        headers.update(crumb_headers)
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"Job '{job_name}' created: HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            # Job already exists — treat as success
            print(f"Job '{job_name}' already exists (HTTP 400), skipping.")
        else:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            print(f"Error while adding job '{job_name}': HTTP {e.code} {e.reason}")
            print(f"Response body: {body}")
    except Exception as e:
        print(f"Error while adding job '{job_name}': {e}")


add_job(sys.argv[3], sys.argv[4])
