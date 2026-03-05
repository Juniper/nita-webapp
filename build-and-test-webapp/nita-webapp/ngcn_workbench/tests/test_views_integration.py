import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse
from django.urls import reverse

from ngcn.models import ActionHistory
from ngcn.models import CampusNetwork
from ngcn.models import CampusType


@pytest.mark.django_db
def test_get_tree_data_returns_network_type_and_network(
    client, campus_type, campus_network
):
    response = client.get(reverse("treepanedata"))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2

    type_node = next(node for node in payload if node["id"] == "campus_type")
    network_node = next(node for node in payload if node["id"] == "campus_network")

    assert any(
        child["id"] == f"campustype_{campus_type.id}" for child in type_node["children"]
    )
    assert any(
        child["id"] == f"campusnetwork_{campus_network.id}"
        for child in network_node["children"]
    )


@pytest.mark.django_db
def test_add_campus_type_view_uses_parser_and_storage(auth_client, monkeypatch):
    from ngcn import views

    parser_called_with = {}

    class FakeParser:
        def parseProjectFile(self, file_name):
            parser_called_with["file_name"] = file_name
            return JsonResponse({"result": "success"})

    monkeypatch.setattr(views, "NetworkTypeParser", FakeParser)
    monkeypatch.setattr(views.default_storage, "exists", lambda _name: False)
    monkeypatch.setattr(views.default_storage, "save", lambda name, _file: name)
    monkeypatch.setattr(views.default_storage, "delete", lambda _name: None)

    response = auth_client.post(
        reverse("campustypeadd"),
        data={"app_zip_file": SimpleUploadedFile("new_type.zip", b"zip-content")},
    )

    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    assert parser_called_with["file_name"] == "new_type.zip"


@pytest.mark.django_db
def test_trigger_action_returns_failure_when_no_workbook(
    auth_client, action, campus_network
):
    response = auth_client.get(
        reverse(
            "trigger_action_view",
            kwargs={"campus_network_id": campus_network.id, "action_id": action.id},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failure"
    assert payload["reason"] == "No data configured"
    assert ActionHistory.objects.count() == 0


@pytest.mark.django_db
def test_delete_campus_type_blocks_when_networks_exist(
    auth_client, campus_type, campus_network
):
    response = auth_client.post(
        reverse("campustypedelete"),
        data={"campus_type_ids": str(campus_type.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert CampusType.objects.filter(id=campus_type.id).exists()
    assert CampusNetwork.objects.filter(id=campus_network.id).exists()
