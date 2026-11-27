#!/usr/bin/env python3

# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Docker HEALTHCHECK probe for the webapp, needing no wget/curl in the image.

Any HTTP answer below 500 from the unauthenticated CSRF endpoint proves the
Django server is serving (a 400 just means DJANGO_ALLOWED_HOSTS omits
``localhost``). No answer, a timeout or a 5xx exits non-zero.
"""

import sys
import urllib.error
import urllib.request

URL = "http://localhost:8000/api/v1/auth/csrf/"


def main():
    try:
        with urllib.request.urlopen(URL, timeout=5):  # noqa: S310
            return 0
    except urllib.error.HTTPError as exc:
        return 0 if exc.code < 500 else 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"healthcheck failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
