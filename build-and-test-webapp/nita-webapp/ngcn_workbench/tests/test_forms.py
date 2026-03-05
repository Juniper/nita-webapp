import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from ngcn.forms import CampusTypeForm
from ngcn.forms import EditCampusTypeForm
from ngcn.models import CampusType


@pytest.mark.django_db
def test_campus_type_form_rejects_duplicate_zip_name(campus_type):
    form = CampusTypeForm(
        data={},
        files={
            "app_zip_file": SimpleUploadedFile("sample.zip", b"zip-content"),
        },
    )

    assert not form.is_valid()
    assert "app_zip_file" in form.errors


@pytest.mark.django_db
def test_edit_campus_type_form_rejects_non_zip_file(campus_type):
    form = EditCampusTypeForm(
        data={
            "name": campus_type.name,
            "description": campus_type.description,
        },
        files={
            "app_zip_file": SimpleUploadedFile("bad.txt", b"not-a-zip"),
        },
        instance=campus_type,
    )

    assert not form.is_valid()
    assert "app_zip_file" in form.errors


@pytest.mark.django_db
def test_edit_campus_type_form_accepts_valid_zip_with_unique_name(campus_type):
    CampusType.objects.filter(pk=campus_type.pk).update(app_zip_name="existing.zip")
    campus_type.refresh_from_db()

    form = EditCampusTypeForm(
        data={
            "name": campus_type.name,
            "description": campus_type.description,
        },
        files={
            "app_zip_file": SimpleUploadedFile("new_file.zip", b"zip-content"),
        },
        instance=campus_type,
    )

    assert form.is_valid()
