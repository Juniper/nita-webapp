# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import base64
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

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


def add_job(job_name, file_name):
    """Create a Jenkins job, handling CSRF crumbs correctly.

    Jenkins binds the crumb to the HTTP session that issued it.
    The GET (crumb fetch) and the POST (createItem) must therefore share
    the same session cookie, which we achieve with a CookieJar opener.
    """
    with open(file_name, "r") as f:
        xml = f.read()

    # Build an opener that automatically stores and resends cookies.
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    crumb_headers = {}
    try:
        crumb_req = urllib.request.Request(
            f"{JENKINS_SERVER_URL}/crumbIssuer/api/json",
            headers={"Authorization": _auth_header()},
        )
        with opener.open(crumb_req, timeout=10) as resp:
            body = json.loads(resp.read())
            field = body.get("crumbRequestField", "Jenkins-Crumb")
            crumb = body.get("crumb", "")
            crumb_headers = {field: crumb}
            print(f"Got Jenkins CSRF crumb (field={field})")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("CSRF crumb issuer not found — CSRF likely disabled, proceeding without crumb.")
        else:
            print(f"Warning: could not fetch CSRF crumb: HTTP {e.code}")
    except Exception as e:
        print(f"Warning: could not fetch CSRF crumb: {e}")

    print("Jenkins server: " + JENKINS_SERVER_URL)
    url = f"{JENKINS_SERVER_URL}/createItem?name={urllib.parse.quote(job_name)}"
    headers = {
        "Authorization": _auth_header(),
        "Content-Type": "text/xml; charset=utf-8",
    }
    headers.update(crumb_headers)
    post_req = urllib.request.Request(url, data=xml.encode("utf-8"), headers=headers, method="POST")
    try:
        with opener.open(post_req, timeout=30) as resp:
            print(f"Job '{job_name}' created: HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print(f"Job '{job_name}' already exists (HTTP 400), skipping.")
        else:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            print(f"Error while adding job '{job_name}': HTTP {e.code} {e.reason}")
            print(f"Response body: {body_text}")
    except Exception as e:
        print(f"Error while adding job '{job_name}': {e}")


add_job(sys.argv[3], sys.argv[4])
