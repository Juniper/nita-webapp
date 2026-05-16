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

import json
import logging
import traceback

from django.http import FileResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

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


class ActionCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list and retrieve for ActionCategory objects."""

    queryset = ActionCategory.objects.all()
    serializer_class = ActionCategorySerializer


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
            200: {
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "name": {"type": "string"},
                },
            }
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


class CampusNetworkViewSet(viewsets.ModelViewSet):
    """Full CRUD for CampusNetwork objects, plus workbook management and action triggering.

    Standard CRUD
        ``GET /api/v1/networks/``                — paginated list
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

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"up_file": {"type": "string", "format": "binary"}},
            }
        },
        responses={200: WorkbookSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="workbook/upload",
    )
    def upload_workbook(self, request, pk=None):
        """Upload an Excel workbook to populate configuration data for this network."""
        up_file = request.FILES.get("up_file")
        if not up_file:
            return Response(
                {"status": "failure", "message": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = parse_workbook(up_file, pk)
            if result != "invalid_host":
                dm = GridDataManager()
                sheets = dm.get_sheets_by_campus_network(pk)
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

    @extend_schema(responses={200: WorkbookSerializer})
    @action(detail=True, methods=["get"], url_path="workbook")
    def get_workbook(self, request, pk=None):
        """Return the current configuration grid data for this network."""
        try:
            dm = GridDataManager()
            sheets = dm.get_sheets_by_campus_network(pk)
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
        """Save updated configuration grid data for this network."""
        try:
            import collections

            grid_list = json.JSONDecoder(
                object_pairs_hook=collections.OrderedDict
            ).decode(request.body.decode("utf-8"))
            dm = GridDataManager()
            sheets = dm.get_sheets_by_campus_network(pk)
            for grid in grid_list["data"]:
                for sheet in sheets:
                    if sheet["name"] == grid["name"]:
                        sheet[grid["name"]] = grid[grid["name"]]
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

        Returns 202 Accepted with the ActionHistory ID immediately.
        Poll GET /api/v1/action-history/{id}/ for status updates.
        """
        from jenkinsapi.jenkins import Jenkins
        from jenkinsapi.utils.crumb_requester import CrumbRequester

        from ngcn.views import (
            JENKINS_SERVER_PASS,
            JENKINS_SERVER_URL,
            JENKINS_SERVER_USER,
            _make_jenkins_server,
            updateCampusNetworkStatusOnDB,
        )

        try:
            action_obj = Action.objects.get(pk=action_id)
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

            server = _make_jenkins_server()
            current_build_number = server.get_job_info(action_url)["nextBuildNumber"]
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
        except Action.DoesNotExist:
            return Response(
                {"status": "failure", "reason": "Action not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error("Error triggering action: %s", exc)
            traceback.print_exc()
            return Response(
                {"status": "failure", "reason": "Internal error triggering action."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ActionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list and retrieve for Action objects.

    Supports ``?campus_type_id=<id>`` query parameter to filter actions
    that belong to a specific network type.
    """

    queryset = Action.objects.all()
    serializer_class = ActionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        campus_type_id = self.request.query_params.get("campus_type_id")
        if campus_type_id:
            qs = qs.filter(campus_type_id=campus_type_id)
        return qs


class ActionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list and retrieve for ActionHistory objects, ordered newest-first.

    Supports ``?campus_network_id=<id>`` query parameter to filter history
    for a specific network.  The ``/console/`` action proxies the Jenkins
    console log for a given history entry.
    """

    queryset = ActionHistory.objects.all().order_by("-timestamp")
    serializer_class = ActionHistorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        campus_network_id = self.request.query_params.get("campus_network_id")
        if campus_network_id:
            qs = qs.filter(campus_network_id=campus_network_id)
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
