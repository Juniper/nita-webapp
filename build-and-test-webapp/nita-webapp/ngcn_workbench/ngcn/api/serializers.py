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
    class Meta:
        model = ActionCategory
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = "__all__"


class CampusTypeSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta:
        model = CampusType
        fields = "__all__"


class ActionPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionProperty
        fields = "__all__"


class ActionSerializer(serializers.ModelSerializer):
    action_property = ActionPropertySerializer(read_only=True)
    action_category = ActionCategorySerializer(read_only=True)

    class Meta:
        model = Action
        fields = "__all__"


class CampusNetworkSerializer(serializers.ModelSerializer):
    campus_type_name = serializers.CharField(
        source="campus_type.name", read_only=True
    )

    class Meta:
        model = CampusNetwork
        fields = "__all__"


class ActionHistorySerializer(serializers.ModelSerializer):
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
    sheets = WorksheetsSerializer(source="worksheets_set", many=True, read_only=True)

    class Meta:
        model = Workbook
        fields = ["id", "name", "campus_network_id", "sheets"]
