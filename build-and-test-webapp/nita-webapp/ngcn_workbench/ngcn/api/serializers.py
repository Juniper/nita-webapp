# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""DRF ModelSerializer classes for the NITA Webapp REST API.

Each model in ``ngcn.models`` has a corresponding serializer here.  Where
useful, read-only computed / nested fields are added so that API consumers
get enough context without having to make extra requests:

* ``CampusTypeSerializer``     — network type fields
* ``ActionSerializer``         — includes nested ``action_property`` and
  ``action_category``
* ``CampusNetworkSerializer``  — adds a ``campus_type_name`` string field
* ``ActionHistorySerializer``  — adds ``action_name``, ``category_name``,
  ``network_name`` string fields
* ``WorkbookSerializer``       — includes nested ``WorksheetsSerializer``
  entries; the ``data`` column is JSON-decoded on read
"""

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ngcn.models import (
    Action,
    ActionCategory,
    ActionHistory,
    ActionProperty,
    CampusNetwork,
    CampusType,
    LifecycleRun,
    Team,
    Workbook,
    Worksheets,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the admin user-management API.

    ``role`` and ``is_active`` are writable (admin-only via the viewset);
    ``username`` and ``email`` are read-only here.
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active"]
        read_only_fields = ["id", "username", "email"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for admin-driven user creation.

    Accepts a writable ``username``, ``email``, ``role``, and a write-only
    ``password`` validated with Django's configured password validators. The
    password is never echoed back — the response uses the read representation.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "role", "is_active"]
        read_only_fields = ["id", "is_active"]
        extra_kwargs = {"email": {"required": False}}

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SetPasswordSerializer(serializers.Serializer):
    """Serializer for an admin setting/resetting a user's password.

    Carries a single write-only ``password`` validated with Django's configured
    password validators. It is never echoed back in any response.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_password(self, value):
        validate_password(value)
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for self-service registration.

    Forces ``role=user`` regardless of any supplied value and validates the
    password with Django's configured password validators.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "role"]
        read_only_fields = ["id", "role"]
        extra_kwargs = {"email": {"required": False}}

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        validated_data.pop("role", None)
        password = validated_data.pop("password")
        user = User(role=User.ROLE_USER, **validated_data)
        user.set_password(password)
        user.save()
        return user


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team. ``members`` is a list of user ids."""

    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "description", "created_by", "members"]


class ActionCategorySerializer(serializers.ModelSerializer):
    """Serializer for ActionCategory (build / test / deploy labels)."""

    class Meta:
        model = ActionCategory
        fields = "__all__"


class CampusTypeSerializer(serializers.ModelSerializer):
    """Serializer for CampusType."""

    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

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
    """Serializer for CampusNetwork.  Adds ``campus_type_name`` for convenience.

    ``owner`` is read-only (assigned automatically to the creating user);
    ``team`` is writable so an owner/admin can share the network with a team.
    ``owner_username`` and ``team_name`` are read-only display helpers.
    """

    campus_type_name = serializers.CharField(source="campus_type.name", read_only=True)
    owner_username = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.STR)
    def get_owner_username(self, obj):
        return obj.owner.username if obj.owner_id else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_team_name(self, obj):
        return obj.team.name if obj.team_id else None

    def validate_team(self, value):
        """A non-privileged owner may only share into a team they belong to.

        ``power_user`` and ``admin`` may assign any network to any team;
        unassigning (``team=None``) is always allowed.
        """
        if value is None:
            return value
        user = getattr(self.context.get("request"), "user", None)
        role = getattr(user, "role", None)
        if role in (User.ROLE_POWER_USER, User.ROLE_ADMIN):
            return value
        if user is None or not value.members.filter(pk=user.pk).exists():
            raise serializers.ValidationError(
                "You can only assign a network to a team you are a member of."
            )
        return value

    class Meta:
        model = CampusNetwork
        fields = "__all__"
        read_only_fields = ["owner"]


class ActionHistorySerializer(serializers.ModelSerializer):
    """Serializer for ActionHistory.

    Adds ``action_name``, ``category_name``, and ``network_name`` as read-only
    string fields so consumers can display context without extra look-ups.
    ``jenkins_job_name`` exposes the Jenkins job for the run
    (``{action.jenkins_url}-{network_name}``) so clients can build a link to the
    build result.
    """

    action_name = serializers.CharField(source="action_id.action_name", read_only=True)
    category_name = serializers.CharField(
        source="category_id.category_name", read_only=True
    )
    network_name = serializers.CharField(
        source="campus_network_id.name", read_only=True
    )
    jenkins_job_name = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.STR)
    def get_jenkins_job_name(self, obj):
        """Return the Jenkins job name for this run."""
        return f"{obj.action_id.jenkins_url}-{obj.campus_network_id.name}"

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

    @extend_schema_field(
        field={"oneOf": [{"type": "object"}, {"type": "array"}, {"type": "string"}]}
    )
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


class LifecycleRunSerializer(serializers.ModelSerializer):
    """Serializer for a network lifecycle Jenkins job run (history entry)."""

    class Meta:
        model = LifecycleRun
        fields = [
            "id",
            "kind",
            "subject",
            "job_name",
            "build_no",
            "timestamp",
            "status",
        ]
