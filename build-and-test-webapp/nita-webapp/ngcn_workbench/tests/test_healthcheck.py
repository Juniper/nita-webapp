import importlib.util
import io
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError


HEALTHCHECK_PATH = Path(__file__).resolve().parents[3] / "healthcheck.py"
SPEC = importlib.util.spec_from_file_location("webapp_healthcheck", HEALTHCHECK_PATH)
healthcheck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(healthcheck)


def test_healthcheck_accepts_successful_response():
    with patch.object(healthcheck.urllib.request, "urlopen"):
        assert healthcheck.main() == 0


def test_healthcheck_treats_client_error_as_healthy():
    error = HTTPError(healthcheck.URL, 400, "Bad Request", {}, io.BytesIO())
    with patch.object(healthcheck.urllib.request, "urlopen", side_effect=error):
        assert healthcheck.main() == 0


def test_healthcheck_treats_server_error_as_unhealthy():
    error = HTTPError(healthcheck.URL, 503, "Service Unavailable", {}, io.BytesIO())
    with patch.object(healthcheck.urllib.request, "urlopen", side_effect=error):
        assert healthcheck.main() == 1


def test_healthcheck_reports_unreachable_server(capsys):
    with patch.object(
        healthcheck.urllib.request, "urlopen", side_effect=URLError("connection refused")
    ):
        assert healthcheck.main() == 1
    assert "healthcheck failed:" in capsys.readouterr().err
