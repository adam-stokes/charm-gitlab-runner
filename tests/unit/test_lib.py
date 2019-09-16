#!/usr/bin/python3
import subprocess
from mock import call


def test_pytest():
    assert True


def test_gitlabrunner(gitlabrunner):
    """ See if the helper fixture works to load charm configs """
    assert isinstance(gitlabrunner.charm_config, dict)
    assert isinstance(gitlabrunner.kv, object)


def test_upgrade(
    gitlabrunner,
    mock_apt_install,
    mock_apt_update,
    mock_get_distrib_codename,
    mock_add_source,
):
    gitlabrunner.upgrade()
    mock_apt_update.assert_called_once()
    mock_apt_install.assert_called_once()


def test_ensure_services(gitlabrunner, mock_service):
    gitlabrunner.ensure_services()
    assert mock_service.call_count == 0
    gitlabrunner.kv.set("registered", True)
    gitlabrunner.ensure_services()
    assert mock_service.call_count == 4
    mock_service.assert_has_calls(
        [
            call("enable", "docker"),
            call("start", "docker"),
            call("enable", "gitlab-runner"),
            call("start", "gitlab-runner"),
        ],
        any_order=True,
    )
    gitlabrunner.kv.set("registered", False)


def test_configure(
    gitlabrunner,
    mock_apt_install,
    mock_apt_update,
    mock_get_distrib_codename,
    mock_check_call,
    mock_add_source,
):
    gitlabrunner.configure()
    assert mock_apt_update.call_count == 1
    assert mock_apt_install.call_count == 1
    assert mock_check_call.call_count == 0
    gitlabrunner.gitlab_uri = "mocked-uri"
    gitlabrunner.gitlab_token = "mocked-token"
    gitlabrunner.hostname = "mocked-hostname"
    gitlabrunner.configure()
    assert mock_apt_update.call_count == 2
    assert mock_apt_install.call_count == 2
    test_command = [
        "/usr/bin/gitlab-runner",
        "register",
        "--non-interactive",
        "--url mocked-uri",
        "--registration-token mocked-token",
        "--name mocked-hostname",
        "--tag-list juju,docker",
        "--executor docker",
    ]
    mock_check_call.assert_called_once_with(test_command, stderr=subprocess.STDOUT)
