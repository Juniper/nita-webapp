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
import traceback

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db.models import Q
from django.http import FileResponse
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
from rest_framework.views import APIView


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
    Team,
    User,
    Workbook,
)
from ngcn.networktypeparser import NetworkTypeParser
from ngcn.workbook import (
    GridDataManager,
    create_new_inv,
    create_workbook,
    create_workbook_from_db,
    parse_workbook,
)

from .permissions import (
    IsAdminOrManagesNonAdminUser,
    IsAdminRole,
    IsOwnerOrTeamMemberOrAdmin,
    IsPowerUserOrAdmin,
)
from .serializers import (
    ActionCategorySerializer,
    ActionHistorySerializer,
    ActionSerializer,
    CampusNetworkSerializer,
    CampusTypeSerializer,
    LifecycleRunSerializer,
    SetPasswordSerializer,
    TeamSerializer,
    UserCreateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
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
                "role": {"type": "string"},
                "teams": {"type": "array", "items": {"type": "integer"}},
            },
        }
    },
    summary="Return the currently authenticated user's info",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return the authenticated user's id, username, is_superuser, role, teams."""
    user = request.user
    return Response(
        {
            "id": user.pk,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "role": getattr(user, "role", None),
            "teams": list(user.teams.values_list("id", flat=True)),
        }
    )


