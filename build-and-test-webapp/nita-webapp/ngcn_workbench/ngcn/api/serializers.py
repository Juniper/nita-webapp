# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""DRF ModelSerializer classes for the NITA Webapp REST API.

Each model in ``ngcn.models`` has a corresponding serializer here.  Where
useful, read-only computed / nested fields are added so that API consumers
get enough context without having to make extra requests:

* ``CampusTypeSerializer``     — includes nested ``roles`` and ``resources``
* ``ActionSerializer``         — includes nested ``action_property`` and
  ``action_category``
* ``CampusNetworkSerializer``  — adds a ``campus_type_name`` string field
* ``ActionHistorySerializer``  — adds ``action_name``, ``category_name``,
  ``network_name`` string fields
* ``WorkbookSerializer``       — includes nested ``WorksheetsSerializer``
  entries; the ``data`` column is JSON-decoded on read
"""

import json

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ngcn.models import (
    Action,
    ActionCategory,
    ActionHistory,
    ActionProperty,
    CampusNetwork,
    CampusType,
    Resource,
    Role,
    Workbook,
    Worksheets,
)


class ActionCategorySerializer(serializers.ModelSerializer):
    """Serializer for ActionCategory (build / test / deploy labels)."""
    class Meta:
        model = ActionCategory
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role (Ansible role assigned to a network type)."""
    class Meta:
        model = Role
        fields = "__all__"


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for Resource (resource allocated to a network type)."""
    class Meta:
        model = Resource
        fields = "__all__"


class CampusTypeSerializer(serializers.ModelSerializer):
    """Serializer for CampusType.  Includes nested roles and resources lists."""
    roles = RoleSerializer(many=True, read_only=True)
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta:
        model = CampusType
        fields = "__all__"


class ActionPropertySerializer(serializers.ModelSerializer):
    """Serializer for ActionProperty (shell command + workspace configuration)."""
    class Meta:
        model = ActionProperty
        fields = "__all__"


class ActionSerializer(serializers.ModelSerializer):
    """Serializer for Action.  Nests ActionProperty and ActionCategory inline."""
    action_property = ActionPropertySerializer(read_only=True)
    action_category = ActionCategorySerializer(read_only=True)

    class Meta:
        model = Action
        fields = "__all__"


class CampusNetworkSerializer(serializers.ModelSerializer):
    """Serializer for CampusNetwork.  Adds ``campus_type_name`` for convenience."""
    campus_type_name = serializers.CharField(
        source="campus_type.name", read_only=True
    )

    class Meta:
        model = CampusNetwork
        fields = "__all__"


class ActionHistorySerializer(serializers.ModelSerializer):
    """Serializer for ActionHistory.

    Adds ``action_name``, ``category_name``, and ``network_name`` as read-only
    string fields so consumers can display context without extra look-ups.
    """
    action_name = serializers.CharField(
        source="action_id.action_name", read_only=True
    )
    category_name = serializers.CharField(
        source="category_id.category_name", read_only=True
    )
    network_name = serializers.CharField(
        source="campus_network_id.name", read_only=True
    )

    class Meta:
        model = ActionHistory
        fields = "__all__"


class WorksheetsSerializer(serializers.ModelSerializer):
    """Serializer for a single worksheet inside a Workbook.

    The ``data`` column is stored as a JSON string in the database; this
    serializer transparently parses it back to a Python object on read.
    """
    data = serializers.SerializerMethodField()

    class Meta:
        model = Worksheets
        fields = ["id", "name", "data"]

    @extend_schema_field(field={"oneOf": [{"type": "object"}, {"type": "array"}, {"type": "string"}]})
    def get_data(self, obj):
        try:
            return json.loads(obj.data) if isinstance(obj.data, str) else obj.data
        except (json.JSONDecodeError, TypeError):
            return obj.data


class WorkbookSerializer(serializers.ModelSerializer):
    """Serializer for a Workbook together with all of its Worksheets."""
    sheets = WorksheetsSerializer(source="worksheets_set", many=True, read_only=True)

    class Meta:
        model = Workbook
        fields = ["id", "name", "campus_network_id", "sheets"]
