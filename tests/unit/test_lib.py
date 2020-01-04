#!/usr/bin/python3
"""Unit test helper module functions."""
import subprocess

from mock import call


def test_pytest():
    """Verify pytest is working."""
    assert True


def test_gitlabrunner(gitlabrunner):
    """See if the helper fixture works to load charm configs."""
    assert isinstance(gitlabrunner.charm_config, dict)
    assert isinstance(gitlabrunner.kv, object)


def test_upgrade(
    gitlabrunner,
    mock_apt_install,
    mock_apt_update,
    mock_get_distrib_codename,
    mock_add_source,
):
    """Test the upgrade function."""
    gitlabrunner.upgrade()
    mock_apt_update.assert_called_once()
    mock_apt_install.assert_called_once()


def test_ensure_services(gitlabrunner, mock_service):
    """Test the ensure_services function of the helper module."""
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
    mock_get_distrib_codename,
    mock_check_call,
    mock_add_source,
):
    """Test the configure method called when the charm configured GitLab runner."""
    gitlabrunner.configure()
    assert mock_check_call.call_count == 0
    gitlabrunner.gitlab_uri = "mocked-uri"
    gitlabrunner.gitlab_token = "mocked-token"
    gitlabrunner.hostname = "mocked-hostname"
    gitlabrunner.configure()
    test_docker = [
        "/usr/bin/gitlab-runner",
        "register",
        "--non-interactive",
        "--url",
        "mocked-uri",
        "--registration-token",
        "mocked-token",
        "--name",
        "mocked-hostname-docker",
        "--tag-list",
        "docker",
        "--executor",
        "docker",
        "--docker-image",
        "ubuntu:latest",
    ]
    test_lxd = [
        "/usr/bin/gitlab-runner",
        "register",
        "--non-interactive",
        "--url",
        "mocked-uri",
        "--registration-token",
        "mocked-token",
        "--name",
        "mocked-hostname-lxd",
        "--tag-list",
        "lxd",
        "--executor",
        "custom",
        "--builds-dir",
        "/builds",
        "--cache-dir",
        "/cache",
        "--custom-run-exec",
        "/opt/lxd-executor/run.sh",
        "--custom-prepare-exec",
        "/opt/lxd-executor/prepare.sh",
        "--custom-cleanup-exec",
        "/opt/lxd-executor/cleanup.sh",
    ]
    calls = [call(test_docker, stderr=subprocess.STDOUT),
             call(test_lxd, stderr=subprocess.STDOUT),
             ]
    mock_check_call.assert_has_calls(calls)
    assert mock_check_call.call_count == 2


def test_setup_lxd(gitlabrunner, mock_check_call):
    """Test the setup_lxd function of the helper module."""
    gitlabrunner.setup_lxd()
    with open(gitlabrunner.executor_dir+"/base.sh", "r") as basefile:
        contents = basefile.read()
        assert "# /opt/lxd-executor/base.sh" in contents
    with open(gitlabrunner.executor_dir+"/prepare.sh", "r") as basefile:
        contents = basefile.read()
        assert "# /opt/lxd-executor/prepare.sh" in contents
    with open(gitlabrunner.executor_dir+"/run.sh", "r") as basefile:
        contents = basefile.read()
        assert "# /opt/lxd-executor/run.sh" in contents
    with open(gitlabrunner.executor_dir+"/cleanup.sh", "r") as basefile:
        contents = basefile.read()
        assert "# /opt/lxd-executor/cleanup.sh" in contents
    assert mock_check_call.call_count == 2
