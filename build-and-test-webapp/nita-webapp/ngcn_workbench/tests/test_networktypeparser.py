import os
from textwrap import dedent
from zipfile import ZipFile

import pytest
from django.core.files.storage import default_storage
from ngcn.models import Action, ActionProperty, CampusType
from ngcn.networktypeparser import NetworkTypeParser


def _write_project_zip(
    tmp_path, zip_name, project_dir, project_yaml, include_ansible=True
):
    root_dir = tmp_path / project_dir
    root_dir.mkdir(parents=True)
    (root_dir / "project.yaml").write_text(project_yaml)
    if include_ansible:
        (root_dir / "ansible.cfg").write_text("[defaults]\n")

    zip_path = tmp_path / zip_name
    with ZipFile(zip_path, "w") as archive:
        for file_path in root_dir.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(tmp_path))
    return zip_path


@pytest.mark.django_db
def test_validate_zip_file_rejects_missing_project_yaml(tmp_path, monkeypatch):
    zip_path = _write_project_zip(
        tmp_path,
        "input.zip",
        "input",
        "name: sample_type\ndescription: Sample type\naction: []\n",
        include_ansible=True,
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(default_storage, "path", lambda name: name)

    with ZipFile(zip_path, "w") as archive:
        archive.writestr("input/ansible.cfg", "[defaults]\n")

    result = NetworkTypeParser().validateZipFile(zip_path.name)

    assert result["status"] is False
    assert result["message"] == "Cannot find the project.yaml file in the zip"


@pytest.mark.django_db
def test_validate_zip_file_rejects_missing_ansible_cfg(tmp_path, monkeypatch):
    project_yaml = dedent(
        """
        name: sample_type
        description: Sample type
        action: []
        """
    ).strip()
    zip_path = _write_project_zip(
        tmp_path,
        "input.zip",
        "input",
        project_yaml,
        include_ansible=False,
    )

    monkeypatch.setattr(
        default_storage,
        "path",
        lambda name: str(name) if os.path.isabs(str(name)) else str(tmp_path / name),
    )

    result = NetworkTypeParser().validateZipFile(zip_path.name)

    assert result["status"] is False
    assert result["message"] == "ansible.cfg is not present in the project directory"


@pytest.mark.django_db
def test_validate_zip_file_accepts_and_normalizes_nested_project(tmp_path, monkeypatch):
    project_yaml = dedent(
        """
        name: project_alpha
        description: Sample type
        action: []
        """
    ).strip()
    zip_path = _write_project_zip(
        tmp_path,
        "input.zip",
        "input",
        project_yaml,
        include_ansible=True,
    )

    monkeypatch.setattr(
        default_storage,
        "path",
        lambda name: str(name) if os.path.isabs(str(name)) else str(tmp_path / name),
    )

    result = NetworkTypeParser().validateZipFile(zip_path.name)

    assert result["status"] is True
    assert result["filename"] == "project_alpha.zip"


@pytest.mark.django_db
def test_validate_project_yaml_rejects_duplicate_campus_type(campus_type):
    project_yaml = dedent(
        f"""
        name: {campus_type.name}
        description: Sample type
        action:
          - name: run_test
            category: TEST
            jenkins_url: job-test
            configuration:
              shell_command: echo ok
              output_path: /tmp/out
        """
    ).strip()

    result = NetworkTypeParser().validateProjectYaml(project_yaml)

    assert campus_type.name in result
    assert result.endswith("already exists.")


@pytest.mark.django_db
def test_validate_project_yaml_rejects_missing_action_list():
    project_yaml = dedent(
        """
        name: sample_type
        description: Sample type
        action: []
        """
    ).strip()

    result = NetworkTypeParser().validateProjectYaml(project_yaml)

    assert result == "Invalid project.yaml file. Actions must not be must be empty"


@pytest.mark.django_db
def test_validate_project_yaml_rejects_test_action_without_output_path(
    action_category,
):
    project_yaml = dedent(
        """
        name: sample_type
        description: Sample type
        action:
          - name: run_test
            category: TEST
            jenkins_url: job-test
            configuration:
              shell_command: echo ok
              output_path: ""
        """
    ).strip()

    result = NetworkTypeParser().validateProjectYaml(project_yaml)

    assert (
        result
        == "Invalid output path. The output path must not be empty for the TEST jobs."
    )


@pytest.mark.django_db
def test_validate_project_yaml_rejects_unknown_category():
    project_yaml = dedent(
        """
        name: sample_type
        description: Sample type
        action:
          - name: run_test
            category: UNKNOWN
            jenkins_url: job-test
            configuration:
              shell_command: echo ok
              output_path: /tmp/out
        """
    ).strip()

    result = NetworkTypeParser().validateProjectYaml(project_yaml)

    assert result == "Invalid Action category name - UNKNOWN"


@pytest.mark.django_db
def test_update_network_type_details_on_db_creates_actions(
    action_category, build_action_category
):
    project_yaml = dedent(
        """
        name: sample_type
        description: Sample type
        action:
          - name: run_test
            category: TEST
            jenkins_url: job-test
            configuration:
              shell_command: echo ok
              output_path: /tmp/out
              custom_workspace: /custom/workspace
          - name: run_build
            category: BUILD
            jenkins_url: job-build
            configuration:
              shell_command: echo build
              custom_workspace: "  "
        """
    ).strip()

    parser = NetworkTypeParser()
    assert parser.updateNetworkTypeDetailsOnDB(project_yaml, "sample.zip") is True

    campus_type = CampusType.objects.get(name="sample_type")
    assert campus_type.description == "Sample type"
    assert campus_type.app_zip_name == "sample.zip"

    test_action = Action.objects.get(action_name="run_test")
    assert test_action.action_category.category_name == "TEST"
    assert test_action.action_property.output_path == "/tmp/out"
    assert test_action.action_property.custom_workspace == "/custom/workspace"

    build_action = Action.objects.get(action_name="run_build")
    assert build_action.action_category.category_name == "BUILD"
    assert build_action.action_property.output_path is None
    assert build_action.action_property.custom_workspace == ""

    assert ActionProperty.objects.count() == 2