@extend_schema(
    request=UserRegistrationSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "role": {"type": "string"},
            },
        },
        400: OpenApiResponse(description="Validation error (duplicate/weak input)"),
        403: OpenApiResponse(description="Self-registration is disabled"),
    },
    auth=[],
    summary="Register a new account (defaults to role=user)",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """Self-service registration. New accounts always get ``role=user``.

    Gated by the ``SELF_REGISTRATION_ENABLED`` setting
    (env ``NITA_SELF_REGISTRATION_ENABLED``, default enabled). When disabled,
    returns 403 and directs the requester to an administrator.
    """
    from django.conf import settings

    if not getattr(settings, "SELF_REGISTRATION_ENABLED", True):
        return Response(
            {"detail": "Self-registration is disabled; contact an administrator."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        {"id": user.pk, "username": user.username, "role": user.role},
        status=status.HTTP_201_CREATED,
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
    """Network types. Create via POST /upload/ (zip); delete via DELETE /{id}/.

    Read (list/retrieve) is open to any authenticated user. Upload and delete are
    restricted to ``power_user``/``admin`` regardless of who created the type.
    Deletion is refused with ``409`` while any network still references the type,
    because ``CampusNetwork.campus_type`` cascades.
    """

    serializer_class = CampusTypeSerializer

    def get_permissions(self):
        if self.action in ("upload", "destroy"):
            return [IsAuthenticated(), IsPowerUserOrAdmin()]
        return [IsAuthenticated()]

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Network type deleted. No content."),
            409: OpenApiResponse(
                description="Network type is still referenced by one or more networks."
            ),
        },
        summary="Delete a network type (power user or admin; refused while in use)",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a network type unless networks still reference it."""
        instance = self.get_object()
        blocking = list(
            CampusNetwork.objects.filter(campus_type=instance).values_list(
                "name", flat=True
            )
        )
        if blocking:
            return Response(
                {
                    "detail": (
                        "Network type is still used by one or more networks. "
                        "Delete them before deleting this type."
                    ),
                    "networks": blocking,
                },
                status=status.HTTP_409_CONFLICT,
            )
        type_id, type_name = instance.id, instance.name
        response = super().destroy(request, *args, **kwargs)
        if getattr(request.user, "role", None) == User.ROLE_POWER_USER:
            logger.info(
                "Power user id=%s deleted network type id=%s name=%s",
                request.user.id,
                type_id,
                type_name,
            )
        return response

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
        # Record the creating user on a freshly registered network type.
        if http_status == status.HTTP_200_OK and data.get("id") is not None:
            CampusType.objects.filter(pk=data["id"]).update(created_by=request.user)
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

    def get_permissions(self):
        """Detail actions enforce owner/team-member/admin object permissions."""
        if self.action in ("list", "create"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrTeamMemberOrAdmin()]

    def get_queryset(self):
        qs = CampusNetwork.objects.all()
        user = self.request.user
        if getattr(user, "role", None) not in (User.ROLE_ADMIN, User.ROLE_POWER_USER):
            qs = qs.filter(Q(owner=user) | Q(team__members=user)).distinct()
        campus_type_id = self.request.query_params.get("campus_type_id")
        if campus_type_id:
            qs = qs.filter(campus_type_id=campus_type_id)
        return qs

    def create(self, request, *args, **kwargs):
        """Create a network, triggering the Jenkins build job without blocking.

        Persists the network row immediately with status ``Initializing``,
        triggers the ``network_template_mgr`` job (``operation=create``) via the
        shared invoke helper, and returns ``201`` with the network data plus
        ``job_name`` and ``build_no`` so the client can open a live console
        stream. Returns ``503`` (no row persisted) if Jenkins is unreachable.
        """
        from ngcn import jenkins_jobs
        from ngcn.utils import ServerProperties

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        campus_type = validated["campus_type"]
        network_name = validated["name"]
        host_file = validated.get("host_file", "")
        network_desc = validated.get("description", "")

        src = ServerProperties.getWorkspaceLocation() + "/" + campus_type.app_zip_name
        action_url = "network_template_mgr"
        build_params = {
            "operation": "create",
            "src": src,
            "network_name": network_name,
            "hosts": host_file,
            "network_desc": network_desc,
        }

        try:
            build_no = jenkins_jobs.invoke_job(action_url, build_params=build_params)
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

        serializer.save(status="Initializing", owner=request.user)
        headers = self.get_success_headers(serializer.data)
        data = dict(serializer.data)
        data["job_name"] = action_url
        data["build_no"] = build_no
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """Delete a network, triggering the Jenkins build job without blocking.

        Triggers the ``network_template_mgr`` job (``operation=delete``) via the
        shared invoke helper, removes the database row once the build has been
        queued, and returns ``202`` with ``job_name`` and ``build_no`` so the
        client can open a live console stream. If Jenkins is unreachable the row
        is left in place and ``503`` is returned.
        """
        from ngcn import jenkins_jobs
        from ngcn.utils import ServerProperties

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

        try:
            build_no = jenkins_jobs.invoke_job(action_url, build_params=build_params)
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

        self.perform_destroy(instance)
        return Response(
            {"name": network_name, "job_name": action_url, "build_no": build_no},
            status=status.HTTP_202_ACCEPTED,
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
                    collections.OrderedDict(zip(headers, row)) for row in new_rows
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
        from ngcn.workbook import updateCampusNetworkStatusOnDB

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

            build_dir = "/var/tmp/build/" + campus_type.name + "-" + campus_network.name

            # Trigger the job through the shared authenticated invoke helper (a
            # CSRF crumb is required; Jenkins rejects anonymous build requests
            # with 403).
            from ngcn import jenkins_jobs

            try:
                current_build_number = jenkins_jobs.invoke_job(
                    action_url,
                    build_params={"build_dir": build_dir},
                    files={"data.json": json.dumps(configuration_data)},
                )
            except Exception as exc:
                logger.error(
                    "Jenkins unreachable during trigger on %s: %s", action_url, exc
                )
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

        from ngcn.jenkins_config import _make_jenkins_server

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
        from ngcn import jenkins_jobs

        history = self.get_object()
        job_url = history.action_id.jenkins_url + "-" + history.campus_network_id.name
        build_no = history.jenkins_job_build_no
        return jenkins_jobs.stream_response(job_url, build_no)

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "available": {"type": "boolean"},
                    "total": {"type": "integer"},
                    "passed": {"type": "integer"},
                    "failed": {"type": "integer"},
                    "skipped": {"type": "integer"},
                    "pass_percentage": {"type": "number"},
                },
            }
        },
    )
    @action(detail=True, methods=["get"], url_path="robot-summary")
    def robot_summary(self, request, pk=None):
        """Return the Robot Framework result totals for this run's Jenkins build.

        Relays the Jenkins Robot Framework plugin summary. Returns
        ``{"available": false}`` when the build has no Robot results.
        """
        from ngcn import jenkins_jobs

        history = self.get_object()
        job_url = history.action_id.jenkins_url + "-" + history.campus_network_id.name
        summary = jenkins_jobs.robot_summary(job_url, history.jenkins_job_build_no)
        if summary is None:
            return Response({"available": False})
        return Response({"available": True, **summary})


class JenkinsJobStreamView(APIView):
    """Generic authenticated SSE stream of any Jenkins job build's console.

    ``GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/``

    Used by the network lifecycle flows (create/delete/network-type load) which
    only have a ``job_name`` + ``build_no`` handle rather than an
    ``ActionHistory`` row. Requires authentication; unauthenticated requests are
    rejected with ``403`` (consistent with the action-history stream).
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [SSERenderer]

    @extend_schema(
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description=(
                    "SSE stream of Jenkins console output for the given job and "
                    "build. Events: data (log line), done (build finished), "
                    "error (Jenkins unreachable), timeout (30-min cap reached)."
                ),
            )
        },
    )
    def get(self, request, job_name, build_no):
        """Stream the console output for ``job_name`` build ``build_no``."""
        from ngcn import jenkins_jobs

        return jenkins_jobs.stream_response(job_name, int(build_no))


