# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

import logging

from ngcn.statusupdater import StatusUpdater

logger = logging.getLogger(__name__)


class StatusStartupServiceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.info("Jenkins Job status updater service has been started")
        StatusUpdater.getInstance().startStatusUpdaterService()
