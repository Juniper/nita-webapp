# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""DRF ViewSet classes for the NITA Webapp REST API.

Endpoints
---------
``/api/v1/action-categories/``
    :class:`ActionCategoryViewSet` — read-only list/retrieve.

``/api/v1/network-types/``
    :class:`CampusTypeViewSet` — list, retrieve, delete, and zip upload.
    POST /create is intentionally disabled; use the ``/upload/`` action.

``/api/v1/networks/``
    :class:`CampusNetworkViewSet` — full CRUD plus workbook and trigger
    actions.

``/api/v1/actions/``
    :class:`ActionViewSet` — read-only, filterable by ``?campus_type_id=``.

``/api/v1/action-history/``
    :class:`ActionHistoryViewSet` — read-only, filterable by
    ``?campus_network_id=``, with a Jenkins console proxy action.
"""

import base64
import json
import logging
import time
import traceback
import urllib.error
import urllib.request

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import FileResponse, StreamingHttpResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response


class SSERenderer(BaseRenderer):
    """Passthrough renderer for Server-Sent Events (text/event-stream)."""

    media_type = "text/event-stream"
    format = "event-stream"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


from ngcn.models import (
    Action,
    ActionCategory,
    ActionHistory,
    CampusNetwork,
    CampusType,
    Workbook,
)
from ngcn.networktypeparser import NetworkTypeParser
from ngcn.views import (
    GridDataManager,
    create_new_inv,
    create_workbook,
    create_workbook_from_db,
    parse_workbook,
)

from .serializers import (
    ActionCategorySerializer,
    ActionHistorySerializer,
    ActionSerializer,
    CampusNetworkSerializer,
    CampusTypeSerializer,
    WorkbookSerializer,
)

logger = logging.getLogger(__name__)

# ── Session auth views ─────────────────────────────────────────────────────────


@extend_schema(
    responses={
        200: {"type": "object", "properties": {"csrfToken": {"type": "string"}}}
    },
    auth=[],
    summary="Return the CSRF token (no authentication required)",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    """Return the current CSRF token as JSON. Also sets the csrftoken cookie."""
    return Response({"csrfToken": get_token(request)})


@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        }
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "is_superuser": {"type": "boolean"},
            },
        },
        400: OpenApiResponse(description="Invalid credentials"),
        403: OpenApiResponse(description="CSRF verification failed"),
    },
    auth=[],
    summary="Log in with username and password, open a Django session",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate and open a Django session. Requires a valid X-CSRFToken header."""
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST
        )
    auth_login(request, user)
    return Response(
        {"id": user.pk, "username": user.username, "is_superuser": user.is_superuser}
    )


@extend_schema(
    responses={204: OpenApiResponse(description="Session destroyed. No content.")},
    summary="Log out and destroy the current Django session",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Destroy the current session. Authentication required."""
    auth_logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    responses={
        200: {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "is_superuser": {"type": "boolean"},
            },
        }
    },
    summary="Return the currently authenticated user's info",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return the authenticated user's id, username, and is_superuser."""
    user = request.user
    return Response(
        {"id": user.pk, "username": user.username, "is_superuser": user.is_superuser}
    )


# ── End session auth views ─────────────────────────────────────────────────────

WORKBOOK_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "data": {
            "oneOf": [
                {"type": "object"},
                {"type": "array", "maxItems": 1000},
                {"type": "string"},
            ]
        },
    },
    "required": ["name", "data"],
}

WORKBOOK_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "workbook": {"type": "array", "maxItems": 1000, "items": WORKBOOK_ITEM_SCHEMA},
    },
    "required": ["status", "workbook"],
}

NETWORK_TYPE_UPLOAD_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {"type": "string"},
        "name": {"type": "string"},
        "id": {"type": "integer"},
    },
    "required": ["result"],
}

NETWORK_TYPE_UPLOAD_FAILURE_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["result", "reason"],
}


class ActionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list and retrieve for ActionCategory objects."""

    queryset = ActionCategory.objects.all()
    serializer_class = ActionCategorySerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=str,
                location="query",
                required=False,
                description="Filter by network type name.",
            )
        ]
    )
)
class CampusTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Network types. Create via POST /upload/ (zip); delete via DELETE /{id}/."""

    serializer_class = CampusTypeSerializer

    def get_queryset(self):
        qs = CampusType.objects.all()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name=name)
        return qs

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"app_zip_file": {"type": "string", "format": "binary"}},
            }
        },
        responses={
            200: NETWORK_TYPE_UPLOAD_SUCCESS_SCHEMA,
            400: NETWORK_TYPE_UPLOAD_FAILURE_SCHEMA,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="upload",
    )
    def upload(self, request):
        """Upload a network-type zip file to register a new CampusType."""
        zip_file = request.FILES.get("app_zip_file")
        if not zip_file:
            return Response(
                {"result": "failure", "reason": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.core.files.storage import default_storage

        if default_storage.exists(zip_file.name):
            default_storage.delete(zip_file.name)
        file_name = default_storage.save(zip_file.name, zip_file)
        zip_file.close()
        parser = NetworkTypeParser()
        result = parser.parseProjectFile(file_name)
        default_storage.delete(file_name)
        if hasattr(result, "status_code"):
            # NetworkTypeParser returns a JsonResponse on success/failure
            data = json.loads(result.content)
            http_status = result.status_code
        else:
            data = {"result": "failure", "reason": str(result)}
            http_status = status.HTTP_400_BAD_REQUEST
        return Response(data, status=http_status)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "campus_type_id",
                type=int,
                location="query",
                required=False,
                description="Filter by campus type ID.",
            )
        ]
    )
)
class CampusNetworkViewSet(viewsets.ModelViewSet):
    """Full CRUD for CampusNetwork objects, plus workbook management and action triggering.

    Standard CRUD
        ``GET /api/v1/networks/``                — paginated list (filter: ``?campus_type_id=``)
        ``POST /api/v1/networks/``               — create
        ``GET /api/v1/networks/{id}/``           — retrieve
        ``PUT/PATCH /api/v1/networks/{id}/``     — update
        ``DELETE /api/v1/networks/{id}/``        — destroy

    Workbook actions
        ``POST   …/{id}/workbook/upload/``   — parse and store Excel data
        ``GET    …/{id}/workbook/``          — retrieve current grid data
        ``POST   …/{id}/workbook/save/``     — save edited grid data
        ``DELETE …/{id}/workbook/clear/``    — remove all grid data
        ``GET    …/{id}/workbook/download/`` — stream as ``.xlsx`` file

    Trigger
        ``POST …/{id}/trigger/{action_id}/`` — queue a Jenkins job;
        returns ``202 Accepted`` with ``action_history_id`` immediately.
        Poll ``GET /api/v1/action-history/{id}/`` for status.
    """

    queryset = CampusNetwork.objects.all()
    serializer_class = CampusNetworkSerializer

    def get_queryset(self):
        qs = CampusNetwork.objects.all()
        campus_type_id = self.request.query_params.get("campus_type_id")
        if campus_type_id:
            qs = qs.filter(campus_type_id=campus_type_id)
        return qs

    def create(self, request, *args, **kwargs):
        """Create a network, synchronously running the Jenkins build job.

        The ``network_template_mgr`` Jenkins job is triggered with
        ``operation=create`` and this request blocks until it completes. The
        database row is only persisted if the job succeeds; on failure a
        cleanup ``delete`` job is triggered and an error response is returned so
        the GUI can report success or failure.
        """
        from ngcn.utils import ServerProperties, wait_and_get_build_status
        from ngcn.views import _make_jenkins_server

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        campus_type = validated["campus_type"]
        network_name = validated["name"]
        host_file = validated.get("host_file", "")
        network_desc = validated.get("description", "")

        src = (
            ServerProperties.getWorkspaceLocation()
            + "/"
            + campus_type.app_zip_name
        )
        action_url = "network_template_mgr"
        build_params = {
            "operation": "create",
            "src": src,
            "network_name": network_name,
            "hosts": host_file,
            "network_desc": network_desc,
        }

        server = _make_jenkins_server()
        try:
            current_build_number = server.get_job_info(action_url)["nextBuildNumber"]
            try:
                server.build_job(action_url, build_params)
            except Exception as exc:  # most likely a Jenkins crumb issue
                if "Forbidden" in str(exc):
                    server = _make_jenkins_server()
                    server.build_job(action_url, build_params)
                else:
                    raise
        except Exception as exc:
            logger.error(
                "Jenkins unreachable while creating network %s: %s",
                network_name,
                exc,
            )
            return Response(
                {
                    "status": "failure",
                    "name": network_name,
                    "reason": "Jenkins service unavailable.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if wait_and_get_build_status(action_url, current_build_number):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        logger.error(
            "Jenkins create job failed for network %s; running cleanup delete",
            network_name,
        )
        try:
            cleanup_build = server.get_job_info(action_url)["nextBuildNumber"]
            server.build_job(
                action_url,
                {
                    "operation": "delete",
                    "src": src,
                    "network_name": network_name,
                },
            )
            wait_and_get_build_status(action_url, cleanup_build)
        except Exception as exc:
            logger.error(
                "Cleanup delete job failed for network %s: %s", network_name, exc
            )
        return Response(
            {
                "status": "failure",
                "name": network_name,
                "reason": "Network creation job failed.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a network, synchronously running the Jenkins build job.

        The ``network_template_mgr`` Jenkins job is triggered with
        ``operation=delete`` and this request blocks until it completes. The
        database row is only removed if the job succeeds, so the GUI can report
        success or failure.
        """
        from ngcn.utils import ServerProperties, wait_and_get_build_status
        from ngcn.views import _make_jenkins_server

        instance = self.get_object()
        network_name = instance.name
        src = (
            ServerProperties.getWorkspaceLocation()
            + "/"
            + instance.campus_type.app_zip_name
        )
        action_url = "network_template_mgr"
        build_params = {
            "operation": "delete",
            "src": src,
            "network_name": network_name,
        }

        server = _make_jenkins_server()
        try:
            current_build_number = server.get_job_info(action_url)["nextBuildNumber"]
            try:
                server.build_job(action_url, build_params)
            except Exception as exc:  # most likely a Jenkins crumb issue
                if "Forbidden" in str(exc):
                    server = _make_jenkins_server()
                    server.build_job(action_url, build_params)
                else:
                    raise
        except Exception as exc:
            logger.error(
                "Jenkins unreachable while deleting network %s: %s",
                network_name,
                exc,
            )
            return Response(
                {
                    "status": "failure",
                    "name": network_name,
                    "reason": "Jenkins service unavailable.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if wait_and_get_build_status(action_url, current_build_number):
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        logger.error("Jenkins delete job failed for network %s", network_name)
        return Response(
            {
                "status": "failure",
                "name": network_name,
                "reason": "Network deletion job failed.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}},
            }
        },
        responses={200: WORKBOOK_RESPONSE_SCHEMA},
    )
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="workbook/upload",
    )
    def upload_workbook(self, request, pk=None):
        """Upload an Excel workbook to populate configuration data for this network.

        Expects multipart/form-data with field name ``file``.
        """
        up_file = request.FILES.get("file")
        if not up_file:
            return Response(
                {"status": "failure", "message": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = parse_workbook(up_file, pk)
            if result != "invalid_host":
                dm = GridDataManager()
                raw_sheets = dm.get_sheets_by_campus_network(pk)
                sheets = []
                for sheet in raw_sheets:
                    name = sheet.get("name", "")
                    columns = sheet.get("columns", [])
                    headers = [col["name"] for col in columns]
                    raw_rows = sheet.get(name, [])
                    rows = [list(row.values()) for row in raw_rows]
                    sheets.append({"name": name, "headers": headers, "rows": rows})
                return Response({"workbook": sheets, "status": "success"})
            return Response(
                {
                    "status": "failure",
                    "message": "Invalid data in host column in Excel file.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error("Error loading Excel file: %s", exc)
            return Response(
                {"status": "failure", "message": "Error while loading the Excel file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: WORKBOOK_RESPONSE_SCHEMA})
    @action(detail=True, methods=["get"], url_path="workbook")
    def get_workbook(self, request, pk=None):
        """Return the current configuration grid data for this network.

        Each sheet is returned as ``{"name", "headers", "rows"}`` where
        ``headers`` is the list of column names and ``rows`` is a list of
        value arrays (one array per data row).
        """
        try:
            dm = GridDataManager()
            raw_sheets = dm.get_sheets_by_campus_network(pk)
            sheets = []
            for sheet in raw_sheets:
                name = sheet.get("name", "")
                columns = sheet.get("columns", [])
                headers = [col["name"] for col in columns]
                raw_rows = sheet.get(name, [])
                rows = [list(row.values()) for row in raw_rows]
                sheets.append({"name": name, "headers": headers, "rows": rows})
            return Response({"workbook": sheets, "status": "success"})
        except Exception as exc:
            logger.error("Error fetching workbook: %s", exc)
            return Response(
                {"status": "failure", "message": "Error retrieving workbook data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"data": {"type": "array"}},
            }
        },
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}}}
        },
    )
    @action(detail=True, methods=["post"], url_path="workbook/save")
    def save_workbook(self, request, pk=None):
        """Save updated configuration grid data for this network.

        Expects a JSON body ``{"data": [{"name": "...", "headers": [...], "rows": [[...]]}]}``.
        """
        try:
            import collections

            payload = json.loads(request.body.decode("utf-8"))
            dm = GridDataManager()
            sheets = dm.get_sheets_by_campus_network(pk)
            for grid in payload["data"]:
                grid_name = grid["name"]
                headers = grid.get("headers", [])
                new_rows = grid.get("rows", [])
                # Reconstruct rows as ordered dicts (internal storage format)
                rows_as_dicts = [
                    collections.OrderedDict(zip(headers, row))
                    for row in new_rows
                ]
                for sheet in sheets:
                    if sheet["name"] == grid_name:
                        sheet[grid_name] = rows_as_dicts
            dm.create_or_update_db(pk, sheets)
            return Response({"status": "success"})
        except Exception as exc:
            logger.error("Error saving workbook: %s", exc)
            return Response(
                {"status": "failure", "message": "Error saving configuration data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["delete"], url_path="workbook/clear")
    def clear_workbook(self, request, pk=None):
        """Delete all configuration grid data for this network."""
        try:
            dm = GridDataManager()
            dm.delete_workbook(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            logger.error("Error clearing workbook: %s", exc)
            return Response(
                {"status": "failure", "message": "Error clearing workbook data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        responses={
            (
                200,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ): OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="Excel workbook",
            )
        }
    )
    @action(detail=True, methods=["get"], url_path="workbook/download")
    def download_workbook(self, request, pk=None):
        """Download the configuration data as an Excel file."""
        try:
            create_workbook(pk)
            dm = GridDataManager()
            workbook_name = dm.get_workbook_name(pk)
            excel = open("/tmp/nita-webapp/export/" + workbook_name, "rb")
            return FileResponse(
                excel,
                as_attachment=True,
                filename=workbook_name,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as exc:
            logger.error("Error downloading workbook: %s", exc)
            return Response(
                {"status": "failure", "message": "Error generating Excel file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                "action_id",
                type=int,
                location="path",
                required=True,
                description="A unique integer value identifying the action to trigger.",
            )
        ],
        responses={
            202: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "action_history_id": {"type": "integer"},
                },
            }
        },
    )
    @action(detail=True, methods=["post"], url_path=r"trigger/(?P<action_id>[0-9]+)")
    def trigger(self, request, pk=None, action_id=None):
        """
        Trigger a Jenkins action for this network.

        Communicates with Jenkins using authenticated python/jenkinsapi calls
        with a CSRF crumb (Jenkins rejects anonymous build requests with 403).

        Returns 202 Accepted with the ActionHistory ID immediately.
        Poll GET /api/v1/action-history/{id}/ for status updates.
        """
        from ngcn.views import (
            JENKINS_SERVER_PASS,
            JENKINS_SERVER_URL,
            JENKINS_SERVER_USER,
            _make_jenkins_server,
            updateCampusNetworkStatusOnDB,
        )

        try:
            action_obj = Action.objects.get(pk=action_id)
        except Action.DoesNotExist:
            return Response(
                {"status": "failure", "reason": "Action not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            campus_network = CampusNetwork.objects.get(pk=pk)

            if Workbook.objects.filter(campus_network_id=pk).count() == 0:
                return Response(
                    {
                        "status": "failure",
                        "reason": "No data configured for this network.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            action_url = action_obj.jenkins_url + "-" + campus_network.name
            updateCampusNetworkStatusOnDB(pk, "Triggered " + action_url)

            campus_type = campus_network.campus_type
            workbook_name = create_workbook_from_db(pk)
            configuration_data = create_new_inv(workbook_name)

            if campus_network.dynamic_ansible_workspace:
                build_dir = (
                    "/var/tmp/build/" + campus_type.name + "-" + campus_network.name
                )
            else:
                build_dir = configuration_data["group_vars/all.yaml"]["build_dir"]

            # Trigger the job with authenticated python/jenkinsapi calls (a CSRF
            # crumb is required; Jenkins rejects anonymous build requests with 403).
            from jenkinsapi.jenkins import Jenkins
            from jenkinsapi.utils.crumb_requester import CrumbRequester

            try:
                server = _make_jenkins_server()
                current_build_number = server.get_job_info(action_url)[
                    "nextBuildNumber"
                ]
                crumb = CrumbRequester(
                    baseurl=JENKINS_SERVER_URL,
                    username=JENKINS_SERVER_USER,
                    password=JENKINS_SERVER_PASS,
                )
                Jenkins(
                    JENKINS_SERVER_URL,
                    username=JENKINS_SERVER_USER,
                    password=JENKINS_SERVER_PASS,
                    requester=crumb,
                ).get_job(action_url).invoke(
                    files={"data.json": json.dumps(configuration_data)},
                    build_params={"build_dir": build_dir},
                )
            except Exception as exc:
                logger.error("Jenkins unreachable during trigger on %s: %s", action_url, exc)
                return Response(
                    {"error": "Jenkins service unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            history = ActionHistory(
                action_id=action_obj,
                timestamp=timezone.now(),
                status="Running",
                jenkins_job_build_no=current_build_number,
                category_id=action_obj.action_category,
                campus_network_id=campus_network,
            )
            history.save()

            return Response(
                {"status": "accepted", "action_history_id": history.id},
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as exc:
            logger.error("Error triggering action: %s", exc)
            traceback.print_exc()
            return Response(
                {"status": "failure", "reason": "Internal error triggering action."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "campus_type_id",
                type=int,
                location="query",
                required=False,
                description="Filter by campus type ID.",
            ),
            OpenApiParameter(
                "action_category_id",
                type=int,
                location="query",
                required=False,
                description="Filter by action category ID.",
            ),
        ]
    )
)
class ActionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list and retrieve for Action objects.

    Supports ``?campus_type_id=<id>`` and ``?action_category_id=<id>`` query
    parameters (combinable) to filter actions by network type and/or category.
    """

    queryset = Action.objects.all()
    serializer_class = ActionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        campus_type_id = self.request.query_params.get("campus_type_id")
        if campus_type_id:
            qs = qs.filter(campus_type_id=campus_type_id)
        action_category_id = self.request.query_params.get("action_category_id")
        if action_category_id:
            qs = qs.filter(action_category_id=action_category_id)
        return qs


def _jenkins_progressive_text_generator(job_url, build_no):
    """Generator that polls Jenkins progressive text API and yields SSE events.

    Uses unauthenticated plain HTTP to the internal Jenkins service.

    Yields ``data: <line>\n\n`` for each output line, then one of:
    - ``event: done\ndata: \n\n``    — build finished normally
    - ``event: error\ndata: <msg>\n\n`` — Jenkins unreachable / exception
    - ``event: timeout\ndata: \n\n``  — 30-minute cap reached
    """
    import re

    from ngcn.views import JENKINS_SERVER_URL

    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    base_url = f"{JENKINS_SERVER_URL}/job/{job_url}/{build_no}/logText/progressiveText"
    offset = 0
    max_polls = 1800  # 30 minutes at 1-second intervals
    # How many consecutive 404s to tolerate before giving up.
    # Jenkins keeps the build in queue for a few seconds before the executor
    # picks it up; during that window progressiveText returns 404.
    max_queued_polls = 60
    queued_polls = 0

    for _ in range(max_polls):
        try:
            url = f"{base_url}?start={offset}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                chunk = resp.read().decode("utf-8", errors="replace")
                more_data = resp.headers.get("X-More-Data", "false").lower() == "true"
                new_offset = resp.headers.get("X-Text-Size")
                if new_offset:
                    offset = int(new_offset)
            queued_polls = 0  # reset once build is reachable
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and queued_polls < max_queued_polls:
                # Build is still queued / executor not yet started — wait and retry.
                queued_polls += 1
                time.sleep(1)
                continue
            yield f"event: error\ndata: {exc}\n\n"
            return
        except Exception as exc:
            yield f"event: error\ndata: {exc}\n\n"
            return

        cleaned = ansi_escape.sub("", chunk)
        for line in cleaned.splitlines():
            if line:
                yield f"data: {line}\n\n"

        if not more_data:
            yield "event: done\ndata: \n\n"
            return

        time.sleep(1)

    yield "event: timeout\ndata: \n\n"


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "campus_network_id",
                type=int,
                location="query",
                required=False,
                description="Filter by campus network ID.",
            ),
            OpenApiParameter(
                "action_category_id",
                type=int,
                location="query",
                required=False,
                description="Filter by action category ID.",
            ),
        ]
    )
)
class ActionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list and retrieve for ActionHistory objects, ordered newest-first.

    Supports ``?campus_network_id=<id>`` and ``?action_category_id=<id>`` query
    parameters (combinable) to filter history by network and/or category.
    The ``/console/`` action proxies the Jenkins console log for a given entry.
    """

    queryset = ActionHistory.objects.all().order_by("-timestamp")
    serializer_class = ActionHistorySerializer

    def get_renderers(self):
        """Use SSERenderer for the stream action; default renderers otherwise."""
        if getattr(self, "action", None) == "stream":
            return [SSERenderer()]
        return super().get_renderers()

    def get_queryset(self):
        qs = super().get_queryset()
        campus_network_id = self.request.query_params.get("campus_network_id")
        if campus_network_id:
            qs = qs.filter(campus_network_id=campus_network_id)
        action_category_id = self.request.query_params.get("action_category_id")
        if action_category_id:
            qs = qs.filter(category_id=action_category_id)
        return qs

    @extend_schema(
        responses={
            "200": {"type": "object", "properties": {"console": {"type": "string"}}}
        },
    )
    @action(detail=True, methods=["get"], url_path="console")
    def console(self, request, pk=None):
        """Return the Jenkins console log for this action history entry."""
        import re

        from ngcn.views import _make_jenkins_server

        history = self.get_object()
        job_url = history.action_id.jenkins_url + "-" + history.campus_network_id.name
        server = _make_jenkins_server()
        try:
            output = server.get_build_console_output(
                job_url, history.jenkins_job_build_no
            )
            ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
            return Response({"console": ansi_escape.sub("", output)})
        except Exception:
            return Response(
                {"console": "Build is queued or console output is not yet available."}
            )

    @extend_schema(
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description=(
                    "SSE stream of Jenkins console output. "
                    "Events: data (log line), done (build finished), "
                    "error (Jenkins unreachable), timeout (30-min cap reached)."
                ),
            )
        },
    )
    @action(detail=True, methods=["get"], url_path="stream")
    def stream(self, request, pk=None):
        """Stream Jenkins console output as Server-Sent Events."""
        history = self.get_object()
        job_url = history.action_id.jenkins_url + "-" + history.campus_network_id.name
        build_no = history.jenkins_job_build_no
        response = StreamingHttpResponse(
            _jenkins_progressive_text_generator(job_url, build_no),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
