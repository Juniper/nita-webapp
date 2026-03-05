import pytest
from django.contrib.auth import get_user_model

from ngcn.models import Action
from ngcn.models import ActionCategory
from ngcn.models import ActionProperty
from ngcn.models import CampusNetwork
from ngcn.models import CampusType


@pytest.fixture
def user(db):
    model = get_user_model()
    return model.objects.create_user(username="tester", password="secret")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def campus_type(db):
    return CampusType.objects.create(
        name="sample_type",
        description="Sample type",
        app_zip_name="sample.zip",
    )


@pytest.fixture
def action_category(db):
    return ActionCategory.objects.create(category_name="TEST")


@pytest.fixture
def action(db, campus_type, action_category):
    prop = ActionProperty.objects.create(
        shell_command="echo ok",
        output_path="/tmp/out",
        custom_workspace="",
    )
    return Action.objects.create(
        action_name="run_test",
        jenkins_url="job-test",
        action_category=action_category,
        campus_type_id=campus_type,
        action_property=prop,
    )


@pytest.fixture
def campus_network(db, campus_type):
    return CampusNetwork.objects.create(
        name="campus_one",
        status="Initialized",
        description="Campus one",
        host_file="hosts data",
        campus_type=campus_type,
    )