class LifecycleRunViewSet(viewsets.ViewSet):
    """Network lifecycle job history, derived live from Jenkins build records.

    Instead of reading a local table, this queries the relevant Jenkins jobs
    directly so the history reflects every run (including those triggered
    outside the React UI) and is not lost when the database is reset.

    ``GET /api/v1/lifecycle-runs/?kind=network_create``
        List runs of a given kind (or all kinds when ``kind`` is omitted),
        newest-first. Each entry has ``id`` (``"<job>#<build>"``), ``kind``,
        ``subject``, ``job_name``, ``build_no``, ``timestamp`` and ``status``.

    ``GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>``
        Return the historical Jenkins console log for a single build.
    """

    # Map each lifecycle kind to its Jenkins job and the build "operation" param
    # value that identifies that kind within the (shared) job.
    _KIND_JOB = {
        "network_create": ("network_template_mgr", "create"),
        "network_delete": ("network_template_mgr", "delete"),
        "network_type_load": ("network_type_validator", "add"),
    }
    # Maximum number of recent builds per job to inspect.
    _MAX_BUILDS = 50

    @staticmethod
    def _status_from_result(result):
        """Translate a Jenkins build result into a display status string."""
        if result is None:
            return "Running"
        return {
            "SUCCESS": "Success",
            "FAILURE": "Failed",
            "ABORTED": "Aborted",
            "UNSTABLE": "Unstable",
        }.get(result, str(result).title())

    @staticmethod
    def _build_params(build_info):
        """Flatten a Jenkins build's parameter actions into a name/value dict."""
        params = {}
        for action_obj in build_info.get("actions") or []:
            for param in (action_obj or {}).get("parameters") or []:
                params[param.get("name")] = param.get("value")
        return params

    def _runs_for_kind(self, server, kind):
        """Return synthesized history entries for a single lifecycle kind."""
        import os
        from datetime import UTC, datetime

        job_name, operation = self._KIND_JOB[kind]
        try:
            info = server.get_job_info(job_name)
        except Exception:
            logger.warning("Jenkins job %s unavailable for lifecycle history", job_name)
            return []

        runs = []
        for build in (info.get("builds") or [])[: self._MAX_BUILDS]:
            number = build["number"]
            try:
                build_info = server.get_build_info(job_name, number)
            except Exception:
                logger.warning(
                    "Skipping unreadable build %s#%s in lifecycle history",
                    job_name,
                    number,
                )
                continue
            params = self._build_params(build_info)
            if (params.get("operation") or "").lower() != operation:
                continue

            if kind == "network_type_load":
                raw = params.get("file_name") or params.get("network_name") or ""
                subject = os.path.basename(str(raw))
                if subject.endswith(".zip"):
                    subject = subject[:-4]
            else:
                subject = params.get("network_name") or ""

            timestamp = datetime.fromtimestamp(
                build_info.get("timestamp", 0) / 1000, tz=UTC
            ).isoformat()
            runs.append(
                {
                    "id": f"{job_name}#{number}",
                    "kind": kind,
                    "subject": subject,
                    "job_name": job_name,
                    "build_no": number,
                    "timestamp": timestamp,
                    "status": self._status_from_result(build_info.get("result")),
                }
            )
        return runs

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "kind",
                type=str,
                location="query",
                required=False,
                description=(
                    "Filter by lifecycle kind: network_create, network_delete, "
                    "or network_type_load."
                ),
            ),
        ],
        responses={"200": LifecycleRunSerializer(many=True)},
    )
    def list(self, request):
        """List lifecycle job runs derived from Jenkins, newest-first."""
        from ngcn.jenkins_config import _make_jenkins_server

        kind = request.query_params.get("kind")
        kinds = [kind] if kind in self._KIND_JOB else list(self._KIND_JOB)

        try:
            server = _make_jenkins_server()
        except Exception:
            logger.warning("Jenkins unreachable while loading lifecycle history")
            return Response([])

        runs = []
        for k in kinds:
            runs.extend(self._runs_for_kind(server, k))
        runs.sort(key=lambda r: r["timestamp"], reverse=True)
        return Response(runs)

    @extend_schema(
        parameters=[
            OpenApiParameter("job_name", type=str, location="query", required=True),
            OpenApiParameter("build_no", type=int, location="query", required=True),
        ],
        responses={
            "200": {"type": "object", "properties": {"console": {"type": "string"}}}
        },
    )
    @action(detail=False, methods=["get"], url_path="console")
    def console(self, request):
        """Return the historical Jenkins console log for a single build."""
        import re

        from ngcn.jenkins_config import _make_jenkins_server

        job_name = request.query_params.get("job_name", "")
        build_no = request.query_params.get("build_no", "")
        if not re.fullmatch(r"[A-Za-z0-9_.\-]+", job_name) or not build_no.isdigit():
            return Response(
                {"console": "Invalid job name or build number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        server = _make_jenkins_server()
        try:
            output = server.get_build_console_output(job_name, int(build_no))
            ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
            return Response({"console": ansi_escape.sub("", output)})
        except Exception:
            return Response(
                {"console": "Build is queued or console output is not yet available."}
            )


class TeamViewSet(viewsets.ModelViewSet):
    """Team management.

    ``power_user`` and ``admin`` may create teams; a ``power_user`` manages only
    the teams they created while an ``admin`` manages all teams. Regular ``user``
    accounts have no access to this resource (403 on list).
    """

    serializer_class = TeamSerializer

    def get_permissions(self):
        if self.action == "mine":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsPowerUserOrAdmin()]

    def get_queryset(self):
        # Power users and admins both see and manage every team.
        return Team.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                },
            }
        },
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """Teams the requesting user is a member of (``id`` + ``name``).

        Available to any authenticated user (including ``role=user``) so an owner
        can pick a team to share a network with. Scoped strictly to the caller's
        own memberships; the full team list stays ``power_user``/``admin`` only.
        """
        teams = request.user.teams.order_by("name").values("id", "name")
        return Response(list(teams), status=status.HTTP_200_OK)

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"user_id": {"type": "integer"}},
                "required": ["user_id"],
            }
        },
        responses={
            200: TeamSerializer,
            400: OpenApiResponse(description="Missing or invalid user_id"),
        },
    )
    @action(detail=True, methods=["post"], url_path="members")
    def add_member(self, request, pk=None):
        """Add a user to this team. Body: ``{"user_id": <id>}``."""
        team = self.get_object()
        user_id = request.data.get("user_id")
        try:
            member = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Invalid user_id."}, status=status.HTTP_400_BAD_REQUEST
            )
        team.members.add(member)
        return Response(TeamSerializer(team).data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={204: OpenApiResponse(description="Member removed. No content.")}
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"members/(?P<user_id>[0-9]+)",
    )
    def remove_member(self, request, pk=None, user_id=None):
        """Remove a user from this team."""
        team = self.get_object()
        try:
            member = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid user_id."}, status=status.HTTP_400_BAD_REQUEST
            )
        team.members.remove(member)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Admin-only user management (create, list, retrieve, role/status update, delete).

    Creation accepts a username, email, role, and an initial password. Deletion
    is PROTECT-guarded: a user who still owns networks or network types cannot be
    deleted until an admin transfers those resources via
    ``POST /api/v1/users/{id}/transfer/``. Operations that would leave zero active
    administrators (demote, deactivate, or delete the last active admin) are
    rejected with ``400``.
    """

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_permissions(self):
        """Admin manages every user. A power_user (junior admin) may view/list,
        reset passwords, deactivate, and change roles (capped below admin) for
        **non-admin** users. Create, delete, and transfer stay admin-only.
        """
        if self.action in ("list", "directory"):
            return [IsAuthenticated(), IsPowerUserOrAdmin()]
        if self.action in ("retrieve", "set_password", "update", "partial_update"):
            return [IsAuthenticated(), IsAdminOrManagesNonAdminUser()]
        return [IsAuthenticated(), IsAdminRole()]

    def get_queryset(self):
        """Power users see the non-admin user list; admins see everyone."""
        qs = User.objects.all().order_by("id")
        if (
            self.action == "list"
            and getattr(self.request.user, "role", None) == User.ROLE_POWER_USER
        ):
            qs = qs.exclude(role=User.ROLE_ADMIN)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """Create a user, returning the read representation (no password echoed)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @staticmethod
    def _would_remove_last_active_admin(
        target, *, new_role=None, new_is_active=None, deleting=False
    ):
        """Return True if the change would leave zero active administrators.

        An active administrator is a user with ``role=admin`` AND
        ``is_active=True``. The guard only fires when ``target`` is currently the
        sole active admin and the operation would drop them from that set.
        """
        if not (target.role == User.ROLE_ADMIN and target.is_active):
            return False
        active_admins = User.objects.filter(
            role=User.ROLE_ADMIN, is_active=True
        ).count()
        if active_admins > 1:
            return False
        if deleting:
            return True
        if new_role is not None and new_role != User.ROLE_ADMIN:
            return True
        if new_is_active is not None and not new_is_active:
            return True
        return False

    def update(self, request, *args, **kwargs):
        """Update a user, blocking changes that would remove the last active admin."""
        target = self.get_object()
        new_role = request.data.get("role")
        new_is_active = request.data.get("is_active")
        if new_is_active is not None and isinstance(new_is_active, str):
            new_is_active = new_is_active.lower() not in ("false", "0", "")
        # A power_user (junior admin) may never grant the admin role.
        if (
            getattr(request.user, "role", None) == User.ROLE_POWER_USER
            and new_role == User.ROLE_ADMIN
        ):
            return Response(
                {"detail": "Power users cannot grant the admin role."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self._would_remove_last_active_admin(
            target, new_role=new_role, new_is_active=new_is_active
        ):
            return Response(
                {"detail": "Cannot remove the last administrator."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=SetPasswordSerializer,
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}}},
            400: OpenApiResponse(description="Password validation error"),
        },
        summary="Set (reset) a user's password (admin any user; power user any non-admin)",
    )
    @action(detail=True, methods=["post"], url_path="set_password")
    def set_password(self, request, pk=None):
        """Set a validated password on the target user (may be the caller)."""
        target = self.get_object()
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target.set_password(serializer.validated_data["password"])
        target.save(update_fields=["password"])
        if getattr(request.user, "role", None) == User.ROLE_POWER_USER:
            logger.info(
                "Power user id=%s reset password for user id=%s",
                request.user.id,
                target.id,
            )
        return Response({"status": "password set"}, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                    },
                },
            }
        },
        summary="Minimal id+username roster for member selection",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="directory",
    )
    def directory(self, request):
        """Return an id+username roster for power_user/admin (e.g. team member pickers)."""
        roster = User.objects.order_by("username").values("id", "username")
        return Response(list(roster))

    def destroy(self, request, *args, **kwargs):
        """Delete a user, unless they are the caller or still own resources."""
        target = self.get_object()
        if target == request.user:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if self._would_remove_last_active_admin(target, deleting=True):
            return Response(
                {"detail": "Cannot remove the last administrator."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        owned_networks = list(
            CampusNetwork.objects.filter(owner=target).values_list("name", flat=True)
        )
        owned_types = list(
            CampusType.objects.filter(created_by=target).values_list("name", flat=True)
        )
        if owned_networks or owned_types:
            return Response(
                {
                    "detail": (
                        "User still owns resources. Transfer them before deletion."
                    ),
                    "networks": owned_networks,
                    "types": owned_types,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "networks_to": {"type": "integer"},
                    "types_to": {"type": "integer"},
                },
            }
        },
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}}},
            400: OpenApiResponse(description="Invalid recipient user id"),
        },
    )
    @action(detail=True, methods=["post"], url_path="transfer")
    def transfer(self, request, pk=None):
        """Reassign the target user's owned networks and/or created types.

        Body may contain ``networks_to`` and/or ``types_to`` (recipient user
        ids). Both reassignments run in a single transaction.
        """
        from django.db import transaction

        target = self.get_object()
        networks_to = request.data.get("networks_to")
        types_to = request.data.get("types_to")

        def _resolve(user_id):
            try:
                return User.objects.get(pk=user_id)
            except (User.DoesNotExist, ValueError, TypeError):
                return None

        net_recipient = None
        type_recipient = None
        if networks_to is not None:
            net_recipient = _resolve(networks_to)
            if net_recipient is None:
                return Response(
                    {"detail": "Invalid networks_to user id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if types_to is not None:
            type_recipient = _resolve(types_to)
            if type_recipient is None:
                return Response(
                    {"detail": "Invalid types_to user id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            if net_recipient is not None:
                CampusNetwork.objects.filter(owner=target).update(owner=net_recipient)
            if type_recipient is not None:
                CampusType.objects.filter(created_by=target).update(
                    created_by=type_recipient
                )
        return Response({"status": "transferred"}, status=status.HTTP_200_OK)
