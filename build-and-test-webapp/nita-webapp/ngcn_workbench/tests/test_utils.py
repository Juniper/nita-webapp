from ngcn import utils


def test_wait_and_get_build_status_returns_true_when_build_succeeds(monkeypatch):
    statuses = [None, "None", "SUCCESS"]

    def fake_get_build_status(action_url, build_number):
        return statuses.pop(0)

    monkeypatch.setattr(utils, "getBuildStatus", fake_get_build_status)
    monkeypatch.setattr(utils, "sleep", lambda _seconds: None)

    assert utils.wait_and_get_build_status("job-name", 1) is True


def test_wait_and_get_build_status_returns_false_when_no_terminal_status(monkeypatch):
    monkeypatch.setattr(utils, "getBuildStatus", lambda *_args: None)
    monkeypatch.setattr(utils, "sleep", lambda _seconds: None)

    assert utils.wait_and_get_build_status("job-name", 1) is False
